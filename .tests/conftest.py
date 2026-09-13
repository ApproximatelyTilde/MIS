import collections.abc        as CollectionsABC
import os                     as OperatingSystem
import typing                 as Typing
import httpx2                 as HTTPClient
import pytest                 as Pytest
import sqlalchemy.ext.asyncio as AsyncIO
import sqlalchemy.pool        as Pool

TEST_ENVIRONMENT_DEFAULTS: dict[str, str] = {
    "ENVIRONMENT"                : "testing",
    "HOST"                       : "127.0.0.1",
    "PORT"                       : "8000",
    "SECRET_KEY"                 : "TestSecretKeyForAutomatedTestingSuiteMinimum32Bytes",
    "ALGORITHM"                  : "HS256",
    "ACCESS_TOKEN_EXPIRE_MINUTES": "60",
    "DATABASE_URL"               : "sqlite+aiosqlite:///:memory:",
    "DISCORD_CLIENT_ID"          : "000000000000000000",
    "DISCORD_CLIENT_SECRET"      : "TestDiscordClientSecretValue",
    "DISCORD_BOT_TOKEN"          : "TestDiscordBotTokenValue",
    "DISCORD_REDIRECT_URI"       : "http://localhost:8000/API/Auth/Callback",
    "DISCORD_GUILD_ID"           : "000000000000000001",
    "DISCORD_INVITE_URL"         : "https://discord.gg/testinvite",
    "OCI_S3_ENDPOINT_URL"        : "https://example.invalid",
    "OCI_S3_ACCESS_KEY_ID"       : "TestStorageAccessKeyID",
    "OCI_S3_SECRET_ACCESS_KEY"   : "TestStorageSecretAccessKey",
    "OCI_S3_BUCKET_NAME"         : "TestStorageBucket",
    "OCI_S3_REGION"              : "us-ashburn-1",
    "USER_STORAGE_QUOTA_BYTES"   : "104857600",
    "DICECLOUD_API_KEY"          : "TestDicecloudAPIKey",
    "DICECLOUD_USERNAME"         : "TestDicecloudUsername",
    "DICECLOUD_PASSWORD"         : "TestDicecloudPassword"
}

for EnvironmentKey, EnvironmentValue in TEST_ENVIRONMENT_DEFAULTS.items():
    OperatingSystem.environ[EnvironmentKey] = EnvironmentValue

import Main                   as MainApplication
import Server.Auth.JWTManager as JWTManager
import Server.Database        as Database
import Server.Models.User     as User

TEST_DATABASE_URL    : str                                              = "sqlite+aiosqlite:///:memory:"
TEST_ENGINE          : AsyncIO.AsyncEngine                              = AsyncIO.create_async_engine(TEST_DATABASE_URL, connect_args = {"check_same_thread": False}, poolclass = Pool.StaticPool)
TEST_SESSION_FACTORY : AsyncIO.async_sessionmaker[AsyncIO.AsyncSession] = AsyncIO.async_sessionmaker(bind = TEST_ENGINE, class_ = AsyncIO.AsyncSession, expire_on_commit = False, autoflush = False)

@Pytest.fixture(autouse = True)
async def InitializeDatabase() -> CollectionsABC.AsyncGenerator[None, None]:
    async with TEST_ENGINE.begin() as DatabaseConnection:
        await DatabaseConnection.run_sync(Database.Base.metadata.drop_all)
        await DatabaseConnection.run_sync(Database.Base.metadata.create_all)

    yield
    async with TEST_ENGINE.begin() as DatabaseConnection:
        await DatabaseConnection.run_sync(Database.Base.metadata.drop_all)

@Pytest.fixture
async def DatabaseSession() -> CollectionsABC.AsyncGenerator[AsyncIO.AsyncSession, None]:
    async with TEST_SESSION_FACTORY() as SessionInstance:
        try:
            yield SessionInstance

        finally:
            await SessionInstance.rollback()
            await SessionInstance.close()

@Pytest.fixture
async def AsyncTestClient(DatabaseSession: AsyncIO.AsyncSession) -> CollectionsABC.AsyncGenerator[HTTPClient.AsyncClient, None]:
    async def OverrideGetDatabaseSession() -> CollectionsABC.AsyncGenerator[AsyncIO.AsyncSession, None]:
        yield DatabaseSession

    MainApplication.APPLICATION_SERVICE.dependency_overrides[Database.GetDatabaseSession] = OverrideGetDatabaseSession
    TransportInstance: HTTPClient.ASGITransport = HTTPClient.ASGITransport(app = MainApplication.APPLICATION_SERVICE)
    async with HTTPClient.AsyncClient(transport = TransportInstance, base_url = "http://testserver") as ClientInstance:
        yield ClientInstance

    MainApplication.APPLICATION_SERVICE.dependency_overrides.clear()

@Pytest.fixture
async def RegularUserRecord(DatabaseSession: AsyncIO.AsyncSession) -> User.User:
    UserRecord: User.User = User.User(DiscordID = "111111111111111111", Username = "RegularUser", DisplayName = "Regular User", Role = User.UserRole.NormalUser, Roles = ["NormalUser"])
    DatabaseSession.add(UserRecord)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(UserRecord)
    return UserRecord

@Pytest.fixture
async def GameMasterUserRecord(DatabaseSession: AsyncIO.AsyncSession) -> User.User:
    UserRecord: User.User = User.User(DiscordID = "222222222222222222", Username = "GameMasterUser", DisplayName = "Game Master", Role = User.UserRole.GameMaster, Roles = ["GameMaster", "Story Manager (DND5E)"])
    DatabaseSession.add(UserRecord)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(UserRecord)
    return UserRecord

@Pytest.fixture
async def AdministratorUserRecord(DatabaseSession: AsyncIO.AsyncSession) -> User.User:
    UserRecord: User.User = User.User(DiscordID = "333333333333333333", Username = "AdministratorUser", DisplayName = "Administrator User", Role = User.UserRole.Administrator, Roles = ["Administrator"])
    DatabaseSession.add(UserRecord)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(UserRecord)
    return UserRecord

@Pytest.fixture
def RegularUserToken(RegularUserRecord: User.User) -> str:
    TokenString: str = JWTManager.CreateAccessToken(PayloadData = {"sub": RegularUserRecord.ID, "username": RegularUserRecord.Username, "role": RegularUserRecord.Role.value, "in_guild": True})
    return TokenString

@Pytest.fixture
def GameMasterToken(GameMasterUserRecord: User.User) -> str:
    TokenString: str = JWTManager.CreateAccessToken(PayloadData = {"sub": GameMasterUserRecord.ID, "username": GameMasterUserRecord.Username, "role": GameMasterUserRecord.Role.value, "in_guild": True})
    return TokenString

@Pytest.fixture
def AdministratorToken(AdministratorUserRecord: User.User) -> str:
    TokenString: str = JWTManager.CreateAccessToken(PayloadData = {"sub": AdministratorUserRecord.ID, "username": AdministratorUserRecord.Username, "role": AdministratorUserRecord.Role.value, "in_guild": True})
    return TokenString
