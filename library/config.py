import json
from pathlib import Path
from typing import NoReturn, List

from loguru import logger
from pydantic import BaseModel
from pydantic.networks import AnyHttpUrl


class EssentialConfig(BaseModel):
    name: str = ""
    account: int = 0
    host: AnyHttpUrl = ""
    verify_key: str = ""


class HubConfig(BaseModel):
    enable: bool = True
    url: List[AnyHttpUrl] = ["https://api.nullqwertyuiop.me"]
    secret: List[str] = [""]
    token: List[str] = [""]
    auth: List[str] = ["/project-null/authorize"]
    metadata: List[str] = ["/project-null/metadata"]


class PathConfig(BaseModel):
    root: Path = Path(__file__).parent.parent
    config: Path = Path(root / "config")
    data: Path = Path(root / "data")


class FunctionConfig(BaseModel):
    default: bool = False


class DatabaseConfig(BaseModel):
    link: str = ""
    disable_pooling: bool = False
    pool_size: int = 40
    max_overflow: int = 60


class Config(BaseModel):
    essential: EssentialConfig = EssentialConfig()
    hub: HubConfig = HubConfig()
    path: PathConfig = PathConfig()
    func: FunctionConfig = FunctionConfig()
    db: DatabaseConfig = DatabaseConfig()


PathConfig().config.mkdir(parents=True, exist_ok=True)
PathConfig().data.mkdir(parents=True, exist_ok=True)


def save_config(cfg: Config) -> NoReturn:
    with open(Path(__file__).parent.parent / "config.json", "w", encoding="utf-8") as _:
        _.write(cfg.json(indent=4, ensure_ascii=False))


def load_config() -> Config:
    if not (Path(__file__).parent.parent / "config.json").exists():
        save_config(Config())
        logger.success("Created config.json using initial values")
        logger.success("Modify \"essential\" field in config.json to continue")
        exit(-1)
    with open(Path(__file__).parent.parent / "config.json", "r", encoding="utf-8") as _:
        return Config(**json.loads(_.read()))


config: Config = load_config()


def config_check() -> NoReturn:
    if any([
        not config.essential.name,
        not config.essential.account,
        not config.essential.host,
        not config.essential.verify_key
    ]):
        logger.critical("Unchanged essential value found in config.json")
        exit(-1)
