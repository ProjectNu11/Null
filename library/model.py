import json
from enum import Enum
from pathlib import Path
from typing import Literal, NoReturn

from loguru import logger
from pydantic import BaseModel, AnyHttpUrl, root_validator, validator


class HubMetadata(BaseModel):
    """
    Metadata for hub.
    """

    __instance: "HubMetadata" = None

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

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance


class HubConfig(BaseModel):
    """
    Configuration for hub.
    """

    __instance: "HubConfig" = None

    enabled: bool = False
    url: AnyHttpUrl = "https://api.nullqwertyuiop.me/project-null"
    secret: str = ""
    meta: str = "/metadata"
    metadata: None | HubMetadata = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

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

    __instance: "PathConfig" = None

    root: Path = Path(__file__).parent.parent
    data: Path = Path(root, "data")
    config: Path = Path(data, "config")
    shared: Path = Path(data, "shared")

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @root_validator()
    def path_check(cls, values: dict):
        values.get("data").mkdir(parents=True, exist_ok=True)
        values.get("config").mkdir(parents=True, exist_ok=True)
        values.get("shared").mkdir(parents=True, exist_ok=True)
        return values


class FunctionConfig(BaseModel):
    """
    Configuration for function.
    """

    __instance: "FunctionConfig" = None

    default: bool = False
    notice: bool = True
    notice_msg: str | None = "模块 {module.name} 已关闭，请联系管理员开启"
    prefix: str = "."
    modules: dict[str, dict] = {}

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def get_config(self, module: str, key: str = None):
        if module_cfg := self.modules.get(module, None):
            return module_cfg.get(key, None) if key else module_cfg

    def update_config(self, module: str, cfg: dict | BaseModel = None):
        if isinstance(cfg, BaseModel):
            cfg = cfg.dict()
        self.modules[module] = cfg

    @root_validator()
    def function_check(cls, values: dict):
        assert not (
            values.get("notice_msg", None) is None and values.get("notice", True)
        ), "Function notice is enabled but notice message is not set"
        return values


class MySQLConfig(BaseModel):
    """
    Configuration for MySQL.
    """

    __instance: "MySQLConfig" = None

    disable_pooling: bool = False
    pool_size: int = 40
    max_overflow: int = 60

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

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

    __instance__: "DatabaseConfig" = None

    link: str = "sqlite+aiosqlite:///data/data.db"
    config: None | MySQLConfig = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance__ is None:
            cls.__instance__ = super().__new__(cls)
        return cls.__instance__

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


class NConfig(BaseModel):
    """
    Configuration for project.
    """

    __instance: "NConfig" = None

    name: str = ""
    num: int = 0
    account: int = 0
    description: str = "Another Modular Bot"
    env: str = ""
    host: AnyHttpUrl = ""
    verify_key: str = ""
    dev_group: list[int] = []
    owners: list[int] = []
    proxy: str = None
    log_retention: None | int = 7
    db: DatabaseConfig = DatabaseConfig()
    func: FunctionConfig = FunctionConfig()
    path: PathConfig = PathConfig()
    hub: HubConfig = HubConfig()

    def __init__(self):
        self.__init_check()
        super().__init__(**self.__load())
        logger.success("Loaded config from config.json")

    def __new__(cls):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    @validator("name", "account", "verify_key")
    def config_check(cls, value):
        assert value, "name, account and verify_key can't be blank"
        return value

    @validator("env")
    def env_check(cls, value):
        value = value.lower()
        assert value in ["pip", "poetry"], "env must be pip or poetry"
        return value

    @staticmethod
    def __load():
        with Path(Path().resolve(), "config.json").open("r", encoding="utf-8") as _f:
            return json.loads(_f.read())

    def __init_check(self):
        if not Path(Path().resolve(), "config.json").exists():
            super().__init__()
            self.save()
            logger.success("Created config.json using initial values")
            logger.success("Modify essential fields in config.json to continue")
            exit(-1)

    def save(self) -> NoReturn:
        """
        Save config to config.json.

        :return: NoReturn
        """

        with Path(Path().resolve(), "config.json").open("w", encoding="utf-8") as _f:
            _f.write(self.json(indent=4, ensure_ascii=False))

    def reload(self) -> NoReturn:
        """
        Reload config from config.json.

        :return: NoReturn
        """

        super().__init__(**self.__load())

    def get_module_config(self, module: str, key: str = None):
        """
        Get module config.

        :param module: module name
        :param key: key name
        :return: module config
        """

        return self.func.get_config(module, key)

    def update_module_config(self, module: str, cfg: dict | BaseModel = None):
        """
        Update module config.

        :param module: module name
        :param cfg: module config
        :return: NoReturn
        """

        self.func.update_config(module, cfg)
        self.save()


class UserPerm(Enum):
    """
    User permission.

    UserPerm.BOT_OWNER: bot owner, 4
    UserPerm.OWNER: group owner, 3
    UserPerm.ADMINISTRATOR: group administrator, 2
    UserPerm.MEMBER: group member, 1
    UserPerm.BLOCKED: blocked, 0
    """

    BLOCKED = ("BLOCKED", 0)
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
    author: list[str] = ["Unknown"]
    pypi: bool = False
    category: Literal[
        "utility", "entertainment", "dependency", "miscellaneous"
    ] = "miscellaneous"
    description: str = ""
    dependency: list[str] = None
    loaded: bool = True
    hidden: bool = False
    override_default: None | bool = None
    override_switch: None | bool = None

    @validator("category", pre=True)
    def category_validator(cls, category: str):
        if category.startswith("uti"):
            category = "utility"
        elif category.startswith("ent"):
            category = "entertainment"
        elif category.startswith("dep"):
            category = "dependency"
        elif category.startswith("mis"):
            category = "miscellaneous"
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
            f"\thidden: {self.hidden}\n"
            f"\toverride_default: {self.override_default}\n"
            f"\toverride_switch: {self.override_switch}\n"
        )

    def __hash__(self):
        return hash(self.name)
