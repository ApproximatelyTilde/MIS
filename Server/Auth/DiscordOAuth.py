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
    DebugService.LogDebugMessage(f"Discord Auth URL Generated: {AuthorizeURL}")
    return AuthorizeURL

async def ExchangeDiscordCode(Code: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage(f"Discord Code Exchange: Code='{Code[:8]}...'")
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
            DebugService.LogDebugMessage("Discord Token Acquired (200 OK)")
            return Response.json()

        DebugService.LogDebugMessage(f"Discord Token Exchange Failed: HTTP {Response.status_code}")
        return None

async def FetchDiscordUserProfile(AccessToken: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me", headers = Headers)
        if Response.status_code == 200:
            ProfileData: Typing.Dict[str, Typing.Any] = Response.json()
            DebugService.LogDebugMessage(f"Discord User Profile Loaded: {ProfileData.get('username')} ({ProfileData.get('id')})")
            return ProfileData

        DebugService.LogDebugMessage(f"Discord User Profile Failed: HTTP {Response.status_code}")
        return None

async def FetchDiscordGuildMemberProfile(AccessToken: str, DiscordUserIdentifier: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage(f"Discord Guild Fetch: User={DiscordUserIdentifier}")
    if not Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID:
        DebugService.LogDebugMessage("Discord Guild Fetch Skipped: DISCORD_GUILD_ID Unset")
        return None

    GuildIdentifier: str = Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    async with HTTPClient.AsyncClient() as AsyncClientConnection:
        Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds/{GuildIdentifier}/member", headers = Headers)
        if Response.status_code == 200:
            DebugService.LogDebugMessage(f"Discord Guild Member Profile Loaded (Guild: {GuildIdentifier})")
            return Response.json()

        DebugService.LogDebugMessage(f"Discord Guild Member Profile Failed: HTTP {Response.status_code} (Guild: {GuildIdentifier})")
        return None

def LoadRolesConfiguration() -> Typing.Dict[str, Typing.List[str]]:
    RolesFilePath: str = OperatingSystem.path.join("Scratch", "RolesList.json")
    if not OperatingSystem.path.exists(RolesFilePath):
        DebugService.LogDebugMessage(f"Roles Config Missing: '{RolesFilePath}' Not Found")
        return {
        }

    with open(RolesFilePath, "r", encoding = "utf-8") as RolesFileHandle:
        RolesData: Typing.Dict[str, Typing.Any] = JSONParser.load(RolesFileHandle)

    RoleMapping: Typing.Dict[str, Typing.List[str]] = {
    }
    for RoleRecord in RolesData.values():
        if not isinstance(RoleRecord, dict):
            continue

        RoleIdentifier: str = str(RoleRecord.get("ID", ""))
        Permissions: Typing.Dict[str, Typing.Any] = RoleRecord.get("Permissions", {})
        ClientRoles: Typing.List[str] = Permissions.get("OnClient", [])
        if RoleIdentifier and ClientRoles:
            RoleMapping[RoleIdentifier] = ClientRoles

    DebugService.LogDebugMessage(f"Roles Config Loaded: {len(RoleMapping)} Roles From '{RolesFilePath}'")
    return RoleMapping

def DetermineUserRolesFromDiscordMember(MemberData: Typing.Optional[Typing.Dict[str, Typing.Any]]) -> Typing.List[str]:
    if not MemberData:
        DebugService.LogDebugMessage("Discord Roles: No Member Data, Assigned: []")
        return []

    DiscordRoleIdentifiers: Typing.List[str] = [str(RoleIdentifier) for RoleIdentifier in MemberData.get("roles", [])]
    RoleMapping: Typing.Dict[str, Typing.List[str]] = LoadRolesConfiguration()
    AssignedRoles: Typing.List[str] = []
    for RoleIdentifier in DiscordRoleIdentifiers:
        if RoleIdentifier in RoleMapping:
            for ClientRole in RoleMapping[RoleIdentifier]:
                if ClientRole not in AssignedRoles:
                    AssignedRoles.append(ClientRole)

    DebugService.LogDebugMessage(f"Discord Roles Resolved: {AssignedRoles} (From {len(DiscordRoleIdentifiers)} Guild Roles)")
    return AssignedRoles

def DeterminePrimaryUserRole(AssignedRoles: Typing.List[str]) -> User.UserRole:
    if "Administrator" in AssignedRoles:
        PrimaryRole = User.UserRole.Administrator
    else:
        PrimaryRole = User.UserRole.NormalUser
        for AssignedRole in AssignedRoles:
            if "Story Manager" in AssignedRole:
                PrimaryRole = User.UserRole.GameMaster
                break
            if "Sheet Checker" in AssignedRole:
                PrimaryRole = User.UserRole.Checker
                break
            if "Character Owner" in AssignedRole:
                PrimaryRole = User.UserRole.NormalUser
                break

    DebugService.LogDebugMessage(f"Primary Role Determined: {PrimaryRole.value} (From: {AssignedRoles})")
    return PrimaryRole
