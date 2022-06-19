import json
from pathlib import Path
from typing import NoReturn, Dict, Union

from graia.ariadne.model import Group
from loguru import logger
from pydantic import BaseModel

from library.model import Config


def save_config(cfg: Config) -> NoReturn:
    with (Path(__file__).parent.parent / "config.json").open(
        "w", encoding="utf-8"
    ) as _:
        _.write(cfg.json(indent=4, ensure_ascii=False))


def load_config() -> Config:
    if not (Path(__file__).parent.parent / "config.json").exists():
        save_config(Config())
        logger.success("Created config.json using initial values")
        logger.success("Modify essential fields in config.json to continue")
        exit(-1)
    with (Path(__file__).parent.parent / "config.json").open(
        "r", encoding="utf-8"
    ) as _:
        return Config(**json.loads(_.read()))


def reload_config() -> NoReturn:
    global config
    config = load_config()


config: Config = load_config()
save_config(config)


def get_module_config(module: str, key: str = None):
    if module_cfg := config.func.modules.get(module, None):
        return module_cfg.get(key, None) if key else module_cfg


def update_module_config(module: str, cfg: Union[dict, BaseModel] = None):
    if isinstance(cfg, BaseModel):
        cfg = cfg.dict()
    config.func.modules[module] = cfg
    save_config(config)


class Switch:
    __switch: dict = Dict[str, Dict[str, bool]]

    def __init__(self):
        self.load()

    def load(self) -> NoReturn:
        if not Path(config.path.data, "switch.json").is_file():
            self.write()
            self.__switch = {}
        with Path(config.path.data, "switch.json").open("r", encoding="utf-8") as f:
            self.__switch = json.loads(f.read())

    def write(self) -> NoReturn:
        with Path(config.path.data, "switch.json").open("w", encoding="utf-8") as f:
            f.write(json.dumps(self.__switch, indent=4, ensure_ascii=False))

    def get(self, pack: str, group: Union[Group, int, str, None]) -> Union[None, bool]:
        if isinstance(group, Group):
            group = str(group.id)
        elif isinstance(group, int):
            group = str(group)
        elif group is None:
            group = "0"
        if module := self.__switch.get(pack, None):
            return module.get(group, None)
        return None

    def update(self, pack: str, group: Union[Group, int, str], value: bool):
        if isinstance(group, Group):
            group = str(group.id)
        elif isinstance(group, int):
            group = str(group)
        if pack in self.__switch.keys():
            self.__switch[pack][group] = value
            self.write()
            return
        self.__switch[pack] = {group: value}
        self.write()
        return


switch = Switch()
