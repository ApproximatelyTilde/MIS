import typing                                    as Typing
import fastapi                                   as FastAPI
import fastapi.responses                         as Responses
import pydantic                                  as Pydantic
import sqlalchemy                                as SQLAlchemy
import sqlalchemy.ext.asyncio                    as AsyncIO
import Server.Auth.RoleBasedAccessControl        as RoleBasedAccessControl
import Server.Database                           as Database
import Server.Models.Character                   as Character
import Server.Models.User                        as User
import Server.Services.CharacterGeneratorService as CharacterGenerator
import Server.Services.DebugService              as DebugService
import Server.Services.TemplateRendererService  as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Characters", tags = ["Characters"])

class CharacterCreateRequest(Pydantic.BaseModel):
    Name                 : str
    GameSystem           : Character.GameSystemType
    IsPublic             : bool = True
    SummaryData          : Typing.Dict[str, Typing.Any] = {}
    DetailData           : Typing.Dict[str, Typing.Any] = {}
    TargetOwnerIdentifier: Typing.Optional[str]         = None

class CharacterUpdateRequest(Pydantic.BaseModel):
    Name       : Typing.Optional[str]                          = None
    IsPublic   : Typing.Optional[bool]                         = None
    SummaryData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    DetailData : Typing.Optional[Typing.Dict[str, Typing.Any]] = None

@Router.get("/Partial", response_class = Responses.HTMLResponse)
async def ListCharactersPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Listing Characters Partial For User: {getattr(CurrentUser, 'Identifier', None)}")
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.IsArchived == False)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    AllCharacters = QueryResult.scalars().all()
    AccessibleCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for Char in AllCharacters:
        if RoleBasedAccessControl.CanViewCharacter(CurrentUser, Char):
            Summary = Char.SummaryData or {}
            DetailsText: str = f"Class: {Summary.get('Class', 'Adventurer')} | Level {Summary.get('Level', 1)} | HP: {Summary.get('HitPoints', 10)}" if (Char.GameSystem == Character.GameSystemType.DND5thEdition) else f"Career: {Summary.get('Career', 'Citizen')} | Terms: {Summary.get('Terms', 1)} | Homeworld: {Summary.get('Homeworld', 'Core')}"
            AccessibleCharacters.append({
                "Character"  : Char,
                "DetailsText": DetailsText,
                "CanArchive" : RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, Char)
            })

    DebugService.LogDebugMessage(f"Rendered {len(AccessibleCharacters)} Accessible Characters In Partial")
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterListPartial.html", {"Characters": AccessibleCharacters})

@Router.post("/{CharacterIdentifier}/Archive/Partial", response_class = Responses.HTMLResponse)
async def ArchiveCharacterPartial(CharacterIdentifier: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Toggling Character Archive Status For Character: {CharacterIdentifier}, User: {CurrentUser.Identifier}")
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.Identifier == CharacterIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogDebugMessage(f"Character Not Found For Archiving: {CharacterIdentifier}")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, TargetCharacter):
        DebugService.LogDebugMessage(f"Permission Denied To Archive Character: {CharacterIdentifier}, User: {CurrentUser.Identifier}")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to archive this character")

    TargetCharacter.IsArchived = not TargetCharacter.IsArchived
    await DatabaseSession.commit()
    DebugService.LogDebugMessage(f"Updated Character Archive Status To: {TargetCharacter.IsArchived} For Character: {CharacterIdentifier}")
    return await ListCharactersPartial(CurrentUser, DatabaseSession)

@Router.get("")
async def ListCharacters(GameSystem: Typing.Optional[Character.GameSystemType] = None, ShowArchived: bool = False, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.List[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage(f"Listing JSON Characters For Game System: {GameSystem}, Show Archived: {ShowArchived}, User: {getattr(CurrentUser, 'Identifier', None)}")
    QueryStatement = SQLAlchemy.select(Character.Character)
    if GameSystem:
        QueryStatement = QueryStatement.where(Character.Character.GameSystem == GameSystem)

    if not ShowArchived:
        QueryStatement = QueryStatement.where(Character.Character.IsArchived == False)

    QueryResult = await DatabaseSession.execute(QueryStatement)
    AllCharacters = QueryResult.scalars().all()
    VisibleCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for Char in AllCharacters:
        if RoleBasedAccessControl.CanViewCharacter(CurrentUser, Char):
            VisibleCharacters.append({"Identifier": Char.Identifier, "OwnerIdentifier": Char.OwnerIdentifier, "Name": Char.Name, "GameSystem": Char.GameSystem.value, "IsPublic": Char.IsPublic, "IsArchived": Char.IsArchived, "SummaryData": Char.SummaryData, "DetailData": Char.DetailData, "CanModify": RoleBasedAccessControl.CanModifyCharacter(CurrentUser, Char), "CanArchive": RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, Char), "CreatedAt": Char.CreatedAt.isoformat(), "UpdatedAt": Char.UpdatedAt.isoformat()})

    DebugService.LogDebugMessage(f"Returning {len(VisibleCharacters)} Visible Characters In JSON Response")
    return VisibleCharacters

@Router.post("")
async def CreateCharacter(RequestPayload: CharacterCreateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    DebugService.LogDebugMessage(f"Creating Character For Game System: {RequestPayload.GameSystem.value}, Name: {RequestPayload.Name}, User: {CurrentUser.Identifier}")
    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser):
        DebugService.LogDebugMessage(f"Permission Denied To Create Character For User: {CurrentUser.Identifier}")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to create characters")

    OwnerID: str = RequestPayload.TargetOwnerIdentifier if (RequestPayload.TargetOwnerIdentifier and CurrentUser.Role in (User.UserRole.GameMaster, User.UserRole.Administrator)) else CurrentUser.Identifier
    NewCharacter = Character.Character(OwnerIdentifier = OwnerID, Name = RequestPayload.Name, GameSystem = RequestPayload.GameSystem, IsPublic = RequestPayload.IsPublic, SummaryData = RequestPayload.SummaryData, DetailData = RequestPayload.DetailData)
    DatabaseSession.add(NewCharacter)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewCharacter)
    DebugService.LogDebugMessage(f"Successfully Created Character With Identifier: {NewCharacter.Identifier}")
    ResultDictionary: Typing.Dict[str, Typing.Any] = {
        "Identifier"     : NewCharacter.Identifier,
        "OwnerIdentifier": NewCharacter.OwnerIdentifier,
        "Name"           : NewCharacter.Name,
        "GameSystem"     : NewCharacter.GameSystem.value,
        "IsPublic"       : NewCharacter.IsPublic,
        "IsArchived"     : NewCharacter.IsArchived,
        "SummaryData"    : NewCharacter.SummaryData,
        "DetailData"     : NewCharacter.DetailData
    }
    return ResultDictionary
