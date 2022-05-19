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
        if key:
            return module_cfg.get(key, None)
        return module_cfg


def update_module_config(module: str, cfg: Union[dict, BaseModel] = None):
    if isinstance(cfg, BaseModel):
        cfg = cfg.dict()
    config.func.modules[module] = cfg
    save_config(config)


def read_switch() -> Dict[str, Dict[str, bool]]:
    if not (config.path.data / "switch.json").is_file():
        write_switch({})
        return {}
    with (config.path.data / "switch.json").open("r", encoding="utf-8") as f:
        return json.loads(f.read())


def write_switch(s: Dict[str, Dict[str, bool]]) -> NoReturn:
    with (config.path.data / "switch.json").open("w", encoding="utf-8") as f:
        f.write(json.dumps(s, indent=4, ensure_ascii=False))


def get_switch(pack: str, group: Union[Group, int, str]) -> Union[None, bool]:
    if isinstance(group, Group):
        group = str(group.id)
    elif isinstance(group, int):
        group = str(group)
    if module := switch.get(pack, None):
        return module.get(group, False)
    return None


def update_switch(pack: str, group: Union[Group, int, str], value: bool):
    if isinstance(group, Group):
        group = str(group.id)
    elif isinstance(group, int):
        group = str(group)
    if pack in switch.keys():
        switch[pack][group] = value
        write_switch(switch)
        return
    switch[pack] = {group: value}
    write_switch(switch)
    return


switch: dict = read_switch()
