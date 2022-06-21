from typing import NoReturn

from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend
from loguru import logger

from library import config
from library.depend.permission import Permission
from library.model import UserPerm
from library.util.switch import switch


class Switch:
    @staticmethod
    def check(
        pack: str,
        override_level: UserPerm = None,
        on_failure: MessageChain = None,
        log: bool = True,
    ) -> Depend:
        """
        Check switch.

        :param pack: Package name.
        :param override_level: Override user permission.
        :param on_failure: Message chain to send when switch is off.
        :param log: Whether to log the call.
        :return: Depend decorator.
        """

        async def switch_check(event: MessageEvent) -> NoReturn:
            if override_level and Permission.permission_check(override_level, event):
                if log:
                    logger.success(f"[Switch] {pack}: Overridden by {override_level}")
                return
            try:
                value = switch.get(
                    pack=pack,
                    group=event.sender.group
                    if isinstance(event, GroupMessage)
                    else None,
                )
                if isinstance(value, bool):
                    if log:
                        logger.success(f"[Switch] {pack}: {value}")
                    if not value:
                        raise ExecutionStop
                    return
                if log:
                    logger.success(
                        f"[Switch] {pack}: Fallback to {config.func.default}"
                    )
                if not config.func.default:
                    raise ExecutionStop
            except ExecutionStop:
                if on_failure:
                    await Ariadne.current().send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_failure.as_sendable(),
                    )
                raise

        return Depend(switch_check)
