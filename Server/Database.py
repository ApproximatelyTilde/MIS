import sqlalchemy.ext.asyncio as AsyncIO
import sqlalchemy.orm         as ObjectRelationalMapper
import typing                 as Typing
import Server.Config          as Config

ASYNC_ENGINE = AsyncIO.create_async_engine(Config.GLOBAL_SETTINGS.DATABASE_URL, echo = False, future = True)
ASYNC_SESSION_FACTORY = AsyncIO.async_sessionmaker(bind = ASYNC_ENGINE, class_ = AsyncIO.AsyncSession, expire_on_commit = False, autoflush = False)
AsyncSessionLocal = ASYNC_SESSION_FACTORY

class Base(ObjectRelationalMapper.DeclarativeBase):
    pass

import Server.Services.DebugService as DebugService

async def GetDatabaseSession() -> Typing.AsyncGenerator[AsyncIO.AsyncSession, None]:
    async with ASYNC_SESSION_FACTORY() as DatabaseSession:
        DebugService.LogDebugMessage(f"Database Session Acquired [{hex(id(DatabaseSession))}]")
        try:
            yield DatabaseSession
        finally:
            DebugService.LogDebugMessage(f"Database Session Closed [{hex(id(DatabaseSession))}]")
            await DatabaseSession.close()
