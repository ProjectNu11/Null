from datetime import datetime
from typing import NoReturn

from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.broadcast.builtin.decorators import Depend

from library.orm import orm
from library.orm.table import FunctionCallRecord


class FunctionCall:
    @classmethod
    def record(cls, pack: str) -> Depend:
        """
        Record function call.

        :param pack: Package name.
        :return: Depend decorator.
        """

        async def function_call_record(event: MessageEvent) -> NoReturn:
            await cls.add_record(pack, event)

        return Depend(function_call_record)

    @staticmethod
    async def add_record(pack: str, event: MessageEvent) -> NoReturn:
        """
        Add function call record.

        :param pack: Package name.
        :param event: Message event.
        :return: NoReturn.
        """

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
