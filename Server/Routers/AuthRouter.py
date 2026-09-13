import typing                             as Typing
import uuid                               as UUID
import fastapi                            as FastAPI
import fastapi.responses                  as Responses
import pydantic                           as Pydantic
import sqlalchemy                         as SQLAlchemy
import sqlalchemy.ext.asyncio             as AsyncIO
import Server.Auth.DiscordOAuth           as DiscordOAuth
import Server.Auth.JWTManager             as JWTManager
import Server.Auth.RoleBasedAccessControl as RoleBasedAccessControl
import Server.Config                      as Config
import Server.Database                    as Database
import Server.Models.User                 as User
import Server.Services.DebugService       as DebugService

Router = FastAPI.APIRouter(prefix = "/API/Auth", tags = ["Authentication"])
AuthenticationCallbackRouter = FastAPI.APIRouter(tags = ["Authentication"])

class DeveloperLoginRequest(Pydantic.BaseModel):
    Role       : User.UserRole
    Username   : str
    DisplayName: str

@Router.get("/Discord/Login")
async def DiscordLogin() -> Responses.RedirectResponse:
    StateToken  : str = str(UUID.uuid4())
    AuthorizeURL: str = DiscordOAuth.GenerateDiscordAuthorizeURL(StateToken)
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"OAuth Login Started: StateToken=\"{StateToken[:8]}…\"")
    Response = Responses.RedirectResponse(url = AuthorizeURL)
    Response.set_cookie(key = "OAuthState", value = StateToken, httponly = True, max_age = 600, samesite = "lax", path = "/")
    return Response

async def HandleDiscordCallback(Request: FastAPI.Request, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)], Code: Typing.Annotated[str | None, FastAPI.Query(alias = "code")] = None, State: Typing.Annotated[str | None, FastAPI.Query(alias = "state")] = None, GuildID: Typing.Annotated[str | None, FastAPI.Query(alias = "guild_id")] = None, Permissions: Typing.Annotated[str | None, FastAPI.Query(alias = "permissions")] = None, Error: Typing.Annotated[str | None, FastAPI.Query(alias = "error")] = None, ErrorDescription: Typing.Annotated[str | None, FastAPI.Query(alias = "error_description")] = None) -> Responses.Response:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Received OAuth Callback: HasCode={Code is not None}, GuildID=\"{GuildID}\"")
    if Error:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"OAuth Callback Failed with Error: \"{Error}\"")
        ErrorResponse = Responses.RedirectResponse(url = f"/?Error={Error}", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        ErrorResponse.delete_cookie(key = "OAuthState", path = "/")
        return ErrorResponse

    if GuildID and Permissions and not Code:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Discord Bot Authorized: GuildID=\"{GuildID}\"")
        return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

    if not Code:
        if GuildID and Permissions:
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Discord Bot Authorized Without Code: GuildID=\"{GuildID}\"")
            return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "OAuth Callback Failed: Missing Code")
        return Responses.RedirectResponse(url = "/?Error=OAuthMissingCode", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

    StoredOAuthState: str | None = Request.cookies.get("OAuthState")
    if not (StoredOAuthState and State and (StoredOAuthState == State)):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"CSRF Verification Failed: Received=\"{State[:8]}…\"")
        CSRFErrorResponse = Responses.RedirectResponse(url = "/?Error=CSRFVerificationFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        CSRFErrorResponse.delete_cookie(key = "OAuthState", path = "/")
        return CSRFErrorResponse

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"CSRF State Verified: State=\"{State[:8]}…\"")

    TokenData = await DiscordOAuth.ExchangeDiscordCode(Code)
    if not TokenData or "access_token" not in TokenData:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Token Exchange Returned Empty Payload")
        FailureResponse = Responses.RedirectResponse(url = "/?Error=OAuthFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        FailureResponse.delete_cookie(key = "OAuthState", path = "/")
        return FailureResponse

    AccessToken: str = TokenData["access_token"]
    UserProfile = await DiscordOAuth.FetchDiscordUserProfile(AccessToken)
    if not UserProfile or "id" not in UserProfile:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Failed to Fetch User Profile from Discord")
        UserProfileErrorResponse = Responses.RedirectResponse(url = "/?Error=UserFetchFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        UserProfileErrorResponse.delete_cookie(key = "OAuthState", path = "/")
        return UserProfileErrorResponse

    DiscordID  : str = UserProfile["id"]
    Username   : str = UserProfile.get("username", "Adventurer")
    DisplayName: str = UserProfile.get("global_name", Username)
    AvatarHash : str | None = UserProfile.get("avatar")
    GuildMemberProfile = await DiscordOAuth.FetchDiscordGuildMemberProfile(AccessToken, DiscordID)
    IsInGuild  : bool = GuildMemberProfile is not None
    AssignedRoles: list[str] = await DiscordOAuth.DetermineUserRolesFromDiscordMember(GuildMemberProfile)
    PrimaryRole: User.UserRole = DiscordOAuth.DeterminePrimaryUserRole(AssignedRoles)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"User Authenticated: Username=\"{Username}\", Role=\"{PrimaryRole.value}\"")
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.DiscordID == DiscordID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    ExistingUser: User.User | None = QueryResult.scalars().first()
    if ExistingUser:
        ExistingUser.Username    = Username
        ExistingUser.DisplayName = DisplayName
        ExistingUser.AvatarHash  = AvatarHash
        ExistingUser.Role        = PrimaryRole
        ExistingUser.Roles       = AssignedRoles
        TargetUser = ExistingUser

    else:
        NewUser = User.User(DiscordID = DiscordID, Username = Username, DisplayName = DisplayName, AvatarHash = AvatarHash, Role = PrimaryRole, Roles = AssignedRoles)
        DatabaseSession.add(NewUser)
        TargetUser = NewUser

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetUser)
    SessionTokenPayload: dict[str, Typing.Any] = {
        "sub"     : TargetUser.ID,
        "role"    : TargetUser.Role.value,
        "roles"   : TargetUser.Roles,
        "in_guild": IsInGuild
    }
    SessionToken: str = JWTManager.CreateAccessToken(SessionTokenPayload)
    if IsInGuild:
        RedirectURL: str = "/?Authenticated=True"

    else:
        RedirectURL: str = "/?Authenticated=True&NotInGuild=True"

    Response = Responses.RedirectResponse(url = RedirectURL, status_code = FastAPI.status.HTTP_303_SEE_OTHER)
    Response.set_cookie(key = "SessionToken", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax", path = "/")
    Response.delete_cookie(key = "OAuthState", path = "/")
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Session Established: UserID=\"{TargetUser.ID[:8]}…\", InGuild={IsInGuild}")
    return Response

@Router.get("/Discord/Callback")
async def DiscordCallback(Request: FastAPI.Request, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)], Code: Typing.Annotated[str | None, FastAPI.Query(alias = "code")] = None, State: Typing.Annotated[str | None, FastAPI.Query(alias = "state")] = None, GuildID: Typing.Annotated[str | None, FastAPI.Query(alias = "guild_id")] = None, Permissions: Typing.Annotated[str | None, FastAPI.Query(alias = "permissions")] = None, Error: Typing.Annotated[str | None, FastAPI.Query(alias = "error")] = None, ErrorDescription: Typing.Annotated[str | None, FastAPI.Query(alias = "error_description")] = None) -> Responses.Response:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Routing to Discord Callback Handler")
    return await HandleDiscordCallback(Request = Request, Code = Code, State = State, GuildID = GuildID, Permissions = Permissions, Error = Error, ErrorDescription = ErrorDescription, DatabaseSession = DatabaseSession)

@AuthenticationCallbackRouter.get("/API/Authentication")
async def DiscordAuthenticationRootCallback(Request: FastAPI.Request, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)], Code: Typing.Annotated[str | None, FastAPI.Query(alias = "code")] = None, State: Typing.Annotated[str | None, FastAPI.Query(alias = "state")] = None, GuildID: Typing.Annotated[str | None, FastAPI.Query(alias = "guild_id")] = None, Permissions: Typing.Annotated[str | None, FastAPI.Query(alias = "permissions")] = None, Error: Typing.Annotated[str | None, FastAPI.Query(alias = "error")] = None, ErrorDescription: Typing.Annotated[str | None, FastAPI.Query(alias = "error_description")] = None) -> Responses.Response:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Routing to Authentication Root Callback Handler")
    return await HandleDiscordCallback(Request = Request, Code = Code, State = State, GuildID = GuildID, Permissions = Permissions, Error = Error, ErrorDescription = ErrorDescription, DatabaseSession = DatabaseSession)

@Router.post("/DeveloperLogin/Partial", response_class = Responses.HTMLResponse)
@Router.post("/DevLogin/Partial", response_class = Responses.HTMLResponse)
async def DeveloperLoginPartial(Role: User.UserRole, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)]) -> Responses.Response:
    if Role == User.UserRole.Visitor:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Switched Developer Role to Visitor")
        Response = Responses.HTMLResponse(content = "Visitor")
        Response.delete_cookie(key = "SessionToken")
        return Response

    DeveloperRolesMapping: dict[User.UserRole, list[str]] = {
        User.UserRole.Administrator: ["Administrator"],
        User.UserRole.GameMaster   : ["Story Manager (DND5thEdition)", "Story Manager (Traveller2ndEdition)"],
        User.UserRole.Checker      : ["Sheet Checker (DND5thEdition)", "Sheet Checker (Traveller2ndEdition)"],
        User.UserRole.NormalUser   : ["Character Owner (DND5thEdition)", "Character Owner (Traveller2ndEdition)"]
    }
    DeveloperRoles: list[str] = DeveloperRolesMapping.get(Role, [])
    DiscordID: str = f"Developer_{Role.value}_Persisted"
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.DiscordID == DiscordID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetUser: User.User | None = QueryResult.scalars().first()
    if not TargetUser:
        TargetUser = User.User(DiscordID = DiscordID, Username = f"{Role.value}User", DisplayName = f"{Role.value} Operator", Role = Role, Roles = DeveloperRoles)
        DatabaseSession.add(TargetUser)

    else:
        TargetUser.Role = Role
        TargetUser.Roles = DeveloperRoles

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetUser)
    SessionTokenPayload: dict[str, Typing.Any] = {
        "sub"     : TargetUser.ID,
        "role"    : TargetUser.Role.value,
        "roles"   : TargetUser.Roles,
        "in_guild": True
    }
    SessionToken: str = JWTManager.CreateAccessToken(SessionTokenPayload)
    Response = Responses.HTMLResponse(content = TargetUser.Role.value)
    Response.set_cookie(key = "SessionToken", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax", path = "/")
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Established Developer Session: Username=\"{TargetUser.Username}\", Role=\"{TargetUser.Role.value}\"")
    return Response

@Router.get("/Me/Partial", response_class = Responses.HTMLResponse)
async def GetCurrentUserRolePartial(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.HTMLResponse:
    if not CurrentUser:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Current User Role: Visitor")
        return Responses.HTMLResponse(content = "Visitor")

    OutputRole: str = ", ".join(CurrentUser.Roles) if CurrentUser.Roles else CurrentUser.Role.value
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Current User Role: UserID=\"{CurrentUser.ID[:8]}…\", Role=\"{OutputRole}\"")
    return Responses.HTMLResponse(content = OutputRole)

@Router.post("/Logout")
async def Logout() -> Responses.Response:
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = "User Logged Out and Session Cookies Cleared")
    Response = Responses.JSONResponse(content = {"Status": "LoggedOut"})
    Response.delete_cookie(key = "SessionToken", path = "/")
    Response.delete_cookie(key = "OAuthState", path = "/")
    return Response

@Router.get("/Session/Status", response_class = Responses.JSONResponse)
async def GetSessionStatus(Request: FastAPI.Request, CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.JSONResponse:
    if not CurrentUser:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Session Status Served for Unauthenticated Visitor")
        SessionStatusData: dict[str, Typing.Any] = {
            "IsAuthenticated" : False,
            "Username"        : None,
            "DisplayName"     : None,
            "AvatarURL"       : None,
            "Role"            : User.UserRole.Visitor.value,
            "Roles"           : [],
            "IsInGuild"       : False,
            "DiscordInviteURL": Config.GLOBAL_SETTINGS.DISCORD_INVITE_URL
        }
        return Responses.JSONResponse(content = SessionStatusData)

    AvatarURL: str | None = None
    if CurrentUser.AvatarHash and CurrentUser.DiscordID:
        AvatarURL = f"https://cdn.discordapp.com/avatars/{CurrentUser.DiscordID}/{CurrentUser.AvatarHash}.png?size=64"

    SessionTokenString: str | None = Request.cookies.get("SessionToken")
    TokenPayload: dict[str, Typing.Any] | None = JWTManager.DecodeAccessToken(SessionTokenString) if SessionTokenString else None
    IsInGuild: bool = bool(TokenPayload.get("in_guild", False)) if TokenPayload else False
    if CurrentUser.Role == User.UserRole.Administrator or (CurrentUser.Roles and len(CurrentUser.Roles) > 0):
        IsInGuild = True

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Session Status Served: UserID=\"{CurrentUser.ID[:8]}…\", Role=\"{CurrentUser.Role.value}\"")
    SessionStatusData: dict[str, Typing.Any] = {
        "IsAuthenticated" : True,
        "Username"        : CurrentUser.Username,
        "DisplayName"     : CurrentUser.DisplayName,
        "AvatarURL"       : AvatarURL,
        "Role"            : CurrentUser.Role.value,
        "Roles"           : CurrentUser.Roles if (CurrentUser.Roles is not None) else [],
        "IsInGuild"       : IsInGuild,
        "DiscordInviteURL": Config.GLOBAL_SETTINGS.DISCORD_INVITE_URL
    }
    return Responses.JSONResponse(content = SessionStatusData)

@Router.post("/GuestLogin", response_class = Responses.JSONResponse)
async def PerformGuestLogin() -> Responses.Response:
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = "Guest Login Established with Visitor Role")
    GuestLoginData: dict[str, Typing.Any] = {
        "Status"          : "GuestAuthenticated",
        "Role"            : User.UserRole.Visitor.value,
        "DiscordInviteURL": Config.GLOBAL_SETTINGS.DISCORD_INVITE_URL
    }
    Response = Responses.JSONResponse(content = GuestLoginData)
    Response.delete_cookie(key = "SessionToken", path = "/")
    return Response
