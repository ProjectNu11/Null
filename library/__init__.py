from datetime import time
from pathlib import Path
from typing import Union, Iterable
from typing_extensions import _SpecialForm

from graia.ariadne.message.parser.twilight import UnionMatch, SpacePolicy
from loguru import logger

from library.config import config

__version__ = "0.1.0"

log_dir = Path(Path().resolve(), "log")
log_dir.mkdir(exist_ok=True)
Path(config.path.data, "library").mkdir(exist_ok=True)

logger.add(
    Path(log_dir, "{time:YYYY-MM-DD}", "common.log"),
    level="INFO",
    retention=f"{config.log_retention} days" if config.log_retention else None,
    encoding="utf-8",
    rotation=time(),
)
logger.add(
    Path(log_dir, "{time:YYYY-MM-DD}", "error.log"),
    level="ERROR",
    retention=f"{config.log_retention} days" if config.log_retention else None,
    encoding="utf-8",
    rotation=time(),
)

PrefixMatch = UnionMatch(*config.func.prefix).space(SpacePolicy.NOSPACE)


def prefix_match(
    optional: bool = False,
    space: SpacePolicy = SpacePolicy.NOSPACE,
    *pattern: Union[str, Iterable[str]],
) -> _SpecialForm | _SpecialForm:
    return UnionMatch(*(config.func.prefix or pattern), optional=optional).space(space)
