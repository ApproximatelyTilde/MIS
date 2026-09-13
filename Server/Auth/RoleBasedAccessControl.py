import fastapi                 as FastAPI
import sqlalchemy              as SQLAlchemy
import sqlalchemy.ext.asyncio  as AsyncIO
import typing                  as Typing
import Server.Auth.JWTManager  as JWTManager
import Server.Database         as Database
import Server.Models.Character as Character
import Server.Models.Story     as Story
import Server.Models.User      as User

async def GetCurrentUser(Request: FastAPI.Request, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Optional[User.User]:
    Token: Typing.Optional[str] = Request.cookies.get("SessionToken") or Request.cookies.get("session_token")
    if not Token:
        AuthorizationHeader: Typing.Optional[str] = Request.headers.get("Authorization")
        if AuthorizationHeader and AuthorizationHeader.startswith("Bearer "):
            Token = AuthorizationHeader[7:]

    if not Token:
        return None

    Payload: Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(Token)
    if not Payload or "sub" not in Payload:
        return None

    UserIdentifier: str = Payload["sub"]
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.Identifier == UserIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    FoundUser: Typing.Optional[User.User] = QueryResult.scalars().first()
    return FoundUser

async def RequireAuthenticatedUser(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(GetCurrentUser)) -> User.User:
    if not CurrentUser:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Authentication required")

    return CurrentUser

def HasUserRole(UserRecord: Typing.Optional[User.User], RoleName: str) -> bool:
    if not UserRecord or not UserRecord.Roles:
        return False

    return RoleName in UserRecord.Roles

def CanViewCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    if not UserRecord:
        return TargetCharacter.IsPublic

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    if HasUserRole(UserRecord, f"Sheet Checker ({TargetCharacter.GameSystem.value})"):
        return True

    if TargetCharacter.IsPublic:
        return True

    return TargetCharacter.OwnerIdentifier == UserRecord.Identifier

def CanCreateCharacter(UserRecord: Typing.Optional[User.User], TargetGameSystem: Typing.Optional[Character.GameSystemType] = None) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role in (User.UserRole.Checker, User.UserRole.GameMaster, User.UserRole.Administrator) or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetGameSystem:
        SystemName: str = TargetGameSystem.value
        return (
            HasUserRole(UserRecord, f"Character Owner ({SystemName})") or
            HasUserRole(UserRecord, f"Sheet Checker ({SystemName})") or
            HasUserRole(UserRecord, f"Story Manager ({SystemName})")
        )

    if UserRecord.Roles:
        for AssignedRole in UserRecord.Roles:
            if "Character Owner" in AssignedRole or "Sheet Checker" in AssignedRole or "Story Manager" in AssignedRole:
                return True

    return False

def CanModifyCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if UserRecord.Role == User.UserRole.Checker or HasUserRole(UserRecord, f"Sheet Checker ({TargetCharacter.GameSystem.value})"):
        return True

    if TargetCharacter.OwnerIdentifier == UserRecord.Identifier:
        if UserRecord.Role == User.UserRole.NormalUser or HasUserRole(UserRecord, f"Character Owner ({TargetCharacter.GameSystem.value})"):
            return True

        if not UserRecord.Roles:
            return True

    return False

def CanArchiveCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetCharacter.OwnerIdentifier == UserRecord.Identifier:
        return True

    return False

def CanViewStory(UserRecord: Typing.Optional[User.User], TargetStory: Story.Story, IsMember: bool = False) -> bool:
    if not UserRecord:
        return TargetStory.IsPublic

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetStory.GameSystem.value})"):
        return True

    if TargetStory.IsPublic or IsMember:
        return True

    return TargetStory.GameMasterIdentifier == UserRecord.Identifier

def CanCreateStory(UserRecord: Typing.Optional[User.User], TargetGameSystem: Typing.Optional[Character.GameSystemType] = None) -> bool:
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
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetStory.GameMasterIdentifier == UserRecord.Identifier:
        if UserRecord.Role == User.UserRole.GameMaster or HasUserRole(UserRecord, f"Story Manager ({TargetStory.GameSystem.value})"):
            return True

        if not UserRecord.Roles:
            return True

    return False

def CanArchiveStory(UserRecord: Typing.Optional[User.User], TargetStory: Story.Story) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetStory.GameMasterIdentifier == UserRecord.Identifier:
        return True

    return False

def CanCommitTransaction(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    if not UserRecord:
        return False

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    return TargetCharacter.OwnerIdentifier == UserRecord.Identifier
