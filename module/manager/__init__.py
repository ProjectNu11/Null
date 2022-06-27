from datetime import datetime, timedelta
from typing import NoReturn, Union, List

from graia.ariadne import Ariadne
from graia.ariadne.event.lifecycle import ApplicationLaunched
from graia.ariadne.event.message import GroupMessage, FriendMessage, MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import Plain, ForwardNode, Forward
from graia.ariadne.message.parser.twilight import (
    Twilight,
    UnionMatch,
    MatchResult,
    ArgumentMatch,
    ArgResult,
    WildcardMatch,
)
from graia.saya import Saya, Channel
from graia.saya.builtins.broadcast import ListenerSchema

from library.config import config
from library.depend import Permission, FunctionCall
from library.model import UserPerm
from library.util.switch import switch
from module import modules as __modules
from .module.install import install_module
from .module.search import search
from .module.switch import module_switch_msg
from library.orm import db_init

try:
    from module.hub_service.exception import HubServiceNotEnabled
    from module.hub_service import hs
except HubServiceNotEnabled:
    hs = None

saya = Saya.current()
channel = Channel.current()

channel.name("ModuleManager")
channel.author("nullqwertyuiop")
channel.description("")


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(".plugin", "插件").help('以 ".plugin" 或 "插件" 开头'),
                    UnionMatch(
                        "install",
                        "uninstall",
                        "load",
                        "reload",
                        "unload",
                        "search",
                        "upgrade",
                        "安装",
                        "删除",
                        "加载",
                        "重载",
                        "卸载",
                        "搜索",
                        "升级",
                    ).help(
                        '功能可选择 "install" "安装" '
                        '"uninstall" "删除" "load" "加载" '
                        '"reload" "重载" "unload" "卸载"'
                        '"search" "搜索" "upgrade" "升级"'
                    )
                    @ "function",
                    ArgumentMatch(
                        "-u", "--upgrade", action="store_true", optional=True
                    ).help("升级插件，安装插件时可选")
                    @ "upgrade",
                    ArgumentMatch(
                        "-f", "--force", action="store_true", optional=True
                    ).help("强制模式，安装或升级插件时可选")
                    @ "force",
                    WildcardMatch(optional=True) @ "name",
                    ArgumentMatch("-c", "--category", optional=True).help("搜索的插件类别")
                    @ "category",
                    ArgumentMatch("-a", "--author", optional=True).help("搜索的插件作者")
                    @ "author",
                ]
            )
        ],
        decorators=[
            Permission.require(
                UserPerm.BOT_OWNER, MessageChain("权限不足，你需要来自 所有人 的权限才能进行本操作")
            ),
            FunctionCall.record(channel.module),
        ],
    )
)
async def module_manager_owner(
    app: Ariadne,
    event: MessageEvent,
    function: MatchResult,
    upgrade: MatchResult,
    force: MatchResult,
    name: ArgResult,
    category: ArgResult,
    author: ArgResult,
):
    function: str = function.result.display
    if not hs and function in {"install", "search", "upgrade", "安装", "搜索", "升级"}:
        return await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender,
            MessageChain(f"HubService 未启用，无法使用 {function}"),
        )
    upgrade: bool = upgrade.matched
    force: bool = force.matched
    name: Union[List[str], str] = str(name.result) if name.matched else ""
    category: str = str(category.result) if category.matched else ""
    author: str = str(author.result) if author.matched else ""
    msg = None
    if function in {"search", "搜索"}:
        msg = await search(name=name, category=category, author=author)
    elif function in {"install", "安装"}:
        name = name.split()
        for mod_name in name:
            await app.send_message(
                event.sender.group if isinstance(event, GroupMessage) else event.sender,
                await install_module(name=mod_name, upgrade=upgrade, version=""),
            )
        return
    elif function in {"load", "加载"}:
        msg = await load_module(name=name)
    elif function in {"reload", "重载"}:
        msg = await reload_module(name=name)
    elif function in {"unload", "卸载"}:
        msg = await unload_module(name=name)
    elif function in {"uninstall", "删除"}:
        pass
    elif function in {"upgrade", "升级"}:
        msg = await upgrade_module(force)
    if msg:
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender, msg
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(".plugin", "插件"),
                    UnionMatch(
                        "list", "enable", "disable", "列表", "枚举", "开启", "打开", "禁用", "关闭"
                    )
                    @ "func",
                    WildcardMatch() @ "param",
                ]
            )
        ],
        decorators=[
            Permission.require(
                UserPerm.ADMINISTRATOR,
                MessageChain("权限不足，你需要来自 管理员 的权限才能进行本操作"),
            ),
            FunctionCall.record(channel.module),
        ],
    )
)
async def module_manager_admin(
    app: Ariadne, event: MessageEvent, func: MatchResult, param: MatchResult
):
    func = func.result.display
    param = param.result.display.strip().split()
    msg = None
    if func in ("list", "枚举"):
        msg = await list_module(
            event.sender.group.id if isinstance(event, GroupMessage) else 0
        )
    elif func in ("enable", "开启", "打开", "disable", "禁用", "关闭"):
        msg = module_switch_msg(
            *param,
            group=event.sender.group.id if isinstance(event, GroupMessage) else 0,
            value=func not in ("disable", "禁用", "关闭"),
        )

    if msg:
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender, msg
        )


@channel.use(
    ListenerSchema(
        listening_events=[GroupMessage, FriendMessage],
        inline_dispatchers=[
            Twilight(
                [
                    UnionMatch(".config", "配置"),
                    UnionMatch("view", "update", "reload", "查看", "更新", "重载") @ "func",
                    WildcardMatch() @ "param",
                ]
            )
        ],
        decorators=[
            Permission.require(
                UserPerm.ADMINISTRATOR,
                MessageChain("权限不足，你需要来自 管理员 的权限才能进行本操作"),
            ),
            FunctionCall.record(channel.module),
        ],
    )
)
async def config_manager_admin(
    app: Ariadne, event: MessageEvent, func: MatchResult, param: MatchResult
):
    func = func.result.display
    # param = param.result.display.strip().split()
    msg = None
    if func in ("view", "查看"):
        # TODO add view_module
        pass
    elif func in ("update", "更新"):
        # TODO add update_module
        pass
    elif func in ("reload", "重载"):
        config.reload()
        msg = MessageChain("成功重载配置")
    if msg:
        await app.send_message(
            event.sender.group if isinstance(event, GroupMessage) else event.sender, msg
        )


async def list_module(group: int = None) -> MessageChain:
    reload_metadata()
    enabled = list(filter(lambda x: x.loaded, __modules))
    disabled = list(filter(lambda x: not x.loaded, __modules))
    fwd_node_list = [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now(),
            message=MessageChain(
                [
                    Plain(text=f"已安装 {len(__modules)} 个插件"),
                    Plain(text="\n==============="),
                    Plain(text=f"\n已加载 {len(enabled)} 个插件") if enabled else Plain(""),
                    Plain(text=f"\n未加载 {len(disabled)} 个插件") if disabled else Plain(""),
                ]
            ),
        )
    ]
    for index, module in enumerate(enabled + disabled):
        module_category = (
            "实用工具"
            if module.category == "utility"
            else "娱乐"
            if module.category == "entertainment"
            else "其他"
        )
        module_dependency = ", ".join(module.dependency) if module.dependency else "无"
        if group:
            if module.pack != channel.module:
                _switch = switch.get(module.pack, group) and module.loaded
            else:
                _switch = True
            switch_status = f"\n - 开关：{'已' if _switch else '未'}开启"
        else:
            switch_status = ""
        fwd_node_list.append(
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=15) * (index + 1),
                message=MessageChain(
                    [
                        Plain(f"{index + 1}. {module.name}"),
                        Plain(f"\n - 包名：{module.pack}"),
                        Plain(f"\n - 版本：{module.version}"),
                        Plain(f"\n - 作者：{', '.join(module.author)}"),
                        Plain(f"\n - 分类：{module_category}"),
                        Plain(f"\n - 描述：{module.description}"),
                        Plain(f"\n - 依赖：{module_dependency}"),
                        Plain(f"\n - 状态：{'已' if module.loaded else '未'}安装"),
                        Plain(f"{switch_status}" if module.loaded else ""),
                    ]
                ),
            )
        )
    return MessageChain([Forward(fwd_node_list)])


async def load_module(name: str) -> MessageChain:
    reload_metadata()
    if module := __modules.get(name):
        try:
            with saya.module_context():
                saya.require(module.pack)
                await db_init()
                saya.require(module.pack)
            module.loaded = True
            return MessageChain(f"已加载插件 {name}")
        except Exception as e:
            return MessageChain(f"加载插件 {name} 时发生错误：\n{e}")
    return MessageChain(f"无法找到插件 {name}")


async def unload_module(name: str) -> MessageChain:
    reload_metadata()
    if module := __modules.get(name):
        if chn := saya.channels.get(module.pack, None):
            if isinstance(module.override_default, bool):
                return MessageChain(
                    f"无法更改插件 {name} 的状态，插件状态固定为 {module.override_default}"
                )
            module.loaded = False
            saya.uninstall_channel(chn)
            return MessageChain(f"已卸载插件 {name}")
    return MessageChain(f"无法找到插件 {name}")


async def reload_module(name: str) -> MessageChain:
    await unload_module(name)
    return await load_module(name)


async def upgrade_module(force: bool = False) -> MessageChain:
    reload_metadata()
    msg = []
    for mod in list(__modules):
        if modules := await hs.search_module(name=mod.pack):
            if modules[0].version == mod.version and not force:
                continue
            msg.append(
                await install_module(
                    name=mod.pack, version=modules[0].version, upgrade=True
                )
            )
        continue
    if msg:
        fwd_node_list = [
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now(),
                message=MessageChain(f"已更新 {len(msg)} 个插件"),
            )
        ] + [
            ForwardNode(
                target=config.account,
                name=f"{config.name}#{config.num}",
                time=datetime.now() + timedelta(seconds=15) * (index + 1),
                message=msg_chain,
            )
            for index, msg_chain in enumerate(msg)
        ]
        return MessageChain([Forward(fwd_node_list)])
    return MessageChain("暂无更新可用")


def reload_metadata() -> NoReturn:
    __modules.load(reorder=True)


@channel.use(ListenerSchema(listening_events=[ApplicationLaunched]))
async def init():
    await db_init()
