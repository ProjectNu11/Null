from datetime import datetime, timedelta
from typing import List

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.message.element import ForwardNode, Forward, Plain

from library import config
from library.model import Module
from ..util import hs


async def search(name: str, category: str, author: str) -> List[Module]:
    return await hs.search_module(name=name, category=category, author=author)


async def search_msg(name: str, category: str, author: str) -> MessageChain:
    if not (modules := await search(name=name, category=category, author=author)):
        return MessageChain("无法找到符合要求的插件")
    fwd_node_list = [
        ForwardNode(
            target=config.account,
            name=f"{config.name}#{config.num}",
            time=datetime.now(),
            message=MessageChain(f"查询到 {len(modules)} 个插件"),
        )
    ]
    fwd_node_list += module_details(modules)
    return MessageChain([Forward(fwd_node_list)])


def module_details(modules: List[Module]) -> List[ForwardNode]:
    result = []
    category_cord = {
        "utility": "实用工具",
        "entertainment": "娱乐",
        "misc": "杂项",
    }
    for index, module in enumerate(modules):
        module_category = category_cord.get(module.category, "未知")
        module_dependency = ", ".join(module.dependency) if module.dependency else "无"
        result += [
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
                        Plain(f"\n - Pypi：{'是' if module.pypi else '否'}"),
                    ]
                ),
            )
        ]
    return result
