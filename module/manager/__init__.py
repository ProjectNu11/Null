from graia.ariadne import Ariadne
from graia.ariadne.event.message import GroupMessage
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    MatchResult,
    ArgumentMatch,
    ArgResult,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.depend import Permission
from library.model import UserPerm

saya = Saya.current()
channel = Channel.current()

channel.name("ModuleManager")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(".plugin", "插件"),
                    UnionMatch(
                        "install",
                        "uninstall",
                        "load",
                        "unload",
                        "info",
                        "list",
                        "search",
                        "安装",
                        "删除",
                        "加载",
                        "卸载",
                        "详情",
                        "枚举",
                        "搜索",
                    )
                    @ "function",
                    UnionMatch("-u", "--update", optional=True) @ "update",
                    ArgumentMatch("-n", "--name", optional=True) @ "name",
                    ArgumentMatch("-c", "--category", optional=True) @ "category",
                    ArgumentMatch("-a", "--author", optional=True) @ "author",
                ]
            )
        ],
        decorators=[Permission.require(UserPerm.BOT_OWNER)],
    )
)
async def module_manager(
    app: Ariadne,
    event: GroupMessage,
    update: MatchResult,
    name: ArgResult,
    category: ArgResult,
    author: ArgResult,
):
    pass
