import asyncio
import base64
import random
from abc import ABC, abstractmethod
from base64 import b64decode
from datetime import datetime
from io import BytesIO
from typing import Literal

import playwright
from PIL import Image
from PIL.Image import Resampling
from graia.ariadne import Ariadne
from graia.ariadne.message.element import Image as GraiaImage
from graiax.playwright import PlaywrightBrowser
from loguru import logger
from typing_extensions import Self

from library import __version__, config
from library.image import ImageUtil, TextUtil, IconUtil
from library.image.oneui_mock.color import Color, PALETTE
from library.util.http import html_escape

DEFAULT_WIDTH: int = 800

ICON_BASE: Image.Image = IconUtil.get_icon("oneui-base", color=(0, 0, 0))
SWITCH_ICON_ON: Image.Image = IconUtil.get_icon("oneui-switch-on", color=(0, 0, 0))
SWITCH_ICON_OFF: Image.Image = IconUtil.get_icon("oneui-switch-off", color=(0, 0, 0))
DEFAULT_ICON: Image.Image = IconUtil.get_icon("toy-brick", color=(252, 252, 252))

BOARDER: int = 40
GAP: int = 10


class Element(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def render(self) -> Image.Image:
        """
        Render the element.

        :return: Image.Image
        """

        pass

    @abstractmethod
    def render_bytes(self, jpeg: bool = True) -> bytes:
        """
        Render the element and return bytes.

        :param jpeg: Whether render as JPEG.
        :return: bytes
        """

        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    @abstractmethod
    def generate_html(self) -> str:
        """
        Generate HTML code.

        :return: str
        """

        pass

    @abstractmethod
    def set_dark(self):
        """
        Set the element to dark mode.

        :return: Self
        """

        pass

    @abstractmethod
    def set_light(self):
        """
        Set the element to light mode.

        :return: Self
        """

        pass

    @abstractmethod
    def set_width(self, width: int):
        """
        Set the width of the element.

        :param width: The width to be set.
        :return: Self
        """

        pass


class Banner(Element):
    """
    Banner is what displays at the top of the column.
    Most of the time, it is a text banner, icon is optional.
    """

    TEXT_COLOR: tuple[int, int, int]
    BACKGROUND_COLOR: tuple[int, int, int]

    TEXT_X: int = BOARDER
    TEXT_Y: int = 90
    TEXT_SIZE: int = 40

    ICON_RIGHT_GAP: int = BOARDER
    ICON_SIZE: int = TEXT_SIZE

    width: int
    text: str
    icon: Image.Image | None
    replace_color: bool

    def __init__(
        self,
        text: str,
        icon: Image.Image | None = None,
        *,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
        replace_color: bool = True,
    ):
        """
        :param text: Text to display
        :param icon: Icon to display
        :param width: Width of the banner
        :param dark: Whether the banner is dark or light
        :param replace_color: Whether replace the color of the icon
        """

        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.width = width
        self.text = text
        self.icon = icon
        self.replace_color = replace_color

    def set_dark(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def __len__(self) -> int:
        return 1

    def __hash__(self):
        return hash(self.text + str(hash(self.icon)))

    def render_icon(self) -> Image.Image:
        icon = self.icon.resize((self.ICON_SIZE, self.ICON_SIZE), Resampling.LANCZOS)
        if self.replace_color:
            icon = IconUtil.replace_color(icon, self.TEXT_COLOR)
        return icon

    def render(self) -> Image.Image:
        text_width = self.width - 2 * BOARDER
        if self.icon:
            text_width -= self.ICON_SIZE + BOARDER

        text = TextUtil.render_text(
            self.text,
            self.TEXT_COLOR,
            ImageUtil.get_font(self.TEXT_SIZE),
            width=text_width,
        )
        height = self.TEXT_Y + text.height
        canvas = Image.new("RGBA", (self.width, height), self.BACKGROUND_COLOR)

        if self.icon is not None:
            icon = self.render_icon()
            icon_x = self.width - self.ICON_RIGHT_GAP - self.ICON_SIZE
            icon_y = self.TEXT_Y + (text.height - self.ICON_SIZE) // 2
            if icon.mode == "RGBA":
                canvas.paste(icon, (icon_x, icon_y), mask=icon)
            else:
                canvas.paste(icon, (icon_x, icon_y))

        canvas.paste(
            text,
            (self.TEXT_X, self.TEXT_Y),
            mask=text,
        )

        return canvas

    def render_bytes(self, jpeg: bool = True) -> bytes:
        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_icon_html(self) -> str:
        if not self.icon:
            return ""
        icon = self.render_icon()
        icon_bytes = BytesIO()
        icon.save(icon_bytes, "PNG")
        icon_base64 = base64.b64encode(icon_bytes.getvalue()).decode("utf-8")
        return f"""
            <div>
                <img 
                    src="data:image/png;base64,{icon_base64}" 
                    style="
                        padding-right: {self.ICON_RIGHT_GAP}px; 
                        padding-top: {self.TEXT_Y}px
                    "
                />
            </div>
            """

    def _generate_text_html(self) -> str:
        return f"""
            <div style="
                padding-left: {self.TEXT_X}px; 
                padding-top: {self.TEXT_Y}px; 
                padding-right: {BOARDER}px; 
                text-align: left; 
                font-size: {self.TEXT_SIZE}px
            ">
                {html_escape(self.text)}
            </div>
            """

    def generate_html(self) -> str:
        icon = self._generate_icon_html()
        text = self._generate_text_html()
        return f"""
            <div style="
                color: rgb{self.TEXT_COLOR}; 
                background-color: rgb{self.BACKGROUND_COLOR}; 
                width: {self.width}px; 
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px; 
                display: flex; 
                align-items: center; 
                justify-content: space-between
            ">
                {text}
                {icon}
            </div>
            """


class Header(Element):
    """
    Header is what displays below the banner, but above the content.
    """

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]

    TEXT_SIZE: int = 40
    DESCRIPTION_SIZE: int = 25

    ICON_BOARDER: int = GAP
    ICON_SIZE = 125

    width: int
    text: str
    description: str
    icon: Image.Image | None

    def __init__(
        self,
        text: str,
        description: str,
        icon: Image.Image | None = None,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param text: Text to display
        :param description: Description to display
        :param icon: Icon to display
        :param width: Width of the header
        :param dark: Whether the header is dark or light
        """

        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.width = width
        self.text = text
        self.description = description
        self.icon = icon

    def set_dark(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def __len__(self) -> int:
        return 1

    def __hash__(self):
        return hash(self.text + self.description + str(hash(self.icon)))

    def render(self) -> Image.Image:
        text_width = self.width - 2 * BOARDER
        if self.icon:
            text_width -= self.ICON_SIZE + BOARDER

        text = TextUtil.render_text(
            self.text,
            self.TEXT_COLOR,
            ImageUtil.get_font(self.TEXT_SIZE),
            width=text_width,
        )
        description = TextUtil.render_text(
            self.description,
            self.DESCRIPTION_COLOR,
            ImageUtil.get_font(self.DESCRIPTION_SIZE),
            width=text_width,
        )
        height = BOARDER * 2 + text.height + GAP + description.height
        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)

        if self.icon is not None:

            if canvas.height < self.ICON_SIZE + 2 * self.ICON_BOARDER:
                icon_size = canvas.height - 2 * self.ICON_BOARDER
            else:
                icon_size = self.ICON_SIZE

            icon = ImageUtil.round_corners(
                self.icon.resize((icon_size, icon_size), Resampling.LANCZOS),
                radius=self.ICON_SIZE // 2,
            )

            icon_x = self.width - icon_size - BOARDER
            icon_y = (canvas.height - icon_size) // 2

            if icon.mode == "RGBA":
                canvas.paste(icon, (icon_x, icon_y), mask=icon)
            else:
                canvas.paste(icon, (icon_x, icon_y))

        canvas.paste(
            text,
            (BOARDER, BOARDER),
            mask=text,
        )
        canvas.paste(
            description,
            (
                BOARDER,
                BOARDER + text.height + GAP,
            ),
            mask=description,
        )

        return ImageUtil.round_corners(canvas, radius=BOARDER)

    def render_bytes(self, jpeg: bool = True) -> bytes:
        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_icon_html(self) -> str:
        if self.icon is None:
            return ""
        icon_bytes = BytesIO()
        self.icon.save(icon_bytes, "PNG")
        icon_base64 = base64.b64encode(icon_bytes.getvalue()).decode("utf-8")
        return f"""
            <div>
                <img 
                    width={self.ICON_SIZE}px 
                    height={self.ICON_SIZE}px 
                    src="data:image/png;base64,{icon_base64}" 
                    style="border-radius: 50%"
                />
            </div>
            """

    def _generate_text_html(self) -> str:
        return f"""
            <div style="padding-right: {BOARDER}px">
                <div style="
                    font-size: {self.TEXT_SIZE}px; 
                    font-weight: bold; 
                    color: rgb{self.TEXT_COLOR}; 
                ">
                    {html_escape(self.text)}
                </div>
                <div style="
                    font-size: {self.DESCRIPTION_SIZE}px; 
                    color: rgb{self.DESCRIPTION_COLOR}
                ">
                    {html_escape(self.description)}
                    </div>
            </div>
            """

    def generate_html(self) -> str:
        icon = self._generate_icon_html()
        text = self._generate_text_html()
        return f"""
            <div style="
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {GAP}px
            ">
                <div style="
                    width: {self.width - BOARDER * 2}px; 
                    border-radius: {BOARDER}px; 
                    background-color: rgb{self.FOREGROUND_COLOR}; 
                    display: flex; 
                    align-items: center; 
                    padding: {BOARDER}px; 
                    justify-content: space-between
                ">
                    {text}
                    {icon}
                </div>
            </div>
            """


class ProgressBar(Element):
    """
    Progress bar is what displays the progress of a task.
    """

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    HIGHLIGHT_COLOR: tuple[int, int, int]
    SECONDARY_HIGHLIGHT_COLOR: tuple[int, int, int]

    TEXT_SIZE: int = 35
    DESCRIPTION_SIZE: int = 25

    width: int
    percentage: float
    text: str | None = None
    description: str | None = None

    def __init__(
        self,
        percentage: float,
        text: str | None = None,
        description: str | None = None,
        *,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        super().__init__()
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        if percentage < 0:
            percentage = -percentage
        self.percentage = percentage
        self.text = text
        self.description = description
        self.width = width

    def __len__(self):
        return 1

    def __hash__(self):
        return hash(f"ProgressBar{self.width}{self.percentage}")

    def set_dark(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        self.SECONDARY_HIGHLIGHT_COLOR = Color.SECONDARY_HIGHLIGHT_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.SECONDARY_HIGHLIGHT_COLOR = Color.SECONDARY_HIGHLIGHT_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def render_base(self) -> Image.Image:
        base = Image.new("RGBA", size=(1000, 1), color=self.SECONDARY_HIGHLIGHT_COLOR)
        if self.percentage == 0:
            return base
        front = Image.new(
            "RGBA",
            size=(int(self.percentage * 10 // 1), base.height),
            color=self.HIGHLIGHT_COLOR,
        )
        base.paste(front, mask=front)
        return base

    def render(self) -> Image.Image:
        bar = self.render_base().resize((self.width - BOARDER * 2, BOARDER))
        bar = ImageUtil.round_corners(bar, bar.height // 2)

        height = BOARDER * 2 + bar.height
        text = None
        description = None

        if self.text:
            text = TextUtil.render_text(
                self.text,
                self.TEXT_COLOR,
                ImageUtil.get_font(self.TEXT_SIZE),
                width=self.width - BOARDER * 2,
            )
            height += text.height + GAP * 2
        if self.description:
            description = TextUtil.render_text(
                self.description,
                self.DESCRIPTION_COLOR,
                ImageUtil.get_font(self.DESCRIPTION_SIZE),
                width=self.width - BOARDER * 2,
            )
            height += description.height + GAP * 2

        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)

        _h = BOARDER
        if text:
            canvas.paste(text, (BOARDER, _h), mask=text)
            _h += text.height + GAP * 2
        canvas.paste(bar, (BOARDER, _h), mask=bar)
        _h += bar.height + GAP * 2
        if description:
            canvas.paste(description, (BOARDER, _h), mask=description)
        return ImageUtil.round_corners(canvas, radius=BOARDER)

    def render_bytes(self, jpeg: bool = True) -> bytes:
        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_text_html(self) -> str:
        return (
            f"""
            <div style="
                width: {self.width - BOARDER * 2}px; 
                padding-left: {BOARDER}px; 
                padding-right: {BOARDER}px; 
                padding-bottom: {GAP}px; 
                font-size: {self.TEXT_SIZE}px; 
                color: rgb{self.TEXT_COLOR}
            ">
                {html_escape(self.text)}
            </div>
            """
            if self.text
            else ""
        )

    def _generate_description_html(self) -> str:
        return (
            f"""
            <div style="
                width: {self.width - BOARDER * 2}px; 
                padding-left: {BOARDER}px; 
                padding-right: {BOARDER}px; 
                padding-top: {GAP}px; 
                font-size: {self.DESCRIPTION_SIZE}px; 
                color: rgb{self.DESCRIPTION_COLOR}
            ">
                {html_escape(self.description)}
            </div>
            """
            if self.description
            else ""
        )

    def _generate_progress_bar_html(self) -> str:
        return f"""
            <div style="
                width: {self.width - BOARDER * 2}px; 
                height: {BOARDER}px; 
                border-radius: {BOARDER}px; 
                background-color: rgb{self.SECONDARY_HIGHLIGHT_COLOR}; 
                overflow: hidden
            ">
                <div style="
                    width: {self.percentage}%; 
                    height: 100%; 
                    background-color: rgb{self.HIGHLIGHT_COLOR}; 
                ">
                </div>
            </div>
            """

    def generate_html(self) -> str:
        progress_bar = self._generate_progress_bar_html()
        text = self._generate_text_html()
        description = self._generate_description_html()
        return f"""
            <div style="
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px
            ">
                <div style="
                    width: {self.width - BOARDER * 2}px; 
                    padding-top: {BOARDER}px; 
                    padding-bottom: {BOARDER}px
                ">
                    {text}
                    <div style="
                        width: {self.width - BOARDER * 2}px; 
                        padding-left: {BOARDER}px; 
                        padding-right: {BOARDER}px
                    ">
                        {progress_bar}
                    </div>
                    {description}
                </div>
            </div>"""


class Box(Element):
    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def add(self, *_, **__):
        pass

    @abstractmethod
    def has_content(self) -> bool:
        """
        :return: Whether the box has content
        """

        pass


class MenuBoxItem(Element):

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]

    TEXT_SIZE: int = 35
    DESCRIPTION_SIZE = 25
    ICON_SIZE = BOARDER + GAP * 3

    width: int
    text: str | None
    description: str | None
    icon: Image.Image | None
    icon_color: tuple[int, int, int] | Literal[True] | None

    def __init__(
        self,
        text: str | None,
        description: str | None,
        icon: Image.Image | None = None,
        icon_color: tuple[int, int, int] | Literal[True] | None = None,
        *,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        super().__init__()
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()

        self.width = width
        self.text = text
        self.description = description
        self.icon = icon
        self.icon_color = icon_color

    def __len__(self):
        return 1

    def __hash__(self):
        return hash(
            str(hash(f"MenuBoxItem{self.text}{self.description}{self.icon_color}"))
            + str(hash(self.icon))
        )

    def set_dark(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def render_icon(self) -> Image.Image | None:
        if self.icon is None:
            return None
        color = self.icon_color
        if isinstance(color, bool):
            palette = random.choice(PALETTE)
            _ = palette.replace("#", "")
            color = (int(_[:2], 16), int(_[2:4], 16), int(_[4:6], 16))
        elif color is None:
            size = ICON_BASE.size[0] // 4 * 3, ICON_BASE.size[1] // 4 * 3
            return self.icon.resize(size, Resampling.LANCZOS)
        icon = IconUtil.replace_color(self.icon, (252, 252, 252))
        base = IconUtil.replace_color(ICON_BASE, color)
        size = base.size[0] // 3 * 2, base.size[1] // 3 * 2
        icon = icon.resize(size, Resampling.LANCZOS)
        icon = ImageUtil.paste_to_center(base, icon)
        return icon

    def render(self, round_corners: bool = False) -> Image.Image:
        height = BOARDER * 2
        text = None
        description = None
        if self.text:
            text = TextUtil.render_text(
                self.text,
                self.TEXT_COLOR,
                ImageUtil.get_font(self.TEXT_SIZE),
                width=self.width - self.ICON_SIZE - BOARDER * 3 + GAP,
            )
            height += text.height
        if self.description:
            description = TextUtil.render_text(
                self.description,
                self.DESCRIPTION_COLOR,
                ImageUtil.get_font(self.DESCRIPTION_SIZE),
                width=self.width - self.ICON_SIZE - BOARDER * 3 + GAP,
            )
            height += description.height
        if text and description:
            height += GAP
        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)

        if icon := self.render_icon():
            icon = icon.resize((self.ICON_SIZE, self.ICON_SIZE))
            icon_x = BOARDER
            icon_y = (canvas.height - icon.height) // 2
            if icon.mode == "RGBA":
                canvas.paste(icon, (icon_x, icon_y), mask=icon)
            else:
                canvas.paste(icon, (icon_x, icon_y))

        _h = BOARDER
        if text:
            canvas.paste(text, (BOARDER * 3 + GAP * 2, _h), mask=text)
            _h += text.height + GAP
        if description:
            canvas.paste(description, (BOARDER * 3 + GAP * 2, _h), mask=description)
            _h += description.height + GAP

        if round_corners:
            return ImageUtil.round_corners(canvas, radius=BOARDER)
        return canvas

    def render_bytes(self, jpeg: bool = True, round_corners: bool = False) -> bytes:
        canvas = self.render(round_corners=round_corners)
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_icon_html(self) -> str:
        if self.icon is None:
            return ""
        color = self.icon_color
        if isinstance(color, bool):
            palette = random.choice(PALETTE)
            _ = palette.replace("#", "")
            color = (int(_[:2], 16), int(_[2:4], 16), int(_[4:6], 16))
        elif color is None:
            size = ICON_BASE.size[0] // 4 * 3, ICON_BASE.size[1] // 4 * 3
            icon = self.icon.resize(size, Resampling.LANCZOS)
            icon_bytes = BytesIO()
            icon.save(icon_bytes, "PNG")
            return (
                f'<img src="data:image/png;base64,'
                f'{base64.b64encode(icon_bytes.getvalue()).decode()}" '
                f'style="width: {self.ICON_SIZE}px; height: {self.ICON_SIZE}px">'
            )
        icon = IconUtil.replace_color(self.icon, (252, 252, 252))
        base = IconUtil.replace_color(ICON_BASE, color)
        size = base.size[0] // 3 * 2, base.size[1] // 3 * 2
        icon = icon.resize(size, Resampling.LANCZOS)
        icon = ImageUtil.paste_to_center(base, icon)
        icon_bytes = BytesIO()
        icon.save(icon_bytes, "PNG")
        return f"""
            <img 
                src="data:image/png;base64,{base64.b64encode(icon_bytes.getvalue()).decode()}" 
                style="
                    width: {self.ICON_SIZE}px; 
                    height: {self.ICON_SIZE}px
                "
            >
            """

    def _generate_title_html(self) -> str:
        if self.text is None:
            return ""
        return f"""
            <div style="
                padding-top: {BOARDER}px; 
                font-size: {self.TEXT_SIZE}px; 
                color: rgb{self.TEXT_COLOR}; 
                width: {self.width - self.ICON_SIZE - BOARDER * 3}px; 
                word-wrap: break-word
            ">
                {html_escape(self.text)}
            </div>
            """

    def _generate_description_html(self) -> str:
        if self.description is None:
            return ""
        return f"""
            <div style="
                font-size: {self.DESCRIPTION_SIZE}px; 
                padding-bottom: {BOARDER}px;
                color: rgb{self.DESCRIPTION_COLOR}; 
                width: {self.width - self.ICON_SIZE - BOARDER * 3}px; 
                word-wrap: break-word
            ">
                {html_escape(self.description)}
            </div>
            """

    def generate_html(self) -> str:
        icon = self._generate_icon_html()
        title = self._generate_title_html()
        description = self._generate_description_html()
        return f"""
            <div style="
                width: {self.width}px; 
                background-color: rgb{self.FOREGROUND_COLOR}; 
                display: flex; 
                align-items: center; 
                border-radius: {BOARDER}px
            ">
                <div style="padding: {BOARDER}px">
                    {icon}
                </div>
                <div>
                    {title}
                    {description}
                </div>
            </div>
            """


class MenuBox(Box):
    """
    A box that mostly used in the menu.
    Each item should have a title, a description, and an icon.
    Each text should be in one line for better display.
    """

    NAME_SIZE: int = 25

    NAME_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    BACKGROUND_COLOR: tuple[int, int, int]
    LINE_COLOR: tuple[int, int, int]

    width: int
    items: list[MenuBoxItem | Element]
    name: str | None

    def __init__(
        self,
        text: str = None,
        description: str = None,
        icon: Image.Image | None = None,
        icon_color: tuple[int, int, int] | Literal[True] | None = True,
        *,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
        name: str | None = None,
    ):
        """
        :param text: Text to display
        :param description: Description to display
        :param icon: Icon to display
        :param icon_color: Color of the icon, True if random color
        :param width: Width of the box
        :param dark: Whether the box is dark or light
        """

        super().__init__()
        self.items = []
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()

        self.width = width
        self.name = name
        if name is None and description is None:
            return
        self.items.append(
            MenuBoxItem(
                text=text,
                description=description,
                icon=icon,
                icon_color=icon_color,
                width=width,
                dark=dark,
            )
        )

    def set_dark(self) -> Self:
        self.NAME_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        self.LINE_COLOR = Color.LINE_COLOR_DARK
        for item in self.items:
            item.set_dark()
        return self

    def set_light(self) -> Self:
        self.NAME_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.LINE_COLOR = Color.LINE_COLOR_LIGHT
        for item in self.items:
            item.set_light()
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        for item in self.items:
            item.set_width(width)
        return self

    def set_name(self, name: str | None) -> Self:
        """
        Set the name of the box.

        :param name: The name to be set
        :return: Self
        """

        self.name = name
        return self

    def __len__(self) -> int:
        return len(self.items)

    def __hash__(self):
        return hash("".join([str(hash(item)) for item in self.items]))

    def has_content(self) -> bool:
        return len(self.items) > 0

    def add(
        self,
        text: str | None = None,
        description: str | None = None,
        icon: Image.Image | None = None,
        icon_color: tuple[int, int, int] | Literal[True] | None = None,
        *,
        element: Element = None,
        sub: bool = True,
    ) -> Self:
        """
        Add an item to the box.

        :param text: The text to display.
        :param description: The description to display.
        :param icon: The icon to display.
        :param icon_color: The color of the icon.
        :param element: The element to be added.
        :param sub: Whether the element is in the sub-level.
        :return: The box itself.
        """

        if text or description:
            self.items.append(
                MenuBoxItem(
                    text=text,
                    description=description,
                    icon=icon,
                    icon_color=icon_color,
                    width=self.width,
                )
            )
        elif element:
            self.items.append(
                element.set_width(self.width - BOARDER * 2 if sub else self.width)
            )
        return self

    def render(self) -> Image.Image | None:
        if not self.has_content():
            return
        items = [item.render() for item in self.items]
        height = sum(item.height for item in items)

        name = None
        base = None
        if self.name:
            name = TextUtil.render_text(
                self.name,
                self.NAME_COLOR,
                ImageUtil.get_font(self.NAME_SIZE),
                width=self.width - BOARDER * 2,
            )
            base = Image.new(
                "RGBA", (self.width, height + name.height + GAP), self.BACKGROUND_COLOR
            )

        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)
        _h = 0
        lines = []
        for item in items:
            canvas.paste(item, ((canvas.width - item.width) // 2, _h), mask=item)
            _h += item.height
            lines.append(_h)
        for line in lines:
            canvas = ImageUtil.draw_line(
                canvas,
                BOARDER * 3 + GAP * 2,
                line,
                canvas.width - BOARDER,
                line,
                color=self.LINE_COLOR,
                width=1,
            )

        canvas = ImageUtil.round_corners(canvas, radius=BOARDER)
        if not name:
            return canvas
        base.paste(name, (BOARDER, 0), mask=name)
        base.paste(canvas, (0, name.height + GAP), mask=canvas)
        return base

    def render_bytes(self, jpeg: bool = True) -> bytes | None:
        if (canvas := self.render()) is None:
            return
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_name_html(self) -> str:
        return (
            f"""
            <div style="
                width: {self.width - BOARDER * 2}px; 
                color: rgb{self.NAME_COLOR}; 
                padding-left: {BOARDER}px; 
                overflow: hidden; 
                text-overflow: ellipsis; 
                white-space: nowrap; 
                font-size: {self.NAME_SIZE}px
            ">
                {html_escape(self.name)}
            </div>
            """
            if self.name
            else ""
        )

    def generate_html(self) -> str:
        if not self.has_content():
            return ""
        name = self._generate_name_html()
        items = [item.generate_html() for item in self.items]
        divider = f"""
            <div style="
                height: 3px; 
                background-color: rgb{self.LINE_COLOR}; 
                margin-left: {BOARDER * 3 + GAP * 3}px; 
                margin-right: {BOARDER}px
            ">
            </div>
            """
        for i in range(len(items) - 1):
            items[i] += divider
        return f"""
            <div style="
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px
            ">
                {name}
                <div style="
                    width: {self.width}px; 
                    background-color: rgb{self.FOREGROUND_COLOR}; 
                    border-radius: {BOARDER}px
                ">
                    {"".join(items)}
                </div>
            </div>"""


class GeneralBoxItem(Element):

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    HIGHLIGHT_COLOR: tuple[int, int, int]
    SWITCH_ENABLED: tuple[int, int, int]
    SWITCH_DISABLED: tuple[int, int, int]

    TEXT_SIZE: int = 35
    SWITCH_WIDTH: int = 75
    DESCRIPTION_SIZE = 25
    UPPER_BOARDER: int = BOARDER // 2

    width: int
    text: str | None
    description: str | None
    highlight: bool
    switch: bool | None

    def __init__(
        self,
        text: str | None,
        description: str | None,
        highlight: bool = False,
        switch: bool | None = None,
        *,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        super().__init__()
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()

        self.width = width
        self.text = text
        self.description = description
        self.highlight = highlight
        self.switch = switch

    def __len__(self):
        return 1

    def __hash__(self):
        return hash(str(hash(f"GeneralBoxItem{self.text}{self.description}")))

    def set_dark(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_DARK
        self.SWITCH_ENABLED = Color.SWITCH_ENABLE_COLOR
        self.SWITCH_DISABLED = Color.SWITCH_DISABLE_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_LIGHT
        self.SWITCH_ENABLED = Color.SWITCH_ENABLE_COLOR
        self.SWITCH_DISABLED = Color.SWITCH_DISABLE_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def render(self, round_corners: bool = False) -> Image.Image | None:
        if not self.text and not self.description:
            return
        height = self.UPPER_BOARDER * 2
        switch = None
        text = None
        description = None
        if isinstance(self.switch, bool):
            switch = SWITCH_ICON_ON if self.switch else SWITCH_ICON_OFF
            switch = IconUtil.replace_color(
                switch, self.SWITCH_ENABLED if self.switch else self.SWITCH_DISABLED
            )

            switch_height = switch.height * self.SWITCH_WIDTH // switch.width
            switch = switch.resize((self.SWITCH_WIDTH, switch_height))
            text_width = self.width - BOARDER * 3 - switch.width
        else:
            text_width = self.width - BOARDER * 2
        if self.text:
            text = TextUtil.render_text(
                self.text,
                self.TEXT_COLOR,
                ImageUtil.get_font(self.TEXT_SIZE),
                width=text_width,
            )
            height += text.height
        if self.description:
            description = TextUtil.render_text(
                self.description,
                self.HIGHLIGHT_COLOR if self.highlight else self.DESCRIPTION_COLOR,
                ImageUtil.get_font(self.DESCRIPTION_SIZE),
                width=text_width,
            )
            height += description.height
        if text and description:
            height += GAP
        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)
        _h = self.UPPER_BOARDER
        if text:
            canvas.paste(text, (BOARDER, _h), mask=text)
            _h += text.height + GAP
        if description:
            canvas.paste(description, (BOARDER, _h), mask=description)
            _h += description.height + GAP
        if switch:
            canvas.paste(
                switch,
                (
                    canvas.width - BOARDER - switch.width,
                    (canvas.height - switch.height) // 2,
                ),
                mask=switch,
            )

        if round_corners:
            return ImageUtil.round_corners(canvas, radius=BOARDER)
        return canvas

    def render_bytes(
        self, jpeg: bool = True, round_corners: bool = False
    ) -> bytes | None:
        canvas = self.render(round_corners=round_corners)
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_switch_html(self) -> str:
        if self.switch is None:
            return ""
        switch = SWITCH_ICON_ON if self.switch else SWITCH_ICON_OFF
        switch = IconUtil.replace_color(
            switch, self.SWITCH_ENABLED if self.switch else self.SWITCH_DISABLED
        )
        switch_height = switch.height * self.SWITCH_WIDTH // switch.width
        switch = switch.resize((self.SWITCH_WIDTH, switch_height))
        switch_bytes = BytesIO()
        switch.save(switch_bytes, "PNG")
        return f"""
            <div style="
                margin-left: {BOARDER}px
            ">
                <img src="data:image/png;base64,{base64.b64encode(switch_bytes.getvalue()).decode()}" />
            </div>
            """

    def _generate_text_html(self) -> str:
        width = self.width - BOARDER * 2
        if self.switch is not None:
            width -= self.SWITCH_WIDTH + BOARDER
        return (
            f"""
            <div style="
                width: {width}px;
                word-wrap: break-word; 
                font-size: {self.TEXT_SIZE}px; 
                color: rgb{self.TEXT_COLOR}
            ">
                {html_escape(self.text)}
            </div>
            """
            if self.text
            else ""
        )

    def _generate_description_html(self) -> str:
        width = self.width - BOARDER * 2
        if self.switch is not None:
            width -= self.SWITCH_WIDTH + BOARDER
        return (
            f"""
            <div style="
                width: {width}px;
                word-wrap: break-word; 
                font-size: {self.DESCRIPTION_SIZE}px; 
                color: rgb{self.HIGHLIGHT_COLOR if self.highlight else self.DESCRIPTION_COLOR}
            ">
                {html_escape(self.description)}
            </div>
            """
            if self.description
            else ""
        )

    def generate_html(self) -> str:
        switch = self._generate_switch_html()
        text = self._generate_text_html()
        description = self._generate_description_html()
        if text or description:
            return f"""
                <div style="
                    width: {self.width}px; 
                    background-color: rgb{self.FOREGROUND_COLOR}; 
                    display: flex; 
                    align-items: center; 
                    border-radius: {BOARDER}px
                ">
                    <div style="
                        display: flex; 
                        justify-content: space-between; 
                        align-items: center; 
                        width: {self.width}px; 
                        margin: {BOARDER}px
                    ">
                        <div>
                            {text}
                            {description}
                        </div>
                        {switch}
                    </div>
                </div>
                """
        else:
            return ""


class GeneralBox(Box):
    """
    A box that displays a general text.
    Each item should have a text and a description, switch icon is optional.
    """

    NAME_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    BACKGROUND_COLOR: tuple[int, int, int]
    LINE_COLOR: tuple[int, int, int]

    NAME_SIZE: int = 30

    width: int
    items: list[GeneralBoxItem | Element]
    name: str | None

    def __init__(
        self,
        text: str = None,
        description: str | None = None,
        switch: bool | None = None,
        highlight: bool = False,
        *,
        name: str = None,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param text: Text to display
        :param description: Description to display
        :param switch: Switch to display
        :param width: Width of the box
        :param dark: Whether the box is dark or light
        """

        super().__init__()
        self.items = []
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.width = width
        self.name = name
        if text or description:
            self.items.append(
                GeneralBoxItem(
                    text=text,
                    description=description,
                    highlight=highlight,
                    switch=switch,
                    width=width,
                    dark=dark,
                )
            )

    def set_dark(self) -> "GeneralBox":
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        self.NAME_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.LINE_COLOR = Color.LINE_COLOR_DARK
        for item in self.items:
            item.set_dark()
        return self

    def set_light(self) -> "GeneralBox":
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.NAME_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.LINE_COLOR = Color.LINE_COLOR_LIGHT
        for item in self.items:
            item.set_light()
        return self

    def set_width(self, width: int) -> "GeneralBox":
        self.width = width
        for item in self.items:
            item.set_width(width)
        return self

    def set_name(self, name: str | None) -> "GeneralBox":
        self.name = name
        return self

    def __len__(self):
        return len(self.items)

    def __hash__(self):
        return hash("".join([str(hash(item)) for item in self.items]))

    def has_content(self) -> bool:
        return len(self.items) > 0

    def add(
        self,
        text: str = None,
        description: str | None = None,
        switch: bool | None = None,
        highlight: bool | None = None,
        *,
        element: Element = None,
        sub: bool = True,
    ) -> "GeneralBox":
        """
        Add a new item to the box.
        :param text: Text to display
        :param description: Description to display
        :param switch: Switch to display
        :param highlight: Whether the item is highlighted
        :param element: The element to be added
        :param sub: Whether the element is in sub-level
        :return: The box itself
        """

        if text or description:
            self.items.append(
                GeneralBoxItem(
                    text=text,
                    description=description,
                    switch=switch,
                    highlight=highlight,
                    width=self.width,
                )
            )
        elif element:
            self.items.append(
                element.set_width(self.width - BOARDER * 2 if sub else self.width)
            )
        return self

    def render(self) -> Image.Image | None:
        if not self.has_content():
            return
        items = [item.render() for item in self.items]
        height = sum(item.height for item in items)

        name = None
        base = None
        if self.name:
            name = TextUtil.render_text(
                self.name,
                self.NAME_COLOR,
                ImageUtil.get_font(self.NAME_SIZE),
                width=self.width - BOARDER * 2,
            )
            base = Image.new(
                "RGBA", (self.width, height + name.height + GAP), self.BACKGROUND_COLOR
            )

        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)
        _h = 0
        lines = []
        for item in items:
            canvas.paste(item, ((canvas.width - item.width) // 2, _h), mask=item)
            _h += item.height
            lines.append(_h)
        for line in lines:
            canvas = ImageUtil.draw_line(
                canvas,
                BOARDER,
                line,
                canvas.width - BOARDER,
                line,
                color=self.LINE_COLOR,
                width=1,
            )

        canvas = ImageUtil.round_corners(canvas, radius=BOARDER)
        if not name:
            return canvas
        base.paste(name, (BOARDER, 0), mask=name)
        base.paste(canvas, (0, name.height + GAP), mask=canvas)
        return base

    def render_bytes(self, jpeg: bool = True) -> bytes | None:
        if (canvas := self.render()) is None:
            return
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_name_html(self) -> str:
        return (
            f"""
            <div style="
                width: {self.width - BOARDER * 2}px; 
                color: rgb{self.NAME_COLOR}; 
                padding-left: {BOARDER}px; 
                overflow: hidden; 
                text-overflow: ellipsis; 
                white-space: nowrap; 
                font-size: {self.NAME_SIZE}px
            ">
                {html_escape(self.name)}
            </div>
            """
            if self.name
            else ""
        )

    def generate_html(self) -> str:
        if not self.has_content():
            return ""
        name = self._generate_name_html()
        items = [item.generate_html() for item in self.items]
        divider = f"""
            <div style="
                height: 3px; 
                background-color: rgb{self.LINE_COLOR}; 
                margin-left: {BOARDER}px; 
                margin-right: {BOARDER}px
            ">
            </div>
            """
        for i in range(len(items) - 1):
            items[i] += divider
        return f"""
            <div style="
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px
            ">
                {name}
                <div style="
                    width: {self.width}px; 
                    background-color: rgb{self.FOREGROUND_COLOR}; 
                    border-radius: {BOARDER}px
                ">
                    {"".join(items)}
                </div>
            </div>
            """


class HintBox(Box):
    """
    A box that displays a highlighted text.
    """

    width: int = ...

    TEXT_COLOR: tuple[int, int, int]
    HIGHLIGHT_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]

    TITLE_SIZE: int = 35
    TEXT_SIZE: int = 30

    title: str | None
    hints: list[str]

    def __init__(
        self,
        title: str | None,
        *hint: str,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param title: Title text
        :param hint: Hints to display
        :param width: Width of the box
        :param dark: Whether the box is dark
        """

        super().__init__()
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.width = width
        self.title = title
        self.hints = list(hint)

    def set_dark(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.FOREGROUND_COLOR = Color.HINT_COLOR_DARK
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.HINT_COLOR_LIGHT
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def __len__(self):
        return len(self.hints) + bool(self.title)

    def __hash__(self):
        return hash(self.title + str(self.hints))

    def has_content(self) -> bool:
        return len(self.hints) + bool(self.title) > 0

    def add(self, *hints: str) -> Self:
        self.hints.extend(hints)
        return self

    def render(self) -> Image.Image | None:
        if not self.has_content():
            return
        height = BOARDER * 2
        title = None
        hints = []
        if self.title:
            title = TextUtil.render_text(
                self.title,
                self.TEXT_COLOR,
                ImageUtil.get_font(self.TITLE_SIZE),
                width=self.width - BOARDER * 2,
            )
            height += title.height
        for hint in self.hints:
            hint = TextUtil.render_text(
                hint,
                self.HIGHLIGHT_COLOR,
                ImageUtil.get_font(self.TEXT_SIZE),
                width=self.width - BOARDER * 2,
            )
            hints.append(hint)
            height += hint.height

        if hints:
            height += BOARDER * (len(hints) - 1)
            if title:
                height += BOARDER

        canvas = Image.new("RGBA", (self.width, height), self.FOREGROUND_COLOR)

        _h = BOARDER
        if title:
            canvas.paste(title, (BOARDER, _h), mask=title)
            _h += title.height + BOARDER

        for hint in hints:
            canvas.paste(hint, (BOARDER, _h), mask=hint)
            _h += hint.height + BOARDER

        return ImageUtil.round_corners(canvas, radius=BOARDER)

    def render_bytes(self, jpeg: bool = True) -> bytes | None:
        if (canvas := self.render()) is None:
            return
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def _generate_title_html(self) -> str:
        return (
            f"""
            <div style="
                width: {self.width - BOARDER * 2}px; 
                color: rgb{self.TEXT_COLOR}; 
                padding-bottom: {GAP}px; 
                font-size: {self.TITLE_SIZE}px
            ">
                {html_escape(self.title)}
            </div>
            """
            if self.title
            else ""
        )

    def _generate_hint_html(self, hint: str) -> str:
        return f"""
            <div style="
                word-wrap: break-word;
                width: {self.width - BOARDER * 2}px; 
                color: rgb{self.HIGHLIGHT_COLOR}; 
                padding-top: {GAP}px; 
                font-size: {self.TEXT_SIZE}px
            ">
                {html_escape(hint)}
            </div>
            """

    def generate_html(self) -> str:
        if not self.has_content():
            return ""
        title = self._generate_title_html()
        hints = [self._generate_hint_html(hint) for hint in self.hints]
        return f"""
            <div style="
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px
            ">
                <div style="
                    width: {self.width - BOARDER * 2}px; 
                    padding: {BOARDER}px; 
                    background-color: rgb{self.FOREGROUND_COLOR}; 
                    border-radius: {BOARDER}px
                ">
                    {title}
                    {"".join(hints)}
                </div>
            </div>
            """


class ImageBox(Box):

    width: int
    MAX_HEIGHT_PER_COLLAGE: int
    single_bypass: bool

    collage: list[list[Image]]
    collage_setting: list[tuple[int, int | None] | None]
    transparent: bool
    crop: bool

    LINE_COLOR: tuple[int, int, int]
    BACKGROUND_COLOR: tuple[int, int, int]

    def __init__(
        self,
        *elements: Image.Image | list[Image.Image],
        width: int = DEFAULT_WIDTH,
        max_height: int = None,
        single_bypass: bool = True,
        dark: bool = None,
        transparent: bool = True,
        crop: bool = True,
    ):
        super().__init__()
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()

        self.MAX_HEIGHT_PER_COLLAGE = max_height or width
        self.width = width
        self.single_bypass = single_bypass
        self.transparent = transparent
        self.crop = crop
        self.collage = [[]]
        self.collage_setting = [None]
        self.add(*elements)

    def __len__(self):
        return len(self.collage)

    def __hash__(self):
        return hash(str(hash(image)) for image in self.extract())

    def add(
        self, *elements: Image.Image | list[Image.Image], index: int = None
    ) -> Self:
        for element in elements:
            if isinstance(element, Image.Image):
                self.collage[index if index is not None else -1].append(element)
                continue
            elif isinstance(element, list):
                if element := [
                    _element
                    for _element in element
                    if isinstance(_element, Image.Image)
                ]:
                    self.collage.append(element)
                    self.collage_setting.append(None)
        return self

    def extract(self) -> list[Image.Image]:
        images: list[Image.Image] = []
        for collage in self.collage:
            images.extend(collage)
        return images

    def has_content(self) -> bool:
        return bool(self.extract())

    def set_dark(self) -> Self:
        self.LINE_COLOR = Color.LINE_COLOR_DARK
        self.BACKGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        return self

    def set_light(self) -> Self:
        self.LINE_COLOR = Color.LINE_COLOR_LIGHT
        self.BACKGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        return self

    def set_collage(self, left: int, right: int | None, index: int = -1) -> Self:
        """
        Set the collage mode of the box.

        :param left: Number of images on the left
        :param right: Number of images on the right
        :param index: Index of collage to be set
        :return: self
        """

        self.collage_setting[index] = (left, right)
        return self

    def resize_image(self, image: Image.Image) -> Image.Image:
        width = self.width
        height = int(image.height * width / image.width)
        return image.resize((width, height))

    def crop_image(self, image: Image.Image, width: int, height: int) -> Image.Image:
        if not self.crop:
            return image.resize((width, height))

        ratio = width / height
        if image.width / image.height < ratio:
            new_width = width
            new_height = int(image.height * width / image.width)
            left = 0
            upper = int((new_height - height) / 2)
            right = new_width
            lower = int((new_height + height) / 2)
        else:
            new_width = int(image.width * height / image.height)
            new_height = height
            left = int((new_width - width) / 2)
            upper = 0
            right = int((new_width + width) / 2)
            lower = new_height
        return image.resize((new_width, new_height)).crop((left, upper, right, lower))

    def combine_images(self, images: list[Image.Image]) -> Image.Image:
        height = sum(image.height for image in images)
        base = Image.new("RGBA", (self.width, height), self.BACKGROUND_COLOR)
        _h = 0
        lines = []
        for image in images:
            if image.mode == "RGBA":
                base.paste(image, (0, _h), mask=image)
            else:
                base.paste(image, (0, _h))
            _h += image.height
            lines.append(_h)
        for line in lines:
            base = ImageUtil.draw_line(
                base, 0, line, base.width, line, color=self.LINE_COLOR, width=1
            )
        return base

    def render_collage(self, index: int) -> Image.Image | None:
        if not (collage := self.collage[index]):
            return
        if len(collage) == 1 and self.single_bypass:
            img: Image.Image = collage[0]
            new_width = self.width
            new_height = img.height * self.width // img.width
            return img.resize((new_width, new_height))

        if not (collage_setting := self.collage_setting[index]):
            images = [self.resize_image(image) for image in collage]
            if not images:
                return
            return self.combine_images(images)

        left_count, right_count = collage_setting
        right_count = left_count + right_count if right_count is not None else -1
        left_images = collage[:left_count]
        right_images = collage[left_count:right_count]
        image_width = int(self.width // 2) if right_images else self.width
        left = [
            self.crop_image(
                image,
                width=image_width,
                height=self.MAX_HEIGHT_PER_COLLAGE // len(left_images),
            )
            for image in left_images
        ]
        right = [
            self.crop_image(
                image,
                width=image_width,
                height=self.MAX_HEIGHT_PER_COLLAGE // len(right_images),
            )
            for image in right_images
        ]
        base = Image.new(
            "RGBA",
            (self.width, self.MAX_HEIGHT_PER_COLLAGE),
            color=self.BACKGROUND_COLOR,
        )

        def _paste(
            _base: Image.Image,
            _images: list[Image.Image],
            _width: int,
            _line_length: int,
        ):
            _h = 0
            for _image in _images:
                if self.transparent and _image.mode == "RGBA":
                    _base.paste(_image, (_width, _h), mask=_image)
                else:
                    _base.paste(_image, (_width, _h))
                if _h != 0:
                    _base = ImageUtil.draw_line(
                        _base,
                        _width,
                        _h,
                        _width + _line_length,
                        _h,
                        color=self.LINE_COLOR,
                        width=1,
                    )
                _h += _image.height
            return _base

        if right:
            base = _paste(base, left, 0, image_width)
            base = _paste(base, right, image_width, image_width)
            base = ImageUtil.draw_line(
                base,
                image_width,
                0,
                image_width,
                base.height,
                color=self.LINE_COLOR,
                width=1,
            )
        else:
            base = _paste(base, left, 0, self.width)

        return base

    def render(self) -> Image.Image | None:
        if not self.extract():
            return

        collages: list[Image.Image] = [
            self.render_collage(index) for index in range(len(self.collage))
        ]

        return ImageUtil.round_corners(self.combine_images(collages), radius=BOARDER)

    def render_bytes(self, jpeg: bool = True) -> bytes | None:
        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def generate_html(self) -> str:
        if not (images := self.extract()):
            return ""
        image = images[0]
        image_bytes = BytesIO()
        image.save(image_bytes, "JPEG" if image.mode == "RGB" else "PNG")
        image_bytes = image_bytes.getvalue()
        return f"""
            <div style="
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px
            ">
                <div style="
                    width: {self.width}px; 
                    border-radius: {BOARDER}px
                ">
                    <img 
                        src="data:image/jpeg;base64,{base64.b64encode(image_bytes).decode()}" 
                        width="{self.width}" 
                        height="{image.height * self.width // image.width}" 
                        style="border-radius: {BOARDER}px" 
                    />
                </div>
            </div>
            """


class Column(Box):
    """
    A column that displays a list of elements.
    """

    BACKGROUND_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    length: int

    width: int
    parts: list[Element | Image.Image]

    def __init__(
        self,
        *args: Element | Image.Image | GraiaImage,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param args: The elements to display.
        :param width: The width of the column.
        :param dark: Whether the column is dark.
        """

        self.parts = []
        self.width = width
        self.length = 0
        for element in args:
            self.add(element)
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()

    def __len__(self):
        return self.length

    def __hash__(self):
        return hash("".join([str(hash(part)) for part in self.parts]))

    def has_content(self) -> bool:
        return self.length > 0

    def set_dark(self) -> Self:
        for element in self.parts:
            element.set_dark()
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        return self

    def set_light(self) -> Self:
        for element in self.parts:
            element.set_light()
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        self.width = width
        for element in self.parts:
            element.set_width(width)
        return self

    def add(
        self, *elements: Element | Image.Image | GraiaImage, dark: bool = None
    ) -> Self:
        """
        Add an element to the column.

        :param elements: The element to add, can be an element or an image.
        :param dark: Override dark mode, None if not override.
        :return: The column itself.
        """

        for element in elements:
            if isinstance(element, GraiaImage):
                try:
                    element = Image.open(BytesIO(b64decode(element.base64)))
                except Exception as err:
                    logger.error(f"Failed to load image from GraiaImage: {err}")
                    continue
            if isinstance(element, Image.Image):
                element = ImageBox(element)
            if dark is not None:
                if dark:
                    element.set_dark()
                else:
                    element.set_light()
            element.set_width(self.width)
            self.length += len(element)
            self.parts.append(element)
        return self

    def render(self) -> Image.Image:
        width = self.width
        rendered = [element.render() for element in self.parts]

        height = sum(element.height for element in rendered) + BOARDER * (len(rendered))

        _height = BOARDER
        canvas = Image.new("RGBA", (width, height), self.BACKGROUND_COLOR)
        for element in rendered:
            if element.mode == "RGBA":
                canvas.paste(
                    element,
                    (0, _height),
                    mask=element,
                )
            else:
                canvas.paste(element, (0, _height))
            _height += element.height + BOARDER

        return canvas

    def render_bytes(self, jpeg: bool = True) -> bytes:
        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def generate_html(self) -> str:
        return (
            f"""
            <div style="
                width: {self.width}px; 
                padding-top: {BOARDER // 2}px; 
                padding-bottom: {BOARDER // 2}px; 
                background-color: rgb{self.BACKGROUND_COLOR}
            ">
                {''.join([part.generate_html() for part in self.parts])}
            </div>
            """
            if self.parts
            else ""
        )


class OneUIMock:
    """
    A mockery of OneUI.
    """

    BACKGROUND_COLOR: tuple[int, int, int]

    GRID_SIZE: int = BOARDER

    dark: bool
    parts: list[Column]

    include_footer: bool
    footer_title: str
    footer_text: str
    title_at_top: bool

    def __init__(
        self,
        *args: Column,
        dark: bool = None,
        footer: bool = True,
        footer_title: str = f"Generated by {config.name}",
        footer_text: str = f"ver. {__version__}",
        title_at_top: bool = True,
    ):
        """
        :param args: The columns to display.
        :param dark: Whether the mockery is dark.
        :param footer: Whether to include the footer.
        :param footer_title: The title of the footer.
        :param footer_text: The text of the footer.
        """

        if dark is None:
            dark = is_dark()
        self.dark = dark
        self.parts = []
        for element in args:
            self.add(element)
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.include_footer = footer
        self.footer_title = footer_title
        self.footer_text = footer_text
        self.title_at_top = title_at_top

    def set_footer(
        self,
        footer: bool = True,
        footer_title: str = "",
        footer_text: str = "",
        title_at_top: bool = True,
    ) -> Self:
        self.include_footer = footer
        self.footer_title = footer_title
        self.footer_text = footer_text
        self.title_at_top = title_at_top
        return self

    def add(self, *elements: Element) -> Self:
        """
        Add a column to the mockery.

        :param elements: The element to add.
        :return: The mockery itself.
        """

        if not elements:
            raise ValueError("No elements to add.")

        if not self.parts and not isinstance(elements[0], Column):
            self.parts = [Column()]
        for element in elements:
            if not isinstance(element, Column):
                self.parts[-1].add(element, dark=self.dark)
            else:
                self.parts.append(element)
        return self

    def set_dark(self) -> Self:
        for element in self.parts:
            element.set_dark()
        self.dark = True
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        return self

    def set_light(self) -> Self:
        for element in self.parts:
            element.set_light()
        self.dark = False
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        return self

    def set_width(self, width: int) -> Self:
        for element in self.parts:
            element.set_width(width)
        return self

    def render(self) -> Image.Image:
        """
        Render the mockery.
        Grids are added between columns if more than one column is added.

        :return: The rendered mockery.
        """

        rendered = [element.render() for element in self.parts]

        height = max(element.height for element in rendered) + self.GRID_SIZE
        width = sum(element.width for element in rendered)
        if len(rendered) > 1:
            width += self.GRID_SIZE * (len(rendered) + 1)
            _width = self.GRID_SIZE
        else:
            _width = 0

        canvas = Image.new("RGBA", (width, height), self.BACKGROUND_COLOR)

        for element in rendered:
            canvas.paste(
                element,
                (_width, 0),
                mask=element,
            )
            _width += element.width + self.GRID_SIZE

        return canvas

    def render_bytes(self, jpeg: bool = True) -> bytes:
        canvas = self.render()
        output = BytesIO()
        if jpeg:
            canvas.convert("RGB").save(output, "JPEG")
        else:
            canvas.save(output, "PNG")
        return output.getvalue()

    def generate_html(self) -> str:
        if not self.parts:
            return ""
        columns = [p for part in self.parts if (p := part.generate_html())]
        width = sum(part.width for part in self.parts)
        style = """
            <style>
                * {
                    margin: 0; 
                    padding: 0; 
                    font-family: Helvetica, Arial, sans-serif
                }
            </style>
            """
        if len(columns) > 1:
            width += self.GRID_SIZE * (len(columns) + 1) - self.GRID_SIZE
        footer_color = (
            Color.FOOTER_COLOR_DARK if self.dark else Color.FOOTER_COLOR_LIGHT
        )
        footer_padding = BOARDER * (2 if len(columns) > 1 else 1)
        footer_width = (
            width - footer_padding * 2 + (self.GRID_SIZE if len(columns) > 1 else 0)
        )
        if self.include_footer and any([self.footer_title, self.footer_text]):
            footer_title = (
                f"""
                <p style="
                    text-align: right;
                    color: rgb{footer_color};
                    font-size: 40px;
                    font-weight: bold;
                ">
                    {self.footer_title}
                </p>
                """
                if self.footer_title
                else ""
            )
            footer_text = (
                f"""
                <p style="
                    text-align: right;
                    color: rgb{footer_color};
                    font-size: 20px;
                ">
                    {self.footer_text}
                </p>
                """
                if self.footer_text
                else ""
            )
            footers = [footer_title, footer_text]
            if not self.title_at_top:
                footers.reverse()
            footer = f"""
                <div style="
                    padding-top: 0px; 
                    padding-left: {footer_padding}px; 
                    padding-right: {footer_padding}px; 
                    padding-bottom: {BOARDER}px; 
                    width: {footer_width}px; 
                    word-wrap: break-word; 
                    background-color: rgb{self.BACKGROUND_COLOR}
                ">
                    {''.join(footers)}
                </div>
                """
        else:
            footer = ""
        if len(columns) == 1:
            return f"""
            <html>
                <head>
                    {style}
                </head>
                <body>
                    <div style="background-color: rgb{self.BACKGROUND_COLOR}">
                        {columns[0]}
                        {footer}
                    </div>
                </body>
            </html>
            """
        modified = []
        for column in columns:
            column = f"""<div style="padding-left: {self.GRID_SIZE}px">{column}</div>"""
            modified.append(column)
        return f"""
            <html>
                <head>
                    {style}
                </head>
                <body>
                    <div>
                        <div style="
                            width: {width}px; 
                            padding-right: {self.GRID_SIZE}px; 
                            display: flex; 
                            background-color: rgb{self.BACKGROUND_COLOR}
                        ">
                            {''.join(modified)}
                        </div>
                        {footer}
                    </div>
                </body>
            </html>
            """

    async def async_render_bytes(self) -> bytes:
        try:
            browser = Ariadne.current().launch_manager.get_interface(PlaywrightBrowser)
            html = await asyncio.to_thread(self.generate_html)
            async with browser.page(
                viewport={"width": self.width, "height": 1},
                device_scale_factor=1.5,
            ) as page:
                await page.set_content(html)
                img = await page.screenshot(
                    type="jpeg", quality=80, full_page=True, scale="device"
                )
                return img
        except playwright._impl._api_types.Error:
            return await asyncio.to_thread(self.render_bytes())

    @property
    def width(self) -> int:
        width = sum(part.width for part in self.parts)
        if len(self.parts) == 1:
            return width
        width += (self.GRID_SIZE // 2) * (len(self.parts) + 1) - self.GRID_SIZE // 2
        return width


def is_dark() -> bool:
    return not (6 < datetime.now().hour < 18)
