import json                as JSONParser
import os                  as OperatingSystem
import httpx2              as HTTPClient
import typing              as Typing
import urllib.parse        as URLParse
import Server.Config       as Config
import Server.Models.User  as User

DISCORD_API_BASE_URL : str = "https://discord.com/api/v10"
DISCORD_AUTHORIZE_URL: str = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL    : str = "https://discord.com/api/oauth2/token"
DISCORD_OAUTH_SCOPES : str = "identify guilds guilds.members.read"

def GenerateDiscordAuthorizeURL(StateToken: str) -> str:
    Parameters: Typing.Dict[str, str] = {
        "client_id"    : Config.GLOBAL_SETTINGS.DISCORD_CLIENT_ID,
        "redirect_uri" : Config.GLOBAL_SETTINGS.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope"        : DISCORD_OAUTH_SCOPES,
        "state"        : StateToken
    }
    QueryString: str = URLParse.urlencode(Parameters)
    return f"{DISCORD_AUTHORIZE_URL}?{QueryString}"

async def ExchangeDiscordCode(Code: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    Payload: Typing.Dict[str, str] = {
        "client_id"    : Config.GLOBAL_SETTINGS.DISCORD_CLIENT_ID,
        "client_secret": Config.GLOBAL_SETTINGS.DISCORD_CLIENT_SECRET,
        "grant_type"   : "authorization_code",
        "code"         : Code,
        "redirect_uri" : Config.GLOBAL_SETTINGS.DISCORD_REDIRECT_URI
    }
    Headers: Typing.Dict[str, str] = {
        "Content-Type": "application/x-www-form-urlencoded"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.post(DISCORD_TOKEN_URL, data = Payload, headers = Headers)
        if Response.status_code == 200:
            return Response.json()

        return None

async def FetchDiscordUserProfile(AccessToken: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me", headers = Headers)
        if Response.status_code == 200:
            return Response.json()

        return None

async def FetchDiscordGuildMemberProfile(AccessToken: str, DiscordUserIdentifier: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    if not Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID:
        return None

    GuildIdentifier: str = Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds/{GuildIdentifier}/member", headers = Headers)
        if Response.status_code == 200:
            return Response.json()

        if Config.GLOBAL_SETTINGS.DISCORD_BOT_TOKEN and DiscordUserIdentifier:
            BotHeaders: Typing.Dict[str, str] = {
                "Authorization": f"Bot {Config.GLOBAL_SETTINGS.DISCORD_BOT_TOKEN}"
            }
            BotResponse = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/guilds/{GuildIdentifier}/members/{DiscordUserIdentifier}", headers = BotHeaders)
            if BotResponse.status_code == 200:
                return BotResponse.json()

        return None

def LoadRolesConfiguration() -> Typing.Dict[str, Typing.List[str]]:
    RolesFilePath: str = OperatingSystem.path.join("Scratch", "RolesList.json")
    if not OperatingSystem.path.exists(RolesFilePath):
        return {}

    with open(RolesFilePath, "r", encoding = "utf-8") as RolesFileHandle:
        RolesData: Typing.Dict[str, Typing.Any] = JSONParser.load(RolesFileHandle)

    RoleMapping: Typing.Dict[str, Typing.List[str]] = {}
    for RoleRecord in RolesData.values():
        if not isinstance(RoleRecord, dict):
            continue

        RoleIdentifier: str = str(RoleRecord.get("ID", ""))
        Permissions: Typing.Dict[str, Typing.Any] = RoleRecord.get("Permissions", {})
        ClientRoles: Typing.List[str] = Permissions.get("OnClient", [])
        if RoleIdentifier and ClientRoles:
            RoleMapping[RoleIdentifier] = ClientRoles

    return RoleMapping

def DetermineUserRolesFromDiscordMember(MemberData: Typing.Optional[Typing.Dict[str, Typing.Any]]) -> Typing.List[str]:
    if not MemberData:
        return []

    DiscordRoleIdentifiers: Typing.List[str] = [str(RoleIdentifier) for RoleIdentifier in MemberData.get("roles", [])]
    RoleMapping: Typing.Dict[str, Typing.List[str]] = LoadRolesConfiguration()
    AssignedRoles: Typing.List[str] = []
    for RoleIdentifier in DiscordRoleIdentifiers:
        if RoleIdentifier in RoleMapping:
            for ClientRole in RoleMapping[RoleIdentifier]:
                if ClientRole not in AssignedRoles:
                    AssignedRoles.append(ClientRole)

    return AssignedRoles

def DeterminePrimaryUserRole(AssignedRoles: Typing.List[str]) -> User.UserRole:
    if "Administrator" in AssignedRoles:
        return User.UserRole.Administrator

    for AssignedRole in AssignedRoles:
        if "Story Manager" in AssignedRole:
            return User.UserRole.GameMaster

    for AssignedRole in AssignedRoles:
        if "Sheet Checker" in AssignedRole:
            return User.UserRole.Checker

    for AssignedRole in AssignedRoles:
        if "Character Owner" in AssignedRole:
            return User.UserRole.NormalUser

    return User.UserRole.NormalUser
