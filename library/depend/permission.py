from typing import NoReturn

from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library import config
from library.model import UserPerm


class Permission:
    @classmethod
    def require(cls, permission: UserPerm, on_failure: MessageChain = None) -> Depend:
        """
        Require user permission.

        :param permission: User permission.
        :param on_failure: Message chain to send when user doesn't have permission.
        :return: Depend decorator.
        """

        async def perm_check(event: MessageEvent) -> NoReturn:
            if not cls.permission_check(permission, event):
                if on_failure:
                    await Ariadne.current().send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_failure.as_sendable(),
                    )
                raise ExecutionStop

        return Depend(perm_check)

    @staticmethod
    def permission_check(permission: UserPerm, event: MessageEvent):
        """
        Check user permission.

        :param permission: User permission.
        :param event: Message event.
        :return: True if user has permission, False otherwise.
        """

        if event.sender.id in config.owners:
            user_perm = UserPerm.BOT_OWNER
        elif isinstance(event, GroupMessage):
            user_perm = getattr(UserPerm, str(event.sender.permission))
        else:
            user_perm = UserPerm.MEMBER
        if user_perm < permission:
            return False
        return True
