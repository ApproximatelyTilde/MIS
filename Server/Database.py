import sqlalchemy.ext.asyncio as AsyncIO
import sqlalchemy.orm         as ORM
import typing                 as Typing
import Server.Config          as Config

class Base(ORM.DeclarativeBase):
    pass

ASYNC_ENGINE          = AsyncIO.create_async_engine(Config.GLOBAL_SETTINGS.DATABASE_URL, echo = False, future = True)
ASYNC_SESSION_FACTORY = AsyncIO.async_sessionmaker(bind = ASYNC_ENGINE, class_ = AsyncIO.AsyncSession, expire_on_commit = False, autoflush = False)

async def GetDatabaseSession() -> Typing.AsyncGenerator[AsyncIO.AsyncSession, None]:
    async with ASYNC_SESSION_FACTORY() as DatabaseSession:
        try:
            yield DatabaseSession

        finally:
            await DatabaseSession.close()
