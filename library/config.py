import json
from pathlib import Path
from typing import NoReturn, List, Union, Dict

from loguru import logger
from pydantic import BaseModel, validator, root_validator
from pydantic.networks import AnyHttpUrl


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
    module_metadata: str = ""
    download_module: str = ""


class HubConfig(BaseModel):
    enabled: bool = False
    url: AnyHttpUrl = "https://api.nullqwertyuiop.me/project-null"
    secret: str = ""
    meta: str = "/metadata"
    metadata: HubMetadata = HubMetadata()

    @root_validator()
    def hub_check(cls, values: dict):
        assert not (
            values.get("enabled", False) and values.get("secret", "") == ""
        ), "secret must be filled when hub is enabled"
        return values


class PathConfig(BaseModel):
    root: Path = Path(__file__).parent.parent
    config: Path = Path(root / "config")
    data: Path = Path(root / "data")

    @root_validator()
    def path_check(cls, values: dict):
        values.get("config").mkdir(parents=True, exist_ok=True)
        values.get("data").mkdir(parents=True, exist_ok=True)
        return values


class FunctionConfig(BaseModel):
    default: bool = False
    modules: Dict[str, Dict[int, bool]] = {}


class MySQLConfig(BaseModel):
    disable_pooling: bool = False
    pool_size: int = 40
    max_overflow: int = 60

    @root_validator()
    def mysql_check(cls, value: dict):
        assert not all(
            [
                value.get("pool_size", 0) + value.get("max_overflow", 0) <= 0,
                not value.get("disable_pooling"),
            ]
        ), "pool_size and max_overflow must be greater than 0 if enabled pooling"
        return value


class DatabaseConfig(BaseModel):
    link: str = "sqlite+aiosqlite:///data/data.db"
    config: Union[None, MySQLConfig] = None

    @validator("link")
    def check_link(cls, link: str):
        example = (
            "Example:\n"
            "MySQL:\tmysql+aiomysql://user:password@localhost:3306/database\n"
            "SQLite:\tsqlite+aiosqlite:///data/data.db"
        )
        assert link != "", f"Database link can't be blank\n{example}"
        assert any(
            [
                link.startswith("mysql+aiomysql://"),
                link.startswith("sqlite+aiosqlite://"),
            ]
        ), f"Only MySQL and SQLite is supported.\n{example}"
        return link


class Config(BaseModel):
    name: str = ""
    num: int = 0
    account: int = 0
    host: AnyHttpUrl = ""
    verify_key: str = ""
    dev_group: List[int] = []
    owners: List[int] = []
    proxy: str = None
    db: DatabaseConfig = DatabaseConfig()
    func: FunctionConfig = FunctionConfig()
    path: PathConfig = PathConfig()
    hub: HubConfig = HubConfig()

    @validator("name", "account", "verify_key")
    def config_check(cls, value):
        assert value, f"empty field found"
        return value


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
