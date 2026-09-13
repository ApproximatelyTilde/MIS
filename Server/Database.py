import sqlalchemy.ext.asyncio as AsyncIO
import sqlalchemy.orm         as ORM
import typing                 as Typing
import Server.Config          as Config

class Base(ORM.DeclarativeBase):
    pass

import Server.Services.DebugService as DebugService

ASYNC_ENGINE          = AsyncIO.create_async_engine(Config.GLOBAL_SETTINGS.DATABASE_URL, echo = False, future = True)
ASYNC_SESSION_FACTORY = AsyncIO.async_sessionmaker(bind = ASYNC_ENGINE, class_ = AsyncIO.AsyncSession, expire_on_commit = False, autoflush = False)

async def GetDatabaseSession() -> Typing.AsyncGenerator[AsyncIO.AsyncSession, None]:
    async with ASYNC_SESSION_FACTORY() as DatabaseSession:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Database Session Acquired: SessionID={hex(id(DatabaseSession))}")
        try:
            yield DatabaseSession

        finally:
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Database Session Closed: SessionID={hex(id(DatabaseSession))}")
            await DatabaseSession.close()
