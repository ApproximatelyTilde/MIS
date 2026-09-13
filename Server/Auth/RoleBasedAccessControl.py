import fastapi                         as FastAPI
import sqlalchemy                      as SQLAlchemy
import sqlalchemy.ext.asyncio          as AsyncIO
import typing                          as Typing
import Server.Auth.JWTManager          as JWTManager
import Server.Database                 as Database
import Server.Models.Character         as Character
import Server.Models.Story             as Story
import Server.Models.User              as User
import Server.Services.DebugService     as DebugService

async def GetCurrentUser(Request: FastAPI.Request, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Optional[User.User]:
    Token: Typing.Optional[str] = Request.cookies.get("SessionToken") or Request.cookies.get("session_token")
    if not Token:
        AuthorizationHeader: Typing.Optional[str] = Request.headers.get("Authorization")
        if AuthorizationHeader and AuthorizationHeader.startswith("Bearer "):
            Token = AuthorizationHeader[7:]

    if not Token:
        DebugService.LogDebugMessage(f"Auth: No Token on '{Request.url.path}'")
        return None

    Payload: Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(Token)
    if not Payload or "sub" not in Payload:
        DebugService.LogDebugMessage(f"Auth: Invalid Claims on '{Request.url.path}'")
        return None

    UserIdentifier: str = Payload["sub"]
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.Identifier == UserIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    FoundUser: Typing.Optional[User.User] = QueryResult.scalars().first()
    if FoundUser:
        FoundUser.IsInGuild = bool(Payload.get("in_guild", False))
        if FoundUser.Role == User.UserRole.Administrator or (FoundUser.Roles and len(FoundUser.Roles) > 0):
            FoundUser.IsInGuild = True

    DebugService.LogDebugMessage(f"Auth: User='{UserIdentifier}', DB={FoundUser is not None}, Guild={getattr(FoundUser, 'IsInGuild', False)}")
    return FoundUser

async def RequireAuthenticatedUser(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(GetCurrentUser)) -> User.User:
    if not CurrentUser:
        DebugService.LogDebugMessage("Auth Gate Denied: Anonymous Access Attempt")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Authentication required")

    return CurrentUser

def IsUserInGuild(UserRecord: Typing.Optional[User.User]) -> bool:
    DebugService.LogDebugMessage(f"Guild Check: User={getattr(UserRecord, 'Identifier', 'Anon')}")
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
    DebugService.LogDebugMessage(f"GameMaster Check: User={getattr(UserRecord, 'Identifier', 'Anon')}")
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
    DebugService.LogDebugMessage(f"Guild Gate: User={CurrentUser.Identifier}")
    if not IsUserInGuild(CurrentUser):
        DebugService.LogDebugMessage(f"Guild Gate Denied: User={CurrentUser.Identifier} Not In Guild")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Discord server membership required")

    return CurrentUser

def HasUserRole(UserRecord: Typing.Optional[User.User], RoleName: str) -> bool:
    DebugService.LogDebugMessage(f"Role Check [{RoleName}]: User={getattr(UserRecord, 'Identifier', 'Anon')}")
    if not UserRecord or not UserRecord.Roles:
        return False

    return RoleName in UserRecord.Roles

def CanViewCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    DebugService.LogDebugMessage(f"Permission [ViewCharacter]: Char={TargetCharacter.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
    if not UserRecord:
        return TargetCharacter.IsPublic and not TargetCharacter.IsArchived

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetCharacter.OwnerIdentifier == UserRecord.Identifier:
        return True

    if TargetCharacter.IsArchived:
        return False

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    if HasUserRole(UserRecord, f"Sheet Checker ({TargetCharacter.GameSystem.value})"):
        return True

    return TargetCharacter.IsPublic

def CanCreateCharacter(UserRecord: Typing.Optional[User.User], TargetGameSystem: Typing.Optional[Character.GameSystemType] = None) -> bool:
    DebugService.LogDebugMessage(f"Permission [CreateCharacter]: System={TargetGameSystem}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Visitor:
        return False

    if not IsUserInGuild(UserRecord):
        return False

    return True

def CanModifyCharacter(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    DebugService.LogDebugMessage(f"Permission [ModifyCharacter]: Char={TargetCharacter.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
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
    DebugService.LogDebugMessage(f"Permission [ArchiveCharacter]: Char={TargetCharacter.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetCharacter.OwnerIdentifier == UserRecord.Identifier:
        return True

    return False

def CanViewStory(UserRecord: Typing.Optional[User.User], TargetStory: Story.Story, IsMember: bool = False) -> bool:
    DebugService.LogDebugMessage(f"Permission [ViewStory]: Story={TargetStory.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
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
    DebugService.LogDebugMessage(f"Permission [CreateStory]: System={TargetGameSystem}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
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
    DebugService.LogDebugMessage(f"Permission [ModifyStory]: Story={TargetStory.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
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
    DebugService.LogDebugMessage(f"Permission [ArchiveStory]: Story={TargetStory.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
    if not UserRecord:
        return False

    if UserRecord.Role == User.UserRole.Administrator or HasUserRole(UserRecord, "Administrator"):
        return True

    if TargetStory.GameMasterIdentifier == UserRecord.Identifier:
        return True

    return False

def CanCommitTransaction(UserRecord: Typing.Optional[User.User], TargetCharacter: Character.Character) -> bool:
    DebugService.LogDebugMessage(f"Permission [CommitTransaction]: Char={TargetCharacter.Identifier}, User={getattr(UserRecord, 'Identifier', 'Anon')}")
    if not UserRecord:
        return False

    if UserRecord.Role in (User.UserRole.Administrator, User.UserRole.GameMaster) or HasUserRole(UserRecord, "Administrator"):
        return True

    if HasUserRole(UserRecord, f"Story Manager ({TargetCharacter.GameSystem.value})"):
        return True

    return TargetCharacter.OwnerIdentifier == UserRecord.Identifier
