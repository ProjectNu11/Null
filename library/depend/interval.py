from datetime import timedelta, datetime
from typing import NoReturn

from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageEvent
from graia.ariadne.message.chain import MessageChain
from graia.ariadne.model import Member, Friend
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library.util import interval


class Interval:
    @classmethod
    def check(
        cls,
        module: str,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        on_failure: MessageChain = None,
    ) -> Depend:
        """
        Check interval.

        :param module: Module name.
        :param seconds: Seconds.
        :param minutes: Minutes.
        :param hours: Hours.
        :param on_failure: Message chain to send when interval is not met.
        Use `{interval}` as placeholder for the interval.
        :return:
        """

        async def interval_check(event: MessageEvent) -> NoReturn:
            await cls.check_and_raise(
                module, event.sender, seconds, minutes, hours, on_failure
            )

        return Depend(interval_check)

    @staticmethod
    async def check_and_raise(
        module: str,
        supplicant: int | Member | Friend,
        seconds: int = 0,
        minutes: int = 0,
        hours: int = 0,
        on_failure: MessageChain = None,
    ):
        if isinstance(
            __interval := interval.check_and_update(
                module,
                supplicant,
                timedelta(hours=hours, minutes=minutes, seconds=seconds),
            ),
            bool,
        ):
            return
        s = (__interval - datetime.now()).seconds
        m, s = divmod(s, 60)
        h, m = divmod(m, 60)
        interval_repr = f"{s:02d} 秒"
        if m:
            interval_repr = f"{m:02d} 分 {interval_repr}"
        if h:
            interval_repr = f"{h:02d} 时 {interval_repr}"
        if on_failure and isinstance(supplicant, (Member, Friend)):
            await Ariadne.current().send_message(
                supplicant.group if isinstance(supplicant, Member) else supplicant,
                on_failure.replace("{interval}", interval_repr).as_sendable(),
            )
        raise ExecutionStop
