from typing import Union

from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Group

from library.util.switch import switch
from module import modules as modules


def module_switch(name: str, group: Union[int, Group], value: bool) -> bool:
    if module := modules.get(name):
        if isinstance(module.override_switch, bool) and module.override_switch != value:
            return False
        switch.update(pack=module.pack, group=group, value=value)
        return True


def module_switch_msg(*args, **kwargs) -> MessageChain:
    """
    Switch module.

    :param args: module names
    :param kwargs: group: Group, value: bool
    :return: MessageChain
    """

    assert (group := kwargs.get("group", None)), "未指定参数 group"
    if not isinstance(value := kwargs.get("value", None), bool):
        raise AssertionError("未指定参数 value")
    success_count = 0
    failed = []
    for name in args:
        if module_switch(name, group, value):
            success_count += 1
        else:
            failed.append(name)
    msg = MessageChain(f"已{'开启' if value else '关闭'} {success_count} 个插件")
    if failed:
        msg += MessageChain(f"\n以下 {len(failed)} 个插件无法找到或无法改动：")
        for fail in failed:
            msg += MessageChain(f"\n - {fail}")
    return msg
