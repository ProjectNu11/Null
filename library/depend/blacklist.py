from typing import NoReturn

from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library.util import blacklist


class Blacklist:
    @staticmethod
    def check(
        on_failure: MessageChain = None,
    ) -> Depend:
        """
        Check switch.

        :param on_failure: Message chain to send when switch is off.
        :return: Depend decorator.
        """

        async def blacklist_check(event: MessageEvent) -> NoReturn:
            field = event.sender.group.id if isinstance(event, GroupMessage) else 0
            target = event.sender.id
            if any(
                [
                    await blacklist.check(field=-1, target=target),
                    await blacklist.check(field=field, target=0),
                    await blacklist.check(field=field, target=target),
                ]
            ):
                if on_failure:
                    await Ariadne.current().send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_failure.as_sendable(),
                    )
                raise ExecutionStop

        return Depend(blacklist_check)
