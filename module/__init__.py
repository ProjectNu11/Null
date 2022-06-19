import json
import os
from pathlib import Path
from typing import List, NoReturn, Union, Optional

from loguru import logger
from pydantic import ValidationError

from library.model import Module


class Modules:
    """
    Modules class contains a list of modules.
    """

    __all__: List[Module] = []

    def __init__(self):
        self.load_modules(reorder=True)

    def __getitem__(self, name: str):
        return self.get_module(name)

    def __contains__(self, module: Union[str, Module]):
        if isinstance(module, str):
            return bool(self.get_module(module))
        return module in self.__all__

    def __iter__(self):
        return iter(self.__all__)

    def __len__(self):
        return len(self.__all__)

    def __repr__(self):
        return f"Modules({self.__all__})"

    def load_modules(self, reorder: bool = True) -> NoReturn:
        """
        Load modules from the module directory.
        :param reorder: Reorder modules after loading.
        :return: None
        """
        __modules = []
        for path in Path(os.path.dirname(__file__)).iterdir():
            if path.name.startswith("_"):
                continue
            if module := ModuleMetadata.read_and_update_metadata(path, path.is_dir()):
                __modules.append(module)
        self.__all__ = __modules
        if not reorder:
            return
        else:
            self.reorder_modules()

    def reorder_modules(self) -> NoReturn:
        """
        Reorder modules by dependency, common and unloaded modules.
        :return: None
        """
        __dependencies = []
        for __has_dependency in self.search_module(match_any=True, dependency=True):
            __dependencies.extend(
                self.get_module(__dependency)
                for __dependency in __has_dependency.dependency
            )
        __dependencies = list(set(__dependencies))
        __dependencies.sort(key=lambda x: x.pack)
        __unloaded = self.__search_module_by_loaded(False)
        __unloaded.sort(key=lambda x: x.pack)
        __common = list(set(self.__all__) - set(__dependencies) - set(__unloaded))
        __common.sort(key=lambda x: x.pack)
        __modules = __dependencies + __common + __unloaded
        self.__all__ = __modules

    def get_module(self, name: str) -> Union[None, Module]:
        """
        Get module by name.
        :param name: Module name.
        :return: Module object.
        """
        if __modules := self.search_module(match_any=True, name=name, pack=name):
            return __modules[0]

    def add_module(self, module: Module) -> NoReturn:
        """
        Add module to the list.
        :param module: Module object.
        :return: None
        """
        self.__all__.append(module)

    def remove_module(self, pack: str) -> NoReturn:
        """
        Remove module from the list.
        :param pack: Module pack.
        :return: None
        """
        self.__all__ = list(filter(lambda x: x.pack != pack, self.__all__))

    def search_module(
        self,
        match_any: bool,
        name: str = None,
        pack: str = None,
        author: str = None,
        pypi: bool = None,
        category: str = None,
        dependency: Union[str, bool] = None,
        loaded: bool = None,
    ) -> List[Module]:
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
            and not loaded
        ):
            raise ValueError("No search criteria provided")
        if match_any:
            return self.__search_module_match_any(
                name=name,
                pack=pack,
                author=author,
                pypi=pypi,
                category=category,
                dependency=dependency,
                loaded=loaded,
            )
        return self.__search_module_match_all(
            name=name,
            pack=pack,
            author=author,
            pypi=pypi,
            category=category,
            dependency=dependency,
            loaded=loaded,
        )

    def __search_module_match_all(
        self,
        name: str = None,
        pack: str = None,
        author: str = None,
        pypi: bool = None,
        category: str = None,
        dependency: Union[str, bool] = None,
        loaded: bool = None,
    ) -> List[Module]:
        """
        Search module by multiple fields.
        :param name: Module name.
        :param pack: Module pack.
        :param author: Module author.
        :param pypi: Module has dependency on PyPI.
        :param category: Module category.
        :param dependency: Module dependency.
        :param loaded: Module is loaded.
        :return: List of modules.
        """
        query = self.__all__
        if name is not None:
            query = self.__search_module_by_name(name, query)
        if pack is not None:
            query = self.__search_module_by_pack(pack, query)
        if author is not None:
            query = self.__search_module_by_author(author, query)
        if pypi is not None:
            query = self.__search_module_by_pypi(pypi, query)
        if category is not None:
            query = self.__search_module_by_category(category, query)
        if dependency is not None:
            query = self.__search_module_by_dependency(dependency, query)
        if loaded is not None:
            query = self.__search_module_by_loaded(loaded, query)
        return query

    def __search_module_match_any(
        self,
        name: str = None,
        pack: str = None,
        author: str = None,
        pypi: bool = None,
        category: str = None,
        dependency: Union[str, bool] = None,
        loaded: bool = None,
    ) -> List[Module]:
        """
        Search module by multiple fields.
        :param name: Module name.
        :param pack: Module pack.
        :param author: Module author.
        :param pypi: Module has dependency on PyPI.
        :param category: Module category.
        :param dependency: Module dependency.
        :param loaded: Module is loaded.
        :return: List of modules.
        """
        query = []
        if name is not None:
            query += self.__search_module_by_name(name)
        if pack is not None:
            query += self.__search_module_by_pack(pack)
        if author is not None:
            query += self.__search_module_by_author(author)
        if pypi is not None:
            query += self.__search_module_by_pypi(pypi)
        if category is not None:
            query += self.__search_module_by_category(category)
        if dependency is not None:
            query += self.__search_module_by_dependency(dependency)
        if loaded is not None:
            query += self.__search_module_by_loaded(loaded)
        return list(set(query))

    def __search_module(
        self, func: callable, field: List[Module] = None
    ) -> List[Module]:
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

    def __search_module_by_name(
        self, name: str, field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by name.
        :param name: Module name.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(
            lambda x: any(
                [
                    name.lower() == x.name.lower(),
                    name.lower() == x.name.lower().split(".", maxsplit=1)[-1],
                ]
            ),
            field,
        )

    def __search_module_by_pack(
        self, pack: str, field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by pack.
        :param pack: Module pack.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(
            lambda x: any(
                [
                    pack.lower() == x.pack.lower(),
                    pack.lower() == x.pack.lower().split(".", maxsplit=1)[-1],
                ]
            ),
            field,
        )

    def __search_module_by_author(
        self, author: str, field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by author.
        :param author: Module author.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(
            lambda x: author.lower() in map(lambda y: y.lower(), x.author),
            field,
        )

    def __search_module_by_pypi(
        self, pypi: bool, field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by dependency on PyPI.
        :param pypi: Module has dependency on PyPI.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(lambda x: x.pypi == pypi, field)

    def __search_module_by_category(
        self, category: str, field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by category.
        :param category: Module category.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(
            lambda x: category.lower() == x.category.lower(),
            field,
        )

    def __search_module_by_dependency(
        self, dependency: Union[str, bool], field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by dependency.
        :param dependency: Module dependency.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(
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

    def __search_module_by_loaded(
        self, loaded: bool, field: List[Module] = None
    ) -> List[Module]:
        """
        Search module by loaded.
        :param loaded: Module is loaded.
        :param field: Field to search.
        :return: List of modules.
        """
        return self.__search_module(lambda x: x.loaded == loaded, field)


class ModuleMetadata:
    @classmethod
    def read_and_update_metadata(
        cls, file: Path, is_dir: bool = False
    ) -> Optional[Module]:
        """
        Reads the metadata from the given file or directory and updates the module with the metadata.
        :param file: The file or directory to read the metadata from.
        :param is_dir: Whether the file is a directory.
        :return: The module with the updated metadata.
        """
        metadata_dir = cls.get_metadata_dir(file, is_dir)
        req_dir = cls.get_requirements_dir(file, is_dir)
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
                cls.write_metadata(metadata_dir, module)
                return module

    @staticmethod
    def get_metadata_dir(file: Path, is_dir: bool = False) -> Path:
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
    def get_requirements_dir(file: Path, is_dir: bool = False) -> Path:
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
    def write_metadata(file: Path, module: Module) -> NoReturn:
        """
        Writes the metadata to the given file.
        :param file: The file to write the metadata to.
        :param module: The module to write the metadata from.
        :return: None.
        """
        with file.open("w", encoding="utf-8") as f:
            f.write(module.json(indent=4, ensure_ascii=False))


modules = Modules()
