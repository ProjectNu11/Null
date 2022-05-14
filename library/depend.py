from typing import NoReturn

from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library.config import config, get_switch
from library.model import UserPerm


class Permission:
    @classmethod
    def require(cls, permission: UserPerm) -> Depend:
        async def perm_check(event: MessageEvent) -> NoReturn:
            if not cls.permission_check(permission, event):
                raise ExecutionStop

        return Depend(perm_check)

    @staticmethod
    def permission_check(permission: UserPerm, event: MessageEvent):
        if event.sender.id in config.owners:
            user_perm = UserPerm.BOT_OWNER
        elif isinstance(event, GroupMessage):
            user_perm = getattr(UserPerm, str(event.sender.permission))
        else:
            user_perm = UserPerm.MEMBER
        if user_perm < permission:
            return False
        return True


class Switch:
    @staticmethod
    def check(pack: str, override_level: UserPerm = None) -> Depend:
        async def switch_check(event: MessageEvent) -> NoReturn:
            if override_level:
                if Permission.permission_check(override_level, event):
                    return
            if isinstance(event, GroupMessage):
                value = get_switch(pack, event.sender.group)
                if isinstance(value, bool):
                    if not value:
                        raise ExecutionStop
                    return
            if not config.func.default:
                raise ExecutionStop

        return Depend(switch_check)
