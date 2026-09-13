import sqlalchemy.ext.asyncio as AsyncIO
import sqlalchemy.orm         as ObjectRelationalMapper
import typing                 as Typing
import Server.Config          as Config

ASYNC_ENGINE = AsyncIO.create_async_engine(Config.GLOBAL_SETTINGS.DATABASE_URL, echo = False, future = True)
AsyncSessionLocal = AsyncIO.async_sessionmaker(bind = ASYNC_ENGINE, class_ = AsyncIO.AsyncSession, expire_on_commit = False, autoflush = False)

class Base(ObjectRelationalMapper.DeclarativeBase):
    pass

async def GetDatabaseSession() -> Typing.AsyncGenerator[AsyncIO.AsyncSession, None]:
    async with AsyncSessionLocal() as DatabaseSession:
        try:
            yield DatabaseSession
        finally:
            await DatabaseSession.close()
