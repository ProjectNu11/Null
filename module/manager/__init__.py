import asyncio
import os
import shutil
from asyncio import Lock
from datetime import datetime, timedelta
from pathlib import Path
from typing import NoReturn, Union, List

from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, ForwardNode, Forward
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    MatchResult,
    ArgumentMatch,
    ArgResult,
    WildcardMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from pip import main as pip
from sqlalchemy.exc import InternalError, ProgrammingError

from library.config import config, get_switch, update_switch
from library.depend import Permission
from library.model import UserPerm, Module
from library.orm import orm
from module import (
    remove_module_index,
    read_and_update_metadata,
    get_module,
    add_module_index,
)

try:
    from module.hub_service.exception import HubServiceNotEnabled
    from module.hub_service import hs
except HubServiceNotEnabled:
    hs = None

saya = Saya.current()
channel = Channel.current()
install_lock = Lock()

channel.name("ModuleManager")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(".plugin", "插件"),
                    UnionMatch(
                        "install",
                        "uninstall",
                        "load",
                        "reload",
                        "unload",
                        "info",
                        "list",
                        "search",
                        "upgrade",
                        "安装",
                        "删除",
                        "加载",
                        "重载",
                        "卸载",
                        "详情",
                        "枚举",
                        "搜索",
                        "升级",
                    )
                    @ "function",
                    UnionMatch("-u", "--upgrade", optional=True) @ "upgrade",
                    WildcardMatch(optional=True) @ "name",
                    ArgumentMatch("-c", "--category", optional=True) @ "category",
                    ArgumentMatch("-a", "--author", optional=True) @ "author",
                ]
            )
        ],
        decorators=[
            Permission.require(
                UserPerm.BOT_OWNER, MessageChain("权限不足，你需要来自 所有人 的权限才能进行本操作")
            )
        ],
    )
)
async def module_manager_owner(
    app: Ariadne,
    event: MessageEvent,
    function: MatchResult,
    upgrade: MatchResult,
    name: ArgResult,
    category: ArgResult,
    author: ArgResult,
):
    function: str = function.result.asDisplay()
    if not hs and function in ("install", "search", "upgrade", "安装", "搜索", "升级"):
        return await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"HubService 未启用，无法使用 {function}"),
        )
    upgrade: bool = upgrade.matched
    name: Union[List[str], str] = str(name.result) if name.matched else ""
    category: str = str(category.result) if category.matched else ""
    author: str = str(author.result) if author.matched else ""
    msg = None
    if function in ("search", "搜索"):
        msg = await search(name=name, category=category, author=author)
    elif function in ("install", "安装"):
        name = name.split()
        for mod_name in name:
            await app.sendMessage(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                await install_module(name=mod_name, upgrade=upgrade, version=""),
            )
        return
    elif function in ("load", "加载"):
        msg = await load_module(name=name)
    elif function in ("reload", "重载"):
        msg = await reload_module(name=name)
    elif function in ("unload", "卸载"):
        msg = await unload_module(name=name)
    elif function in ("uninstall", "删除"):
        pass
    elif function in ("upgrade", "升级"):
        msg = await upgrade_module()
    if msg:
        await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender, msg
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(".plugin", "插件"),
                    UnionMatch(
                        "list", "enable", "disable", "列表", "枚举", "开启", "打开", "禁用", "关闭"
                    )
                    @ "func",
                    WildcardMatch() @ "param",
                ]
            )
        ],
        decorators=[
            Permission.require(
                UserPerm.ADMINISTRATOR,
                MessageChain("权限不足，你需要来自 管理员 的权限才能进行本操作"),
            )
        ],
    )
)
async def module_manager_admin(
    app: Ariadne, event: MessageEvent, func: MatchResult, param: MatchResult
):
    func = func.result.asDisplay()
    param = param.result.asDisplay().strip().split()
    msg = None
    if func in ("list", "枚举"):
        msg = await list_module(
            event.sender.group.id if isinstance(event, GroupMessage) else None
        )
    elif func in ("enable", "开启", "打开", "disable", "禁用", "关闭") and isinstance(
        event, GroupMessage
    ):
        msg = module_switch(
            param,
            event.sender.group.id,
            False if func in ("disable", "禁用", "关闭") else True,
        )
    if msg:
        await app.sendMessage(
            event.sender.group if isinstance(event, GroupMessage) else event.sender, msg
        )


def module_switch(modules: list, group: int, value: bool) -> MessageChain:
    success_count = 0
    failed = []
    for name in modules:
        if module := get_module(name):
            if module.pack == channel.module:
                failed.append(name)
                continue
            update_switch(pack=module.pack, group=group, value=value)
            success_count += 1
        else:
            failed.append(name)
    msg = MessageChain(f"已{'开启' if value else '关闭'} {success_count} 个插件")
    if failed:
        msg += MessageChain(f"\n以下 {len(failed)} 个插件无法找到或无法改动：")
        for fail in failed:
            msg += MessageChain(f"\n - {fail}")
    return msg


async def search(name: str, category: str, author: str) -> MessageChain:
    if modules := await hs.search_module(name=name, category=category, author=author):
        fwd_node_list = [
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now(),
                message=MessageChain(f"查询到 {len(modules)} 个插件"),
            )
        ]
        for index, module in enumerate(modules):
            module_category = (
                "实用工具"
                if module.category == "utility"
                else "娱乐"
                if module.category == "entertainment"
                else "其他"
            )
            module_dependency = (
                ", ".join(module.dependency) if module.dependency else "无"
            )
            fwd_node_list += [
                ForwardNode(
                    target=config.account,
                    name=f"{config.name}#{config.num}",
                    time=datetime.now() + timedelta(seconds=15) * (index + 1),
                    message=MessageChain(
                        f"{index + 1}. {module.name}"
                        f"\n - 包名：{module.pack}"
                        f"\n - 版本：{module.version}"
                        f"\n - 作者：{', '.join(module.author)}"
                        f"\n - 分类：{module_category}"
                        f"\n - 描述：{module.description}"
                        f"\n - 依赖：{module_dependency}"
                        f"\n - Pypi：{'是' if module.pypi else '否'}"
                    ),
                )
            ]
        return MessageChain.create([Forward(nodeList=fwd_node_list)])
    else:
        return MessageChain(f"无法找到符合要求的插件")


async def list_module(group: int = None) -> MessageChain:
    reload_metadata()

    from module import __all__ as modules

    enabled = list(filter(lambda x: x.installed, modules))
    disabled = list(filter(lambda x: not x.installed, modules))
    fwd_node_list = [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now(),
            message=MessageChain.create(
                [
                    Plain(text=f"已安装 {len(modules)} 个插件"),
                    Plain(text="\n==============="),
                    Plain(text=f"\n已加载 {len(enabled)} 个插件") if enabled else None,
                    Plain(text=f"\n未加载 {len(disabled)} 个插件") if disabled else None,
                ]
            ),
        )
    ]
    for index, module in enumerate(enabled + disabled):
        module_category = (
            "实用工具"
            if module.category == "utility"
            else "娱乐"
            if module.category == "entertainment"
            else "其他"
        )
        module_dependency = ", ".join(module.dependency) if module.dependency else "无"
        if group:
            if module.pack != channel.module:
                switch = get_switch(module.pack, group) and module.installed
            else:
                switch = True
            switch_status = f"\n - 开关：{'已' if switch else '未'}开启"
        else:
            switch_status = ""
        fwd_node_list.append(
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=15) * (index + 1),
                message=MessageChain(
                    f"{index + 1}. {module.name}"
                    f"\n - 包名：{module.pack}"
                    f"\n - 版本：{module.version}"
                    f"\n - 作者：{', '.join(module.author)}"
                    f"\n - 分类：{module_category}"
                    f"\n - 描述：{module.description}"
                    f"\n - 依赖：{module_dependency}"
                    f"\n - 状态：{'已' if module.installed else '未'}安装"
                    f"{switch_status}"
                ),
            )
        )
    return MessageChain.create([Forward(nodeList=fwd_node_list)])


async def install_module(
    name: str,
    upgrade: bool,
    version: str = "",
    *,
    is_dependency: bool = False,
) -> Union[str, MessageChain]:
    if module := get_module(name):
        if not upgrade:
            return MessageChain(f"已安装插件 {name}，将不会作出改动\n已安装版本：{module.version}")
        elif chn := saya.channels.get(module.pack, None):
            remove_module_index(module.pack)
            saya.uninstall_channel(chn)
    if data_bytes := await hs.download_module(name=name, version=version):
        msg = []
        cache_dir = Path(__file__).parent.parent / "__cache__"
        if is_dependency:
            cache_dir = cache_dir / "__dependency__"
        module_dir = Path(__file__).parent.parent
        try:
            if not is_dependency:
                await install_lock.acquire()
            cache_dir.mkdir(exist_ok=True)
            with (cache_dir / f"{name}.zip").open("wb") as f:
                f.write(data_bytes)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                shutil.unpack_archive,
                cache_dir / f"{name}.zip",
                cache_dir,
            )
            (cache_dir / f"{name}.zip").unlink(missing_ok=True)
            ignore_list = ["README.md", "LICENSE", "metadata.json"]
            for path in cache_dir.iterdir():
                if path.is_dir():
                    if (
                        path.stem.startswith("_")
                        or path.name in ignore_list
                        or path.name.startswith(".")
                    ):
                        continue
                    module = read_and_update_metadata(path, path.is_dir())
                    if module.pypi:
                        await loop.run_in_executor(
                            None,
                            pip,
                            [
                                "install",
                                "-r",
                                str(path / "requirements.txt"),
                            ],
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
                    path_name = path.name.replace("-", "_").strip("_")
                    if path.name != path_name:
                        os.rename(path, path.parent / path_name)
                    if (module_dir / path_name).is_file():
                        (module_dir / path_name).unlink(missing_ok=True)
                    elif (module_dir / path_name).is_dir():
                        shutil.rmtree(module_dir / path_name)
                    shutil.move(
                        os.path.join(path.parent / path_name),
                        os.path.join(module_dir),
                    )
                    break
            with saya.module_context():
                saya.require(module.pack)
                if module.db:
                    await db_init()
            module.installed = True
            add_module_index(module)
            msg.append(f"成功安装插件 {name}\n已安装版本：{module.version}")
        except Exception as e:
            msg.append(f"安装插件 {name} 时发生错误：\n{e}")
        finally:
            shutil.rmtree(cache_dir)
            if not is_dependency:
                install_lock.release()
            text = "\n===============\n".join(msg)
            return MessageChain(text) if not is_dependency else text
    return MessageChain("无法找到符合要求的插件") if not is_dependency else "无法找到符合要求的插件"


async def load_module(name: str) -> MessageChain:
    reload_metadata()
    if module := get_module(name):
        try:
            with saya.module_context():
                saya.require(module.pack)
                if module.db:
                    await db_init()
                saya.require(module.pack)
            module.installed = True
            return MessageChain(f"已加载插件 {name}")
        except Exception as e:
            return MessageChain(f"加载插件 {name} 时发生错误：\n{e}")
    return MessageChain(f"无法找到插件 {name}")


async def unload_module(name: str) -> MessageChain:
    reload_metadata()
    if module := get_module(name):
        if chn := saya.channels.get(module.pack, None):
            module.installed = False
            saya.uninstall_channel(chn)
            return MessageChain(f"已卸载插件 {name}")
    return MessageChain(f"无法找到插件 {name}")


async def reload_module(name: str) -> MessageChain:
    await unload_module(name)
    return await load_module(name)


async def upgrade_module() -> MessageChain:
    reload_metadata()
    from module import __all__

    msg = []
    for mod in list(__all__):
        if modules := await hs.search_module(name=mod.pack):
            if modules[0].version == mod.version:
                continue
            msg.append(
                await install_module(
                    name=mod.pack, version=modules[0].version, upgrade=True
                )
            )
        continue
    if msg:
        fwd_node_list = [
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now(),
                message=MessageChain(f"已更新 {len(msg)} 个插件"),
            )
        ] + [
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=15) * (index + 1),
                message=msg_chain,
            )
            for index, msg_chain in enumerate(msg)
        ]
        return MessageChain.create([Forward(nodeList=fwd_node_list)])
    return MessageChain("暂无更新可用")


def reload_metadata() -> NoReturn:
    from module import __all__

    saya_modules = list(saya.channels.keys())
    enabled = []
    for mod in saya_modules:
        if _mod := get_module(mod):
            enabled.append(_mod)
            continue
        enabled.append(
            Module(name=mod.split(".", maxsplit=1)[-1], pack=mod, installed=True)
        )
    disabled = list(filter(lambda x: not x.installed, __all__))
    for path in Path(__file__).parent.parent.iterdir():
        if (
            path.name.startswith("_")
            or (path.is_file() and not path.name.endswith(".py"))
            or f"module.{path.stem}" in [x.pack for x in enabled + disabled]
        ):
            continue
        disabled.append(
            Module(name=path.stem, pack=f"module.{path.stem}", installed=False)
        )
    __all__.clear()
    for mod in enabled + disabled:
        __all__.append(mod)


async def db_init():
    try:
        await orm.init_check()
    except (AttributeError, InternalError, ProgrammingError):
        await orm.create_all()


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def init():
    await db_init()
