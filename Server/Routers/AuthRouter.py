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
    DebugService.LogDebugMessage("Initiating Discord OAuth Login Flow")
    StateToken  : str = str(UniversallyUniqueIdentifier.uuid4())
    AuthorizeURL: str = DiscordOAuth.GenerateDiscordAuthorizeURL(StateToken)
    Response = Responses.RedirectResponse(url = AuthorizeURL)
    Response.set_cookie(key = "OAuthState", value = StateToken, httponly = True, max_age = 600, samesite = "lax")
    return Response

async def HandleDiscordCallback(
    Request: FastAPI.Request,
    Code: Typing.Optional[str] = None,
    State: Typing.Optional[str] = None,
    GuildIdentifier: Typing.Optional[str] = FastAPI.Query(default = None, alias = "guild_id"),
    Permissions: Typing.Optional[str] = None,
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.Response:
    DebugService.LogDebugMessage(f"Handling Discord OAuth Callback With Code: {Code}, State: {State}, Guild Identifier: {GuildIdentifier}, Permissions: {Permissions}")
    if GuildIdentifier and Permissions and not Code:
        DebugService.LogDebugMessage("Bot Authorization Flow Succeeded Without Code Parameter")
        return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

    if not Code:
        if GuildIdentifier and Permissions:
            DebugService.LogDebugMessage("Bot Authorization Succeeded Without Code")
            return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

        DebugService.LogDebugMessage("OAuth Callback Failed: Missing Authorization Code")
        return Responses.RedirectResponse(url = "/?Error=OAuthMissingCode", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

    StoredOAuthState: Typing.Optional[str] = Request.cookies.get("OAuthState") or Request.cookies.get("oauth_state")
    if not StoredOAuthState or not State or StoredOAuthState != State:
        if GuildIdentifier and Permissions:
            DebugService.LogDebugMessage("Bot Authorization State Fallback Permitted")
            return Responses.RedirectResponse(url = "/?BotAuthorized=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)

        DebugService.LogDebugMessage("OAuth Callback Failed: CSRF State Verification Failed")
        CSRFErrorResponse = Responses.RedirectResponse(url = "/?Error=CSRFVerificationFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        CSRFErrorResponse.delete_cookie(key = "OAuthState")
        CSRFErrorResponse.delete_cookie(key = "oauth_state")
        return CSRFErrorResponse

    TokenData = await DiscordOAuth.ExchangeDiscordCode(Code)
    if not TokenData or "access_token" not in TokenData:
        DebugService.LogDebugMessage("OAuth Callback Failed: Token Exchange Failed")
        FailureResponse = Responses.RedirectResponse(url = "/?Error=OAuthFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        FailureResponse.delete_cookie(key = "OAuthState")
        FailureResponse.delete_cookie(key = "oauth_state")
        return FailureResponse

    AccessToken: str = TokenData["access_token"]
    UserProfile = await DiscordOAuth.FetchDiscordUserProfile(AccessToken)
    if not UserProfile or "id" not in UserProfile:
        DebugService.LogDebugMessage("OAuth Callback Failed: User Profile Fetch Failed")
        UserProfileErrorResponse = Responses.RedirectResponse(url = "/?Error=UserFetchFailed", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
        UserProfileErrorResponse.delete_cookie(key = "OAuthState")
        UserProfileErrorResponse.delete_cookie(key = "oauth_state")
        return UserProfileErrorResponse

    DiscordID  : str = UserProfile["id"]
    Username   : str = UserProfile.get("username", "Adventurer")
    DisplayName: str = UserProfile.get("global_name", Username)
    AvatarHash : Typing.Optional[str] = UserProfile.get("avatar")
    GuildMemberProfile = await DiscordOAuth.FetchDiscordGuildMemberProfile(AccessToken, DiscordID)
    AssignedRoles: Typing.List[str] = DiscordOAuth.DetermineUserRolesFromDiscordMember(GuildMemberProfile)
    AssignedPrimaryRole: User.UserRole = DiscordOAuth.DeterminePrimaryUserRole(AssignedRoles)
    DebugService.LogDebugMessage(f"Authenticated Discord User: {DiscordID} With Assigned Primary Role: {AssignedPrimaryRole.value}")
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
        "roles": TargetUser.Roles
    })
    Response = Responses.RedirectResponse(url = "/?Authenticated=True", status_code = FastAPI.status.HTTP_303_SEE_OTHER)
    Response.set_cookie(key = "SessionToken", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax")
    Response.delete_cookie(key = "OAuthState")
    Response.delete_cookie(key = "oauth_state")
    DebugService.LogDebugMessage(f"Successfully Created Session Cookie For User: {TargetUser.Identifier}")
    return Response

@Router.get("/Discord/Callback")
async def DiscordCallback(
    Request: FastAPI.Request,
    Code: Typing.Optional[str] = None,
    State: Typing.Optional[str] = None,
    GuildIdentifier: Typing.Optional[str] = FastAPI.Query(default = None, alias = "guild_id"),
    Permissions: Typing.Optional[str] = None,
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.Response:
    DebugService.LogDebugMessage("Routing Discord Callback Request")
    return await HandleDiscordCallback(
        Request = Request,
        Code = Code,
        State = State,
        GuildIdentifier = GuildIdentifier,
        Permissions = Permissions,
        DatabaseSession = DatabaseSession
    )

@AuthenticationCallbackRouter.get("/API/Authentication")
async def DiscordAuthenticationRootCallback(
    Request: FastAPI.Request,
    Code: Typing.Optional[str] = None,
    State: Typing.Optional[str] = None,
    GuildIdentifier: Typing.Optional[str] = FastAPI.Query(default = None, alias = "guild_id"),
    Permissions: Typing.Optional[str] = None,
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.Response:
    DebugService.LogDebugMessage("Routing Discord Authentication Root Callback Request")
    return await HandleDiscordCallback(
        Request = Request,
        Code = Code,
        State = State,
        GuildIdentifier = GuildIdentifier,
        Permissions = Permissions,
        DatabaseSession = DatabaseSession
    )

@Router.post("/DevLogin/Partial", response_class = Responses.HTMLResponse)
async def DevLoginPartial(Role: User.UserRole, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    DebugService.LogDebugMessage(f"Executing Development Login For Role: {Role.value}")
    if Role == User.UserRole.Visitor:
        DebugService.LogDebugMessage("Switched To Visitor Role In Development Login")
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
        "roles": TargetUser.Roles
    })
    Response = Responses.HTMLResponse(content = TargetUser.Role.value)
    Response.set_cookie(key = "SessionToken", value = SessionToken, httponly = True, max_age = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES * 60, samesite = "lax")
    DebugService.LogDebugMessage(f"Created Session Token For Dev User: {TargetUser.Username} With Role: {TargetUser.Role.value}")
    return Response

@Router.get("/Me/Partial", response_class = Responses.HTMLResponse)
async def GetCurrentUserRolePartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Retrieving Current User Role Partial For User: {getattr(CurrentUser, 'Identifier', None)}")
    if not CurrentUser:
        return Responses.HTMLResponse(content = "Visitor")

    if CurrentUser.Roles:
        return Responses.HTMLResponse(content = ", ".join(CurrentUser.Roles))

    return Responses.HTMLResponse(content = CurrentUser.Role.value)

@Router.post("/Logout")
async def Logout() -> Responses.Response:
    DebugService.LogDebugMessage("Executing User Logout And Clearing Cookies")
    Response = Responses.JSONResponse(content = {
        "Status": "LoggedOut"
    })
    Response.delete_cookie(key = "SessionToken")
    Response.delete_cookie(key = "session_token")
    return Response

@Router.get("/Session/Status", response_class = Responses.JSONResponse)
async def GetSessionStatus(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    DebugService.LogDebugMessage(f"Querying Session Status For User: {getattr(CurrentUser, 'Identifier', None)}")
    if not CurrentUser:
        return Responses.JSONResponse(content = {
            "IsAuthenticated": False,
            "Username": None,
            "DisplayName": None,
            "AvatarURL": None,
            "Role": User.UserRole.Visitor.value,
            "Roles": []
        })

    AvatarURL: Typing.Optional[str] = None
    if CurrentUser.AvatarHash and CurrentUser.DiscordIdentifier:
        AvatarURL = f"https://cdn.discordapp.com/avatars/{CurrentUser.DiscordIdentifier}/{CurrentUser.AvatarHash}.png?size=64"

    elif CurrentUser.DiscordIdentifier:
        AvatarURL = "https://cdn.discordapp.com/embed/avatars/0.png"

    return Responses.JSONResponse(content = {
        "IsAuthenticated": True,
        "Username": CurrentUser.Username,
        "DisplayName": CurrentUser.DisplayName,
        "AvatarURL": AvatarURL,
        "Role": CurrentUser.Role.value,
        "Roles": CurrentUser.Roles if CurrentUser.Roles is not None else []
    })

@Router.post("/GuestLogin", response_class = Responses.JSONResponse)
async def PerformGuestLogin() -> Responses.Response:
    DebugService.LogDebugMessage("Performing Guest Login")
    Response = Responses.JSONResponse(content = {
        "Status": "GuestAuthenticated",
        "Role": User.UserRole.Visitor.value
    })
    Response.delete_cookie(key = "SessionToken")
    Response.delete_cookie(key = "session_token")
    return Response
