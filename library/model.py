from enum import Enum
from pathlib import Path
from typing import Dict, Union, List, Literal

from pydantic import BaseModel, AnyHttpUrl, root_validator, validator


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
    search_module: str = ""


class HubConfig(BaseModel):
    enabled: bool = False
    url: AnyHttpUrl = "https://api.nullqwertyuiop.me/project-null"
    secret: str = ""
    meta: str = "/metadata"
    metadata: Union[None, HubMetadata] = None

    @root_validator()
    def hub_check(cls, values: dict):
        assert not (
            values.get("enabled", False) and values.get("secret", "") == ""
        ), "secret must be filled when hub is enabled"
        if not values.get("enabled", False):
            values["metadata"] = None
        elif values.get("metadata") is None:
            values["metadata"] = HubMetadata()
        return values


class PathConfig(BaseModel):
    root: Path = Path(__file__).parent.parent
    # config: Path = Path(root / "config")
    data: Path = Path(root / "data")

    @root_validator()
    def path_check(cls, values: dict):
        # values.get("config").mkdir(parents=True, exist_ok=True)
        values.get("data").mkdir(parents=True, exist_ok=True)
        return values


class FunctionConfig(BaseModel):
    default: bool = False
    modules: Dict[str, dict] = {}


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

    @root_validator()
    def config_check(cls, value: dict):
        if value.get("link", None).startswith("mysql+aiomysql://") and not value.get(
            "config", None
        ):
            value["config"] = MySQLConfig()
        elif value.get("link", None).startswith(
            "sqlite+aiosqlite:///data/data.db"
        ) and value.get("config", None):
            value["config"] = None
        return value


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
        assert value, "empty field found"
        return value


class UserPerm(Enum):
    MEMBER = "MEMBER"
    ADMINISTRATOR = "ADMINISTRATOR"
    OWNER = "OWNER"
    BOT_OWNER = "BOT_OWNER"

    def __lt__(self, other: "UserPerm"):
        lv_map = {
            UserPerm.MEMBER: 1,
            UserPerm.ADMINISTRATOR: 2,
            UserPerm.OWNER: 3,
            UserPerm.BOT_OWNER: 4,
        }
        return lv_map[self] < lv_map[other]


class Module(BaseModel):
    name: str = "Unknown"
    pack: str
    version: str = "Unknown"
    author: List[str] = ["Unknown"]
    pypi: bool = False
    db: bool = False
    category: Literal["utility", "entertainment", "misc"] = "misc"
    description: str = ""
    dependency: List[str] = None
    installed: bool = False

    @validator("category", pre=True)
    def category_validator(cls, category: str):
        if category.startswith("util"):
            category = "utility"
        elif category.startswith("enter"):
            category = "entertainment"
        return category
