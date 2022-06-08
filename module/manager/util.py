from sqlalchemy.exc import InternalError, ProgrammingError

from library.orm import orm


async def db_init():
    try:
        await orm.init_check()
    except (AttributeError, InternalError, ProgrammingError):
        await orm.create_all()
