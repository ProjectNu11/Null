import asyncio
import json
import os
import shutil
import traceback
from pathlib import Path
from typing import NoReturn

from graia.saya import Saya
from loguru import logger
from pydantic import ValidationError

from library import config
from library.model import Module
from library.util.dependency import install_dependency


class Modules:
    """
    Modules class contains a list of modules.
    """

    __all__: list[Module] = []
    __instance: "Modules" = None

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        self.load(reorder=True)

    def __getitem__(self, item: str | slice):
        return self.get(item) if isinstance(item, str) else self.__all__[item]

    def __contains__(self, module: str | Module):
        if isinstance(module, str):
            return bool(self.get(module))
        return module in self.__all__

    def __iter__(self):
        return iter(self.__all__)

    def __len__(self):
        return len(self.__all__)

    def __repr__(self):
        return f"Modules({len(self)})\n{''.join(map(repr, self))}"

    def __call__(self, match_any: bool = True, *args, **kwargs):
        if len(args) == 1:
            return self.search(match_any=True, name=args[0], pack=args[0])
        if not kwargs:
            raise ValueError("No search criteria provided")
        return self.search(match_any, **kwargs)

    def require_modules(self, saya: Saya, log_exception: bool = False) -> NoReturn:
        """
        Load modules by Saya.

        :param saya: Saya instance.
        :param log_exception: Log exception.
        :return: None
        """

        with saya.module_context():
            for module in modules:
                if not module.loaded:
                    continue
                self.require_module(module, saya, log_exception)

    def require_module(
        self, module: Module, saya: Saya, log: bool, retries: int = 1
    ) -> NoReturn:
        """
        Load module by Saya.

        :param module: Module object.
        :param saya: Saya instance.
        :param log: Log exception.
        :param retries: Retry times.
        :return: None
        """

        try:
            saya.require(module.pack)
        except ModuleNotFoundError as e:
            install_dependency(module)
            if retries > 0:
                retries -= 1
                return self.require_module(module, saya, log, retries - 1)
            if log:
                logger.exception(traceback.format_exc())
            logger.error(e)
        except Exception as e:
            if log:
                logger.exception(traceback.format_exc())
            logger.error(e)

    async def async_require_modules(self, saya: Saya, log_exception: bool) -> NoReturn:
        """
        Load modules by Saya asynchronously.

        :param saya: Saya instance.
        :param log_exception: Log exception.
        :return: None
        """

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, self.require_modules, saya, log_exception)

    async def async_require_module(
        self, module: Module, saya: Saya, log: bool, retries: int = 1
    ) -> NoReturn:
        """
        Load module by Saya asynchronously.

        :param module: Module object.
        :param saya: Saya instance.
        :param log: Log exception.
        :param retries: Retry times.
        :return: None
        """

        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None, self.require_module, module, saya, log, retries
        )

    def load(self, reorder: bool = True) -> NoReturn:
        """
        Load modules from the module directory.

        :param reorder: Reorder modules after loading.
        :return: None
        """

        __modules: list[Module] = []
        for path in Path(os.path.dirname(__file__)).iterdir():
            if path.name.startswith("_"):
                continue
            if module := ModuleMetadata.read_and_update(path, path.is_dir()):
                __modules.append(module)
        self.__all__ = __modules
        if not reorder:
            return
        else:
            self.reorder()

    def reorder(self) -> NoReturn:
        """
        Reorder modules by dependency, common and unloaded modules.

        :return: None
        """

        __dependencies = []
        for __has_dependency in self.search(match_any=True, dependency=True):
            __dependencies.extend(
                self.get(__dependency) for __dependency in __has_dependency.dependency
            )
        __dependencies = list(set(__dependencies))
        __dependencies.sort(key=lambda x: x.pack)
        __unloaded = self.__search_by_loaded(False)
        __unloaded.sort(key=lambda x: x.pack)
        __common = list(set(self.__all__) - set(__dependencies) - set(__unloaded))
        __common.sort(key=lambda x: x.pack)
        __modules = __dependencies + __common + __unloaded
        self.__all__ = __modules

    def get(self, name: str) -> None | Module:
        """
        Get module by name.

        :param name: Module name.
        :return: Module object.
        """

        if __modules := self.search(match_any=True, name=name, pack=name):
            return __modules[0]

    def add(self, module: Module) -> NoReturn:
        """
        Add module to the list.

        :param module: Module object.
        :return: None
        """

        self.__all__.append(module)

    @staticmethod
    def __remove_dir(path: Path) -> NoReturn:
        """
        Remove directory.

        :param path: Path object.
        :return: None
        """

        if not path.exists():
            return
        if path.is_dir():
            logger.info(f"Removing directory {path}")
            shutil.rmtree(path)
        else:
            logger.info(f"Removing file {path}")
            path.unlink(missing_ok=True)

    def remove(self, pack: str, keep_data: bool = True) -> bool:
        """
        Remove module from the list.

        :param pack: Module pack.
        :param keep_data: Keep module data.
        :return: None
        """

        if not (module := self.get(pack)):
            return False
        path = Path(Path().resolve(), *module.pack.split("."))
        self.__all__ = list(filter(lambda x: x.pack != pack, self.__all__))
        self.__remove_dir(path)
        if keep_data:
            return True
        path = Path(config.path.data, module.pack)
        self.__remove_dir(path)
        return True

    def search(
        self,
        match_any: bool,
        name: str = None,
        pack: str = None,
        author: str = None,
        pypi: bool = None,
        category: str = None,
        dependency: str | bool = None,
        loaded: bool = None,
    ) -> list[Module]:
        """
        Search module by multiple fields.

        :param match_any: If True, search will return modules that match any of the fields.
        :param name: Module name.
        :param pack: Module pack.
        :param author: Module author.
        :param pypi: Module has dependency on PyPI.
        :param category: Module category.
        :param dependency: Module dependency.
        :param loaded: Module is loaded.
        :return: List of modules.
        """

        if (
            not name
            and not pack
            and not author
            and not pypi
            and not category
            and not dependency
            and not isinstance(loaded, bool)
        ):
            raise ValueError("No search criteria provided")
        kwargs = {
            "name": name,
            "pack": pack,
            "author": author,
            "pypi": pypi,
            "category": category,
            "dependency": dependency,
            "loaded": loaded,
        }
        kwargs = {k: v for k, v in kwargs.items() if v is not None}
        if match_any:
            return self.__search_match_any(**kwargs)
        return self.__search_match_all(
            name=name,
            pack=pack,
            author=author,
            pypi=pypi,
            category=category,
            dependency=dependency,
            loaded=loaded,
        )

    def __search_match_all(self, **kwargs) -> list[Module]:
        """
        Search module by multiple fields.

        :param kwargs: Search criteria.
        """

        query = self.__all__
        if "name" in kwargs:
            query = self.__search_by_name(kwargs.get("name"), query)
        if "pack" in kwargs:
            query = self.__search_by_pack(kwargs.get("pack"), query)
        if "author" in kwargs:
            query = self.__search_by_author(kwargs.get("author"), query)
        if "pypi" in kwargs:
            query = self.__search_by_pypi(kwargs.get("pypi"), query)
        if "category" in kwargs:
            query = self.__search_by_category(kwargs.get("category"), query)
        if "dependency" in kwargs:
            query = self.__search_by_dependency(kwargs.get("dependency"), query)
        if "loaded" in kwargs:
            query = self.__search_by_loaded(kwargs.get("loaded"), query)
        return query

    def __search_match_any(self, **kwargs) -> list[Module]:
        """
        Search module by multiple fields.

        :param kwargs: Search criteria.
        """

        query = []
        if "name" in kwargs:
            query += self.__search_by_name(kwargs.get("name"))
        if "pack" in kwargs:
            query += self.__search_by_pack(kwargs.get("pack"))
        if "author" in kwargs:
            query += self.__search_by_author(kwargs.get("author"))
        if "pypi" in kwargs:
            query += self.__search_by_pypi(kwargs.get("pypi"))
        if "category" in kwargs:
            query += self.__search_by_category(kwargs.get("category"))
        if "dependency" in kwargs:
            query += self.__search_by_dependency(kwargs.get("dependency"))
        if "loaded" in kwargs:
            query += self.__search_by_loaded(kwargs.get("loaded"))
        return list(set(query))

    def __search(self, func: callable, field: list[Module] = None) -> list[Module]:
        """
        Search module by field.

        :param func: Function to search.
        :param field: Field to search.
        :return: List of modules.
        """

        if field is None:
            field = self.__all__
        if module := list(filter(func, field)):
            return module
        return []

    def __search_by_name(self, name: str, field: list[Module] = None) -> list[Module]:
        """
        Search module by name.

        :param name: Module name.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(
            lambda x: any(
                [
                    name.lower() == x.name.lower(),
                    name.lower() == x.name.lower().split(".", maxsplit=1)[-1],
                ]
            ),
            field,
        )

    def __search_by_pack(self, pack: str, field: list[Module] = None) -> list[Module]:
        """
        Search module by pack.

        :param pack: Module pack.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(
            lambda x: any(
                [
                    pack.lower() == x.pack.lower(),
                    pack.lower() == x.pack.lower().split(".", maxsplit=1)[-1],
                ]
            ),
            field,
        )

    def __search_by_author(
        self, author: str, field: list[Module] = None
    ) -> list[Module]:
        """
        Search module by author.

        :param author: Module author.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(
            lambda x: author.lower() in map(lambda y: y.lower(), x.author),
            field,
        )

    def __search_by_pypi(self, pypi: bool, field: list[Module] = None) -> list[Module]:
        """
        Search module by dependency on PyPI.

        :param pypi: Module has dependency on PyPI.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(lambda x: x.pypi == pypi, field)

    def __search_by_category(
        self, category: str, field: list[Module] = None
    ) -> list[Module]:
        """
        Search module by category.

        :param category: Module category.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(
            lambda x: category.lower() == x.category.lower(),
            field,
        )

    def __search_by_dependency(
        self, dependency: str | bool, field: list[Module] = None
    ) -> list[Module]:
        """
        Search module by dependency.

        :param dependency: Module dependency.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(
            lambda x: any(
                [
                    isinstance(dependency, bool) and x.dependency,
                    isinstance(dependency, str)
                    and dependency.lower() in map(lambda y: y.lower(), x.dependency),
                    isinstance(dependency, str)
                    and dependency.lower()
                    in map(
                        lambda y: y.lower().split(".", maxsplit=1)[-1], x.dependency
                    ),
                ]
            ),
            field,
        )

    def __search_by_loaded(
        self, loaded: bool, field: list[Module] = None
    ) -> list[Module]:
        """
        Search module by loaded.

        :param loaded: Module is loaded.
        :param field: Field to search.
        :return: List of modules.
        """

        return self.__search(lambda x: x.loaded == loaded, field)


class ModuleMetadata:
    def __new__(cls, *args, **kwargs):
        raise NotImplementedError("ModuleMetadata is not meant to be instantiated.")

    @staticmethod
    def __get_metadata_dir(file: Path, is_dir: bool = False) -> Path:
        """
        Returns the metadata directory for the given file or directory.

        :param file: The file or directory to get the metadata directory for.
        :param is_dir: Whether the file is a directory.
        :return: The metadata directory.
        """

        return (
            Path(file, "metadata.json")
            if is_dir
            else Path(file.parent, f"{file.stem}-metadata.json")
        )

    @staticmethod
    def __get_requirements_dir(file: Path, is_dir: bool = False) -> Path:
        """
        Returns the requirements directory for the given file or directory.

        :param file: The file or directory to get the requirements directory for.
        :param is_dir: Whether the file is a directory.
        :return: The requirements directory.
        """

        return (
            Path(file, "requirements.txt")
            if is_dir
            else Path(file.parent, f"{file.stem}-requirements.txt")
        )

    @staticmethod
    def write(file: Path, module: Module) -> NoReturn:
        """
        Writes the metadata to the given file.

        :param file: The file to write the metadata to.
        :param module: The module to write the metadata from.
        :return: None.
        """

        with file.open("w", encoding="utf-8") as f:
            f.write(module.json(indent=4, ensure_ascii=False))

    @classmethod
    def read_and_update(cls, file: Path, is_dir: bool = False) -> Module | None:
        """
        Reads the metadata from the given file or directory and updates the module with the metadata.

        :param file: The file or directory to read the metadata from.
        :param is_dir: Whether the file is a directory.
        :return: The module with the updated metadata.
        """

        metadata_dir = cls.__get_metadata_dir(file, is_dir)
        req_dir = cls.__get_requirements_dir(file, is_dir)
        module = None
        try:
            with metadata_dir.open("r", encoding="utf-8") as f:
                content = json.loads(f.read())
                module = Module(**content)
        except (ValidationError, FileNotFoundError):
            logger.error(f"Validation failed for module/{file.stem}")
            module = Module(
                name=file.stem,
                pack=f"module.{file.stem}",
                pypi=req_dir.is_file(),
            )
        finally:
            if module:
                cls.write(metadata_dir, module)
                return module


modules = Modules()
