import datetime               as DateTime
import typing                 as Typing
import sqlalchemy             as SQLAlchemy
import sqlalchemy.ext.asyncio as AsyncIO
import Server.Models.User     as User

class TestUserModels:
    def TestUserRoleEnumValues(self) -> None:
        assert (User.UserRole.Visitor.value == "Visitor")
        assert (User.UserRole.NormalUser.value == "NormalUser")
        assert (User.UserRole.Checker.value == "Checker")
        assert (User.UserRole.GameMaster.value == "GameMaster")
        assert (User.UserRole.Administrator.value == "Administrator")

    async def TestUserCreationAndDefaults(self, DatabaseSession: AsyncIO.AsyncSession) -> None:
        CreatedUser: User.User = User.User(DiscordID = "555555555555555555", Username = "UniqueUser", DisplayName = "Display Unique")
        DatabaseSession.add(CreatedUser)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(CreatedUser)

        assert (CreatedUser.ID is not None)
        assert (len(CreatedUser.ID) == 36)
        assert (CreatedUser.DiscordID == "555555555555555555")
        assert (CreatedUser.Username == "UniqueUser")
        assert (CreatedUser.Role == User.UserRole.NormalUser)
        assert (CreatedUser.Roles == [])
        assert (CreatedUser.StorageUsedBytes == 0)
        assert (isinstance(CreatedUser.CreatedAt, DateTime.datetime))
        assert (isinstance(CreatedUser.UpdatedAt, DateTime.datetime))

    async def TestUserQueryByDiscordID(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        QueryStatement: SQLAlchemy.Select[Typing.Tuple[User.User]] = SQLAlchemy.select(User.User).where(User.User.DiscordID == RegularUserRecord.DiscordID)
        QueryResult   : SQLAlchemy.Result[Typing.Tuple[User.User]] = await DatabaseSession.execute(QueryStatement)
        FoundUser     : Typing.Optional[User.User]                 = QueryResult.scalars().first()

        assert (FoundUser is not None)
        assert (FoundUser.ID == RegularUserRecord.ID)
        assert (FoundUser.Username == RegularUserRecord.Username)
