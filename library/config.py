import json
from pathlib import Path
from typing import NoReturn, List, Union

from loguru import logger
from pydantic import BaseModel
from pydantic.networks import AnyHttpUrl


class EssentialConfig(BaseModel):
    name: str = ""
    num: int = 0
    account: int = 0
    host: AnyHttpUrl = ""
    verify_key: str = ""
    dev_group: List[int] = []
    owners: List[int] = []


class HubMetadata(BaseModel):
    authorize: str = ""
    get_me: str = ""
    get_bot_list: str = ""
    heartbeat: str = ""
    notified_missing: str = ""
    online_event: str = ""
    offline_event: str = ""
    register_bot: str = ""
    metadata: str = ""
    announcement: str = ""


class HubConfig(BaseModel):
    enabled: bool = False
    url: AnyHttpUrl = "https://api.nullqwertyuiop.me/project-null"
    secret: str = ""
    meta: str = "/metadata"
    metadata: HubMetadata = HubMetadata()


class PathConfig(BaseModel):
    root: Path = Path(__file__).parent.parent
    config: Path = Path(root / "config")
    data: Path = Path(root / "data")


class FunctionConfig(BaseModel):
    default: bool = False


class MySQLConfig(BaseModel):
    disable_pooling: bool = False
    pool_size: int = 40
    max_overflow: int = 60


class DatabaseConfig(BaseModel):
    link: str = ""
    config: Union[None, MySQLConfig] = None


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
        logger.success('Modify "essential" field in config.json to continue')
        exit(-1)
    with open(Path(__file__).parent.parent / "config.json", "r", encoding="utf-8") as _:
        return Config(**json.loads(_.read()))


def config_check() -> NoReturn:
    if any([
        not config.essential.name,
        not config.essential.account,
        not config.essential.host,
        not config.essential.verify_key,
        (config.hub.enabled
         and not config.hub.secret)
    ]):
        logger.critical("Unchanged essential value found in config.json")
        exit(-1)


config: Config = load_config()
config_check()
save_config(config)
