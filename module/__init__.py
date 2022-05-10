import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import List, Literal

from pydantic import BaseModel, ValidationError


class Module(BaseModel):
    name: str = "Unknown"
    pack: str
    version: str = "Unknown"
    author: List[str] = ["Unknown"]
    pypi: bool = False
    category: Literal["utility", "entertainment", "misc"] = "misc"
    description: str = ""
    dependency: List[str] = None


def load_metadata() -> List[Module]:
    metadata = []
    for path in Path(os.path.dirname(__file__)).iterdir():
        if path.is_dir() and Path(path / "metadata.json").is_file():
            try:
                with Path(path / "metadata.json").open("r", encoding="utf-8") as f:
                    metadata.append(
                        Module(**json.loads(f.read()), pack=f"module.{path.stem}")
                    )
            except (ValidationError, JSONDecodeError):
                metadata.append(Module(name=path.stem, pack=f"module.{path.stem}"))
            finally:
                continue
        if (path.is_dir() or path.name.endswith(".py")) and not path.name.startswith(
            "_"
        ):
            metadata.append(Module(name=path.stem, pack=f"module.{path.stem}"))
    return metadata


__all__: List[Module] = load_metadata()
