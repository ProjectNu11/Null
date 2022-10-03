from loguru import logger
from typing_extensions import Self

from library import config
from library.image.oneui_mock.elements import (
    Element,
    OneUIMock,
    Column,
    About,
    GeneralBox,
)
from library.model import Module
from library.util.switch import switch
from module import modules, category_locale


class ModuleHelp:
    class ModulePage:
        module: Module
        elements: list[Element]

        def __init__(self, pack: str | Module):
            self.module = modules.get(pack) if isinstance(pack, str) else pack
            self.elements = []

        def add(self, *element: Element) -> Self:
            self.elements.extend(
                [
                    e
                    for e in element
                    if hash(e) not in [hash(ee) for ee in self.elements]
                    and isinstance(e, Element)
                ]
            )
            return self

        def flush(self) -> Self:
            self.elements = []
            return self

        def generate_mock(self, field: int = 0) -> OneUIMock:
            box = GeneralBox(divider=False)
            for title, content in self.module.help.items():
                box.add(
                    title,
                    content.format(
                        prefix=config.func.prefix[0] if config.func.prefix else ""
                    ),
                )
            _switch = switch.get(self.module.pack, field)
            if _switch is None:
                _switch = config.func.default
            return OneUIMock(
                Column(
                    About(
                        title=self.module.name,
                        description=[
                            f"ver. {self.module.version}",
                            *self.module.author,
                        ],
                        buttons=[
                            category.title()
                            for _category in self.module.category
                            if (category := category_locale.get(_category, _category))
                        ],
                    ),
                    GeneralBox(divider=False)
                    .set_name("插件详情")
                    .add("插件包名", self.module.pack)
                    .add("插件描述", self.module.description)
                    .add(
                        "插件依赖",
                        "\n".join(
                            [
                                modules(match_any=True, pack=dependency)[0].name
                                for dependency in self.module.dependency
                            ]
                        )
                        if self.module.dependency
                        else "无",
                    )
                    .add("加载状态", switch=self.module.loaded)
                    .add("开关状态", switch=_switch),
                    box,
                    *self.elements,
                )
            )

        async def render(self, field: int = 0) -> bytes:
            return await self.generate_mock(field=field).async_render_bytes()

    modules: dict[str, ModulePage]

    def __init__(self):
        self.modules = {
            module.pack: ModuleHelp.ModulePage(module)
            for module in modules
            if isinstance(module, Module)
        }

    def __call__(self, pack: str | Module, __retry: bool = True) -> ModulePage:
        if isinstance(pack, Module):
            pack = pack.pack
        if pack in self.modules:
            return self.modules[pack]
        if not __retry:
            raise KeyError(f"Module {pack} not found")
        self.__init__()
        return self(pack, False)


module_help = ModuleHelp()
