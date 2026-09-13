import hashlib                       as HashLib
import json                          as JSONParser
import os                            as OperatingSystem
import time                          as SystemTime
import typing                        as Typing
import urllib.parse                  as URLParse
import httpx2                        as HTTPClient
import Server.Config                 as Config
import Server.Models.User            as User
import Server.Services.DebugService  as DebugService

DISCORD_API_BASE_URL        : str   = "https://discord.com/api/v10"
DISCORD_AUTHORIZE_URL       : str   = "https://discord.com/oauth2/authorize"
DISCORD_TOKEN_URL           : str   = "https://discord.com/api/oauth2/token"
DISCORD_OAUTH_SCOPES        : str   = "identify guilds guilds.members.read"
ONE_WEEK_SECONDS            : float = 604800.0
ONE_MONTH_SECONDS           : float = 2592000.0
GUILD_ROLES_CACHE_FILE_PATH : str   = OperatingSystem.path.join("Server", "Data", "GuildRolesCache.json")

def GenerateDiscordAuthorizeURL(StateToken: str) -> str:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"State Token Generated: StateToken=\"{StateToken[:8]}…\"")
    Parameters: Typing.Dict[str, str] = {
        "client_id"    : Config.GLOBAL_SETTINGS.DISCORD_CLIENT_ID,
        "redirect_uri" : Config.GLOBAL_SETTINGS.DISCORD_REDIRECT_URI,
        "response_type": "code",
        "scope"        : DISCORD_OAUTH_SCOPES,
        "state"        : StateToken
    }
    QueryString: str = URLParse.urlencode(Parameters)
    AuthorizeURL: str = f"{DISCORD_AUTHORIZE_URL}?{QueryString}"
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Authorization URL Generated Successfully")
    return AuthorizeURL

async def ExchangeDiscordCode(Code: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Code Exchange Initiated: Code=\"{Code[:8]}…\"")
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
    try:
        async with HTTPClient.AsyncClient() as AsyncClientConnection:
            Response = await AsyncClientConnection.post(DISCORD_TOKEN_URL, data = Payload, headers = Headers, timeout = 10.0)
            if Response.status_code == 200:
                DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Access Token Acquired: Status=200")
                return Response.json()

            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Access Token Exchange Failed: Status={Response.status_code}")
            return None

    except (HTTPClient.RequestError, HTTPClient.TimeoutException, JSONParser.JSONDecodeError, Exception) as NetworkException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Access Token Transport Error: {type(NetworkException).__name__}")
        return None

async def FetchDiscordUserProfile(AccessToken: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    try:
        async with HTTPClient.AsyncClient() as AsyncClientConnection:
            Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me", headers = Headers, timeout = 10.0)
            if Response.status_code == 200:
                ProfileData: Typing.Dict[str, Typing.Any] = Response.json()
                DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"User Profile Loaded: \"{ProfileData.get("username")}\" ({ProfileData.get("id")})")
                return ProfileData

            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"User Profile Fetch Failed: Status={Response.status_code}")
            return None

    except (HTTPClient.RequestError, HTTPClient.TimeoutException, JSONParser.JSONDecodeError, Exception) as NetworkException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"User Profile Transport Error: {type(NetworkException).__name__}")
        return None

async def FetchDiscordGuildMemberProfile(AccessToken: str, DiscordUserID: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Fetching Guild Member: UserID=\"{DiscordUserID}\"")
    if not Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Guild Member Fetch Skipped: Guild ID Unconfigured")
        return None

    GuildID: str = Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID
    Headers: Typing.Dict[str, str] = {
        "Authorization": f"Bearer {AccessToken}"
    }
    try:
        async with HTTPClient.AsyncClient() as AsyncClientConnection:
            Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/users/@me/guilds/{GuildID}/member", headers = Headers, timeout = 10.0)
            if Response.status_code == 200:
                DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Guild Member Profile Loaded: GuildID=\"{GuildID}\"")
                return Response.json()

            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Guild Member Profile Failed: Status={Response.status_code}")
            return None

    except (HTTPClient.RequestError, HTTPClient.TimeoutException, JSONParser.JSONDecodeError, Exception) as NetworkException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Guild Member Transport Error: {type(NetworkException).__name__}")
        return None

def MapDiscordRoleNameToClientRoles(RoleName: str) -> Typing.List[str]:
    NormalizedName: str = RoleName.strip().lower()
    if ("administrator" in NormalizedName) or ("high commissioner" in NormalizedName):
        return ["Administrator"]

    if ("narrative officer" in NormalizedName) and ("class-d" in NormalizedName):
        return ["Story Manager (DND5thEdition)"]

    if ("narrative officer" in NormalizedName) and ("class-t" in NormalizedName):
        return ["Story Manager (Traveller2ndEdition)"]

    if ("certification officer" in NormalizedName) and ("class-d" in NormalizedName):
        return ["Sheet Checker (DND5thEdition)"]

    if ("certification officer" in NormalizedName) and ("class-t" in NormalizedName):
        return ["Sheet Checker (Traveller2ndEdition)"]

    if "enrollee" in NormalizedName:
        return ["Character Owner (DND5thEdition)"]

    if "pioneer" in NormalizedName:
        return ["Character Owner (Traveller2ndEdition)"]

    return []

def ReadCachedGuildRoles() -> Typing.Dict[str, Typing.Any]:
    if not OperatingSystem.path.exists(GUILD_ROLES_CACHE_FILE_PATH):
        return {
        }

    try:
        with open(GUILD_ROLES_CACHE_FILE_PATH, "r", encoding = "utf-8") as RolesFileHandle:
            return JSONParser.load(RolesFileHandle)

    except (JSONParser.JSONDecodeError, OSError) as ReadException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Cache File Read Error: {type(ReadException).__name__}")
        return {
        }

def WriteCachedGuildRoles(CachePayload: Typing.Dict[str, Typing.Any]) -> None:
    ParentDirectory: str = OperatingSystem.path.dirname(GUILD_ROLES_CACHE_FILE_PATH)
    if not OperatingSystem.path.exists(ParentDirectory):
        OperatingSystem.makedirs(ParentDirectory, exist_ok = True)

    try:
        with open(GUILD_ROLES_CACHE_FILE_PATH, "w", encoding = "utf-8") as RolesFileHandle:
            JSONParser.dump(CachePayload, RolesFileHandle, indent = 4)

    except OSError as WriteException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Cache File Write Error: {type(WriteException).__name__}")

async def SynchronizeGuildRoles() -> Typing.Dict[str, Typing.List[str]]:
    CurrentTimestamp: float = SystemTime.time()
    CachedData: Typing.Dict[str, Typing.Any] = ReadCachedGuildRoles()
    LastCheckedTimestamp: float = float(CachedData.get("LastCheckedTimestamp", 0.0))
    LastUpdatedTimestamp: float = float(CachedData.get("LastUpdatedTimestamp", 0.0))
    CachedHash: str = str(CachedData.get("RolesHash", ""))
    RoleMapping: Typing.Dict[str, Typing.List[str]] = CachedData.get("RoleMapping", {})
    TimeSinceLastCheck: float = CurrentTimestamp - LastCheckedTimestamp
    TimeSinceLastUpdate: float = CurrentTimestamp - LastUpdatedTimestamp

    if (TimeSinceLastCheck < ONE_WEEK_SECONDS) and RoleMapping:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Cached Roles Fresh: Age Seconds={int(TimeSinceLastCheck)}, Roles={len(RoleMapping)}")
        return RoleMapping

    GuildID: str | None = Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID
    BotToken: str | None = Config.GLOBAL_SETTINGS.DISCORD_BOT_TOKEN
    if not GuildID or not BotToken:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Role Synchronization Skipped: Credentials Unconfigured")
        return RoleMapping

    try:
        Headers: Typing.Dict[str, str] = {
            "Authorization": f"Bot {BotToken}"
        }
        async with HTTPClient.AsyncClient() as AsyncClientConnection:
            Response = await AsyncClientConnection.get(f"{DISCORD_API_BASE_URL}/guilds/{GuildID}/roles", headers = Headers, timeout = 10.0)
            if Response.status_code == 200:
                ResponseBytes: bytes = Response.content
                NewHash: str = HashLib.sha256(ResponseBytes).hexdigest()
                if (NewHash == CachedHash) and RoleMapping:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Roles Unchanged: Hash=\"{NewHash[:8]}…\", Timestamp Refreshed")
                    CachedData["LastCheckedTimestamp"] = CurrentTimestamp
                    WriteCachedGuildRoles(CachedData)
                    return RoleMapping

                RawRolesList: Typing.List[Typing.Dict[str, Typing.Any]] = Response.json()
                NewRoleMapping: Typing.Dict[str, Typing.List[str]] = {
                }
                for RoleRecord in RawRolesList:
                    RoleID: str = str(RoleRecord.get("id", ""))
                    RoleName: str = str(RoleRecord.get("name", ""))
                    MappedRoles: Typing.List[str] = MapDiscordRoleNameToClientRoles(RoleName)
                    if RoleID and MappedRoles:
                        NewRoleMapping[RoleID] = MappedRoles

                UpdatedCachePayload: Typing.Dict[str, Typing.Any] = {
                    "LastCheckedTimestamp": CurrentTimestamp,
                    "LastUpdatedTimestamp": CurrentTimestamp,
                    "RolesHash"           : NewHash,
                    "RoleMapping"         : NewRoleMapping
                }
                WriteCachedGuildRoles(UpdatedCachePayload)
                DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Roles Updated: {len(NewRoleMapping)} Mapped Roles Cached")
                return NewRoleMapping

            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Role Synchronization Failed: Status={Response.status_code}")

    except (HTTPClient.RequestError, HTTPClient.TimeoutException, JSONParser.JSONDecodeError, Exception) as NetworkException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Role Synchronization Network Error: {type(NetworkException).__name__}")

    if (TimeSinceLastUpdate <= ONE_MONTH_SECONDS) and RoleMapping:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Using Cached Roles: Age Seconds={int(TimeSinceLastUpdate)}")
        return RoleMapping

    return RoleMapping

async def DetermineUserRolesFromDiscordMember(MemberData: Typing.Optional[Typing.Dict[str, Typing.Any]]) -> Typing.List[str]:
    if not MemberData:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "No Member Data Provided: Assigned Roles Empty")
        return []

    DiscordRoleIDs: Typing.List[str] = [str(RoleID) for RoleID in MemberData.get("roles", [])]
    RoleMapping: Typing.Dict[str, Typing.List[str]] = await SynchronizeGuildRoles()
    AssignedRoles: Typing.List[str] = []
    for RoleID in DiscordRoleIDs:
        if RoleID in RoleMapping:
            for ClientRole in RoleMapping[RoleID]:
                if ClientRole not in AssignedRoles:
                    AssignedRoles.append(ClientRole)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Resolved {len(AssignedRoles)} Roles from {len(DiscordRoleIDs)} Guild Roles")
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

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Determined Primary Role: \"{PrimaryRole.value}\"")
    return PrimaryRole
