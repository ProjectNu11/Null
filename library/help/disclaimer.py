import math

from PIL import Image

from library import config
from library.image.oneui_mock.elements import (
    GeneralBox,
    is_dark,
    Element,
    Column,
    Banner,
    Header,
    OneUIMock,
)
from library.model import Module


class Disclaimer:
    disclaimer: set[GeneralBox] = set()
    rendered: bytes | None = None
    hash: int | None = None

    @classmethod
    def register(cls, module: Module | str, *disclaimers: str, box: GeneralBox = None):
        """
        Register a disclaimer for a module, will override the previous one.

        :param module: The module to register the disclaimer for.
        :param disclaimers: The disclaimers to register.
        :param box: The box to register.
        :return: None
        """

        if isinstance(box, GeneralBox):
            cls.disclaimer.add(box)
            return

        disclaimer = "\n".join([disc for disc in disclaimers if isinstance(disc, str)])
        if not disclaimer:
            raise ValueError("disclaimer cannot be empty")
        cls.unregister(module)
        if isinstance(module, Module):
            module = module.name
        cls.disclaimer.add(
            GeneralBox(
                text=module,
                description=disclaimer,
            )
        )

    @classmethod
    def unregister(cls, module: Module | str):
        """
        Unregister a disclaimer for a module.

        :param module: The module to unregister the disclaimer for.
        :return: None
        """

        if isinstance(module, Module):
            module = module.name
        for box in cls.disclaimer:
            for item in box.items:
                if module in item.text:
                    cls.disclaimer.remove(box)

    @classmethod
    def render(
        cls,
        avatar: Image.Image | None = None,
        dark: bool | None = None,
        jpeg: bool = True,
    ) -> bytes:
        """
        Render the disclaimer.

        :param avatar: The avatar to render.
        :param dark: Whether to render in dark mode.
        :param jpeg: Whether to render in jpeg format.
        :return: The rendered disclaimer.
        """

        if (current_hash := cls.get_hash()) == cls.hash and cls.rendered:
            return cls.rendered

        if dark is None:
            dark = is_dark()

        elements: list[Element] = list(cls.disclaimer)

        columns = [
            Column(dark=dark) for _ in range(math.floor(math.sqrt(len(elements))))
        ]

        columns[0].add(Banner(text="免责声明", dark=True))

        if avatar:
            columns[0].add(
                Header(
                    text=f"{config.name}#{config.num}",
                    description=config.description,
                    icon=avatar,
                    dark=dark,
                )
            )

        for element in elements:
            min(columns, key=lambda column: len(column)).add(element, dark=dark)

        rendered = OneUIMock(*columns, dark=dark).render_bytes(jpeg=jpeg)
        cls.rendered = rendered
        cls.hash = current_hash

        return rendered

    @classmethod
    def get_hash(cls) -> int:
        """
        Get the hash of the disclaimers registered.

        :return: The hash of the disclaimer.
        """

        return hash("".join([str(hash(box)) for box in cls.disclaimer]))
