import pickle
from datetime import datetime, timedelta
from pathlib import Path

from graia.ariadne.model import Member, Friend
from graia.scheduler import GraiaScheduler, timers
from loguru import logger

from library import config
from library.context import scheduler


class Interval:
    __instance: "Interval" = None
    __pickle_path: Path = Path(Path(config.path.data), "library", "interval.pickle")
    __cache: dict[str, dict[int, datetime]] = {}

    def __init__(self):
        if not self.__pickle_path.exists():
            logger.success(f"Creating interval pickle file at {self.__pickle_path}")
            self.__save_pickle()
        self.__load_pickle()

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __repr__(self):
        return str(self.__cache)

    def __str__(self):
        return str(self.__cache)

    def __load_pickle(self):
        try:
            with self.__pickle_path.open("rb") as f:
                self.__cache = pickle.load(f)
        except EOFError:
            logger.error(
                f"Failed to load interval from pickle file at {self.__pickle_path}, resetting..."
            )
            self.__pickle_path.unlink(missing_ok=True)
            self.__init__()

    def __save_pickle(self):
        with self.__pickle_path.open("wb") as f:
            pickle.dump(self.__cache, f)

    def __del__(self):
        self.__save_pickle()

    @staticmethod
    def __type_convert(supplicant: int | Member | Friend | None) -> int | None:
        if supplicant is None:
            return supplicant
        if isinstance(supplicant, (Member, Friend)):
            return supplicant.id
        return supplicant

    def update(
        self,
        module: str,
        supplicant: int | Member | Friend,
        _interval: timedelta | None,
    ):
        """
        Update the interval of a user.

        :param module: Module name.
        :param supplicant: User ID or Member or Friend object.
        :param _interval: Interval to update.
        :return: None
        """

        supplicant = self.__type_convert(supplicant)
        if _interval is None:
            if module in self.__cache and supplicant in self.__cache[module]:
                del self.__cache[module][supplicant]
            return
        if module not in self.__cache:
            self.__cache[module] = {}
        self.__cache[module][supplicant] = datetime.now() + _interval
        self.__save_pickle()

    def get(self, module: str, supplicant: int | Member | Friend) -> datetime | None:
        """
        Get the interval of a user.

        :param module: Module name.
        :param supplicant: User ID or Member or Friend object.
        :return: Interval or None
        """

        if module not in self.__cache:
            return None
        supplicant = self.__type_convert(supplicant)
        if supplicant not in self.__cache[module]:
            return None
        return self.__cache[module][supplicant]

    def check(self, module: str, supplicant: int | Member | Friend) -> bool:
        """
        Check if a user is in the interval.

        :param module: Module name.
        :param supplicant: User ID or Member or Friend object.
        :return: True if not in the interval, False otherwise.
        """

        if _interval := self.get(module, supplicant):
            return _interval < datetime.now()
        return True

    def check_and_update(
        self, module: str, supplicant: int | Member | Friend, _interval: timedelta
    ) -> bool | datetime:
        """
        Check if a user is in the interval and update it.

        :param module: Module name.
        :param supplicant: User ID or Member or Friend object.
        :param _interval: Interval to update.
        :return: True if not in the interval, datetime of the interval otherwise.
        """

        if self.check(module, supplicant):
            self.update(module, supplicant, _interval)
            return True
        return self.get(module, supplicant)

    def flush(
        self,
        module: str | None = None,
        supplicant: int | Member | Friend | None = None,
        *,
        skip_saving: bool = False,
    ):
        supplicant = self.__type_convert(supplicant)
        if not module:
            self.__cache = {}
        elif not supplicant:
            del self.__cache[module]
        else:
            del self.__cache[module][supplicant]
        if skip_saving:
            return
        self.__save_pickle()

    def cleanup(self):
        cleaned = False
        for module, users in self.__cache.copy().items():
            for user, __interval in users.items():
                if __interval < datetime.now():
                    cleaned = True
                    self.flush(module, user, skip_saving=True)
        if cleaned:
            self.__save_pickle()


interval = Interval()
scheduler: GraiaScheduler = scheduler.get()


@scheduler.schedule(timers.crontabify("* * * * *"))
async def __auto_cleanup():
    interval.cleanup()
