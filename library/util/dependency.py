import asyncio
import subprocess
from pathlib import Path
from typing import NoReturn

from loguru import logger

from library.config import config
from library.model import Module


def install_dependency(
    module: Module = None, requirements: list[str] = None
) -> NoReturn:
    """
    Install dependency for module.

    :param module: Module.
    :param requirements: List of requirements.
    :return: None.
    """

    if not module and not requirements:
        raise ValueError("module or requirements must be filled")
    if module:
        requirements_path = Path(
            Path().resolve(), *module.pack.split("."), "requirements.txt"
        )
        if not requirements_path.is_file():
            return
        requirements = requirements_path.read_text().splitlines()
    command = ["pip", "install"] if config.env == "pip" else ["poetry", "add"]
    process = subprocess.Popen(
        [*command, *requirements],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    stdout, stderr = process.communicate()
    if info := stdout.decode("utf-8"):
        logger.info(info)
    if err := stderr.decode("utf-8"):
        logger.error(err)


async def async_install_dependency(
    module: Module = None, requirements: list[str] = None
) -> NoReturn:
    """
    Install dependency for module asynchronously.

    :param module: Module.
    :param requirements: List of requirements.
    :return: None.
    """

    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, install_dependency, module, requirements)
