import json                             as JSONParser
import os                               as OperatingSystem
import httpx2                           as HTTPClient
import typing                           as Typing
import urllib.parse                     as URLParse
import Server.Config                    as Config
import Server.Models.User               as User
import Server.Services.DebugService     as DebugService

DISCORD_API_BASE_URL : str = "https://discord.com/api/v10"
DISCORD_AUTHORIZE_URL: str = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL    : str = "https://discord.com/api/oauth2/token"
DISCORD_OAUTH_SCOPES : str = "identify guilds guilds.members.read"

def GenerateDiscordAuthorizeURL(StateToken: str) -> str:
    DebugService.LogDebugMessage(f"Generating Discord Authorization URL With State Token: {StateToken}")
    Parameters: Typing.Dict[str, str] = {
        "client_id"    : Config.GLOBAL_SETTINGS.DISCORD_CLIENT_ID,
        "redirect_uri" : Config.GLOBAL_SETTINGS.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope"        : DISCORD_OAUTH_SCOPES,
        "state"        : StateToken
    }
    QueryString: str = URLParse.urlencode(Parameters)
    AuthorizeURL: str = f"{DISCORD_AUTHORIZE_URL}?{QueryString}"
    DebugService.LogDebugMessage(f"Generated Discord Authorization URL: {AuthorizeURL}")
    return AuthorizeURL

async def ExchangeDiscordCode(Code: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage(f"Exchanging Discord Authorization Code: {Code}")
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
            DebugService.LogDebugMessage("Successfully Exchanged Discord Authorization Code For Access Token")
            return Response.json()

        DebugService.LogDebugMessage(f"Failed To Exchange Discord Code With Status Code: {Response.status_code}")
        return None

async def FetchDiscordUserProfile(AccessToken: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage("Fetching Discord User Profile From API")
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me", headers = Headers)
        if Response.status_code == 200:
            DebugService.LogDebugMessage("Successfully Fetched Discord User Profile")
            return Response.json()

        DebugService.LogDebugMessage(f"Failed To Fetch Discord User Profile With Status Code: {Response.status_code}")
        return None

async def FetchDiscordGuildMemberProfile(AccessToken: str, DiscordUserIdentifier: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage(f"Fetching Discord Guild Member Profile For User Identifier: {DiscordUserIdentifier}")
    if not Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID:
        DebugService.LogDebugMessage("Guild Member Profile Fetch Skipped Because Discord Guild Identifier Is Not Configured")
        return None

    GuildIdentifier: str = Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds/{GuildIdentifier}/member", headers = Headers)
        if Response.status_code == 200:
            DebugService.LogDebugMessage("Successfully Fetched Discord Guild Member Profile Via User Token")
            return Response.json()

        if Config.GLOBAL_SETTINGS.DISCORD_BOT_TOKEN and DiscordUserIdentifier:
            DebugService.LogDebugMessage("Attempting To Fetch Discord Guild Member Profile Via Bot Token Fallback")
            BotHeaders: Typing.Dict[str, str] = {
                "Authorization": f"Bot {Config.GLOBAL_SETTINGS.DISCORD_BOT_TOKEN}"
            }
            BotResponse = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/guilds/{GuildIdentifier}/members/{DiscordUserIdentifier}", headers = BotHeaders)
            if BotResponse.status_code == 200:
                DebugService.LogDebugMessage("Successfully Fetched Discord Guild Member Profile Via Bot Token")
                return BotResponse.json()

        DebugService.LogDebugMessage("Failed To Fetch Discord Guild Member Profile")
        return None

def LoadRolesConfiguration() -> Typing.Dict[str, Typing.List[str]]:
    DebugService.LogDebugMessage("Loading Roles Configuration From Storage File")
    RolesFilePath: str = OperatingSystem.path.join("Scratch", "RolesList.json")
    if not OperatingSystem.path.exists(RolesFilePath):
        DebugService.LogDebugMessage(f"Roles Configuration File Not Found At Path: {RolesFilePath}")
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

    DebugService.LogDebugMessage(f"Successfully Loaded {len(RoleMapping)} Role Mappings From Configuration")
    return RoleMapping

def DetermineUserRolesFromDiscordMember(MemberData: Typing.Optional[Typing.Dict[str, Typing.Any]]) -> Typing.List[str]:
    DebugService.LogDebugMessage("Determining User Roles From Discord Member Data")
    if not MemberData:
        DebugService.LogDebugMessage("No Member Data Provided, Returning Empty Role List")
        return []

    DiscordRoleIdentifiers: Typing.List[str] = [str(RoleIdentifier) for RoleIdentifier in MemberData.get("roles", [])]
    RoleMapping: Typing.Dict[str, Typing.List[str]] = LoadRolesConfiguration()
    AssignedRoles: Typing.List[str] = []
    for RoleIdentifier in DiscordRoleIdentifiers:
        if RoleIdentifier in RoleMapping:
            for ClientRole in RoleMapping[RoleIdentifier]:
                if ClientRole not in AssignedRoles:
                    AssignedRoles.append(ClientRole)

    DebugService.LogDebugMessage(f"Resolved Assigned Roles For Member: {AssignedRoles}")
    return AssignedRoles

def DeterminePrimaryUserRole(AssignedRoles: Typing.List[str]) -> User.UserRole:
    DebugService.LogDebugMessage(f"Determining Primary User Role From Assigned Roles: {AssignedRoles}")
    if "Administrator" in AssignedRoles:
        DebugService.LogDebugMessage("Selected Primary User Role: Administrator")
        return User.UserRole.Administrator

    for AssignedRole in AssignedRoles:
        if "Story Manager" in AssignedRole:
            DebugService.LogDebugMessage("Selected Primary User Role: GameMaster")
            return User.UserRole.GameMaster

    for AssignedRole in AssignedRoles:
        if "Sheet Checker" in AssignedRole:
            DebugService.LogDebugMessage("Selected Primary User Role: Checker")
            return User.UserRole.Checker

    for AssignedRole in AssignedRoles:
        if "Character Owner" in AssignedRole:
            DebugService.LogDebugMessage("Selected Primary User Role: NormalUser")
            return User.UserRole.NormalUser

    DebugService.LogDebugMessage("Defaulted Primary User Role: NormalUser")
    return User.UserRole.NormalUser
