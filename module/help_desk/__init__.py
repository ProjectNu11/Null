import asyncio
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
    ArgResult,
    UnionMatch,
    ElementMatch,
    WildcardMatch,
)
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graiax.playwright import PlaywrightBrowser

from library import config, prefix_match
from library.depend import Blacklist, FunctionCall, Switch
from library.help import HelpMenu, Disclaimer, module_help
from library.image.oneui_mock.elements import (
    HintBox,
    OneUIMock,
    Column,
    Banner,
    GeneralBox,
)
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
                    WildcardMatch() @ "module",
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
async def help_menu(app: Ariadne, event: MessageEvent, module: ArgResult):
    if not module.matched or not (module := module.result.display):
        await get_avatar(app)
        field = event.sender.group.id if isinstance(event, GroupMessage) else 0
        menu = await get_help(app, field)
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(Image(data_bytes=menu)),
        )
    module = module.strip().lower().replace(" ", "_").replace("-", "_")
    if not (result := modules.search(match_any=True, name=module, pack=module)):
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(
                Image(
                    data_bytes=await OneUIMock(
                        Column(
                            Banner(
                                "帮助菜单",
                                icon=PillowImage.open(
                                    Path(__file__).parent / "icon.png"
                                ),
                            ),
                            GeneralBox(f"无法找到模块 {module}"),
                            HintBox("可以尝试以下解决方案", "检查模块名是否正确", "检查模块是否已正确安装"),
                        )
                    ).async_render_bytes()
                )
            ),
        )
    result = result[0]
    return await app.send_message(
        event.sender.group if isinstance(event, GroupMessage) else event.sender,
        MessageChain(
            Image(
                data_bytes=await module_help(result).render(
                    field=event.sender.group.id
                    if isinstance(event, GroupMessage)
                    else 0
                )
            )
        ),
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
                    prefix_match(),
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


HelpMenu.register_box(HintBox('您可发送 ".help 插件名" 取得插件的详细帮助'))
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
