import random
from abc import ABC, abstractmethod
from datetime import datetime
from io import BytesIO

from PIL import Image
from PIL.Image import Resampling

from library.image import ImageUtil, TextUtil, IconUtil
from .color import Color, PALETTE

DEFAULT_WIDTH: int = 720

ICON_BASE: Image.Image = IconUtil.get_icon("oneui-base", color=(0, 0, 0))
SWITCH_ICON_ON: Image.Image = IconUtil.get_icon("oneui-switch-on", color=(0, 0, 0))
SWITCH_ICON_OFF: Image.Image = IconUtil.get_icon("oneui-switch-off", color=(0, 0, 0))
DEFAULT_ICON: Image.Image = IconUtil.get_icon("toy-brick", color=(252, 252, 252))


class Element(ABC):
    @abstractmethod
    def __init__(self):
        pass

    @abstractmethod
    def __len__(self):
        pass

    @abstractmethod
    def render(self) -> Image.Image:
        """
        Render the element.

        :return: Image.Image
        """

        pass

    @abstractmethod
    def set_dark(self):
        pass

    @abstractmethod
    def set_light(self):
        pass


class Banner(Element):
    """
    Banner is what displays at the top of the column.
    Most of the time, it is a text banner, icon is optional.
    """

    HEIGHT: int = 140
    WIDTH: int = ...

    TEXT_COLOR: tuple[int, int, int]
    BACKGROUND_COLOR: tuple[int, int, int]

    TEXT_X_RATIO: float = 0.06
    TEXT_HEIGHT_RATIO: float = 0.35
    TEXT_X: int = ...
    TEXT_HEIGHT: int = int(HEIGHT * TEXT_HEIGHT_RATIO)
    TEXT_Y: int = HEIGHT - TEXT_HEIGHT
    TEXT_SIZE: int = int(TEXT_HEIGHT * 0.8)

    ICON_X_RATIO: float = 0.13
    ICON_Y_RATIO: float = 0.20
    ICON_X: int = ...
    ICON_Y: int = int(HEIGHT * ICON_Y_RATIO)

    __text: str
    __icon: Image.Image | None

    def __init__(
        self,
        text: str,
        icon: Image.Image | None = None,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param text: Text to display
        :param icon: Icon to display
        :param width: Width of the banner
        :param dark: Whether the banner is dark or light
        """

        if width <= self.HEIGHT:
            raise ValueError(f"Width must be greater than {self.HEIGHT}")
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.WIDTH = width
        self.__text = text
        self.__icon = icon
        self.TEXT_X = int(width * self.TEXT_X_RATIO)
        self.ICON_X = width - int(width * self.ICON_X_RATIO)

    def set_dark(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK

    def set_light(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT

    def __len__(self) -> int:
        return 1

    def render(self) -> Image.Image:
        canvas = Image.new("RGBA", (self.WIDTH, self.HEIGHT), self.BACKGROUND_COLOR)
        font = ImageUtil.get_font(self.TEXT_SIZE)
        text = TextUtil.render_text(self.__text, self.TEXT_COLOR, font)

        if self.__icon is not None:
            icon_size = text.height, text.height
            self.__icon = self.__icon.resize(icon_size, Resampling.LANCZOS)

            try:
                canvas.paste(
                    self.__icon,
                    (self.TEXT_X, self.TEXT_Y),
                    mask=self.__icon,
                )
            except ValueError:
                canvas.paste(
                    self.__icon,
                    (self.ICON_X, self.TEXT_Y),
                    mask=self.__icon.convert("L"),
                )

        canvas.paste(
            text,
            (self.TEXT_X, self.TEXT_Y),
            mask=text,
        )

        return canvas


class Header(Element):
    """
    Header is what displays below the banner, but above the content.
    """

    HEIGHT: int = 133
    WIDTH: int = ...

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]

    LEFT_BOARDER_RATIO: float = 0.06
    RIGHT_BOARDER_RATIO: float = 0.05
    UP_BOARDER_RATIO: float = 0.19
    TEXT_HEIGHT_RATIO: float = 0.39
    DESCRIPTION_HEIGHT_RATIO: float = 0.22
    ICON_BOARDER_RATIO: float = 0.14

    TEXT_HEIGHT: int = int(HEIGHT * TEXT_HEIGHT_RATIO)
    DESCRIPTION_HEIGHT: int = int(HEIGHT * DESCRIPTION_HEIGHT_RATIO)
    LEFT_BOARDER: int = ...
    RIGHT_BOARDER: int = ...
    UP_BOARDER: int = int(HEIGHT * UP_BOARDER_RATIO)
    ICON_BOARDER: int = int(HEIGHT * ICON_BOARDER_RATIO)

    ICON_SIZE = (HEIGHT - 2 * ICON_BOARDER, HEIGHT - 2 * ICON_BOARDER)

    __text: str
    __description: str
    __icon: Image.Image | None

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

        if width <= self.HEIGHT:
            raise ValueError(f"Width must be greater than {self.HEIGHT}")
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.WIDTH = width
        self.__text = text
        self.__description = description
        self.__icon = icon
        self.LEFT_BOARDER = int(width * self.LEFT_BOARDER_RATIO)
        self.RIGHT_BOARDER = int(width * self.RIGHT_BOARDER_RATIO)

    def set_dark(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK

    def set_light(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT

    def __len__(self) -> int:
        return 1

    def render(self) -> Image.Image:
        canvas = Image.new("RGBA", (self.WIDTH, self.HEIGHT), self.FOREGROUND_COLOR)
        font = ImageUtil.get_font(int(self.TEXT_HEIGHT * 0.8))
        text = TextUtil.render_text(self.__text, self.TEXT_COLOR, font)
        description_font = ImageUtil.get_font(int(self.DESCRIPTION_HEIGHT * 0.8))
        description = TextUtil.render_text(
            self.__description, self.DESCRIPTION_COLOR, description_font
        )

        if self.__icon is not None:
            self.__icon = ImageUtil.round_corners(
                self.__icon.resize(self.ICON_SIZE, Resampling.LANCZOS),
                radius=self.ICON_SIZE[0] // 2,
            )
            icon_location = (
                self.WIDTH - self.RIGHT_BOARDER - self.ICON_SIZE[0],
                self.ICON_BOARDER,
            )

            try:
                canvas.paste(
                    self.__icon,
                    icon_location,
                    mask=self.__icon,
                )
            except ValueError:
                canvas.paste(
                    self.__icon,
                    icon_location,
                    mask=self.__icon.convert("L"),
                )

        canvas.paste(text, (self.LEFT_BOARDER, self.UP_BOARDER), mask=text)
        canvas.paste(
            description,
            (self.LEFT_BOARDER, self.UP_BOARDER + self.TEXT_HEIGHT),
            mask=description,
        )

        canvas = ImageUtil.round_corners(canvas, radius=self.LEFT_BOARDER)
        return canvas


class Box(Element):
    @abstractmethod
    def __len__(self):
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


class MenuBox(Box):
    """
    A box that mostly used in the menu.
    Each item should have a title, a description, and an icon.
    Each text should be in one line for better display.
    """

    HEIGHT: int = 120
    WIDTH: int = ...

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    LINE_COLOR: tuple[int, int, int]

    ICON_BOARDER_RATIO: float = 0.29
    LEFT_BOARDER_RATIO: float = 0.23
    UP_BOARDER_RATIO: float = 0.20
    TEXT_HEIGHT_RATIO: float = 0.34
    DESCRIPTION_HEIGHT_RATIO: float = 0.25

    ICON_BOARDER: int = int(HEIGHT * ICON_BOARDER_RATIO)
    TEXT_HEIGHT: int = int(HEIGHT * TEXT_HEIGHT_RATIO)
    DESCRIPTION_HEIGHT: int = int(HEIGHT * DESCRIPTION_HEIGHT_RATIO)
    UP_BOARDER: int = int(HEIGHT * UP_BOARDER_RATIO)

    ICON_SIZE = (HEIGHT - 2 * ICON_BOARDER, HEIGHT - 2 * ICON_BOARDER)
    LEFT_BOARDER: int = ICON_BOARDER + ICON_SIZE[0] + int(HEIGHT * LEFT_BOARDER_RATIO)

    __text: list[str]
    __description: list[str]
    __icon: list[Image.Image | None]
    __icon_color: list[tuple[int, int, int] | None]

    def __init__(
        self,
        text: str = None,
        description: str = None,
        icon: Image.Image | None = None,
        icon_color: tuple[int, int, int] = None,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param text: Text to display
        :param description: Description to display
        :param icon: Icon to display
        :param icon_color: Color of the icon
        :param width: Width of the box
        :param dark: Whether the box is dark or light
        """

        super().__init__()
        if width <= self.HEIGHT:
            raise ValueError(f"Width must be greater than {self.HEIGHT}")
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.WIDTH = width
        if text and description:
            self.__text = [text]
            self.__description = [description]
            self.__icon = [icon]
            self.__icon_color = [icon_color]
            return
        self.__text = []
        self.__description = []
        self.__icon = []
        self.__icon_color = []

    def set_dark(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        self.LINE_COLOR = Color.LINE_COLOR_DARK

    def set_light(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.LINE_COLOR = Color.LINE_COLOR_LIGHT

    def __len__(self) -> int:
        return len(self.__text)

    def has_content(self) -> bool:
        return len(self.__text) > 0

    def add(
        self,
        text: str,
        description: str,
        icon: Image.Image | None = None,
        icon_color: tuple[int, int, int] = None,
    ):
        """
        Add an item to the box.

        :param text: The text to display.
        :param description: The description to display.
        :param icon: The icon to display.
        :param icon_color: The color of the icon.
        :return: None
        """

        self.__text.append(text)
        self.__description.append(description)
        self.__icon.append(icon)
        self.__icon_color.append(icon_color)

    @staticmethod
    def render_icon(
        icon: Image.Image | None, color: tuple[int, int, int] | None
    ) -> Image.Image | None:
        """
        Render an icon.

        :param icon: The icon to render.
        :param color: The color of the icon.
        :return: The rendered icon.
        """

        if icon is None:
            return None
        icon = IconUtil.replace_color(icon, (252, 252, 252))
        if not color:
            palette = random.choice(PALETTE)
            _ = palette[1:]
            color = (int(_[:2], 16), int(_[2:4], 16), int(_[4:6], 16))
        base = IconUtil.replace_color(ICON_BASE, color)
        size = base.size[0] // 3 * 2, base.size[1] // 3 * 2
        icon = icon.resize(size, Resampling.LANCZOS)
        icon = ImageUtil.paste_to_center(base, icon)
        return icon

    def render(self) -> Image.Image | None:
        if not self.has_content():
            return
        canvas = Image.new(
            "RGBA", (self.WIDTH, self.HEIGHT * len(self.__text)), self.FOREGROUND_COLOR
        )
        for index, (text, description, icon, icon_color) in enumerate(
            zip(self.__text, self.__description, self.__icon, self.__icon_color)
        ):
            if icon := self.render_icon(icon, icon_color):
                icon = icon.resize(self.ICON_SIZE, Resampling.LANCZOS)
                canvas.paste(
                    icon,
                    (self.ICON_BOARDER, self.ICON_BOARDER + index * self.HEIGHT),
                    mask=icon,
                )
            font = ImageUtil.get_font(int(self.TEXT_HEIGHT * 0.8))
            text = TextUtil.render_text(text, self.TEXT_COLOR, font)
            description_font = ImageUtil.get_font(int(self.DESCRIPTION_HEIGHT * 0.8))
            description = TextUtil.render_text(
                description, self.DESCRIPTION_COLOR, description_font
            )
            canvas.paste(
                text,
                (
                    self.LEFT_BOARDER,
                    self.UP_BOARDER + index * self.HEIGHT,
                ),
                mask=text,
            )
            canvas.paste(
                description,
                (
                    self.LEFT_BOARDER,
                    self.UP_BOARDER + index * self.HEIGHT + self.TEXT_HEIGHT,
                ),
                mask=description,
            )
            if index == len(self.__text) - 1:
                continue
            canvas = ImageUtil.draw_line(
                canvas,
                self.LEFT_BOARDER,
                self.HEIGHT * (index + 1),
                canvas.width - self.ICON_BOARDER,
                self.HEIGHT * (index + 1),
                self.LINE_COLOR,
                2,
            )

        canvas = ImageUtil.round_corners(canvas, radius=self.ICON_BOARDER)
        return canvas


class GeneralBox(Box):
    """
    A box that displays a general text.
    Each item should have a text and a description, switch icon is optional.
    """

    STANDARD_HEIGHT = 120

    TEXT_COLOR: tuple[int, int, int]
    DESCRIPTION_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    LINE_COLOR: tuple[int, int, int]
    HIGHLIGHT_COLOR: tuple[int, int, int]

    LEFT_BOARDER_RATIO: float = 0.06
    UP_BOARDER_RATIO: float = 0.2
    TEXT_ICON_BOARDER_RATIO: float = 0.8

    TEXT_HEIGHT_RATIO: float = 0.34
    DESCRIPTION_HEIGHT_RATIO: float = 0.25

    TEXT_HEIGHT: int = int(STANDARD_HEIGHT * TEXT_HEIGHT_RATIO)
    DESCRIPTION_HEIGHT: int = int(STANDARD_HEIGHT * DESCRIPTION_HEIGHT_RATIO)

    TEXT_FONT = ImageUtil.get_font(int(TEXT_HEIGHT * 0.8))
    DESCRIPTION_FONT = ImageUtil.get_font(int(DESCRIPTION_HEIGHT * 0.8))

    LEFT_BOARDER: int = ...
    TEXT_ICON_BOARDER: int = ...
    UP_BOARDER: int = int(STANDARD_HEIGHT * UP_BOARDER_RATIO)

    DESCRIPTION_OFFSET_Y: int = 7

    __text: list[str]
    __description: list[str | None]
    __switch: list[bool | None]
    __highlight: list[bool]
    __dark: bool

    def __init__(
        self,
        text: str = None,
        description: str | None = None,
        switch: bool | None = None,
        highlight: bool = False,
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
        self.__dark = dark
        if width <= self.STANDARD_HEIGHT:
            raise ValueError(f"Width must be greater than {self.STANDARD_HEIGHT}")
        if dark is None:
            dark = is_dark()
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.WIDTH = width
        self.LEFT_BOARDER = int(self.WIDTH * self.LEFT_BOARDER_RATIO)
        self.TEXT_ICON_BOARDER = int(self.WIDTH * self.TEXT_ICON_BOARDER_RATIO)
        if text:
            self.__text = [text]
            self.__description = [description]
            self.__switch = [switch]
            self.__highlight = [highlight]
            return
        self.__text = []
        self.__description = []
        self.__switch = []
        self.__highlight = []

    def set_dark(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        self.LINE_COLOR = Color.LINE_COLOR_DARK
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_DARK

    def set_light(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.LINE_COLOR = Color.LINE_COLOR_LIGHT
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_LIGHT

    def __len__(self):
        return len(self.__text)

    def has_content(self) -> bool:
        return len(self.__text) > 0

    def add(
        self,
        text: str,
        description: str | None,
        switch: bool | None = None,
        highlight: bool | None = None,
    ):
        """
        Add a new item to the box.
        :param text: Text to display
        :param description: Description to display
        :param switch: Switch to display
        :param highlight: Whether the item is highlighted
        """
        self.__text.append(text)
        self.__description.append(description)
        self.__switch.append(switch)
        self.__highlight.append(highlight)

    def render_item(
        self,
        text: str,
        description: str | None,
        switch: bool | None,
        highlight: bool,
    ):
        canvas_height = self.UP_BOARDER * 2
        text_width = (
            int(self.WIDTH * self.TEXT_ICON_BOARDER_RATIO - self.LEFT_BOARDER)
            if switch is not None
            else self.WIDTH - self.LEFT_BOARDER * 2
        )
        text_img = TextUtil.render_text(
            text=text, color=self.TEXT_COLOR, font=self.TEXT_FONT, width=text_width
        )
        canvas_height += text_img.height
        description_img = None
        if description:
            description_color = (
                self.HIGHLIGHT_COLOR if highlight else self.DESCRIPTION_COLOR
            )
            description_img = TextUtil.render_text(
                text=description,
                color=description_color,
                font=self.DESCRIPTION_FONT,
                width=text_width,
            )
            canvas_height += description_img.height + self.DESCRIPTION_OFFSET_Y
        canvas = Image.new(
            "RGBA",
            (
                self.WIDTH,
                canvas_height,
            ),
            self.FOREGROUND_COLOR,
        )
        canvas.paste(
            text_img,
            (self.LEFT_BOARDER, self.UP_BOARDER),
            mask=text_img,
        )
        if description_img:
            canvas.paste(
                description_img,
                (
                    self.LEFT_BOARDER,
                    self.UP_BOARDER + text_img.height + self.DESCRIPTION_OFFSET_Y,
                ),
                mask=description_img,
            )
        if switch is None:
            return canvas
        switch_icon = SWITCH_ICON_ON if switch else SWITCH_ICON_OFF
        switch_size = (
            switch_icon.width * self.TEXT_HEIGHT // switch_icon.height,
            self.TEXT_HEIGHT,
        )
        if switch:
            switch_color = Color.SWITCH_ENABLE_COLOR
        else:
            switch_color = (
                Color.SWITCH_DISABLE_COLOR_DARK
                if self.__dark
                else Color.SWITCH_DISABLE_COLOR
            )
        switch_img = IconUtil.replace_color(
            switch_icon.resize(switch_size, Resampling.LANCZOS),
            switch_color,
        )
        canvas.paste(
            switch_img,
            (
                self.WIDTH - self.LEFT_BOARDER - switch_img.width,
                (canvas.height - switch_img.height) // 2,
            ),
            mask=switch_img,
        )

        return canvas

    def render(self) -> Image.Image | None:
        if not self.has_content():
            return
        rendered = [
            self.render_item(text, description, switch, highlight)
            for text, description, switch, highlight in zip(
                self.__text, self.__description, self.__switch, self.__highlight
            )
        ]
        width = self.WIDTH
        height = sum(map(lambda x: x.height, rendered))
        canvas = Image.new("RGBA", (width, height), self.FOREGROUND_COLOR)
        _height = 0

        line_y: list[int] = []
        for index, item in enumerate(rendered):
            canvas.paste(
                item,
                (0, _height),
                mask=item,
            )
            _height += item.height
            if index == len(self.__text) - 1:
                continue
            line_y.append(_height)

        for y in line_y:
            canvas = ImageUtil.draw_line(
                canvas,
                self.LEFT_BOARDER,
                y,
                canvas.width - self.LEFT_BOARDER,
                y,
                self.LINE_COLOR,
                2,
            )

        canvas = ImageUtil.round_corners(canvas, radius=self.LEFT_BOARDER)
        return canvas


class HintBox(Box):
    """
    A box that displays a highlighted text.
    """

    STANDARD_HEIGHT: int = 200

    TEXT_COLOR: tuple[int, int, int]
    HIGHLIGHT_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]

    LEFT_BOARDER_RATIO: float = 0.06
    UP_BOARDER_RATIO: float = 0.18

    LEFT_BOARDER: int = ...
    UP_BOARDER: int = int(STANDARD_HEIGHT * UP_BOARDER_RATIO)

    TITLE_GRID_RATIO: float = 0.11
    GRID_RATIO: float = 0.10

    TITLE_GRID: int = int(STANDARD_HEIGHT * TITLE_GRID_RATIO)
    GRID: int = int(STANDARD_HEIGHT * GRID_RATIO)

    TITLE_FONT = ImageUtil.get_font(33)
    TEXT_FONT = ImageUtil.get_font(30)

    __title: str | None
    __hints: list[str]

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
        if width <= self.STANDARD_HEIGHT:
            raise ValueError(f"Width must be greater than {self.STANDARD_HEIGHT}")
        if dark is None:
            dark = is_dark()
        self.__dark = dark
        if dark:
            self.set_dark()
        else:
            self.set_light()
        self.WIDTH = width
        self.LEFT_BOARDER = int(self.WIDTH * self.LEFT_BOARDER_RATIO)
        self.__title = title
        self.__hints = list(hint)

    def set_dark(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_DARK
        self.FOREGROUND_COLOR = Color.HINT_COLOR_DARK
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_DARK

    def set_light(self):
        self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
        self.FOREGROUND_COLOR = Color.HINT_COLOR_LIGHT
        self.HIGHLIGHT_COLOR = Color.HIGHLIGHT_COLOR_LIGHT

    def __len__(self):
        return len(self.__hints) + bool(self.__title)

    def has_content(self) -> bool:
        return len(self.__hints) + bool(self.__title) > 0

    def add(self, *hints: str):
        self.__hints.extend(hints)

    def render(self) -> Image.Image | None:
        if not self.has_content():
            return
        height = self.UP_BOARDER * 2
        parts: list[Image.Image] = []
        part_y: list[int] = [self.UP_BOARDER]
        if self.__title:
            title = TextUtil.render_text(
                self.__title,
                self.TEXT_COLOR,
                self.TITLE_FONT,
                self.WIDTH - self.LEFT_BOARDER * 2,
            )
            parts.append(title)
            height += title.height + self.TITLE_GRID
            part_y.append(part_y[-1] + title.height + self.TITLE_GRID)
        for index, hint in enumerate(self.__hints):
            part = TextUtil.render_text(
                hint,
                self.HIGHLIGHT_COLOR,
                self.TEXT_FONT,
                self.WIDTH - self.LEFT_BOARDER * 2,
            )
            parts.append(part)
            height += part.height
            if index == len(self.__hints) - 1:
                continue
            height += self.GRID
            part_y.append(part_y[-1] + part.height + self.GRID)

        canvas = Image.new("RGBA", (self.WIDTH, height), self.FOREGROUND_COLOR)
        for y, part in zip(part_y, parts):
            canvas.paste(part, (self.LEFT_BOARDER, y), mask=part)

        canvas = ImageUtil.round_corners(canvas, radius=self.LEFT_BOARDER)
        return canvas


class Column(Box):
    """
    A column that displays a list of elements.
    """

    BACKGROUND_COLOR: tuple[int, int, int]
    FOREGROUND_COLOR: tuple[int, int, int]
    LENGTH: int

    GRID_SIZE: int = 36

    width: int
    has_banner: bool
    __rendered: list[Image.Image]

    def __init__(
        self,
        *args: Element | Image.Image,
        width: int = DEFAULT_WIDTH,
        dark: bool = None,
    ):
        """
        :param args: The elements to display.
        :param width: The width of the column.
        :param dark: Whether the column is dark.
        """

        if dark is None:
            dark = is_dark()
        if dark:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
            self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        else:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
            self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.LENGTH = 0
        self.width = width
        self.has_banner = False
        self.__rendered = []
        for element in args:
            self.add(element)

    def set_dark(self):
        raise NotImplementedError(
            "Dark mode of Column cannot be set once it is created."
        )

    def set_light(self):
        raise NotImplementedError(
            "Dark mode of Column cannot be set once it is created."
        )

    def __len__(self):
        return self.LENGTH

    def has_content(self) -> bool:
        return self.LENGTH > 0

    def add(self, *elements: Element | Image.Image):
        """
        Add an element to the column.

        :param elements: The element to add, can be an element or an image.
        :return: None
        """

        for element in elements:
            if isinstance(element, Image.Image):
                size = (self.width, self.width * element.height // element.width)
                element = element.resize(size, Resampling.LANCZOS)
                element = ImageUtil.round_corners(element, radius=self.GRID_SIZE)
                self.__rendered.append(element)
                self.LENGTH += 1
                continue
            if not (rendered := element.render()):
                continue
            if isinstance(element, Element):
                self.LENGTH += len(element)
            else:
                self.LENGTH += round(element.height / MenuBox.HEIGHT)
            if isinstance(element, Banner):
                self.has_banner = True
                self.__rendered.insert(0, rendered)
                continue
            self.__rendered.append(rendered)

    def render(self) -> Image.Image:
        width = self.width
        rendered = []
        for element in self.__rendered:
            if element.width != width:
                size = (width, width * element.height // element.width)
                element = element.resize(size, Resampling.LANCZOS)
                element = ImageUtil.round_corners(element, radius=self.GRID_SIZE)
            rendered.append(element)
        height = sum(element.height for element in rendered) + self.GRID_SIZE * (
            len(rendered) - 1
        )

        if not self.has_banner:
            height += self.GRID_SIZE
            _height = self.GRID_SIZE
        else:
            _height = 0

        canvas = Image.new("RGBA", (width, height), self.BACKGROUND_COLOR)
        for element in rendered:
            try:
                canvas.paste(
                    element,
                    (0, _height),
                    mask=element,
                )
            except ValueError:
                canvas.paste(element, (0, _height))
            _height += element.height + self.GRID_SIZE

        return canvas


class OneUIMock:
    """
    A mockery of OneUI.
    """

    BACKGROUND_COLOR: tuple[int, int, int]

    GRID_SIZE: int = 36

    __rendered: list[Image.Image]

    def __init__(self, *args: Column, dark: bool = None):
        """
        :param args: The columns to display.
        :param dark: Whether the mockery is dark.
        """

        if dark is None:
            dark = is_dark()
        if dark:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        else:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.__rendered = []
        for element in args:
            self.add(element)

    def add(self, element: Column):
        """
        Add a column to the mockery.

        :param element: The column to add.
        :return: None
        """

        rendered = element.render()
        self.__rendered.append(rendered)

    def render(self) -> Image.Image:
        """
        Render the mockery.
        Grids are added between columns if more than one column is added.

        :return: The rendered mockery.
        """

        height = max(element.height for element in self.__rendered) + self.GRID_SIZE
        width = sum(element.width for element in self.__rendered)
        if len(self.__rendered) > 1:
            width += self.GRID_SIZE * (len(self.__rendered) + 1)
            _width = self.GRID_SIZE
        else:
            _width = 0

        canvas = Image.new("RGBA", (width, height), self.BACKGROUND_COLOR)

        for element in self.__rendered:
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


def is_dark() -> bool:
    return not (6 < datetime.now().hour < 18)
