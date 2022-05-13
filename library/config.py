import json
from pathlib import Path
from typing import NoReturn

from loguru import logger

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


config: Config = load_config()
save_config(config)


def get_module_config(module: str, key: str = None):
    if module_cfg := config.func.modules.get(module, None):
        if key:
            return module_cfg.get(key, None)
        return module_cfg


def update_module_config(module: str, cfg: dict = None):
    config.func.modules[module] = cfg
    save_config(config)
