import pickle
from datetime import datetime
from hashlib import md5
from io import BytesIO
from pathlib import Path

from PIL import Image as PillowImage
from aiohttp import ClientSession
from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import (
    Twilight,
    FullMatch,
    SpacePolicy,
    ArgumentMatch,
    ArgResult,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from loguru import logger
from pydantic import BaseModel

from library import config
from library.depend import Permission
from library.help import HelpMenu
from library.model import UserPerm
from library.util.switch import switch
from module import modules

channel = Channel.current()

data_path = Path(config.path.data, channel.module)
data_path.mkdir(exist_ok=True)

avatar_img: PillowImage.Image


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    FullMatch(config.func.prefix).space(SpacePolicy.NOSPACE),
                    FullMatch("help"),
                    ArgumentMatch("-i", "--invalidate", action="store_true")
                    @ "invalidate",
                ]
            )
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
    global avatar_img
    field = event.sender.group.id if isinstance(event, GroupMessage) else 0
    async with ClientSession() as session:
        async with session.get(
            f"https://q2.qlogo.cn/headimg_dl?dst_uin={app.account}&spec=640"
        ) as resp:
            avatar = BytesIO(await resp.read())
    avatar_img = PillowImage.open(avatar)
    menu = await one_ui_help_menu.get(field, app)
    await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain([Image(data_bytes=menu)]),
    )


class GroupCache(BaseModel):
    id: int
    light: bytes = None
    dark: bytes = None
    hash: str = None

    def generate_hash(self) -> str:
        data: dict[str:int] = {}
        for module in modules:
            offset = 0
            if not module.loaded:
                offset = 2
            if (status := switch.get(module.pack, self.id)) is None:
                status = config.func.default
            status = int(status) + offset
            data[module.pack] = status
        return md5(pickle.dumps(data)).hexdigest()

    def compare_hash(self) -> bool:
        return self.hash == self.generate_hash()

    def update_hash(self) -> None:
        self.hash = self.generate_hash()

    async def cache(self, dark: bool = False) -> None:
        menu = HelpMenu(self.id, avatar_img, dark=dark)
        menu_image = await menu.async_compose()
        self.update_hash()
        output = BytesIO()
        menu_image.convert("RGB").save(output, format="JPEG")
        if dark:
            self.dark = output.getvalue()
            return
        self.light = output.getvalue()

    async def invalidate(self) -> None:
        self.hash = ""

    async def get(self, dark: bool, app: Ariadne):
        if self.compare_hash():
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


def is_dark() -> bool:
    return not (6 < datetime.now().hour < 18)


one_ui_help_menu = OneUIHelpMenu()
