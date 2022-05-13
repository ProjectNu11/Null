import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import List, NoReturn, Union

from loguru import logger
from pydantic import ValidationError

from library.model import Module


def read_and_update_metadata(file: Path, is_dir: bool = False) -> Module:
    metadata_dir = (
        (file / "metadata.json")
        if is_dir
        else (file.parent / f"{file.stem}-metadata.json")
    )
    req_dir = (
        (file / "requirements.txt")
        if is_dir
        else (file.parent / f"{file.stem}-requirements.txt")
    )
    module = None
    try:
        with metadata_dir.open("r", encoding="utf-8") as f:
            content = json.loads(f.read())
            module = Module(**content)
    except (ValidationError, JSONDecodeError, FileNotFoundError):
        logger.error(f"Validation failed for module/{file.stem}")
        module = Module(
            name=file.stem,
            pack=f"module.{file.stem}",
            pypi=req_dir.is_file(),
        )
    finally:
        if module:
            write_metadata(metadata_dir, module)
            return module


def write_metadata(file: Path, module: Module) -> NoReturn:
    with file.open("w", encoding="utf-8") as f:
        f.write(module.json(exclude={"installed"}, indent=4, ensure_ascii=False))


def load_metadata() -> List[Module]:
    metadata = []
    for path in Path(os.path.dirname(__file__)).iterdir():
        if path.name.startswith("_"):
            continue
        if module := read_and_update_metadata(path, path.is_dir()):
            metadata.append(module)
    return metadata


__all__: List[Module] = load_metadata()


def remove_module_index(pack: str):
    global __all__
    __all__ = list(filter(lambda x: x.pack != pack, __all__))


def add_module_index(module: Module):
    __all__.append(module)


def get_module(name: str) -> Union[None, Module]:
    if module := list(
        filter(
            lambda x: any(
                [
                    name.lower()
                    in (
                        x.name.lower(),
                        x.name.lower().split(".", maxsplit=1)[-1],
                    ),
                    name.lower()
                    in (
                        x.pack.lower(),
                        x.pack.lower().split(".", maxsplit=1)[-1],
                    ),
                ]
            ),
            __all__,
        )
    ):
        return module[0]
