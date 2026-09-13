import asyncio                   as AsyncIO
import sys                       as System
import sqlalchemy                as SQLAlchemy
import Server.Config             as Config
import Server.Database           as Database
import Server.Models.User        as User
import Server.Models.Character   as Character
import Server.Models.Story       as Story
import Server.Models.Economy     as Economy
import Server.Models.StorageFile as StorageFile

async def ResetDevelopmentDatabase() -> None:
    if Config.GLOBAL_SETTINGS.ENVIRONMENT != "development":
        System.stdout.write("FAILED.")
        System.exit(1)

    async with Database.ASYNC_ENGINE.begin() as DatabaseConnection:
        await DatabaseConnection.run_sync(Database.Base.metadata.drop_all)
        await DatabaseConnection.execute(SQLAlchemy.text("DROP TYPE IF EXISTS \"UserRole\" CASCADE;"))
        await DatabaseConnection.execute(SQLAlchemy.text("DROP TYPE IF EXISTS \"GameSystemType\" CASCADE;"))
        await DatabaseConnection.execute(SQLAlchemy.text("DROP TYPE IF EXISTS \"StoryMembershipStatus\" CASCADE;"))
        await DatabaseConnection.execute(SQLAlchemy.text("DROP TYPE IF EXISTS userrole CASCADE;"))
        await DatabaseConnection.execute(SQLAlchemy.text("DROP TYPE IF EXISTS gamesystemtype CASCADE;"))
        await DatabaseConnection.execute(SQLAlchemy.text("DROP TYPE IF EXISTS storymembershipstatus CASCADE;"))
        await DatabaseConnection.run_sync(Database.Base.metadata.create_all)

    System.stdout.write("SUCCESS.\n")
    await Database.ASYNC_ENGINE.dispose()

def Main() -> None:
    AsyncIO.run(ResetDevelopmentDatabase())

if __name__ == "__main__":
    Main()
