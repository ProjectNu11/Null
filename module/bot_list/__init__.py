import asyncio

from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Image
from graia.ariadne.message.parser.twilight import Twilight, FullMatch
from graia.ariadne.model import Group
from graia.saya import Channel
from graia.saya.builtins.broadcast import ListenerSchema
from graia.scheduler import timers
from graia.scheduler.saya import SchedulerSchema
from loguru import logger

from library import PrefixMatch, config
from library.depend import Blacklist, FunctionCall
from library.help import HelpMenu
from library.image.oneui_mock.elements import (
    GeneralBox,
    Column,
    Banner,
    OneUIMock,
    HintBox,
)
from library.util.blacklist.bot import bot_list, Bot

channel = Channel.current()


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight([PrefixMatch, FullMatch("botlist"), FullMatch("check")])
        ],
        decorators=[
            Blacklist.check(),
            FunctionCall.record(channel.module),
        ],
    )
)
async def botlist_check(app: Ariadne, event: GroupMessage):
    if not (members := await app.get_member_list(event.sender.group)):
        return await app.send_group_message(
            event.sender.group, MessageChain("无法获取群员列表")
        )
    return (
        await app.send_group_message(
            event.sender.group,
            MessageChain(
                Image(
                    data_bytes=await asyncio.to_thread(
                        generate_bot_summary, event.sender.group, *bots
                    )
                )
            ),
        )
        if (bots := bot_list.bulk_check(*members))
        else await app.send_group_message(
            event.sender.group, MessageChain("本群暂无已登记的其他 Bot")
        )
    )


def generate_bot_summary(group: Group, *bots: Bot) -> bytes:
    columns = [
        Column(
            Banner("机器人名单"),
            GeneralBox(group.name, str(group.id)).add(
                f"一共有 {len(bots)} 个机器人", "仅包含已注册的机器人"
            ),
        )
    ]
    if len(bots) > 10:
        columns.append(Column())

    for bot in bots:
        min(columns, key=lambda column: len(column)).add(
            GeneralBox(f"{bot.name}#{bot.num}", bot.kind.name)
        )

    return OneUIMock(*columns).render_bytes()


@channel.use(SchedulerSchema(timer=timers.every_custom_hours(24)))
@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def bot_list_fetch_update():
    await bot_list.update()
    logger.success("更新机器人列表成功")


HelpMenu.register_box(
    HintBox(
        "本项目默认不响应其他机器人的指令", f'可发送 "{config.func.prefix[0]}botlist check" 查看本群是否有其他机器人'
    )
)
