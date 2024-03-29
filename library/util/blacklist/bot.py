import pickle
from abc import ABC, abstractmethod
from pathlib import Path

from graia.ariadne.model import Member, Friend
from loguru import logger
from pydantic import BaseModel

from library import config


class BotKind(BaseModel):
    name: str
    """ The name of the bot kind. """

    repo: str = ""
    """ The repository of the bot kind. """

    description: str = ""
    """ The description of the bot kind. """


class Bot(BaseModel):
    """
    Bot class, used to store bot information
    """

    id: int
    """ Bot ID """

    name: str
    """ Bot name """

    num: int = 1
    """
    Bot number, used to distinguish different bots
    with the same name
    """

    maintainer: list[int | str | dict[str, int]] = []
    """
    Bot maintainer, can be a list of user ID,
    user name, or a dict of user name and user ID
    """

    kind: BotKind = BotKind(name="Unknown")
    """
    Bot kind, used to distinguish the kind of bot
    """

    def __hash__(self):
        return self.id


class BotSource(ABC):
    """
    The source defines the way to get the bot list
    """

    URL: str
    """ Bot source URL """

    NAME: str
    """ Bot source name """

    @staticmethod
    @abstractmethod
    async def fetch() -> set[Bot]:
        """
        Fetch the bot list

        :return: a set of Bot objects
        """

        pass

    def __hash__(self):
        return hash(self.NAME + self.URL)


class BotList:
    __instance: "BotList" = None
    __pickle_path: Path = Path(Path(config.path.data), "library", "bot.pickle")
    __cache: set[Bot]

    __registered_source: set[BotSource]

    def __init__(self):
        self.__cache = set()
        self.__registered_source = set()
        if not self.__pickle_path.exists():
            logger.success(f"Creating bot_list pickle file at {self.__pickle_path}")
            self.__save_pickle()
        self.__load_pickle()

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __load_pickle(self):
        try:
            with self.__pickle_path.open("rb") as f:
                self.__cache = pickle.load(f)
        except EOFError:
            logger.error(
                f"Failed to load bot_list from pickle file at {self.__pickle_path}, resetting..."
            )
            self.__pickle_path.unlink(missing_ok=True)
            self.__init__()

    def __save_pickle(self):
        with self.__pickle_path.open("wb") as f:
            pickle.dump(self.__cache, f)

    def register(self, source: BotSource):
        """
        Register a source to fetch the bot list

        :param source: BotSource object
        :return: None
        """

        self.__registered_source.add(source)

    async def update(self):
        """
        Update the bot list

        :return: None
        """

        for source in self.__registered_source:
            if isinstance(result := await source.fetch(), set):
                self.__cache = self.__cache.union(
                    {bot for bot in result if isinstance(bot, Bot)}
                )
        self.__save_pickle()

    def add(self, bot: Bot):
        """
        Add a bot to the bot list manually

        :param bot: Bot object
        :return: None
        """

        self.__cache.add(bot)
        self.__save_pickle()

    def remove(self, bot_id: int):
        """
        Remove a bot from the bot list

        :param bot_id: Bot ID
        :return: None
        """

        if bot := list(filter(lambda _bot: _bot.id == bot_id, self.__cache)):
            self.__cache.remove(bot[0])

    def check(self, target: int) -> bool:
        """
        Check if the target is in the bot list

        :param target: Target ID
        :return: True if the target is in the bot list
        """

        return bool(list(filter(lambda bot: bot.id == target, self.__cache)))

    def bulk_check(self, *targets: int | Member | Friend) -> list[Bot]:
        """
        Find if targets contains bots

        :param targets: Target ID, Member object, Friend object
        :return: List of Bots found
        """

        targets = [int(target) for target in targets]
        return list(filter(lambda bot: bot.id in targets, self.__cache))

    def get_all(self) -> set[Bot]:
        """
        Get all the bots in the bot list

        :return: Set of Bots
        """

        return self.__cache


bot_list = BotList()
