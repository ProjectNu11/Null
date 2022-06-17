import asyncio
import shutil
from pathlib import Path

from loguru import logger

from library.model import Module


def uninstall_module(module: Module = None, path: Path = None):
    if not (module or path):
        raise ValueError("module or path is required")
    if module:
        path = Path(Path().resolve(), *module.pack.split("."))
    if not path.exists():
        raise FileNotFoundError(f"{path} not found")
    if path.is_file():
        logger.info(f"Removing file {path}")
        path.unlink(missing_ok=True)
        return
    logger.info(f"Removing directory {path}")
    shutil.rmtree(str(path))


async def async_uninstall_module(module: Module = None, path: Path = None):
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, uninstall_module, module, path)
