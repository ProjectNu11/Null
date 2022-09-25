import asyncio
import pickle
from hashlib import md5
from io import BytesIO
from pathlib import Path

from PIL import Image as PillowImage
from aiohttp import ClientSession
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image, At
from graia.ariadne.message.parser.twilight import (
    Twilight,
    SpacePolicy,
    ArgumentMatch,
    ArgResult,
    UnionMatch,
    ElementMatch,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graiax.playwright import PlaywrightBrowser
from loguru import logger
from pydantic import BaseModel

from library import config, PrefixMatch
from library.depend import Permission, Blacklist, FunctionCall, Switch
from library.help import HelpMenu, Disclaimer
from library.image.oneui_mock.elements import is_dark, HintBox
from library.model import UserPerm
from library.util.switch import switch
from module import modules

channel = Channel.current()

data_path = Path(config.path.data, channel.module)
data_path.mkdir(exist_ok=True)

avatar_img: PillowImage.Image | None = None


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    ElementMatch(At, optional=True),
                    UnionMatch(
                        *config.func.prefix, ".", "/", "?", "#", "。", "？", optional=True
                    ).space(SpacePolicy.NOSPACE),
                    UnionMatch("help", "帮助", "菜单"),
                    ArgumentMatch("-i", "--invalidate", action="store_true")
                    @ "invalidate",
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module, global_only=True),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def help_menu(app: Ariadne, event: MessageEvent, invalidate: ArgResult):
    if invalidate.result:
        if not Permission.permission_check(UserPerm.BOT_OWNER, event):
            return
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"已清空 {one_ui_help_menu.invalidate()} 个群组的缓存"),
        )
    await get_avatar(app)
    field = event.sender.group.id if isinstance(event, GroupMessage) else 0
    # menu = await one_ui_help_menu.get(field, app)
    menu = await get_help(app, field)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain([Image(data_bytes=menu)]),
    )


async def get_help(app: Ariadne, field: int) -> bytes:
    mock = await HelpMenu(field, avatar_img).async_get_mock()
    browser = app.launch_manager.get_interface(PlaywrightBrowser)
    async with browser.page(
        viewport={"width": mock.width, "height": 10},
        device_scale_factor=1.5,
    ) as page:
        await page.set_content(mock.generate_html())
        img = await page.screenshot(
            type="jpeg", quality=80, full_page=True, scale="device"
        )
        return img


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    PrefixMatch,
                    UnionMatch("disclaimer", "免责声明"),
                ]
            )
        ],
        decorators=[
            Switch.check(channel.module, global_only=True),
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def disclaimer(app: Ariadne, event: MessageEvent):
    await get_avatar(app)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            [
                Image(
                    data_bytes=await asyncio.to_thread(
                        Disclaimer.render, avatar=avatar_img
                    )
                )
            ]
        ),
    )


async def get_avatar(app: Ariadne) -> PillowImage.Image:
    global avatar_img
    if not isinstance(avatar_img, PillowImage.Image):
        async with ClientSession() as session:
            async with session.get(
                f"https://q2.qlogo.cn/headimg_dl?dst_uin={app.account}&spec=640"
            ) as resp:
                avatar = BytesIO(await resp.read())
        avatar_img = PillowImage.open(avatar)
    return avatar_img


class GroupCache(BaseModel):
    id: int
    light: bytes | None = None
    light_hash: str | None = None
    dark: bytes | None = None
    dark_hash: str | None = None

    def generate_hash(self) -> str:
        data: dict[str, int] = {}
        for module in modules:
            offset = 0
            if not module.loaded:
                offset = 2
            if (status := switch.get(module.pack, self.id)) is None:
                status = config.func.default
            status = int(status) + offset
            data[module.pack] = status
        return md5(pickle.dumps(data)).hexdigest()

    def compare_hash(self, dark: bool) -> bool:
        if dark:
            return self.dark_hash == self.generate_hash()
        return self.light_hash == self.generate_hash()

    def update_hash(self, dark: bool) -> None:
        if dark:
            self.dark_hash = self.generate_hash()
        else:
            self.light_hash = self.generate_hash()

    async def cache(self, dark: bool = False) -> None:
        menu = HelpMenu(self.id, avatar_img, dark=dark)
        menu_image = await menu.async_compose()
        self.update_hash(dark)
        output = BytesIO()
        menu_image.convert("RGB").save(output, format="JPEG")
        if dark:
            self.dark = output.getvalue()
            return
        self.light = output.getvalue()

    def invalidate(self) -> None:
        self.light = None
        self.light_hash = None
        self.dark = None
        self.dark_hash = None

    async def get(self, dark: bool, app: Ariadne):
        if self.compare_hash(dark):
            return self.dark if dark else self.light
        if self.id != 0:
            await app.send_group_message(self.id, MessageChain("正在更新缓存..."))
        await self.cache(dark)
        one_ui_help_menu.save_pickle()
        return self.dark if dark else self.light


class OneUIHelpMenu:
    __cached_menu: dict[int, GroupCache] = {}

    def __init__(self):
        self.load_pickle()

    async def get(self, group: int, app: Ariadne):
        dark = is_dark()
        if group not in self.__cached_menu:
            self.__cached_menu[group] = GroupCache(id=group)
        return await self.__cached_menu[group].get(dark=dark, app=app)

    def invalidate(self) -> int:
        for _, cache in self.__cached_menu.items():
            cache.invalidate()
        self.save_pickle()
        return len(self.__cached_menu)

    def save_pickle(self):
        with Path(data_path, "cache.pickle").open("wb") as f:
            f.write(pickle.dumps(self.__cached_menu))

    def load_pickle(self):
        pickle_path = Path(data_path, "cache.pickle")
        if not pickle_path.is_file():
            self.__cached_menu = {}
            self.save_pickle()
            return
        try:
            with pickle_path.open("rb") as f:
                self.__cached_menu = pickle.load(f)
        except EOFError:
            logger.error(
                f"Failed to load help cache from pickle file at {pickle_path}, resetting..."
            )
            pickle_path.unlink(missing_ok=True)
            self.__init__()


one_ui_help_menu = OneUIHelpMenu()

HelpMenu.register_box(
    HintBox(
        "本项目开源于以下 Github 仓库",
        "项目本体 ProjectNu11/Project-Null",
        "插件仓库 ProjectNu11/PN-Plugins",
        "中心服务 ProjectNu11/PN-Hub",
    ),
)
HelpMenu.register_box(
    HintBox(
        "免责声明",
        "本项目仅供学习交流使用，不得用于商业用途。",
        f"您可发送“{config.func.prefix[0]}免责声明”查看本项目及其附属插件的免责声明。",
    )
)

Disclaimer.register(
    "开源协议", "本项目基于以下 AGPL v3 开源组件开发", "mirai", "mirai-api-http", "Ariadne"
)
Disclaimer.register(
    "隐私策略",
    "本项目尊重并保护所有使用服务用户的个人隐私权。为了给您提供更准确、更"
    "有个性化的服务，本项目会按照本隐私权政策的规定使用和披露您的个人信息"
    "。但本项目将以高度的勤勉、审慎义务对待这些信息。除本隐私权政策另有规"
    "定外，在未征得您事先许可的情况下，本项目不会将这些信息对外披露或向第"
    "三方提供。本项目会不时更新本隐私权政策。",
    "您在同意本项目服务使用协议之时，即视为您已经同意本隐私权政策全部内容。",
    "本隐私权政策属于本项目服务使用协议不可分割的一部分。",
)
Disclaimer.register(
    "免责声明",
    "本项目仅限学习使用，不涉及任何商业或者金钱用途，禁止用于非法行为。您的使用行为将被是为对本声明全部内容的认可。",
    "本声明在您邀请该账号进入任何腾讯 QQ 群组或通过私聊该账号调用功能时生效。",
    "Project. Null （下简称为“本项目”）在运行时不可避免地会使用到您的 "
    "QQ 号、QQ 昵称、群名片、群号、群组权限等信息。本项目后台默认会收集您"
    "的聊天内容（见“隐私策略”）以实现部分功能及故障诊断，您可在任何时期"
    "选择停止对您的聊天内容的收集、请求下载您的聊天内容归档并从数据库中删"
    "除。如果您对此持有疑问，请停止使用本项目。",
    "本项目有权停止对任何对象的服务，所有解释权归项目组所有。",
)
Disclaimer.register(
    "隐私策略的更改",
    "如果决定更改隐私政策，项目组将会在本政策中发布这些更改，以便您了解我们"
    "如何收集、使用您的个人信息，哪些人可以访问这些信息，以及什么情况下我们"
    "会透露这些信息。",
    "项目组保留随时修改本政策的权力，因此请经常查看。",
)
