import json
import os
from json import JSONDecodeError
from pathlib import Path
from typing import List, Literal

from loguru import logger
from pydantic import BaseModel, ValidationError, validator


class Module(BaseModel):
    name: str = "Unknown"
    pack: str
    version: str = "Unknown"
    author: List[str] = ["Unknown"]
    pypi: bool = False
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


def load_metadata() -> List[Module]:
    metadata = []
    for path in Path(os.path.dirname(__file__)).iterdir():
        if path.name.startswith("_"):
            continue
        if path.is_dir():
            if Path(path / "metadata.json").is_file():
                try:
                    with Path(path / "metadata.json").open("r", encoding="utf-8") as f:
                        metadata.append(Module(**json.loads(f.read())))
                except (ValidationError, JSONDecodeError):
                    logger.error(f"Validation failed for module/{path.stem}/metadata.json")
                    metadata.append(
                        Module(
                            name=path.stem,
                            pack=f"module.{path.stem}",
                            pypi=Path(path / "requirements.txt").is_file(),
                        )
                    )
            else:
                module = Module(
                    name=path.stem,
                    pack=f"module.{path.stem}",
                    pypi=Path(path / "requirements.txt").is_file(),
                )
                metadata.append(module)
                with Path(path / "metadata.json").open("w", encoding="utf-8") as f:
                    f.write(
                        module.json(exclude={"installed"}, indent=4, ensure_ascii=False)
                    )
        elif path.name.endswith(".py"):
            if Path(path.parent / f"{path.stem}-metadata.json").is_file():
                try:
                    with Path(path.parent / f"{path.stem}-metadata.json").open(
                        "r", encoding="utf-8"
                    ) as f:
                        module = Module(**json.loads(f.read()))
                    module.pack = f"module.{path.stem}"
                    metadata.append(module)
                except (ValidationError, JSONDecodeError):
                    logger.error(f"Validation failed for module/{path.stem}/metadata.json")
                    metadata.append(
                        Module(
                            name=path.stem,
                            pack=f"module.{path.stem}",
                            pypi=Path(
                                path.parent / f"{path.stem}-requirements.txt"
                            ).is_file(),
                        )
                    )
            else:
                module = Module(
                    name=path.stem,
                    pack=f"module.{path.stem}",
                    pypi=Path(path.parent / f"{path.stem}-requirements.txt").is_file(),
                )
                metadata.append(module)
                with Path(path.parent / f"{path.stem}-metadata.json").open(
                    "w", encoding="utf-8"
                ) as f:
                    f.write(
                        module.json(exclude={"installed"}, indent=4, ensure_ascii=False)
                    )
    return metadata


__all__: List[Module] = load_metadata()
print(__all__)
