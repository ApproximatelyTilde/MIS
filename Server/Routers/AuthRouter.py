import typing                             as Typing
import uuid                               as UniversallyUniqueIdentifier
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
import Server.Services.DebugService      as DebugService

Router = FastAPI.APIRouter(prefix = "/API/Auth", tags = ["Authentication"])
AuthenticationCallbackRouter = FastAPI.APIRouter(tags = ["Authentication"])

class DevLoginRequest(Pydantic.BaseModel):
    Role       : User.UserRole
    Username   : str
    DisplayName: str

@Router.get("/Discord/Login")
async def DiscordLogin() -> Responses.RedirectResponse:
    StateToken  : str = str(UniversallyUniqueIdentifier.uuid4())
    AuthorizeURL: str = DiscordOAuth.GenerateDiscordAuthorizeURL(StateToken)
    DebugService.LogDebugMessage(f"Discord OAuth Login Started: StateToken='{StateToken[:8]}...'")
    Response = Responses.RedirectResponse(url = AuthorizeURL)
    Response.set_cookie(key = "OAuthState", value = StateToken, httponly = True, max_age = 600, samesite = "lax", path = "/")
    Response.set_cookie(key = "oauth_state", value = StateToken, httponly = True, max_age = 600, samesite = "lax", path = "/")
    return Response

async def HandleDiscordCallback(
    Request: FastAPI.Request,
    Code: Typing.Optional[str] = FastAPI.Query(default = None, alias = "code"),
    State: Typing.Optional[str] = FastAPI.Query(default = None, alias = "state"),
    GuildIdentifier: Typing.Optional[str] = FastAPI.Query(default = None, alias = "guild_id"),
    Permissions: Typing.Optional[str] = FastAPI.Query(default = None, alias = "permissions"),
    Error: Typing.Optional[str] = FastAPI.Query(default = None, alias = "error"),
    ErrorDescription: Typing.Optional[str] = FastAPI.Query(default = None, alias = "error_description"),
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.Response:
    DebugService.LogDebugMessage(f"Discord OAuth Callback: Code={'Yes' if Code else 'None'}, State={'Yes' if State else 'None'}, Guild={GuildIdentifier}")
    if Error:
        DebugService.LogDebugMessage(f"OAuth Callback Failed: Error='{Error}', Desc='{ErrorDescription}'")
        ErrorResponse = Responses.RedirectResponse(url = f"/?Error={Error}", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        ErrorResponse.delete_cookie(key = "OAuthState", path = "/")
        ErrorResponse.delete_cookie(key = "oauth_state", path = "/")
        return ErrorResponse

    if GuildIdentifier and Permissions and not Code:
        DebugService.LogDebugMessage(f"OAuth Callback: Bot Authorized (Guild={GuildIdentifier}, Perms={Permissions})")
        return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

    if not Code:
        if GuildIdentifier and Permissions:
            DebugService.LogDebugMessage(f"OAuth Callback: Bot Authorized Without Code (Guild={GuildIdentifier})")
            return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

        DebugService.LogDebugMessage("OAuth Callback Failed: Missing Code")
        return Responses.RedirectResponse(url = "/?Error=OAuthMissingCode", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

    StoredOAuthState: Typing.Optional[str] = Request.cookies.get("OAuthState") or Request.cookies.get("oauth_state")
    if not (StoredOAuthState and State and (StoredOAuthState == State)):
        DebugService.LogDebugMessage(f"OAuth Callback Failed: CSRF Mismatch (Stored='{StoredOAuthState}', Received='{State}')")
        CSRFErrorResponse = Responses.RedirectResponse(url = "/?Error=CSRFVerificationFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        CSRFErrorResponse.delete_cookie(key = "OAuthState", path = "/")
        CSRFErrorResponse.delete_cookie(key = "oauth_state", path = "/")
        return CSRFErrorResponse

    DebugService.LogDebugMessage(f"OAuth Callback: CSRF Verified (State='{State[:8]}...')")

    TokenData = await DiscordOAuth.ExchangeDiscordCode(Code)
    if not TokenData or "access_token" not in TokenData:
        DebugService.LogDebugMessage("OAuth Callback Failed: Token Exchange Returned None")
        FailureResponse = Responses.RedirectResponse(url = "/?Error=OAuthFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        FailureResponse.delete_cookie(key = "OAuthState", path = "/")
        FailureResponse.delete_cookie(key = "oauth_state", path = "/")
        return FailureResponse

    AccessToken: str = TokenData["access_token"]
    UserProfile = await DiscordOAuth.FetchDiscordUserProfile(AccessToken)
    if not UserProfile or "id" not in UserProfile:
        DebugService.LogDebugMessage("OAuth Callback Failed: Discord User Profile Fetch Failed")
        UserProfileErrorResponse = Responses.RedirectResponse(url = "/?Error=UserFetchFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        UserProfileErrorResponse.delete_cookie(key = "OAuthState", path = "/")
        UserProfileErrorResponse.delete_cookie(key = "oauth_state", path = "/")
        return UserProfileErrorResponse

    DiscordID  : str = UserProfile["id"]
    Username   : str = UserProfile.get("username", "Adventurer")
    DisplayName: str = UserProfile.get("global_name", Username)
    AvatarHash : Typing.Optional[str] = UserProfile.get("avatar")
    GuildMemberProfile = await DiscordOAuth.FetchDiscordGuildMemberProfile(AccessToken, DiscordID)
    IsInGuild  : bool = GuildMemberProfile is not None
    AssignedRoles: Typing.List[str] = DiscordOAuth.DetermineUserRolesFromDiscordMember(GuildMemberProfile)
    AssignedPrimaryRole: User.UserRole = DiscordOAuth.DeterminePrimaryUserRole(AssignedRoles)
    DebugService.LogDebugMessage(f"OAuth User Authenticated: ID='{DiscordID}', User='{Username}', Role='{AssignedPrimaryRole.value}', InGuild={IsInGuild}")
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.DiscordIdentifier == DiscordID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    ExistingUser: Typing.Optional[User.User] = QueryResult.scalars().first()
    if ExistingUser:
        ExistingUser.Username    = Username
        ExistingUser.DisplayName = DisplayName
        ExistingUser.AvatarHash  = AvatarHash
        ExistingUser.Role        = AssignedPrimaryRole
        ExistingUser.Roles       = AssignedRoles
        TargetUser = ExistingUser

    else:
        NewUser = User.User(
            DiscordIdentifier = DiscordID,
            Username = Username,
            DisplayName = DisplayName,
            AvatarHash = AvatarHash,
            Role = AssignedPrimaryRole,
            Roles = AssignedRoles
        )
        DatabaseSession.add(NewUser)
        TargetUser = NewUser

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetUser)
    SessionToken: str = JWTManager.CreateAccessToken({
        "sub": TargetUser.Identifier,
        "role": TargetUser.Role.value,
        "roles": TargetUser.Roles,
        "in_guild": IsInGuild
    })
    if IsInGuild:
        RedirectURL: str = "/?Authenticated=True"

    else:
        RedirectURL: str = "/?Authenticated=True&NotInGuild=True"

    Response = Responses.RedirectResponse(url = RedirectURL, status_code = FastAPI.status.HTTP_303_SEE_OTHER)
    Response.set_cookie(key = "SessionToken", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax", path = "/")
    Response.set_cookie(key = "session_token", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax", path = "/")
    Response.delete_cookie(key = "OAuthState", path = "/")
    Response.delete_cookie(key = "oauth_state", path = "/")
    DebugService.LogDebugMessage(f"OAuth Session Established: User='{TargetUser.Identifier}', Redirect='{RedirectURL}'")
    return Response

@Router.get("/Discord/Callback")
async def DiscordCallback(
    Request: FastAPI.Request,
    Code: Typing.Optional[str] = FastAPI.Query(default = None, alias = "code"),
    State: Typing.Optional[str] = FastAPI.Query(default = None, alias = "state"),
    GuildIdentifier: Typing.Optional[str] = FastAPI.Query(default = None, alias = "guild_id"),
    Permissions: Typing.Optional[str] = FastAPI.Query(default = None, alias = "permissions"),
    Error: Typing.Optional[str] = FastAPI.Query(default = None, alias = "error"),
    ErrorDescription: Typing.Optional[str] = FastAPI.Query(default = None, alias = "error_description"),
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.Response:
    DebugService.LogDebugMessage("OAuth Router: /Discord/Callback")
    return await HandleDiscordCallback(
        Request = Request,
        Code = Code,
        State = State,
        GuildIdentifier = GuildIdentifier,
        Permissions = Permissions,
        Error = Error,
        ErrorDescription = ErrorDescription,
        DatabaseSession = DatabaseSession
    )

@AuthenticationCallbackRouter.get("/API/Authentication")
async def DiscordAuthenticationRootCallback(
    Request: FastAPI.Request,
    Code: Typing.Optional[str] = FastAPI.Query(default = None, alias = "code"),
    State: Typing.Optional[str] = FastAPI.Query(default = None, alias = "state"),
    GuildIdentifier: Typing.Optional[str] = FastAPI.Query(default = None, alias = "guild_id"),
    Permissions: Typing.Optional[str] = FastAPI.Query(default = None, alias = "permissions"),
    Error: Typing.Optional[str] = FastAPI.Query(default = None, alias = "error"),
    ErrorDescription: Typing.Optional[str] = FastAPI.Query(default = None, alias = "error_description"),
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.Response:
    DebugService.LogDebugMessage("OAuth Router: /API/Authentication")
    return await HandleDiscordCallback(
        Request = Request,
        Code = Code,
        State = State,
        GuildIdentifier = GuildIdentifier,
        Permissions = Permissions,
        Error = Error,
        ErrorDescription = ErrorDescription,
        DatabaseSession = DatabaseSession
    )

@Router.post("/DevLogin/Partial", response_class = Responses.HTMLResponse)
async def DevLoginPartial(Role: User.UserRole, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    if Role == User.UserRole.Visitor:
        DebugService.LogDebugMessage("Dev Login: Role Switched To Visitor")
        Response = Responses.HTMLResponse(content = "Visitor")
        Response.delete_cookie(key = "SessionToken")
        Response.delete_cookie(key = "session_token")
        return Response

    DevRolesMapping: Typing.Dict[User.UserRole, Typing.List[str]] = {
        User.UserRole.Administrator: [
            "Administrator"
        ],
        User.UserRole.GameMaster: [
            "Story Manager (DND5thEdition)",
            "Story Manager (Traveller2ndEdition)"
        ],
        User.UserRole.Checker: [
            "Sheet Checker (DND5thEdition)",
            "Sheet Checker (Traveller2ndEdition)"
        ],
        User.UserRole.NormalUser: [
            "Character Owner (DND5thEdition)",
            "Character Owner (Traveller2ndEdition)"
        ]
    }
    DevRoles: Typing.List[str] = DevRolesMapping.get(Role, [])
    DiscordID: str = f"Dev_{Role.value}_Persisted"
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.DiscordIdentifier == DiscordID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetUser: Typing.Optional[User.User] = QueryResult.scalars().first()
    if not TargetUser:
        TargetUser = User.User(
            DiscordIdentifier = DiscordID,
            Username = f"{Role.value}User",
            DisplayName = f"{Role.value} Operator",
            Role = Role,
            Roles = DevRoles
        )
        DatabaseSession.add(TargetUser)

    else:
        TargetUser.Role = Role
        TargetUser.Roles = DevRoles

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetUser)
    SessionToken: str = JWTManager.CreateAccessToken({
        "sub": TargetUser.Identifier,
        "role": TargetUser.Role.value,
        "roles": TargetUser.Roles,
        "in_guild": True
    })
    Response = Responses.HTMLResponse(content = TargetUser.Role.value)
    Response.set_cookie(key = "SessionToken", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax", path = "/")
    Response.set_cookie(key = "session_token", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax", path = "/")
    DebugService.LogDebugMessage(f"Dev Login Established: User='{TargetUser.Username}', Role='{TargetUser.Role.value}', ID='{TargetUser.Identifier}'")
    return Response

@Router.get("/Me/Partial", response_class = Responses.HTMLResponse)
async def GetCurrentUserRolePartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    if not CurrentUser:
        DebugService.LogDebugMessage("Served Role Partial: Visitor")
        return Responses.HTMLResponse(content = "Visitor")

    OutputRole: str = ", ".join(CurrentUser.Roles) if CurrentUser.Roles else CurrentUser.Role.value
    DebugService.LogDebugMessage(f"Served Role Partial: User='{CurrentUser.Identifier}', Role='{OutputRole}'")
    return Responses.HTMLResponse(content = OutputRole)

@Router.post("/Logout")
async def Logout() -> Responses.Response:
    DebugService.LogDebugMessage("User Logout Completed: Session Cookies Cleared")
    Response = Responses.JSONResponse(content = {
        "Status": "LoggedOut"
    })
    Response.delete_cookie(key = "SessionToken", path = "/")
    Response.delete_cookie(key = "session_token", path = "/")
    Response.delete_cookie(key = "OAuthState", path = "/")
    Response.delete_cookie(key = "oauth_state", path = "/")
    return Response

@Router.get("/Session/Status", response_class = Responses.JSONResponse)
async def GetSessionStatus(Request: FastAPI.Request, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    if not CurrentUser:
        DebugService.LogDebugMessage("Session Status Served: Unauthenticated Visitor")
        return Responses.JSONResponse(content = {
            "IsAuthenticated": False,
            "Username": None,
            "DisplayName": None,
            "AvatarURL": None,
            "Role": User.UserRole.Visitor.value,
            "Roles": [],
            "IsInGuild": False,
            "DiscordInviteURL": Config.GLOBAL_SETTINGS.DISCORD_INVITE_URL
        })

    AvatarURL: Typing.Optional[str] = None
    if CurrentUser.AvatarHash and CurrentUser.DiscordIdentifier:
        AvatarURL = f"https://cdn.discordapp.com/avatars/{CurrentUser.DiscordIdentifier}/{CurrentUser.AvatarHash}.png?size=64"

    elif CurrentUser.DiscordIdentifier:
        AvatarURL = "https://cdn.discordapp.com/embed/avatars/0.png"

    SessionTokenString: Typing.Optional[str] = Request.cookies.get("SessionToken") or Request.cookies.get("session_token")
    TokenPayload: Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(SessionTokenString) if SessionTokenString else None
    IsInGuild: bool = bool(TokenPayload.get("in_guild", False)) if TokenPayload else False
    if CurrentUser.Role == User.UserRole.Administrator or (CurrentUser.Roles and len(CurrentUser.Roles) > 0):
        IsInGuild = True

    DebugService.LogDebugMessage(f"Session Status Served: User='{CurrentUser.Identifier}', Role='{CurrentUser.Role.value}', InGuild={IsInGuild}")
    return Responses.JSONResponse(content = {
        "IsAuthenticated": True,
        "Username": CurrentUser.Username,
        "DisplayName": CurrentUser.DisplayName,
        "AvatarURL": AvatarURL,
        "Role": CurrentUser.Role.value,
        "Roles": CurrentUser.Roles if CurrentUser.Roles is not None else [],
        "IsInGuild": IsInGuild,
        "DiscordInviteURL": Config.GLOBAL_SETTINGS.DISCORD_INVITE_URL
    })

@Router.post("/GuestLogin", response_class = Responses.JSONResponse)
async def PerformGuestLogin() -> Responses.Response:
    DebugService.LogDebugMessage("Guest Login Established: Role=Visitor")
    Response = Responses.JSONResponse(content = {
        "Status": "GuestAuthenticated",
        "Role": User.UserRole.Visitor.value
    })
    Response.delete_cookie(key = "SessionToken", path = "/")
    Response.delete_cookie(key = "session_token", path = "/")
    return Response
