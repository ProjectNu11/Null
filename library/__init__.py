from datetime import time
from pathlib import Path

from loguru import logger

from library.config import config

__version__ = "0.1.0"

log_dir = Path(Path().resolve(), "log")
log_dir.mkdir(exist_ok=True)

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
