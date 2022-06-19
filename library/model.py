from enum import Enum
from pathlib import Path
from typing import Dict, Union, List, Literal

from pydantic import BaseModel, AnyHttpUrl, root_validator, validator


class HubMetadata(BaseModel):
    """
    Metadata for hub.
    """

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
    """
    Configuration for hub.
    """

    enabled: bool = False
    url: AnyHttpUrl = "https://api.nullqwertyuiop.me/project-null"
    secret: str = ""
    meta: str = "/metadata"
    metadata: Union[None, HubMetadata] = None

    @root_validator()
    def hub_check(cls, values: dict):
        assert not (
            values.get("enabled", False) and values.get("secret", "") == ""
        ), "Hub config is enabled but secret is not set"
        if not values.get("enabled", False):
            values["metadata"] = None
        elif values.get("metadata") is None:
            values["metadata"] = HubMetadata()
        return values


class PathConfig(BaseModel):
    """
    Configuration for path.
    """

    root: Path = Path(__file__).parent.parent
    data: Path = Path(root / "data")

    @root_validator()
    def path_check(cls, values: dict):
        values.get("data").mkdir(parents=True, exist_ok=True)
        return values


class FunctionConfig(BaseModel):
    """
    Configuration for function.
    """

    default: bool = False
    modules: Dict[str, dict] = {}


class MySQLConfig(BaseModel):
    """
    Configuration for MySQL.
    """

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
        ), "pool_size and max_overflow must be positive when pooling is disabled"
        return value


class DatabaseConfig(BaseModel):
    """
    Configuration for database.
    """

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
    """
    Configuration for project.
    """

    name: str = ""
    num: int = 0
    account: int = 0
    env: str = ""
    host: AnyHttpUrl = ""
    verify_key: str = ""
    dev_group: List[int] = []
    owners: List[int] = []
    proxy: str = None
    log_retention: Union[None, int] = 7
    db: DatabaseConfig = DatabaseConfig()
    func: FunctionConfig = FunctionConfig()
    path: PathConfig = PathConfig()
    hub: HubConfig = HubConfig()

    @validator("name", "account", "verify_key")
    def config_check(cls, value):
        assert value, "name, account and verify_key can't be blank"
        return value

    @validator("env")
    def env_check(cls, value):
        assert value in ["pip", "poetry"], "env must be pip or poetry"
        return value


class UserPerm(Enum):
    """
    User permission.
    """

    MEMBER = ("MEMBER", 1)
    ADMINISTRATOR = ("ADMINISTRATOR", 2)
    OWNER = ("OWNER", 3)
    BOT_OWNER = ("BOT_OWNER", 4)

    def __lt__(self, other: "UserPerm"):
        return self.value[1] < other.value[1]

    def __le__(self, other: "UserPerm"):
        return self.value[1] <= other.value[1]

    def __eq__(self, other: "UserPerm"):
        return self.value[1] == other.value[1]

    def __gt__(self, other: "UserPerm"):
        return self.value[1] > other.value[1]

    def __ge__(self, other: "UserPerm"):
        return self.value[1] >= other.value[1]

    def __repr__(self):
        return self.value[0]

    def __str__(self):
        return self.value[0]


class Module(BaseModel):
    """
    Module.
    """

    name: str = "Unknown"
    pack: str
    version: str = "Unknown"
    author: List[str] = ["Unknown"]
    pypi: bool = False
    category: Literal["utility", "entertainment", "misc"] = "misc"
    description: str = ""
    dependency: List[str] = None
    loaded: bool = True
    override_default: Union[None, bool] = None

    @validator("category", pre=True)
    def category_validator(cls, category: str):
        if category.startswith("util"):
            category = "utility"
        elif category.startswith("enter"):
            category = "entertainment"
        return category

    def __str__(self):
        return self.name

    def __repr__(self):
        return (
            f"Module({self.name})\n"
            f"\tpack: {self.pack}\n"
            f"\tversion: {self.version}\n"
            f"\tauthor: {self.author}\n"
            f"\tpypi: {self.pypi}\n"
            f"\tcategory: {self.category}\n"
            f"\tdescription: {self.description}\n"
            f"\tdependency: {self.dependency}\n"
            f"\tloaded: {self.loaded}\n"
            f"\toverride_default: {self.override_default}\n"
        )

    def __hash__(self):
        return hash(self.name)
