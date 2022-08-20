import json
from pathlib import Path

from graia.ariadne.model import Group

from library.config import config
from library.model import Module


class GroupConfig:
    __instance: "GroupConfig" = None
    __cache: dict[int, dict[str, dict]] = {}
    __template: dict[str, dict]

    def __init__(self):
        self.__load()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __load(self):
        if not Path(config.path.data, "library", "group_config.json").is_file():
            self.__save()
        with Path(config.path.data, "library", "group_config.json").open(
            "r", encoding="utf-8"
        ) as f:
            self.__cache = json.loads(f.read())

    def __save(self):
        with Path(config.path.data, "library", "group_config.json").open(
            "w", encoding="utf-8"
        ) as f:
            f.write(json.dumps(self.__cache, indent=4, ensure_ascii=False))

    @staticmethod
    def __type_convert(value: int | str | Group | Module) -> int | str:
        if isinstance(value, (int, str)):
            return value
        if isinstance(value, Group):
            return value.id
        if isinstance(value, Module):
            return value.pack

    def register_template(self, module: str | Module, data: dict):
        module: str = self.__type_convert(module)
        self.__template[module] = data

    def get(self, group: int | Group, module: str | Module) -> dict | None:
        """
        Get group config, if not exists, will return None.

        :param group: Group id or Group object.
        :param module: Module pack or Module object.
        :return: Group config, or None if not found.
        """

        group = self.__type_convert(group)
        if (gc := self.__cache.get(group, None)) is None:
            return
        module: dict | None = gc.get(module, None)
        return module

    def update(
        self,
        group: int | Group,
        module: str | Module,
        data: dict | None = None,
        key: str = None,
        value: str = None,
    ) -> None:
        """
        Update group config.

        :param group: Group id or Group object.
        :param module: Module pack or Module object.
        :param data: Data to update, if None, will reset the config.
        :param key: Key to update.
        :param value: Value to update.
        :return: None.
        """

        group: int = self.__type_convert(group)
        module: str = self.__type_convert(module)
        if data is None:
            if group not in self.__cache.keys() or module not in self.__cache.keys():
                return
            del self.__cache[group][module]
            return
        if key and value:
            self.__cache[group][module][key] = value

    def get_or_update(self, group: int | Group, module: str | Module) -> dict:
        """
        Get group config, if not exists, will create a new one.

        :param group: Group id or Group object.
        :param module: Module pack or Module object.
        :return: Group config.
        """

        group: int = self.__type_convert(group)
        module: str = self.__type_convert(module)
        if isinstance(cfg := self.get(group, module), dict):
            return cfg
        self.update(group, module, self.__template.get(module, None))
