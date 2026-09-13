import fastapi                      as FastAPI
import sqlalchemy                   as SQLAlchemy
import sqlalchemy.ext.asyncio       as AsyncIO
import typing                       as Typing
import Server.Auth.JWTManager       as JWTManager
import Server.Database              as Database
import Server.Models.Character      as Character
import Server.Models.Story          as Story
import Server.Models.User           as User
import Server.Services.DebugService as Debug

async def GetCurrentUser(Request: FastAPI.Request, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Optional[User.User]:
    Token: Typing.Optional[str] = Request.cookies.get("SessionToken")
    if not Token:
        AuthorizationHeader: Typing.Optional[str] = Request.headers.get("Authorization")
        if AuthorizationHeader and AuthorizationHeader.startswith("Bearer "):
            Token = AuthorizationHeader[7:]

    if not Token:
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"No Session Token Provided on Route: \"{Request.url.path}\"")
        return None

    Payload: Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(Token)
    if not Payload or "sub" not in Payload:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Invalid Session Claims on Route: \"{Request.url.path}\"")
        return None

    UserID: str = Payload["sub"]
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.ID == UserID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    FoundUser: Typing.Optional[User.User] = QueryResult.scalars().first()
    if FoundUser:
        FoundUser.IsInGuild = bool(Payload.get("in_guild", False))
        if FoundUser.Role == User.UserRole.Administrator or (FoundUser.Roles and len(FoundUser.Roles) > 0):
            FoundUser.IsInGuild = True

    return FoundUser

async def RequireAuthenticatedUser(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(GetCurrentUser)) -> User.User:
    if not CurrentUser:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Authentication Required: Anonymous Access Attempt Denied")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Authentication required")

    return CurrentUser

def IsUserInGuild(UserRecord: Typing.Optional[User.User]) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Visitor:
        return False

    if getattr(UserRecord, "IsInGuild", None) is not None:
        return bool(UserRecord.IsInGuild)

    if UserRecord.Role == User.UserRole.Administrator:
        return True

    if UserRecord.Roles and len(UserRecord.Roles) > 0:
        return True

    return False

def IsGameMaster(UserRecord: Typing.Optional[User.User]) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster):
        return True

    if HasUserRole(UserRecord, "Administrator") or HasUserRole(UserRecord, "GameMaster"):
        return True

    if UserRecord.Roles:
        for AssignedRole in UserRecord.Roles:
            if "Story Manager" in AssignedRole:
                return True

    return False

async def RequireGuildMember(CurrentUser: User.User = FastAPI.Depends(RequireAuthenticatedUser)) -> User.User:
    if not IsUserInGuild(CurrentUser):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Guild Member Gate Denied: User \"{CurrentUser.ID[:8]}…\" Not in Guild")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Discord server membership required")

    return CurrentUser

def HasUserRole(UserRecord: Typing.Optional[User.User], RoleName: str) -> bool:
    if not UserRecord or not UserRecord.Roles:
        return False

    return RoleName in UserRecord.Roles

def CanViewCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating View Permission: Character=\"{TargetCharacter.ID[:8]}…\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return TargetCharacter.IsPublic and not TargetCharacter.IsArchived

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetCharacter.OwnerID == UserRecord.ID:
        return True

    if TargetCharacter.IsArchived:
        return False

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    if HasUserRole(UserRecord, f"Sheet Checker ({TargetCharacter.GameSystem.value})"):
        return True

    return TargetCharacter.IsPublic

def CanCreateCharacter(UserRecord: Typing.Optional[User.User], TargetGameSystem: Typing.Optional[Character.GameSystemType] = None) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Creation Permission: System=\"{TargetGameSystem}\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Visitor:
        return False

    if not IsUserInGuild(UserRecord):
        return False

    return True

def CanModifyCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Modification for Character \"{TargetCharacter.ID[:8]}…\" and User \"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if UserRecord.Role == User.UserRole.Checker or HasUserRole(UserRecord, f"Sheet Checker ({TargetCharacter.GameSystem.value})"):
        return True

    if TargetCharacter.OwnerID == UserRecord.ID:
        if UserRecord.Role == User.UserRole.NormalUser or HasUserRole(UserRecord, f"Character Owner ({TargetCharacter.GameSystem.value})"):
            return True

        if not UserRecord.Roles:
            return True

    return False

def CanArchiveCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Archive Permission: Character=\"{TargetCharacter.ID[:8]}…\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetCharacter.OwnerID == UserRecord.ID:
        return True

    return False

def CanProtectCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Typing.Optional[Character.Character] = None) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Protection Permission: Character=\"{getattr(TargetCharacter, "ID", "None")[:8]}…\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if (UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster)) or HasUserRole(UserRecord, "Administrator") or HasUserRole(UserRecord, "GameMaster"):
        return True

    if TargetCharacter and (TargetCharacter.OwnerID == UserRecord.ID):
        return True

    if not TargetCharacter:
        return True

    return False

def CanOverrideCharacter(UserRecord: Typing.Optional[User.User]) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Override Permission for User: ID=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if (UserRecord.Role == User.UserRole.Administrator) or HasUserRole(UserRecord, "Administrator"):
        return True

    return False

def CanViewStory(UserRecord: Typing.Optional[User.User], TargetStory: Story.Story, IsMember: bool = False) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating View Permission: Story=\"{TargetStory.ID[:8]}…\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return TargetStory.IsPublic

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetStory.GameSystem.value})"):
        return True

    if TargetStory.IsPublic or IsMember:
        return True

    return TargetStory.GameMasterID == UserRecord.ID

def CanCreateStory(UserRecord: Typing.Optional[User.User], TargetGameSystem: Typing.Optional[Character.GameSystemType] = None) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Creation Permission: System=\"{TargetGameSystem}\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role in (User.UserRole.GameMaster, User.UserRole.Administrator) or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetGameSystem:
        return HasUserRole(UserRecord, f"Story Manager ({TargetGameSystem.value})")

    if UserRecord.Roles:
        for AssignedRole in UserRecord.Roles:
            if "Story Manager" in AssignedRole:
                return True

    return False

def CanModifyStory(UserRecord: Typing.Optional[User.User], TargetStory: Story.Story) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Modification Permission: Story=\"{TargetStory.ID[:8]}…\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetStory.GameMasterID == UserRecord.ID:
        if UserRecord.Role == User.UserRole.GameMaster or HasUserRole(UserRecord, f"Story Manager ({TargetStory.GameSystem.value})"):
            return True

        if not UserRecord.Roles:
            return True

    return False

def CanArchiveStory(UserRecord: Typing.Optional[User.User], TargetStory: Story.Story) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Archive Permission: Story=\"{TargetStory.ID[:8]}…\", User=\"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetStory.GameMasterID == UserRecord.ID:
        return True

    return False

def CanCommitTransaction(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluating Transaction for Character \"{TargetCharacter.ID[:8]}…\" and User \"{getattr(UserRecord, "ID", "Anonymous")}\"")
    if not UserRecord:
        return False

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    return TargetCharacter.OwnerID == UserRecord.ID

def IsServiceContext(CallerContext: Typing.Any) -> bool:
    if isinstance(CallerContext, dict):
        return (CallerContext.get("sub") == "Tally") or (CallerContext.get("role") == "Administrator")

    return False

def CanTransferCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character, IsOwnerChange: bool) -> bool:
    if not UserRecord:
        return False

    if (UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster)) or HasUserRole(UserRecord, "Administrator") or HasUserRole(UserRecord, "GameMaster"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    if IsOwnerChange:
        return False

    return CanModifyCharacter(UserRecord, TargetCharacter)

async def RequireServiceToken(Request: FastAPI.Request) -> Typing.Dict[str, Typing.Any]:
    AuthorizationHeader: Typing.Optional[str] = Request.headers.get("Authorization")
    if (AuthorizationHeader is None) or (not AuthorizationHeader.startswith("Bearer ")):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Service Token Missing on Route: \"{Request.url.path}\"")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Bearer service token required")

    Token: str = AuthorizationHeader[7:].strip()
    Payload: Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(Token)
    if (Payload is None) or ("sub" not in Payload):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Invalid Service Token on Route: \"{Request.url.path}\"")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Invalid or expired service token")

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Service Token Validated: Subject=\"{Payload.get("sub")}\"")
    return Payload

async def GetOptionalServiceOrUser(Request: FastAPI.Request, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Union[User.User, Typing.Dict[str, Typing.Any], None]:
    AuthorizationHeader: Typing.Optional[str] = Request.headers.get("Authorization")
    if AuthorizationHeader and AuthorizationHeader.startswith("Bearer "):
        Token: str = AuthorizationHeader[7:].strip()
        Payload: Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(Token)
        if Payload and ("sub" in Payload):
            if (Payload.get("sub") == "Tally") or (Payload.get("role") == "Administrator"):
                Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Authorized via Service Token: Subject=\"{Payload.get("sub")}\"")
                return Payload

    return await GetCurrentUser(Request = Request, DatabaseSession = DatabaseSession)

async def RequireServiceOrAuthenticatedUser(Request: FastAPI.Request, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Union[User.User, Typing.Dict[str, Typing.Any]]:
    ResolvedContext: Typing.Union[User.User, Typing.Dict[str, Typing.Any], None] = await GetOptionalServiceOrUser(Request = Request, DatabaseSession = DatabaseSession)
    if (ResolvedContext is not None):
        return ResolvedContext

    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Service or User Authentication Denied on Route: \"{Request.url.path}\"")
    raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Authentication required")
