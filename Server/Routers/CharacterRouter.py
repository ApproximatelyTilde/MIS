import json                                       as JSON
import re                                         as RegularExpressions
import typing                                     as Typing
import fastapi                                    as FastAPI
import fastapi.responses                          as Responses
import pydantic                                   as Pydantic
import sqlalchemy                                 as SQLAlchemy
import sqlalchemy.ext.asyncio                     as AsyncIO
import Server.Auth.RoleBasedAccessControl         as RoleBasedAccessControl
import Server.Database                            as Database
import Server.Models.Character                    as Character
import Server.Models.StorageFile                  as StorageFile
import Server.Models.User                         as User
import Server.Services                            as Services
import Server.Services.CharacterGeneratorService  as CharacterGenerator
import Server.Services.DebugService               as DebugService
import Server.Services.ImageProcessingService     as ImageProcessingService
import Server.Services.OracleStorageService       as OracleStorage
import Server.Services.TemplateRendererService   as TemplateRenderer
import Server.Services.External5ETools             as External5ETools

Router = FastAPI.APIRouter(prefix = "/API/Characters", tags = ["Characters"])
FiveEToolsService: External5ETools.External5ETools = External5ETools.External5ETools()

@Router.get("/Rules/Classes", response_class = Responses.JSONResponse)
async def GetClassRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    RulesSummary: Typing.Dict[str, Typing.Any] = FiveEToolsService.GetClassRulesSummary()
    DebugService.LogDebugMessage(f"Served Class Rules: {len(RulesSummary)} Classes")
    return Responses.JSONResponse(content = RulesSummary)

@Router.get("/Rules/SpellcastingAbility", response_class = Responses.JSONResponse)
async def GetClassSpellcastingAbilityRule(ClassName: str, SubclassName: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ResolvedAbility: Typing.Optional[str] = FiveEToolsService.GetCanonicalSpellcastingAbility(ClassName, SubclassName)
    DebugService.LogDebugMessage(f"Spellcasting Rule Served: Class='{ClassName}', Subclass='{SubclassName}', Ability='{ResolvedAbility or 'None'}'")
    return Responses.JSONResponse(content = {
        "ClassName": ClassName,
        "SubclassName": SubclassName,
        "SpellcastingAbility": ResolvedAbility or "None"
    })

class CharacterCreateRequest(Pydantic.BaseModel):
    Name                 : str
    GameSystem           : Character.GameSystemType
    IsPublic             : bool = True
    IsAccepted           : bool = False
    SummaryData          : Typing.Dict[str, Typing.Any] = Pydantic.Field(default_factory = dict)
    DetailData           : Typing.Dict[str, Typing.Any] = Pydantic.Field(default_factory = dict)
    TargetOwnerIdentifier: Typing.Optional[str]         = None

class CharacterUpdateRequest(Pydantic.BaseModel):
    Name       : Typing.Optional[str]                          = None
    IsPublic   : Typing.Optional[bool]                         = None
    IsAccepted : Typing.Optional[bool]                         = None
    SummaryData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    DetailData : Typing.Optional[Typing.Dict[str, Typing.Any]] = None

@Router.get("/Partial", response_class = Responses.HTMLResponse)
async def ListCharactersPartial(SearchQuery: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character)
    if SearchQuery and SearchQuery.strip():
        NormalizedSearchTerm: str = f"%{SearchQuery.strip()}%"
        QueryStatement = QueryStatement.where(Character.Character.Name.ilike(NormalizedSearchTerm))

    QueryStatement = QueryStatement.order_by(Character.Character.IsPinned.desc(), Character.Character.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    AllCharacters = QueryResult.scalars().all()
    AccessibleCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for CharacterRecord in AllCharacters:
        if RoleBasedAccessControl.CanViewCharacter(CurrentUser, CharacterRecord):
            Summary = CharacterRecord.SummaryData or {}
            DetailsText: str = f"Class: {Summary.get('Class', 'Adventurer')} | Level {Summary.get('Level', 1)} | HP: {Summary.get('HitPoints', 10)}" if (CharacterRecord.GameSystem == Character.GameSystemType.DND5thEdition) else f"Career: {Summary.get('Career', 'Citizen')} | Terms: {Summary.get('Terms', 1)} | Homeworld: {Summary.get('Homeworld', 'Core')}"
            FirstName: str = CharacterRecord.Name.strip().split()[0] if CharacterRecord.Name and CharacterRecord.Name.strip() else ""
            AccessibleCharacters.append({
                "Character"  : CharacterRecord,
                "FirstName"  : FirstName,
                "DetailsText": DetailsText,
                "CanModify"  : RoleBasedAccessControl.CanModifyCharacter(CurrentUser, CharacterRecord),
                "CanArchive" : RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, CharacterRecord)
            })

    DebugService.LogDebugMessage(f"Characters Partial Rendered: {len(AccessibleCharacters)} Accessible (Total={len(AllCharacters)}, Search='{SearchQuery or ''}', User={getattr(CurrentUser, 'Identifier', None)})")
    TemplateContext: Typing.Dict[str, Typing.Any] = {
        "Characters" : AccessibleCharacters,
        "SearchQuery": SearchQuery or ""
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterListPartial.html", TemplateContext)

@Router.post("/{CharacterIdentifier}/Pin/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterPinPartial(CharacterIdentifier: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.Identifier == CharacterIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogDebugMessage(f"Pin Failed: Character '{CharacterIdentifier}' Not Found (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter):
        DebugService.LogDebugMessage(f"Pin Forbidden: Character '{CharacterIdentifier}' (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to modify this character")

    if TargetCharacter.IsArchived and not TargetCharacter.IsPinned:
        DebugService.LogDebugMessage(f"Pin Rejected: Character '{CharacterIdentifier}' Is Archived")
        raise FastAPI.HTTPException(status_code = 400, detail = "Archived characters cannot be pinned")

    if not TargetCharacter.IsPinned:
        CountStatement = SQLAlchemy.select(SQLAlchemy.func.count(Character.Character.Identifier)).where(
            Character.Character.OwnerIdentifier == TargetCharacter.OwnerIdentifier,
            Character.Character.IsPinned == True
        )
        CountResult = await DatabaseSession.execute(CountStatement)
        PinnedCount: int = CountResult.scalar() or 0
        if PinnedCount >= 6:
            DebugService.LogDebugMessage(f"Pin Limit Exceeded: Owner='{TargetCharacter.OwnerIdentifier}' Already Has {PinnedCount}/6 Pinned")
            raise FastAPI.HTTPException(status_code = 400, detail = "Maximum of six pinned characters allowed")

        TargetCharacter.IsPinned = True
    else:
        TargetCharacter.IsPinned = False

    await DatabaseSession.commit()
    DebugService.LogDebugMessage(f"Pin Toggled: Char='{CharacterIdentifier}', Pinned={TargetCharacter.IsPinned}, User='{CurrentUser.Identifier}'")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.post("/{CharacterIdentifier}/Visibility/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterVisibilityPartial(CharacterIdentifier: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.Identifier == CharacterIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogDebugMessage(f"Visibility Toggle Failed: Character '{CharacterIdentifier}' Not Found (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter):
        DebugService.LogDebugMessage(f"Visibility Toggle Forbidden: Character '{CharacterIdentifier}' (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to modify this character")

    TargetCharacter.IsPublic = not TargetCharacter.IsPublic
    await DatabaseSession.commit()
    DebugService.LogDebugMessage(f"Visibility Toggled: Char='{CharacterIdentifier}', Public={TargetCharacter.IsPublic}, User='{CurrentUser.Identifier}'")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.post("/{CharacterIdentifier}/Archive/Partial", response_class = Responses.HTMLResponse)
async def ArchiveCharacterPartial(CharacterIdentifier: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.Identifier == CharacterIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogDebugMessage(f"Archive Failed: Character '{CharacterIdentifier}' Not Found (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, TargetCharacter):
        DebugService.LogDebugMessage(f"Archive Forbidden: Character '{CharacterIdentifier}' (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to archive this character")

    if TargetCharacter.IsPinned and not TargetCharacter.IsArchived:
        DebugService.LogDebugMessage(f"Archive Rejected: Character '{CharacterIdentifier}' Is Pinned")
        raise FastAPI.HTTPException(status_code = 400, detail = "Pinned characters cannot be archived")

    TargetCharacter.IsArchived = not TargetCharacter.IsArchived
    await DatabaseSession.commit()
    DebugService.LogDebugMessage(f"Archive Toggled: Char='{CharacterIdentifier}', Archived={TargetCharacter.IsArchived}, User='{CurrentUser.Identifier}'")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.get("")
async def ListCharacters(GameSystem: Typing.Optional[Character.GameSystemType] = None, ShowArchived: bool = False, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.List[Typing.Dict[str, Typing.Any]]:
    QueryStatement = SQLAlchemy.select(Character.Character)
    if GameSystem:
        QueryStatement = QueryStatement.where(Character.Character.GameSystem == GameSystem)

    if not ShowArchived:
        QueryStatement = QueryStatement.where(Character.Character.IsArchived == False)

    QueryStatement = QueryStatement.order_by(Character.Character.IsPinned.desc(), Character.Character.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    AllCharacters = QueryResult.scalars().all()
    VisibleCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for Char in AllCharacters:
        if RoleBasedAccessControl.CanViewCharacter(CurrentUser, Char):
            VisibleCharacters.append({"Identifier": Char.Identifier, "OwnerIdentifier": Char.OwnerIdentifier, "Name": Char.Name, "GameSystem": Char.GameSystem.value, "IsPublic": Char.IsPublic, "IsArchived": Char.IsArchived, "IsPinned": Char.IsPinned, "IsAccepted": Char.IsAccepted, "SummaryData": Char.SummaryData, "DetailData": Char.DetailData, "CanModify": RoleBasedAccessControl.CanModifyCharacter(CurrentUser, Char), "CanArchive": RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, Char), "CreatedAt": Char.CreatedAt.isoformat(), "UpdatedAt": Char.UpdatedAt.isoformat()})

    DebugService.LogDebugMessage(f"Characters JSON Listed: {len(VisibleCharacters)} Visible (Total={len(AllCharacters)}, System={GameSystem}, Archived={ShowArchived}, User={getattr(CurrentUser, 'Identifier', None)})")
    return VisibleCharacters

@Router.post("")
async def CreateCharacter(RequestPayload: CharacterCreateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser):
        DebugService.LogDebugMessage(f"Character Creation Forbidden: User='{CurrentUser.Identifier}', System={RequestPayload.GameSystem.value}")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to create characters")

    OwnerID: str = RequestPayload.TargetOwnerIdentifier if (RequestPayload.TargetOwnerIdentifier and CurrentUser.Role in (User.UserRole.GameMaster, User.UserRole.Administrator)) else CurrentUser.Identifier
    NewCharacter = Character.Character(OwnerIdentifier = OwnerID, Name = RequestPayload.Name, GameSystem = RequestPayload.GameSystem, IsPublic = RequestPayload.IsPublic, IsAccepted = RequestPayload.IsAccepted, SummaryData = RequestPayload.SummaryData, DetailData = RequestPayload.DetailData)
    DatabaseSession.add(NewCharacter)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewCharacter)
    DebugService.LogDebugMessage(f"Character Created: ID='{NewCharacter.Identifier}', Name='{NewCharacter.Name}', System={NewCharacter.GameSystem.value}, Owner='{NewCharacter.OwnerIdentifier}'")
    ResultDictionary: Typing.Dict[str, Typing.Any] = {
        "Identifier"     : NewCharacter.Identifier,
        "OwnerIdentifier": NewCharacter.OwnerIdentifier,
        "Name"           : NewCharacter.Name,
        "GameSystem"     : NewCharacter.GameSystem.value,
        "IsPublic"       : NewCharacter.IsPublic,
        "IsArchived"     : NewCharacter.IsArchived,
        "IsAccepted"     : NewCharacter.IsAccepted,
        "SummaryData"    : NewCharacter.SummaryData,
        "DetailData"     : NewCharacter.DetailData
    }
    return ResultDictionary

@Router.post("/Portrait/Upload/Partial", response_class = Responses.HTMLResponse)
async def UploadCharacterPortraitPartial(File: FastAPI.UploadFile = FastAPI.File(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not RoleBasedAccessControl.IsUserInGuild(CurrentUser):
        DebugService.LogDebugMessage(f"Portrait Upload Rejected: User '{CurrentUser.Identifier}' Not In Guild")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Discord server membership required")

    RawBytes: bytes = await File.read()
    SanitizedBytes, ContentType = ImageProcessingService.GLOBAL_IMAGE_PROCESSING_SERVICE.SanitizeAndOptimizeImage(RawBytes, File.filename or "portrait.jpg")
    FileSizeBytes: int = len(SanitizedBytes)
    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        DebugService.LogDebugMessage(f"Portrait Upload Rejected: Quota Exceeded (User='{CurrentUser.Identifier}', Needed={FileSizeBytes}B)")
        raise FastAPI.HTTPException(status_code = 400, detail = "Storage quota exceeded")

    OriginalFileName: str = File.filename or "portrait.jpg"
    ObjectKey: Typing.Optional[str] = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, OriginalFileName, ContentType, SanitizedBytes)
    if not ObjectKey:
        DebugService.LogDebugMessage(f"Portrait Storage Failed: Provider Error (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 500, detail = "Storage provider error during portrait upload")

    NewStorageFile = StorageFile.StorageFile(
        OwnerIdentifier = CurrentUser.Identifier,
        FileName = OriginalFileName,
        ContentType = ContentType,
        FileSizeBytes = FileSizeBytes,
        ObjectKey = ObjectKey
    )
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewStorageFile)
    DebugService.LogDebugMessage(f"Portrait Upload Succeeded: File='{NewStorageFile.Identifier}', Size={FileSizeBytes}B, User='{CurrentUser.Identifier}'")

    Context: Typing.Dict[str, Typing.Any] = {
        "PortraitFileIdentifier": NewStorageFile.Identifier
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterPortraitPartial.html", Context, Headers = {"HX-Trigger": "portraitSelected"})

@Router.post("/Portrait/Select/Partial", response_class = Responses.HTMLResponse)
async def SelectCharacterPortraitPartial(FileIdentifier: str = FastAPI.Form(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(
        StorageFile.StorageFile.Identifier == FileIdentifier,
        StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier
    )
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogDebugMessage(f"Portrait Selection Failed: File '{FileIdentifier}' Not Found (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    DebugService.LogDebugMessage(f"Portrait Selected: File='{TargetFile.Identifier}', User='{CurrentUser.Identifier}'")
    Context: Typing.Dict[str, Typing.Any] = {
        "PortraitFileIdentifier": TargetFile.Identifier
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterPortraitPartial.html", Context, Headers = {"HX-Trigger": "portraitSelected"})

@Router.post("/Manual/Partial", response_class = Responses.HTMLResponse)
async def CreateCharacterManualPartial(
    Request: FastAPI.Request,
    CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser),
    DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)
) -> Responses.HTMLResponse:
    FormData = await Request.form()
    GameSystemValue: str = str(FormData.get("GameSystem") or "DND5thEdition")
    try:
        GameSystem: Character.GameSystemType = Character.GameSystemType(GameSystemValue)
    except Exception:
        GameSystem = Character.GameSystemType.DND5thEdition

    Name: str = str(FormData.get("Name") or "").strip()
    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser, GameSystem):
        DebugService.LogDebugMessage(f"Manual Character Creation Forbidden: User='{CurrentUser.Identifier}', System={GameSystem.value}")
        raise FastAPI.HTTPException(status_code = 403, detail = "Permission denied")

    PlayerName: Typing.Optional[str] = FormData.get("PlayerName")
    PortraitFileIdentifier: Typing.Optional[str] = FormData.get("PortraitFileIdentifier")
    HitPoints: int = int(FormData.get("HitPoints", 10) or 10)
    ArmorClass: int = int(FormData.get("ArmorClass", 10) or 10)
    Speed: int = int(FormData.get("Speed", 30) or 30)
    IsPublic: bool = str(FormData.get("IsPublic", "true")).lower() in ["true", "1", "on"]
    Alignment: Typing.Optional[str] = FormData.get("Alignment")
    Faith: Typing.Optional[str] = FormData.get("Faith")
    Lifestyle: Typing.Optional[str] = FormData.get("Lifestyle")
    Inspiration: bool = str(FormData.get("Inspiration", "false")).lower() in ["true", "1", "on"]
    Species: Typing.Optional[str] = FormData.get("Species")
    Subrace: Typing.Optional[str] = FormData.get("Subrace")
    Background: Typing.Optional[str] = FormData.get("Background")
    Languages: Typing.Optional[str] = FormData.get("Languages")
    Strength: int = int(FormData.get("Strength", 10) or 10)
    Dexterity: int = int(FormData.get("Dexterity", 10) or 10)
    Constitution: int = int(FormData.get("Constitution", 10) or 10)
    Intelligence: int = int(FormData.get("Intelligence", 10) or 10)
    Wisdom: int = int(FormData.get("Wisdom", 10) or 10)
    Charisma: int = int(FormData.get("Charisma", 10) or 10)
    Features: Typing.Optional[str] = FormData.get("Features")
    PersonalityTraits: Typing.Optional[str] = FormData.get("PersonalityTraits")
    Ideals: Typing.Optional[str] = FormData.get("Ideals")
    Bonds: Typing.Optional[str] = FormData.get("Bonds")
    Flaws: Typing.Optional[str] = FormData.get("Flaws")
    Age: Typing.Optional[str] = FormData.get("Age")
    Height: Typing.Optional[str] = FormData.get("Height")
    Weight: Typing.Optional[str] = FormData.get("Weight")
    Backstory: Typing.Optional[str] = FormData.get("Backstory")

    ClassPattern = RegularExpressions.compile(r"^Classes\[(\d+)\]\.?(\w+)$")
    SpellListPattern = RegularExpressions.compile(r"^SpellLists\[(\d+)\]\.?(\w+)$")
    SpellSlotPattern = RegularExpressions.compile(r"^SpellSlots\[(\d+)\]\.?(\w+)$")

    ClassEntriesDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
    }
    SpellListsDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
    }
    SpellSlotsDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
    }

    for FieldKey, FieldValue in FormData.items():
        ClassMatch = ClassPattern.match(FieldKey)
        if ClassMatch:
            ClassIndex: int = int(ClassMatch.group(1))
            ClassProperty: str = ClassMatch.group(2)
            if ClassIndex not in ClassEntriesDictionary:
                ClassEntriesDictionary[ClassIndex] = {
                }
            ClassEntriesDictionary[ClassIndex][ClassProperty] = FieldValue
            continue

        SpellListMatch = SpellListPattern.match(FieldKey)
        if SpellListMatch:
            ListIndex: int = int(SpellListMatch.group(1))
            ListProperty: str = SpellListMatch.group(2)
            if ListIndex not in SpellListsDictionary:
                SpellListsDictionary[ListIndex] = {
                }
            SpellListsDictionary[ListIndex][ListProperty] = FieldValue
            continue

        SpellSlotMatch = SpellSlotPattern.match(FieldKey)
        if SpellSlotMatch:
            SlotIndex: int = int(SpellSlotMatch.group(1))
            SlotProperty: str = SpellSlotMatch.group(2)
            if SlotIndex not in SpellSlotsDictionary:
                SpellSlotsDictionary[SlotIndex] = {
                }
            SpellSlotsDictionary[SlotIndex][SlotProperty] = FieldValue
            continue

    SummaryData: Typing.Dict[str, Typing.Any] = {
    }
    DetailData: Typing.Dict[str, Typing.Any] = {
    }

    if GameSystem == Character.GameSystemType.DND5thEdition:
        ClassesList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        if ClassEntriesDictionary:
            SortedIndices = sorted(ClassEntriesDictionary.keys())
            HasInitialClassAssigned: bool = False
            for IndexItem in SortedIndices:
                EntryData = ClassEntriesDictionary[IndexItem]
                EntryClassName: str = str(EntryData.get("ClassName") or "").strip() or "Adventurer"
                EntrySubclass: Typing.Optional[str] = str(EntryData.get("Subclass") or "").strip() or None
                EntryLevel: int = int(EntryData.get("Level", 1) or 1)
                EntryExperience: int = int(EntryData.get("Experience", 0) or 0)
                IsInitialRaw = EntryData.get("IsInitialClass", False)
                EntryIsInitial: bool = str(IsInitialRaw).lower() in ["true", "1", "on"]
                if EntryIsInitial and not HasInitialClassAssigned:
                    HasInitialClassAssigned = True
                elif EntryIsInitial and HasInitialClassAssigned:
                    EntryIsInitial = False

                ClassHitDie: int = Services.GLOBAL_5E_TOOLS.GetClassHitDie(EntryClassName) or 8
                ClassesList.append({
                    "ClassName": EntryClassName,
                    "Level": EntryLevel,
                    "SubclassName": EntrySubclass,
                    "HitDie": ClassHitDie,
                    "HitDiceTotal": EntryLevel,
                    "HitDiceUsed": 0,
                    "IsStartingClass": EntryIsInitial,
                    "ExperiencePoints": EntryExperience
                })

            if ClassesList and not any(ClassItem["IsStartingClass"] for ClassItem in ClassesList):
                ClassesList[0]["IsStartingClass"] = True
        else:
            FlatClassName: str = str(FormData.get("ClassOrCareer") or "Adventurer").strip()
            FlatSubclass: Typing.Optional[str] = FormData.get("Subclass")
            FlatLevel: int = int(FormData.get("LevelOrTerms", 1) or 1)
            FlatExperience: int = int(FormData.get("ExperiencePoints", 0) or 0)
            FlatHitDie: int = Services.GLOBAL_5E_TOOLS.GetClassHitDie(FlatClassName) or 8
            ClassesList.append({
                "ClassName": FlatClassName,
                "Level": FlatLevel,
                "SubclassName": FlatSubclass,
                "HitDie": FlatHitDie,
                "HitDiceTotal": FlatLevel,
                "HitDiceUsed": 0,
                "IsStartingClass": True,
                "ExperiencePoints": FlatExperience
            })

        InitialClassItem = next((ClassItem for ClassItem in ClassesList if ClassItem["IsStartingClass"]), ClassesList[0])
        InitialClassName: str = InitialClassItem["ClassName"]
        TotalCharacterLevel: int = sum(ClassItem["Level"] for ClassItem in ClassesList)
        TotalExperiencePoints: int = sum(ClassItem["ExperiencePoints"] for ClassItem in ClassesList)

        BoundedCharacterLevel: int = max(1, min(20, TotalCharacterLevel))
        ProficiencyBonus: int = 2 + ((BoundedCharacterLevel - 1) // 4)

        SpellcastingEntriesList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        SpellsList: Typing.List[Typing.Dict[str, Typing.Any]] = []

        if SpellListsDictionary:
            for ListIndex in sorted(SpellListsDictionary.keys()):
                SpellListData = SpellListsDictionary[ListIndex]
                SpellListName: str = str(SpellListData.get("Name") or "").strip()
                SpellListAbility: Typing.Optional[str] = str(SpellListData.get("Ability") or "").strip() or None
                SpellListSpellsRaw: str = str(SpellListData.get("Spells") or "").strip()

                if SpellListAbility and SpellListAbility.lower() != "none":
                    AbilityScoreValue: int = 10
                    if SpellListAbility.lower() == "intelligence":
                        AbilityScoreValue = Intelligence
                    elif SpellListAbility.lower() == "wisdom":
                        AbilityScoreValue = Wisdom
                    elif SpellListAbility.lower() == "charisma":
                        AbilityScoreValue = Charisma
                    elif SpellListAbility.lower() == "strength":
                        AbilityScoreValue = Strength
                    elif SpellListAbility.lower() == "dexterity":
                        AbilityScoreValue = Dexterity
                    elif SpellListAbility.lower() == "constitution":
                        AbilityScoreValue = Constitution

                    AbilityModifierValue: int = (AbilityScoreValue - 10) // 2
                    SpellcastingEntriesList.append({
                        "SpellcastingClass": SpellListName or InitialClassName,
                        "SpellcastingAbility": SpellListAbility,
                        "SpellSaveDC": 8 + ProficiencyBonus + AbilityModifierValue,
                        "SpellAttackBonus": ProficiencyBonus + AbilityModifierValue
                    })

                if SpellListSpellsRaw:
                    for RawSpellItem in RegularExpressions.split(r"[,\n]", SpellListSpellsRaw):
                        SpellNameCandidate: str = RawSpellItem.strip()
                        if SpellNameCandidate:
                            IsCantripList: bool = "cantrip" in SpellListName.lower()
                            IsSpellbookList: bool = "spellbook" in SpellListName.lower()
                            SpellsList.append({
                                "Identifier": SpellNameCandidate.lower().replace(" ", "-"),
                                "Name": SpellNameCandidate,
                                "Level": 0 if IsCantripList else 1,
                                "School": "Universal",
                                "CastingTime": "1 Action",
                                "RangeDescription": "Self",
                                "DurationDescription": "Instantaneous",
                                "IsPrepared": False if IsSpellbookList else True,
                                "SourceType": "SpellList",
                                "SourceName": SpellListName or "Spells"
                            })
        else:
            FlatSpellClass = FormData.get("SpellcastingClass")
            FlatSpellAbility = FormData.get("SpellcastingAbility")
            FlatSpells = FormData.get("Spells")
            if FlatSpellClass and FlatSpellAbility:
                IntelligenceModifier = (Intelligence - 10) // 2
                SpellcastingEntriesList.append({
                    "SpellcastingClass": FlatSpellClass,
                    "SpellcastingAbility": FlatSpellAbility,
                    "SpellSaveDC": 8 + ProficiencyBonus + IntelligenceModifier,
                    "SpellAttackBonus": ProficiencyBonus + IntelligenceModifier
                })
            if FlatSpells:
                for FlatSpellItem in FlatSpells.split(","):
                    CleanSpellName = FlatSpellItem.strip()
                    if CleanSpellName:
                        SpellsList.append({
                            "Identifier": CleanSpellName.lower().replace(" ", "-"),
                            "Name": CleanSpellName,
                            "Level": 1,
                            "School": "Universal",
                            "CastingTime": "1 Action",
                            "RangeDescription": "Self",
                            "DurationDescription": "Instantaneous",
                            "IsPrepared": True,
                            "SourceType": "Class",
                            "SourceName": FlatSpellClass or InitialClassName
                        })

        SpellSlotsList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        if SpellSlotsDictionary:
            for SlotIndex in sorted(SpellSlotsDictionary.keys()):
                SlotData = SpellSlotsDictionary[SlotIndex]
                SlotLevel: int = int(SlotData.get("Level", SlotIndex) or SlotIndex)
                SlotTotal: int = int(SlotData.get("Total", 0) or 0)
                SlotUsed: int = int(SlotData.get("Used", 0) or 0)
                if SlotTotal > 0:
                    SpellSlotsList.append({
                        "Level": SlotLevel,
                        "TotalSlots": SlotTotal,
                        "UsedSlots": SlotUsed,
                        "AvailableSlots": max(0, SlotTotal - SlotUsed)
                    })
        else:
            ProgressionTuples = [(ClassEntry["ClassName"], ClassEntry["Level"], ClassEntry["SubclassName"]) for ClassEntry in ClassesList]
            ComputedSlots = Services.GLOBAL_5E_TOOLS.CalculateMulticlassSpellSlots(ProgressionTuples)
            for SlotLevelNumber, SlotCountNumber in ComputedSlots:
                SpellSlotsList.append({
                    "Level": SlotLevelNumber,
                    "TotalSlots": SlotCountNumber,
                    "UsedSlots": 0,
                    "AvailableSlots": SlotCountNumber
                })

        WarlockLevelSum: int = sum(
            ClassEntry["Level"] for ClassEntry in ClassesList
            if (Services.GLOBAL_5E_TOOLS.FindCanonicalClassName(ClassEntry["ClassName"]) or ClassEntry["ClassName"]).lower() == "warlock"
        )
        PactMagicDictionary: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
        if WarlockLevelSum > 0:
            PactSlotInformation = Services.GLOBAL_5E_TOOLS.CalculatePactMagicSlots(WarlockLevelSum)
            if PactSlotInformation:
                RawPactUsed = FormData.get("PactMagic.UsedSlots")
                PactUsedCount: int = min(PactSlotInformation[1], max(0, int(RawPactUsed or 0))) if RawPactUsed is not None else 0
                PactMagicDictionary = {
                    "SlotLevel": PactSlotInformation[0],
                    "TotalSlots": PactSlotInformation[1],
                    "UsedSlots": PactUsedCount,
                    "AvailableSlots": max(0, PactSlotInformation[1] - PactUsedCount)
                }

        FeaturesList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        if Features:
            for RawFeatureItem in RegularExpressions.split(r"[,\n]", Features):
                CleanFeature = RawFeatureItem.strip()
                if CleanFeature:
                    FeaturesList.append({
                        "Identifier": CleanFeature.lower().replace(" ", "-"),
                        "Name": CleanFeature,
                        "SourceType": "Class",
                        "SourceName": InitialClassName
                    })

        SummaryData = {
            "Class": InitialClassName,
            "Level": TotalCharacterLevel,
            "HitPoints": HitPoints,
            "Species": Species or "Human",
            "PortraitFileIdentifier": PortraitFileIdentifier
        }
        DetailData = {
            "SchemaVersion": "1.0.0",
            "GameSystem": "DND5thEdition",
            "OriginalSource": "MIS",
            "Name": Name,
            "PlayerName": PlayerName,
            "Alignment": Alignment,
            "Faith": Faith,
            "Lifestyle": Lifestyle,
            "TotalLevel": TotalCharacterLevel,
            "ExperiencePoints": TotalExperiencePoints,
            "Inspiration": Inspiration,
            "Species": {
                "RaceName": Species or "Human",
                "SubraceName": Subrace,
                "FullName": f"{Subrace} {Species}".strip() if (Subrace and Species) else (Species or "Human"),
                "Modifiers": []
            },
            "Background": {
                "Name": Background or "Folk Hero",
                "Modifiers": []
            },
            "Classes": ClassesList,
            "AbilityScores": {
                "Strength": {"BaseScore": Strength, "BonusScore": 0, "TotalScore": Strength, "Modifier": (Strength - 10) // 2},
                "Dexterity": {"BaseScore": Dexterity, "BonusScore": 0, "TotalScore": Dexterity, "Modifier": (Dexterity - 10) // 2},
                "Constitution": {"BaseScore": Constitution, "BonusScore": 0, "TotalScore": Constitution, "Modifier": (Constitution - 10) // 2},
                "Intelligence": {"BaseScore": Intelligence, "BonusScore": 0, "TotalScore": Intelligence, "Modifier": (Intelligence - 10) // 2},
                "Wisdom": {"BaseScore": Wisdom, "BonusScore": 0, "TotalScore": Wisdom, "Modifier": (Wisdom - 10) // 2},
                "Charisma": {"BaseScore": Charisma, "BonusScore": 0, "TotalScore": Charisma, "Modifier": (Charisma - 10) // 2}
            },
            "HitPoints": {
                "MaxHitPoints": HitPoints,
                "CurrentHitPoints": HitPoints,
                "TemporaryHitPoints": 0,
                "BaseHitPoints": HitPoints,
                "BonusHitPoints": 0
            },
            "ArmorClass": {
                "BaseArmorClass": ArmorClass,
                "TotalArmorClass": ArmorClass
            },
            "Speed": {
                "WalkingSpeedFeet": Speed
            },
            "LanguageProficiencies": [LanguageItem.strip() for LanguageItem in Languages.split(",") if LanguageItem.strip()] if Languages else [],
            "Spellcasting": {
                "SpellcastingEntries": SpellcastingEntriesList,
                "SpellSlots": SpellSlotsList,
                "PactMagic": PactMagicDictionary,
                "Spells": SpellsList
            },
            "Features": FeaturesList,
            "Personality": {
                "PersonalityTraits": PersonalityTraits,
                "Ideals": Ideals,
                "Bonds": Bonds,
                "Flaws": Flaws
            },
            "PhysicalAppearance": {
                "Age": Age,
                "Height": Height,
                "Weight": Weight,
                "PortraitFileIdentifier": PortraitFileIdentifier
            },
            "Notes": {
                "Backstory": Backstory
            }
        }
    else:
        CareerName: str = str(FormData.get("ClassOrCareer") or "Citizen").strip()
        TermsCount: int = int(FormData.get("LevelOrTerms", 1) or 1)
        SummaryData = {
            "Career": CareerName,
            "Terms": TermsCount,
            "Homeworld": "Core",
            "PortraitFileIdentifier": PortraitFileIdentifier
        }
        DetailData = {
            "Name": Name,
            "GameSystem": GameSystem.value,
            "Career": CareerName,
            "Terms": TermsCount,
            "PortraitFileIdentifier": PortraitFileIdentifier
        }

    NewCharacter = Character.Character(OwnerIdentifier = CurrentUser.Identifier, Name = Name, GameSystem = GameSystem, IsPublic = IsPublic, IsAccepted = False, SummaryData = SummaryData, DetailData = DetailData)
    DatabaseSession.add(NewCharacter)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewCharacter)
    DebugService.LogDebugMessage(f"Manual Character Created: ID='{NewCharacter.Identifier}', Name='{NewCharacter.Name}', System={NewCharacter.GameSystem.value}, User='{CurrentUser.Identifier}'")
    Context: Typing.Dict[str, Typing.Any] = {
        "IsSuccess": True,
        "CharacterName": NewCharacter.Name,
        "GameSystem": NewCharacter.GameSystem.value
    }
    ResponseHeaders: Typing.Dict[str, str] = {
        "HX-Trigger": JSON.dumps({"characterSaved": {"CharacterName": NewCharacter.Name}})
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)
