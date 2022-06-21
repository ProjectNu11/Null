from asyncio import Lock
from typing import NoReturn

from sqlalchemy import (
    select,
    update,
    insert,
    delete,
    inspect,
    Column,
    DateTime,
    Integer,
    BIGINT,
    String,
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

from library.config import config
from library.model import MySQLConfig

if isinstance(config.db.config, MySQLConfig):
    db_mutex = None
    if config.db.config.disable_pooling:
        adapter = {"poolclass": NullPool}
    else:
        adapter = config.db.config.dict(exclude={"disable_pooling"})
else:
    db_mutex = Lock()
    adapter = {}


class AsyncEngine:
    def __init__(self, db_link):
        self.engine = create_async_engine(db_link, **adapter, echo=False)

    async def execute(self, sql, **kwargs):
        """
        Execute SQL.

        :param sql: SQL string.
        :param kwargs: SQL parameters.
        :return: SQL result.
        """

        async with AsyncSession(self.engine) as session:
            try:
                if db_mutex:
                    await db_mutex.acquire()
                result = await session.execute(sql, **kwargs)
                await session.commit()
                return result
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                if db_mutex:
                    db_mutex.release()

    async def fetchall(self, sql):
        """
        Fetch all SQL result.

        :param sql: SQL string.
        :return: SQL result.
        """

        return (await self.execute(sql)).fetchall()

    async def fetchone(self, sql):
        """
        Fetch one SQL result.

        :param sql: SQL string.
        :return: SQL result.
        """

        result = await self.execute(sql)
        return one if (one := result.fetchone()) else None

    async def fetchone_dt(self, sql, n=999999):
        """
        Fetch one SQL result with datetime.

        :param sql: SQL string.
        :param n: amount of rows to fetch.
        :return: SQL result.
        """

        result = await self.execute(sql)
        columns = result.keys()
        length = len(columns)
        for _ in range(n):
            if one := result.fetchone():
                yield {columns[i]: one[i] for i in range(length)}


class AsyncORM(AsyncEngine):
    """Object-Relational Mapping"""

    def __init__(self, conn):
        super().__init__(conn)
        self.session = AsyncSession(bind=self.engine)
        self.Base = declarative_base(self.engine)
        self.async_session = sessionmaker(
            self.engine, expire_on_commit=False, class_=AsyncSession
        )

    async def create_all(self):
        """Create all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.create_all)

    async def drop_all(self):
        """Drop all tables"""
        async with self.engine.begin() as conn:
            await conn.run_sync(self.Base.metadata.drop_all)

    async def add(self, table, dt):
        """
        Add data to table.

        :param table: 表名
        :param dt: 数据
        """
        async with self.async_session() as session:
            async with session.begin():
                session.add(table(**dt), _warn=False)
            await session.commit()

    async def update(self, table, condition, dt):
        """
        Update data.

        :param table: 表名
        :param condition: 条件
        :param dt: 数据
        :return: SQL result
        """
        await self.execute(update(table).where(*condition).values(**dt))

    async def insert_or_update(self, table, condition, dt):
        """
        Insert or update.

        :param table: 表名
        :param condition: 条件
        :param dt: 数据
        :return: SQL result
        """
        if (await self.execute(select(table).where(*condition))).all():
            return await self.execute(update(table).where(*condition).values(**dt))
        else:
            return await self.execute(insert(table).values(**dt))

    async def insert_or_ignore(self, table, condition, dt):
        """
        Insert or ignore.

        :param table: 表名
        :param condition: 条件
        :param dt: 数据
        :return: SQL result
        """
        if not (await self.execute(select(table).where(*condition))).all():
            return await self.execute(insert(table).values(**dt))

    async def delete(self, table, condition):
        """
        Delete data.

        :param table: 表名
        :param condition: 条件
        :return: SQL result
        """
        return await self.execute(delete(table).where(*condition))

    async def init_check(self) -> NoReturn:
        """
        Initial check.

        :return: None
        """
        for table in self.Base.__subclasses__():
            if not await self.table_exists(table.__tablename__):
                table.__table__.create(self.engine)
        return None

    @staticmethod
    def use_inspector(conn):
        """
        Get table names.

        :param conn: 数据库连接
        :return: 表名
        """
        inspector = inspect(conn)
        return inspector.get_table_names()

    async def table_exists(self, table_name: str) -> bool:
        """
        Check if table exists.

        :param table_name: 表名
        :return: 是否存在
        """
        async with self.engine.connect() as conn:
            tables = await conn.run_sync(self.use_inspector)
        return table_name in tables


orm = AsyncORM(config.db.link)
Base = orm.Base


class FunctionCallRecord(Base):
    """Function call record"""

    __tablename__ = "function_call_record"

    id = Column(Integer, primary_key=True)
    time = Column(DateTime, nullable=False)
    field = Column(BIGINT, nullable=False)
    supplicant = Column(BIGINT, nullable=False)
    function = Column(String(length=4000), nullable=False)
