import asyncio
import contextlib
import os
import shutil
import traceback
from asyncio import Lock
from pathlib import Path
from typing import Union, List, NoReturn, Optional

from graia.ariadne.message.chain import MessageChain
from graia.saya import Saya
from loguru import logger

from library.model import Module
from library.orm import db_init
from library.util.dependency import async_install_dependency
from module import modules, ModuleMetadata
from .uninstall import uninstall_module
from ..util import hs

saya = Saya.current()

install_lock = Lock()
module_dir = Path(Path().resolve(), "module")


async def install_module(
    name: str,
    upgrade: bool,
    version: str = "",
    *,
    is_dependency: bool = False,
) -> Union[str, MessageChain]:
    if pre_install := await pre_installation(name, upgrade):
        return pre_install
    if not (data_bytes := await hs.download_module(name=name, version=version)):
        return "无法找到符合要求的插件" if is_dependency else MessageChain("无法找到符合要求的插件")
    msg = []
    cache_dir = Path(Path(__file__).parent.parent, "__cache__")
    if is_dependency:
        cache_dir = Path(cache_dir, f"__dependency_{name}__")
    try:
        if not is_dependency:
            await install_lock.acquire()
        await async_prepare_cache(cache_dir, name, data_bytes)
        module = await find_and_install(cache_dir)
        await post_installation(module)
        msg.append(f"成功安装插件 {name}\n已安装版本：{module.version}")
    except Exception as e:
        msg.append(f"安装插件 {name} 时发生错误：\n{e}")
        logger.error(traceback.format_exc())
    finally:
        shutil.rmtree(cache_dir)
        if not is_dependency:
            install_lock.release()
        text = "\n===============\n".join(msg)
        return text if is_dependency else MessageChain(text)


async def pre_installation(name: str, upgrade: bool) -> Optional[MessageChain]:
    if not (module := modules.get(name)):
        return
    if not upgrade:
        return MessageChain(f"已安装插件 {name}，将不会作出改动\n已安装版本：{module.version}")
    if chn := saya.channels.get(module.pack, None):
        modules.remove(module.pack)
        saya.uninstall_channel(chn)
        return


def prepare_cache(cache_dir: Path, name: str, data: bytes) -> NoReturn:
    cache_dir.mkdir(exist_ok=True)
    with Path(cache_dir, f"{name}.zip").open("wb") as f:
        f.write(data)
    shutil.unpack_archive(
        Path(cache_dir, f"{name}.zip"),
        cache_dir,
    )
    Path(cache_dir, f"{name}.zip").unlink(missing_ok=True)


async def async_prepare_cache(cache_dir: Path, name: str, data: bytes) -> NoReturn:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, prepare_cache, cache_dir, name, data)


async def find_and_install(cache_dir: Path) -> Module:
    for path in cache_dir.iterdir():
        if path.is_dir():
            if (
                path.stem.startswith("_")
                or path.name in ["README.md", "LICENSE", "metadata.json"]
                or path.name.startswith(".")
            ):
                continue
            module = ModuleMetadata.read_and_update(path, path.is_dir())
            await resolve_dependency(module, path)
            await async_move_module(path)
            return module


async def resolve_dependency(module: Module, path: Path) -> List[str]:
    msg = []
    if module.pypi and Path(path, "requirements.txt").is_file():
        await async_install_dependency(
            requirements=Path(path, "requirements.txt").read_text().splitlines()
        )
    if module.dependency:
        for dependency in module.dependency:
            logger.info(f"Installing dependency: {dependency}")
            msg.append(
                await install_module(
                    dependency,
                    upgrade=True,
                    is_dependency=True,
                )
            )
    return msg


def move_module(path: Path) -> NoReturn:
    path_name = path.name.replace("-", "_").strip("_")
    if path.name != path_name:
        os.rename(path, Path(path.parent, path_name))
    with contextlib.suppress(FileNotFoundError):
        uninstall_module(path=Path(module_dir, path_name))
    shutil.move(
        os.path.join(Path(path.parent, path_name)),
        os.path.join(module_dir),
    )


async def async_move_module(path: Path) -> NoReturn:
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, move_module, path)


async def post_installation(module: Module) -> NoReturn:
    with saya.module_context():
        saya.require(module.pack)
        await db_init()
    module.loaded = True
    modules.add(module)
