import asyncio
import pickle
from pathlib import Path

from PIL import Image

from library import config
from library.image import IconUtil
from library.image.oneui_mock.color import Color
from library.image.oneui_mock.elements import Banner, Header, Box, Column, OneUIMock
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
    __banner: Banner
    __header: Header
    __field: int
    __dark: bool

    def __init__(
        self,
        field: int,
        avatar: Image.Image,
        *,
        banner: str = "帮助菜单",
        dark: bool = False,
    ) -> None:
        self.__banner = Banner(banner, dark=dark)
        self.__header = Header(
            text=f"{config.name}#{config.num}",
            description=config.description,
            icon=avatar,
            dark=dark,
        )
        self.__field = field
        self.__dark = dark

    @staticmethod
    def __get_module_icon(module: Module) -> Image.Image:
        icon = Path(module.pack, "icon.png")
        if icon.is_file():
            return Image.open(icon)
        else:
            return IconUtil.get_icon("toy-brick", color=Color.FOREGROUND_COLOR_LIGHT)

    def compose_module_boxes(self) -> list[Box]:
        boxes: dict[int, Box] = {
            0: Box(dark=self.__dark),
            1: Box(dark=self.__dark),
            2: Box(dark=self.__dark),
            3: Box(dark=self.__dark),
        }

        for module in modules:
            if module.hidden:
                continue
            icon = self.__get_module_icon(module)
            offset = 0
            if not module.loaded:
                offset = 2
            status = self.__get_switch(module.pack, self.__field)
            status = int(status) + offset
            boxes[status].add(
                module.name, module.description or "暂无描述", icon, COLOR_PALETTE[status]
            )

        box_list = [boxes[0], boxes[1], boxes[2], boxes[3]]
        return [box for box in box_list if box.has_content()]

    @staticmethod
    def __get_switch(module: str, field: int) -> bool:
        if (status := switch.get(module, field)) is None:
            status = config.func.default
        return status

    def compose_module_summary_box(self) -> Box:
        total = len(modules)
        enabled = len(
            [
                module
                for module in modules
                if self.__get_switch(module.pack, self.__field)
            ]
        )
        hidden = len([module for module in modules if module.hidden])
        unloaded = len([module for module in modules if not module.loaded])

        box = Box(dark=self.__dark)
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
                icon_color=COLOR_PALETTE[3],
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

    def load_custom_element(self) -> list[Box, Image.Image]:
        elements = []
        for file in custom_element_path.iterdir():
            if file.name.startswith("DARK-") and not self.__dark:
                continue
            if file.name.endswith(".pickle"):
                with file.open("rb") as f:
                    element = pickle.load(f)
                    if isinstance(element, (Box, Image.Image)):
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
        column1 = Column(dark=self.__dark)
        column1.add(self.__banner)
        column1.add(self.__header)
        summary_box = self.compose_module_summary_box()
        column1.add(summary_box)

        column2 = Column(dark=self.__dark)

        elements = self.compose_module_boxes()
        elements.sort(key=lambda box: len(box))
        elements.extend(self.load_custom_element())

        for element in elements:
            min([column1, column2], key=lambda column: len(column)).add(element)
        return [column for column in [column1, column2] if column.has_content()]

    def compose(self) -> Image.Image:
        menu = OneUIMock(*self.compose_columns(), dark=self.__dark)
        return menu.render()

    async def async_compose(self) -> Image.Image:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.compose)
