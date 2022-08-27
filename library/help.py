import asyncio
import itertools
import math
import pickle
from pathlib import Path

from PIL import Image

from library import config
from library.image import IconUtil
from library.image.oneui_mock.color import Color
from library.image.oneui_mock.elements import (
    Banner,
    Header,
    Box,
    MenuBox,
    Column,
    OneUIMock,
    GeneralBox,
    Element,
    is_dark,
)
from library.model import Module
from library.util.switch import switch
from module import modules

custom_element_path = Path(config.path.data, "library", "help")
custom_element_path.mkdir(exist_ok=True)

COLOR_PALETTE = {
    -1: (69, 90, 100),
    0: (183, 28, 28),
    1: (27, 94, 32),
    2: (127, 0, 0),
    3: (0, 51, 0),
}


class HelpMenu:
    banner: Banner
    header: Header
    field: int
    dark: bool

    registered_boxes: set[Box | Image.Image] = set()

    def __init__(
        self,
        field: int,
        avatar: Image.Image,
        *,
        banner: str = "帮助菜单",
        dark: bool = False,
    ) -> None:
        self.banner = Banner(banner, dark=dark)
        self.header = Header(
            text=f"{config.name}#{config.num}",
            description=config.description,
            icon=avatar,
            dark=dark,
        )
        self.field = field
        self.dark = dark

    @staticmethod
    def __get_module_icon(module: Module) -> Image.Image:
        icon = Path(Path().resolve(), *module.pack.split("."), "icon.png")
        if icon.is_file():
            return Image.open(icon)
        else:
            return IconUtil.get_icon("toy-brick", color=Color.FOREGROUND_COLOR_LIGHT)

    def compose_module_boxes(self) -> list[Box]:
        boxes: dict[int, list[MenuBox]] = {
            0: [],
            1: [],
            2: [],
            3: [],
        }

        categories = modules.get_categories()

        for box_list, _ in itertools.product(boxes.values(), categories):
            box_list.append(MenuBox())
        box_cord = {key: value for value, key in enumerate(categories)}

        for module in modules:
            if module.hidden:
                continue
            box_index = box_cord.get(module.category, 0)
            icon = self.__get_module_icon(module)
            offset = 0
            if not module.loaded:
                offset = 2
            status = self.__get_switch(module.pack, self.field)
            status = int(status) + offset
            boxes[status][box_index].add(
                module.name, module.description or "暂无描述", icon, COLOR_PALETTE[status]
            )

        box_list = [*boxes[0], *boxes[1], *boxes[2], *boxes[3]]
        return [box for box in box_list if box.has_content()]

    @staticmethod
    def __get_switch(module: str, field: int) -> bool:
        if (status := switch.get(module, field)) is None:
            status = config.func.default
        return status

    def compose_module_summary_box(self) -> MenuBox:
        total = len(modules)
        enabled = len(
            [module for module in modules if self.__get_switch(module.pack, self.field)]
        )
        hidden = len([module for module in modules if module.hidden])
        unloaded = len([module for module in modules if not module.loaded])

        box = MenuBox(dark=self.dark)
        box.add(
            text=f"已安装 {total} 个插件",
            description="包括本地安装及网络安装",
            icon=IconUtil.get_icon("download", color=Color.FOREGROUND_COLOR_LIGHT),
            icon_color=COLOR_PALETTE[-1],
        )
        if enabled:
            box.add(
                text=f"已启用 {enabled} 个插件",
                description="将以 浅绿色 显示",
                icon=IconUtil.get_icon("check", color=Color.FOREGROUND_COLOR_LIGHT),
                icon_color=COLOR_PALETTE[1],
            )
        if disabled := total - enabled:
            box.add(
                text=f"已禁用 {disabled} 个插件",
                description="将以 浅红色 显示",
                icon=IconUtil.get_icon("close", color=Color.FOREGROUND_COLOR_LIGHT),
                icon_color=COLOR_PALETTE[0],
            )
        if hidden:
            box.add(
                text=f"已隐藏 {hidden} 个插件",
                description="将不会显示，但是可被调用",
                icon=IconUtil.get_icon("blur", color=Color.FOREGROUND_COLOR_LIGHT),
                icon_color=COLOR_PALETTE[2],
            )
        if unloaded:
            box.add(
                text=f"未安装 {unloaded} 个插件",
                description="将以 深色 显示",
                icon=IconUtil.get_icon(
                    "exclamation", color=Color.FOREGROUND_COLOR_LIGHT
                ),
                icon_color=COLOR_PALETTE[-1],
            )

        return box

    def get_switch_box(self) -> GeneralBox:
        return GeneralBox(
            text="默认插件开关",
            description="是否默认打开所有插件",
            switch=config.func.default,
            dark=self.dark,
        ).add(text="开关提醒", description="插件关闭时被调用是否发送提醒", switch=config.func.notice)

    def load_custom_element(self) -> list[MenuBox, Image.Image]:
        elements = []
        for file in custom_element_path.iterdir():
            if not file.name.startswith("UNIVERSAL-"):
                if self.dark and not file.name.startswith("DARK-"):
                    continue
                if not self.dark and file.name.startswith("DARK-"):
                    continue
            if file.name.endswith(".pickle"):
                with file.open("rb") as f:
                    element = pickle.load(f)
                    if isinstance(element, (MenuBox, Image.Image)):
                        elements.append(element)
                continue
            if (
                file.name.endswith(".png")
                or file.name.endswith(".jpg")
                or file.name.endswith(".jpeg")
            ):
                elements.append(Image.open(file))
        return elements

    def compose_columns(self) -> list[Column]:
        column1 = Column(dark=self.dark)
        column1.add(self.banner)
        column1.add(self.header)
        summary_box = self.compose_module_summary_box()
        column1.add(summary_box)

        column2 = Column(dark=self.dark)
        column3 = Column(dark=self.dark)

        elements = self.compose_module_boxes()
        elements.append(self.get_switch_box())
        elements.extend(self.registered_boxes)
        elements.sort(key=lambda box: len(box))
        elements.extend(self.load_custom_element())

        columns = [column1, column2]
        if len(elements) >= 9:
            columns.append(column3)

        for element in elements:
            min(columns, key=lambda column: len(column)).add(element, dark=self.dark)
        return [column for column in columns if column.has_content()]

    def compose(self) -> Image.Image:
        menu = OneUIMock(*self.compose_columns(), dark=self.dark)
        return menu.render()

    async def async_compose(self) -> Image.Image:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.compose)

    @classmethod
    def register_box(cls, *elements: Box | Image.Image):
        for element in elements:
            element_hash = hash(element)
            if bool(
                list(filter(lambda x: hash(x) == element_hash, cls.registered_boxes))
            ):
                continue
            cls.registered_boxes.add(element)

    @classmethod
    def unregister_all(cls):
        cls.registered_boxes.clear()


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
            if module in box.text:
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
        elements.sort(
            key=lambda box: len("".join([line for line in box.description if line])),
            reverse=True,
        )

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
