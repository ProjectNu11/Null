import pickle
from datetime import datetime
from pathlib import Path

from graia.ariadne.model import Group, Member, Friend
from loguru import logger
from pydantic import BaseModel
from sqlalchemy import select

from library import config
from library.orm import orm
from library.orm.table import BlacklistTable


class BlacklistUser(BaseModel):
    id: int
    time: datetime
    reason: str
    supplicant: int

    def __hash__(self):
        return self.id

    def __repr__(self):
        return (
            f"BlacklistUser:\n"
            f"\tid: {self.id}\n"
            f"\ttime: {self.time}\n"
            f"\treason: {self.reason}\n"
            f"\tsupplicant: {self.supplicant}\n"
        )


class Blacklist:
    __instance: "Blacklist" = None
    __pickle_path: Path = Path(Path(config.path.data), "library", "blacklist.pickle")
    __cache: dict[int, set[BlacklistUser]] = {}

    def __init__(self):
        if not self.__pickle_path.exists():
            logger.success(f"Creating blacklist pickle file at {self.__pickle_path}")
            self.__save_pickle()
        self.__load_pickle()

    def __new__(cls, *args, **kwargs):
        if not cls.__instance:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __repr__(self):
        repr_body = ""
        for field in sorted(self.__cache.keys()):
            repr_body += f"Field {field}\n"
            for user in self.__cache[field]:
                repr_body += f"\t{repr(user)}\n"
        return f"Blacklist:\n{repr_body}"

    def __load_pickle(self):
        try:
            with self.__pickle_path.open("rb") as f:
                self.__cache = pickle.load(f)
        except EOFError:
            logger.error(
                f"Failed to load blacklist from pickle file at {self.__pickle_path}, resetting..."
            )
            self.__pickle_path.unlink(missing_ok=True)
            self.__init__()

    def __save_pickle(self):
        with self.__pickle_path.open("wb") as f:
            pickle.dump(self.__cache, f)

    async def check(
        self, *, field: int | Group | None, target: int | Member | Friend | None
    ) -> bool:
        """
        Check if the target is in the blacklist

        :param field: Field ID, -1 for global, 0 for direct message, >0 for group
        :param target: Target ID, 0 for group, >0 for user
        :return: True if the target is in the blacklist
        """

        if not isinstance(field, int) or not isinstance(target, int):
            field, target = self.__convert_type(field, target)
        if field < -1 or target < 0:
            raise ValueError("Invalid field or target")
        if (field_data := self.__cache.get(field, None)) is not None:
            return bool(list(filter(lambda x: x.id == target, field_data)))
        await self.__cache_field(field)
        return target in self.__cache[field]

    async def add(
        self,
        *,
        field: int | Group | None,
        target: int | Member | Friend | None,
        reason: str,
        supplicant: int | Member | Friend,
    ):
        """
        Add the target to the blacklist

        :param field: Field ID, -1 for global, 0 for direct message, >0 for group
        :param target: Target ID, 0 for group, >0 for user
        :param reason: Reason for blacklisting
        :param supplicant: Supplicant ID
        :return: True if the target is added to the blacklist
        """

        field, target = self.__convert_type(field, target)
        supplicant = (
            supplicant.id if isinstance(supplicant, (Member, Friend)) else supplicant
        )
        await orm.insert_or_update(
            BlacklistTable,
            [BlacklistTable.field == field, BlacklistTable.target == target],
            {
                "field": field,
                "target": target,
                "time": datetime.now(),
                "reason": reason,
                "supplicant": supplicant,
            },
        )
        await self.__cache_field(field)
        logger.success(f"Added target {target} to blacklist for field {field}")
        self.__save_pickle()

    @staticmethod
    def __convert_type(
        field: int | Group | None, target: int | Member | Friend | None
    ) -> tuple[int, int]:
        if field is None and target is None:
            raise ValueError("field and target cannot be both None")
        if isinstance(field, Group):
            field = field.id
        elif field is None:
            field = -1
        if isinstance(target, (Member, Friend)):
            target = target.id
        elif target is None:
            target = 0
        if field == -1 and target == 0:
            raise ValueError("field cannot be -1 while target is 0")
        return field, target

    async def __cache_field(self, field: int):
        self.__cache[field] = set()
        if group_data := await orm.all(
            select(
                BlacklistTable.target,
                BlacklistTable.time,
                BlacklistTable.reason,
                BlacklistTable.supplicant,
            ).where(BlacklistTable.field == field)
        ):
            for target_id, time, reason, supplicant in group_data:
                self.__cache[field].add(
                    BlacklistUser(
                        id=target_id, time=time, reason=reason, supplicant=supplicant
                    )
                )
        logger.success(f"Cached blacklist for field {field}")
        self.__save_pickle()


blacklist = Blacklist()
