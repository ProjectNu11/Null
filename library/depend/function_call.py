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
            await cls.add_record(
                pack=pack,
                field=event.sender.group.id if isinstance(event, GroupMessage) else 0,
                supplicant=event.sender.id,
            )

        return Depend(function_call_record)

    @staticmethod
    async def add_record(pack: str, field: int, supplicant: int) -> NoReturn:
        """
        Add function call record.

        :param pack: Package name.
        :param field: Field.
        :param supplicant: Supplicant.
        :return: NoReturn.
        """

        await orm.add(
            FunctionCallRecord,
            {
                "time": datetime.now(),
                "field": field,
                "supplicant": supplicant,
                "function": pack,
            },
        )
