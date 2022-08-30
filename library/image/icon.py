import asyncio
from pathlib import Path

import numpy as np
from PIL import Image


class IconUtil:
    def __int__(self):
        raise NotImplementedError("This class is not intended to be instantiated.")

    @classmethod
    def get_icon(
        cls,
        icon: str | Path,
        size: tuple = None,
        color: tuple[int, int, int] | None = (63, 63, 63),
    ):
        """
        Get an icon from the assets/icons folder

        :param icon: Name of the icon, must be in the assets/icons folder
        :param size: Size of the icon
        :param color: Color of the icon
        :return: Image of the icon, may be transparent if icon is not found
        """

        path = (
            Path("library", "assets", "icons", f"{icon}.png")
            if isinstance(icon, str)
            else icon
        )
        if not path.exists():
            return Image.new("RGBA", size, (0, 0, 0, 0))
        icon = Image.open(str(path))
        if size is not None:
            icon = icon.resize(size)
        if color is not None:
            icon = cls.replace_color(icon, color)
        return icon

    @classmethod
    async def async_get_icon(
        cls, icon: str, size: tuple = None, color: tuple[int, int, int] = (63, 63, 63)
    ):
        """
        Get an icon from the assets/icons folder

        :param icon: Name of the icon, must be in the assets/icons folder
        :param size: Size of the icon
        :param color: Color of the icon
        :return: Image of the icon, may be transparent if icon is not found
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.get_icon, icon, size, color)

    @staticmethod
    def replace_color(icon: Image.Image, color: tuple[int, int, int]):
        """
        Replace the color of the icon

        :param icon: Icon to replace the color
        :param color: Color to replace
        :return: Icon with the specified color
        """

        icon = icon.convert("RGBA")
        data = np.array(icon)
        red, green, blue, alpha = data.T
        black = (red == 0) & (blue == 0) & (green == 0)
        data[..., :-1][black.T] = color
        icon = Image.fromarray(data)
        return icon

    @classmethod
    async def async_replace_color(cls, icon: Image.Image, color: tuple[int, int, int]):
        """
        Replace the color of the icon

        :param icon: Icon to replace the color
        :param color: Color to replace
        :return: Icon with the specified color
        """

        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, cls.replace_color, icon, color)
