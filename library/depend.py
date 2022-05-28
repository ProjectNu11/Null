from datetime import datetime
from typing import NoReturn

from graia.ariadne import get_running, Ariadne
from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library.config import config, get_switch
from library.model import UserPerm
from library.orm import orm, FunctionCallRecord


class Permission:
    @classmethod
    def require(cls, permission: UserPerm, on_failure: MessageChain = None) -> Depend:
        async def perm_check(event: MessageEvent) -> NoReturn:
            if not cls.permission_check(permission, event):
                if on_failure:
                    await get_running(Ariadne).sendMessage(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_failure.asSendable(),
                    )
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
    def check(
        pack: str, override_level: UserPerm = None, on_failure: MessageChain = None
    ) -> Depend:
        async def switch_check(event: MessageEvent) -> NoReturn:
            if override_level and Permission.permission_check(override_level, event):
                return
            try:
                value = get_switch(
                    pack, event.sender.group if isinstance(event, GroupMessage) else 0
                )
                if isinstance(value, bool):
                    if not value:
                        raise ExecutionStop
                    return
                if not config.func.default:
                    raise ExecutionStop
            except ExecutionStop:
                if on_failure:
                    await get_running(Ariadne).sendMessage(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_failure.asSendable(),
                    )
                raise

        return Depend(switch_check)


class FunctionCall:
    @classmethod
    def record(cls, pack: str) -> Depend:
        async def function_call_record(event: MessageEvent) -> NoReturn:
            await cls.add_record(pack, event)

        return Depend(function_call_record)

    @staticmethod
    async def add_record(pack: str, event: MessageEvent) -> NoReturn:
        await orm.add(
            FunctionCallRecord,
            {
                "time": datetime.now(),
                "field": event.sender.group.id
                if isinstance(event, GroupMessage)
                else 0,
                "supplicant": event.sender.id,
                "function": pack,
            },
        )
