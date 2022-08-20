import json
from pathlib import Path

from pydantic import BaseModel

from library import config


class ModuleConfig:
    __instance: "ModuleConfig" = None
    __cache: dict[str, dict]

    def __init__(self):
        self.__cache = {}
        for module in Path(config.path.config).iterdir():
            if module.is_dir():
                self.__cache[module.name] = {}
                for file in module.iterdir():
                    if file.is_file() and file.suffix == ".json":
                        with file.open("r", encoding="utf-8") as f:
                            self.__cache[module.name][file.stem] = json.load(f)

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def update(
        self,
        module: str,
        data: str | dict | BaseModel,
        chunk: str = "main",
        key: str = None,
    ):
        data = data.dict() if isinstance(data, BaseModel) else data
        if module not in self.__cache:
            self.__cache[module] = {}
        if key and chunk in self.__cache[module]:
            self.__cache[module][chunk][key] = data
        else:
            self.__cache[module][chunk] = data
        module_dir = Path(config.path.config, module)
        module_dir.mkdir(exist_ok=True)
        with Path(module_dir, f"{chunk}.json").open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)

    def get(self, module: str, chunk: str = "main", key: str = None):
        if module in self.__cache and chunk in self.__cache[module]:
            if key:
                return self.__cache[module][chunk].get(key, None)
            return self.__cache[module][chunk]
        return None
