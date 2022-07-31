import random
from abc import ABC, abstractmethod

from PIL import Image
from PIL.Image import Resampling

from library.image import ImageUtil, TextUtil, IconUtil
from .color import Color, PALETTE

DEFAULT_WIDTH: int = 720
ICON_BASE: Image.Image = IconUtil.get_icon("oneui-base", color=(0, 0, 0))
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
        pass


class Banner(Element):
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
        dark: bool = False,
    ):
        if width <= self.HEIGHT:
            raise ValueError(f"Width must be greater than {self.HEIGHT}")
        if dark:
            self.TEXT_COLOR = Color.TEXT_COLOR_DARK
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        else:
            self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.WIDTH = width
        self.__text = text
        self.__icon = icon
        self.TEXT_X = int(width * self.TEXT_X_RATIO)
        self.ICON_X = width - int(width * self.ICON_X_RATIO)

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
        dark: bool = False,
    ):
        if width <= self.HEIGHT:
            raise ValueError(f"Width must be greater than {self.HEIGHT}")
        if dark:
            self.TEXT_COLOR = Color.TEXT_COLOR_DARK
            self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
            self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
        else:
            self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
            self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
            self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
        self.WIDTH = width
        self.__text = text
        self.__description = description
        self.__icon = icon
        self.LEFT_BOARDER = int(width * self.LEFT_BOARDER_RATIO)
        self.RIGHT_BOARDER = int(width * self.RIGHT_BOARDER_RATIO)

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
        dark: bool = False,
    ):
        if width <= self.HEIGHT:
            raise ValueError(f"Width must be greater than {self.HEIGHT}")
        if dark:
            self.TEXT_COLOR = Color.TEXT_COLOR_DARK
            self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_DARK
            self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_DARK
            self.LINE_COLOR = Color.LINE_COLOR_DARK
        else:
            self.TEXT_COLOR = Color.TEXT_COLOR_LIGHT
            self.DESCRIPTION_COLOR = Color.DESCRIPTION_COLOR_LIGHT
            self.FOREGROUND_COLOR = Color.FOREGROUND_COLOR_LIGHT
            self.LINE_COLOR = Color.LINE_COLOR_LIGHT
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

    def __len__(self):
        return len(self.__text)

    def has_content(self):
        return len(self.__text) > 0

    def add(
        self,
        text: str,
        description: str,
        icon: Image.Image | None = None,
        icon_color: tuple[int, int, int] = None,
    ):
        self.__text.append(text)
        self.__description.append(description)
        self.__icon.append(icon)
        self.__icon_color.append(icon_color)

    @staticmethod
    def render_icon(
        icon: Image.Image | None, color: tuple[int, int, int] | None
    ) -> Image.Image | None:
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
        if not self.__text and not self.__description:
            return None
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


class Column(Element):
    BACKGROUND_COLOR: tuple[int, int, int]
    LENGTH: int

    GRID_SIZE: int = 36

    width: int
    has_banner: bool
    __rendered: list[Image.Image]

    def __init__(
        self,
        *args: Element | Image.Image,
        width: int = DEFAULT_WIDTH,
        dark: bool = False,
    ):
        if dark:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        else:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.LENGTH = 0
        self.width = width
        self.has_banner = False
        self.__rendered = []
        for element in args:
            self.add(element)

    def __len__(self):
        return self.LENGTH

    def has_content(self):
        return self.LENGTH > 0

    def add(self, element: Element | Image.Image):
        if isinstance(element, Image.Image):
            if self.width != DEFAULT_WIDTH:
                size = (self.width, self.width * element.height // element.width)
                element = element.resize(size, Resampling.LANCZOS)
                element = ImageUtil.round_corners(element, radius=self.GRID_SIZE)
            self.__rendered.append(element)
            self.LENGTH += 1
            return
        if not (rendered := element.render()):
            return
        if isinstance(element, Element):
            self.LENGTH += len(element)
        else:
            self.LENGTH += round(element.height / Box.HEIGHT)
        if isinstance(element, Banner):
            self.has_banner = True
            self.__rendered.insert(0, rendered)
            return
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
            canvas.paste(
                element,
                (0, _height),
                mask=element,
            )
            _height += element.height + self.GRID_SIZE

        return canvas


class OneUIMock:
    BACKGROUND_COLOR: tuple[int, int, int]

    GRID_SIZE: int = 36

    __rendered: list[Image.Image]

    def __init__(self, *args: Column, dark: bool = False):
        if dark:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_DARK
        else:
            self.BACKGROUND_COLOR = Color.BACKGROUND_COLOR_LIGHT
        self.__rendered = []
        for element in args:
            self.add(element)

    def add(self, element: Column):
        rendered = element.render()
        self.__rendered.append(rendered)

    def render(self) -> Image.Image:
        height = max(element.height for element in self.__rendered) + self.GRID_SIZE
        width = sum(element.width for element in self.__rendered) + self.GRID_SIZE * (
            len(self.__rendered) + 1
        )
        canvas = Image.new("RGBA", (width, height), self.BACKGROUND_COLOR)
        _width = self.GRID_SIZE
        for element in self.__rendered:
            canvas.paste(
                element,
                (_width, 0),
                mask=element,
            )
            _width += element.width + self.GRID_SIZE
        return canvas
