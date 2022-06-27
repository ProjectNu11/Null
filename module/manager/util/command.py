import re
from typing import List, Callable, Tuple

from . import hs
from ..module.switch import module_switch
from ..module.search import search_msg
from ..module.install import install_module
from ..module.uninstall import async_uninstall_module

module_commands = {
    "install": install_module,
    "uninstall": async_uninstall_module,
    "load": ...,
    "reload": ...,
    "unload": ...,
    "search": search_msg,
    "upgrade": ...,
    "list": ...,
    "enable": module_switch,
    "disable": module_switch,
    "安装": install_module,
    "删除": async_uninstall_module,
    "加载": ...,
    "重载": ...,
    "卸载": ...,
    "搜索": ...,
    "升级": ...,
    "列表": ...,
    "枚举": ...,
    "开启": module_switch,
    "打开": module_switch,
    "禁用": module_switch,
    "关闭": module_switch,
}


def argument_parse(argument: str) -> List[str]:
    """
    Parse the command argument into a list of arguments

    :param argument: Command argument
    :return: List of arguments
    """

    if __arguments := re.findall(r"""".+?"|'.+?'|[^ "']+""", argument):
        return [arg.strip("'").strip('"') for arg in __arguments]


def module_command_parse(function: str, argument: str) -> Tuple[Callable, List[str]]:
    """
    Parse the command text into a list of commands

    :param function: Command function
    :param argument: Command argument
    :return: List of commands
    """

    if not hs and function in {"install", "search", "upgrade", "安装", "搜索", "升级"}:
        raise AssertionError(f"HubService 未启用，无法使用 {function} 命令")
    function = module_commands[function]
    return function, argument_parse(argument)
