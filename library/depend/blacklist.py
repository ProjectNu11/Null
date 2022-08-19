from typing import NoReturn

from graia.ariadne import Ariadne
from graia.ariadne.event.message import MessageEvent, GroupMessage
from graia.ariadne.message.chain import MessageChain
from graia.broadcast import ExecutionStop
from graia.broadcast.builtin.decorators import Depend

from library.util import blacklist
from library.util.blacklist.bot import bot_list


class Blacklist:
    @classmethod
    def check(
        cls,
        on_failure: MessageChain = None,
        allow_anonymous: bool = False,
        on_anonymous: MessageChain | None = MessageChain("本服务不允许匿名用户使用"),
        allow_bot: bool = False,
        on_bot: MessageChain | None = None,
    ) -> Depend:
        """
        Check switch.

        :param on_failure: Message chain to send when switch is off.
        :param allow_anonymous: Allow anonymous user to use this module.
        :param on_anonymous: Message chain to send when anonymous user use this module.
        :param allow_bot: Allow bot to use this module.
        :param on_bot: Message chain to send when bot use this module.
        :return: Depend decorator.
        """

        async def blacklist_check(event: MessageEvent) -> NoReturn:
            field = event.sender.group.id if isinstance(event, GroupMessage) else 0
            target = event.sender.id
            if cls.user_is_anonymous(target) and not allow_anonymous:
                if on_anonymous:
                    await Ariadne.current().send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_anonymous.as_sendable(),
                    )
                raise ExecutionStop

            if cls.user_is_bot(target) and not allow_bot:
                if on_bot:
                    await Ariadne.current().send_message(
                        event.sender.group
                        if isinstance(event, GroupMessage)
                        else event.sender,
                        on_bot.as_sendable(),
                    )
                raise ExecutionStop

            if (
                await cls.group_in_blacklist(field)
                or await cls.user_in_global_blacklist(target)
                or await cls.user_in_field_blacklist(field, target)
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

    @classmethod
    async def manually_check(
        cls,
        field: int,
        target: int,
        allow_anonymous: bool = False,
        allow_bot: bool = False,
    ) -> bool:
        """
        Manually check if user is in blacklist.

        :param field: Field.
        :param target: Target.
        :param allow_anonymous: Allow anonymous user to use this module.
        :param allow_bot: Allow bot to use this module.
        :return: False if the user failed the check.
        """

        if cls.user_is_anonymous(target) and not allow_anonymous:
            return False

        if cls.user_is_bot(target) and not allow_bot:
            return False

        if await cls.group_in_blacklist(field):
            return False

        if await cls.user_in_global_blacklist(
            target
        ) or await cls.user_in_field_blacklist(field, target):
            return False

    @staticmethod
    def user_is_anonymous(target: int) -> bool:
        """
        Check if user is anonymous.

        :param target: Target.
        :return: True if user is anonymous.
        """

        return target == 80000000

    @staticmethod
    def user_is_bot(target: int) -> bool:
        """
        Check if user is bot.

        :param target: Target.
        :return: True if user is bot.
        """

        return bot_list.check(target)

    @staticmethod
    async def group_in_blacklist(field: int) -> bool:
        """
        Check if group is in blacklist.

        :param field: Field.
        :return: True if group is in blacklist.
        """

        return await blacklist.check(field=field, target=-1)

    @staticmethod
    async def user_in_global_blacklist(target: int) -> bool:
        """
        Check if user is in global blacklist.

        :param target: Target.
        :return: True if user is in global blacklist.
        """

        return await blacklist.check(field=-1, target=target)

    @staticmethod
    async def user_in_field_blacklist(field: int, target: int) -> bool:
        """
        Check if user is in field blacklist.

        :param field: Field, 0 for direct message.
        :param target: Target.
        :return: True if user is in field blacklist.
        """

        return await blacklist.check(field=field, target=target)
