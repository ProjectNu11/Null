from typing import NoReturn

from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library.config import config
from library.model import UserPerm


class Permission:
    @staticmethod
    def require(permission: UserPerm) -> Depend:
        async def perm_check(event: MessageEvent) -> NoReturn:
            if event.sender.id in config.owners:
                user_perm = UserPerm.BOT_OWNER
            elif isinstance(event, GroupMessage):
                user_perm = getattr(UserPerm, str(event.sender.permission))
            else:
                user_perm = UserPerm.MEMBER
            if user_perm < permission:
                raise ExecutionStop

        return Depend(perm_check)
