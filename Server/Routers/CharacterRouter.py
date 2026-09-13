import datetime                                  as DateTime
import json                                      as JSON
import re                                        as RegularExpressions
import typing                                    as Typing
import uuid                                      as UUID
import fastapi                                   as FastAPI
import fastapi.responses                         as Responses
import pydantic                                  as Pydantic
import sqlalchemy                                as SQLAlchemy
import sqlalchemy.ext.asyncio                    as AsyncIO
import sqlalchemy.orm.attributes                 as Attributes
import Server.Auth.RoleBasedAccessControl        as RoleBasedAccessControl
import Server.Database                           as Database
import Server.Models.AutomationModels             as AutomationModels
import Server.Models.Character                   as Character
import Server.Models.Mail                        as Mail
import Server.Models.StorageFile                 as StorageFile
import Server.Models.User                        as User
import Server.Services                           as Services
import Server.Services.AutomationService         as AutomationService
import Server.Services.CharacterGeneratorService as CharacterGenerator
import Server.Services.CharacterImportService    as CharacterImportService
import Server.Services.CharacterMappingService   as CharacterMappingService
import Server.Services.DebugService              as DebugService
import Server.Services.ImageProcessingService    as ImageProcessingService
import Server.Services.MailService               as MailService
import Server.Services.OracleStorageService      as OracleStorage
import Server.Services.TemplateRendererService   as TemplateRenderer
import Server.Services.External5ETools           as External5ETools

Router = FastAPI.APIRouter(prefix = "/API/Characters", tags = ["Characters"])
FiveEToolsService: External5ETools.External5ETools = External5ETools.External5ETools()

@Router.get("/Rules/Classes", response_class = Responses.JSONResponse)
async def GetClassRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    RulesSummary: Typing.Dict[str, Typing.Any] = FiveEToolsService.GetClassRulesSummary()
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Class Rules: Count={len(RulesSummary)}")
    return Responses.JSONResponse(content = RulesSummary)

@Router.get("/Rules/SpellcastingAbility", response_class = Responses.JSONResponse)
async def GetClassSpellcastingAbilityRule(ClassName: str, SubclassName: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ResolvedAbility: Typing.Optional[str] = FiveEToolsService.GetCanonicalSpellcastingAbility(ClassName, SubclassName)
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Spellcasting Rule: Class=\"{ClassName}\", Ability=\"{ResolvedAbility}\"")
    return Responses.JSONResponse(content = {"ClassName": ClassName, "SubclassName": SubclassName, "SpellcastingAbility": ResolvedAbility})

@Router.get("/Rules/DataStore", response_class = Responses.JSONResponse)
async def GetRulesDataStore(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    DataStoreDictionary: Typing.Dict[str, Typing.Any] = FiveEToolsService.GetRulesDataStore()
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Rules Data Store: System=\"{DataStoreDictionary.get("GameSystem")}\"")
    return Responses.JSONResponse(content = DataStoreDictionary)

@Router.get("/Rules/Cantrips", response_class = Responses.JSONResponse)
async def GetCantripsRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    CantripsList: Typing.List[str] = FiveEToolsService.GetCantripsList()
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Cantrips Rules: Count={len(CantripsList)}")
    return Responses.JSONResponse(content = CantripsList)

@Router.get("/Rules/EquipmentData", response_class = Responses.JSONResponse)
async def GetEquipmentRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    EquipmentData: Typing.Dict[str, Typing.Any] = FiveEToolsService.GetEquipmentRulesData()
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Equipment Rules: Items={len(EquipmentData.get("Weights", {}))}, Armors={len(EquipmentData.get("Armors", {}))}")
    return Responses.JSONResponse(content = EquipmentData)

@Router.get("/Rules/Spells/{SpellName}", response_class = Responses.JSONResponse)
async def GetSpellRule(SpellName: str, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    SpellRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = FiveEToolsService.GetSpellData(SpellName)
    if (SpellRecord is not None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Spell Rule: Name=\"{SpellName}\"")
        return Responses.JSONResponse(content = SpellRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Spell not found")

@Router.get("/Rules/Monsters/{MonsterName}", response_class = Responses.JSONResponse)
async def GetMonsterRule(MonsterName: str, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    MonsterRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = FiveEToolsService.GetMonsterData(MonsterName)
    if (MonsterRecord is not None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Monster Rule: Name=\"{MonsterName}\"")
        return Responses.JSONResponse(content = MonsterRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Monster not found")

@Router.get("/Rules/Items/{ItemName}", response_class = Responses.JSONResponse)
async def GetItemRule(ItemName: str, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ItemRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = FiveEToolsService.GetItemData(ItemName)
    if (ItemRecord is not None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Item Rule: Name=\"{ItemName}\"")
        return Responses.JSONResponse(content = ItemRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Item not found")

class CharacterCreateRequest(Pydantic.BaseModel):
    Name                 : str
    GameSystem           : Character.GameSystemType
    IsPublic             : bool                         = True
    IsAccepted   : bool                         = False
    IsProtected  : bool                         = False
    IsOverridden : bool                         = False
    ImportSource : Typing.Optional[str]         = None
    SummaryData  : Typing.Dict[str, Typing.Any] = Pydantic.Field(default_factory = dict)
    DetailData   : Typing.Dict[str, Typing.Any] = Pydantic.Field(default_factory = dict)
    TargetOwnerID: Typing.Optional[str]         = None

class CharacterUpdateRequest(Pydantic.BaseModel):
    Name        : Typing.Optional[str]                          = None
    IsPublic    : Typing.Optional[bool]                         = None
    IsAccepted  : Typing.Optional[bool]                         = None
    IsProtected : Typing.Optional[bool]                         = None
    IsOverridden: Typing.Optional[bool]                         = None
    ImportSource: Typing.Optional[str]                          = None
    SummaryData : Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    DetailData  : Typing.Optional[Typing.Dict[str, Typing.Any]] = None

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
            SummaryData   : Typing.Dict[str, Typing.Any] = CharacterRecord.SummaryData or {}
            GameSystemName: str                          = CharacterRecord.GameSystem.value if hasattr(CharacterRecord.GameSystem, "value") else str(CharacterRecord.GameSystem)
            FirstName     : str                          = CharacterRecord.Name.strip().split()[0] if (CharacterRecord.Name and CharacterRecord.Name.strip()) else ""

            CharacterClass    : str = ""
            CharacterSpecies  : str = ""
            CharacterLevel    : int = 1
            CharacterCareer   : str = ""
            CharacterHomeworld: str = ""
            CharacterTerms    : int = 1

            if CharacterRecord.GameSystem == Character.GameSystemType.DND5thEdition:
                CharacterClass   = str(SummaryData.get("Class", ""))
                CharacterSpecies = str(SummaryData.get("Species", ""))
                RawLevelValue    = SummaryData.get("Level")
                CharacterLevel   = int(RawLevelValue) if (RawLevelValue is not None) else 1

            elif CharacterRecord.GameSystem == Character.GameSystemType.Traveller2ndEdition:
                CharacterCareer    = str(SummaryData.get("Career", ""))
                CharacterHomeworld = str(SummaryData.get("Homeworld", ""))
                RawTermsValue      = SummaryData.get("Terms")
                CharacterTerms     = int(RawTermsValue) if (RawTermsValue is not None) else 1

            PortraitURL     : Typing.Optional[str] = SummaryData.get("PortraitURL")
            PortraitFileID  : Typing.Optional[str] = SummaryData.get("PortraitFileID")
            DefaultClass    : str                  = "Adventurer"
            DefaultCareer   : str                  = "Citizen"
            DefaultHomeworld: str                  = "Core"
            ClassDisplay    : str                  = CharacterClass or DefaultClass
            CareerDisplay   : str                  = CharacterCareer or DefaultCareer
            HomeworldDisplay: str                  = CharacterHomeworld or DefaultHomeworld
            HitPointsValue  : int                  = SummaryData.get("HitPoints", 10)
            DetailsText     : str                  = (f"Class: {ClassDisplay} | Level {CharacterLevel} | HP: {HitPointsValue}" if (CharacterRecord.GameSystem == Character.GameSystemType.DND5thEdition) else f"Career: {CareerDisplay} | Terms: {CharacterTerms} | Homeworld: {HomeworldDisplay}")

            CharacterEntry: Typing.Dict[str, Typing.Any] = {
                "Character"         : CharacterRecord,
                "GameSystemName"    : GameSystemName,
                "FirstName"         : FirstName,
                "CharacterClass"    : CharacterClass,
                "CharacterSpecies"  : CharacterSpecies,
                "CharacterLevel"    : CharacterLevel,
                "CharacterCareer"   : CharacterCareer,
                "CharacterHomeworld": CharacterHomeworld,
                "CharacterTerms"    : CharacterTerms,
                "PortraitURL"       : PortraitURL,
                "PortraitFileID"    : PortraitFileID,
                "DetailsText"       : DetailsText,
                "CanModify"         : RoleBasedAccessControl.CanModifyCharacter(CurrentUser, CharacterRecord),
                "CanArchive"        : RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, CharacterRecord)
            }
            AccessibleCharacters.append(CharacterEntry)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Characters Partial: {len(AccessibleCharacters)} of {len(AllCharacters)}")
    TemplateContext: Typing.Dict[str, Typing.Any] = {
        "Characters" : AccessibleCharacters,
        "SearchQuery": SearchQuery or ""
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterListPartial.html", TemplateContext)

@Router.get("/Search/Partial", response_class = Responses.HTMLResponse)
async def SearchCharactersPartial(SearchQuery: Typing.Optional[str] = None, SortBy: Typing.Optional[str] = "Name", SortOrder: Typing.Optional[str] = "Ascending", GameSystem: Typing.Optional[str] = "DND5thEdition", DNDClass: Typing.Optional[str] = None, DNDSpecies: Typing.Optional[str] = None, DNDLevelMin: Typing.Optional[int] = 1, DNDLevelMax: Typing.Optional[int] = 20, TravellerCareer: Typing.Optional[str] = None, TravellerHomeworld: Typing.Optional[str] = None, TravellerTermsMin: Typing.Optional[int] = 1, TravellerTermsMax: Typing.Optional[int] = 10, IncludePrivate: Typing.Optional[bool] = False, IncludeArchived: Typing.Optional[bool] = False, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character)
    if SearchQuery and SearchQuery.strip():
        NormalizedTerm: str = f"%{SearchQuery.strip()}%"
        QueryStatement = QueryStatement.where(Character.Character.Name.ilike(NormalizedTerm))

    if GameSystem and (GameSystem != "All"):
        QueryStatement = QueryStatement.where(Character.Character.GameSystem == GameSystem)

    QueryResult    = await DatabaseSession.execute(QueryStatement)
    AllCharacters  = QueryResult.scalars().all()
    IsElevatedUser: bool = RoleBasedAccessControl.IsGameMaster(CurrentUser)

    FilteredCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for CharacterRecord in AllCharacters:
        if not RoleBasedAccessControl.CanViewCharacter(CurrentUser, CharacterRecord):
            continue

        IsOwner: bool = (CurrentUser is not None) and (CharacterRecord.OwnerID == CurrentUser.ID)
        if not CharacterRecord.IsPublic:
            if (not IsOwner) and ((not IsElevatedUser) or (not IncludePrivate)):
                continue

        if CharacterRecord.IsArchived:
            if (not IsOwner) and ((not IsElevatedUser) or (not IncludeArchived)):
                continue

        SummaryData: Typing.Dict[str, Typing.Any] = CharacterRecord.SummaryData or {}
        GameSystemName: str = CharacterRecord.GameSystem.value if hasattr(CharacterRecord.GameSystem, "value") else str(CharacterRecord.GameSystem)
        LevelSortValue: int = 1

        CharacterClass     : str = ""
        CharacterSpecies   : str = ""
        CharacterLevel     : int = 1
        CharacterCareer    : str = ""
        CharacterHomeworld : str = ""
        CharacterTerms     : int = 1

        if CharacterRecord.GameSystem == Character.GameSystemType.DND5thEdition:
            CharacterClass = str(SummaryData.get("Class", ""))
            CharacterSpecies = str(SummaryData.get("Species", ""))
            RawLevelValue = SummaryData.get("Level")
            CharacterLevel = int(RawLevelValue) if (RawLevelValue is not None) else 1
            LevelSortValue = CharacterLevel

            if DNDClass and DNDClass.strip() and (CharacterClass != DNDClass):
                continue

            if DNDSpecies and DNDSpecies.strip() and (CharacterSpecies != DNDSpecies):
                continue

            if (DNDLevelMin is not None) and (CharacterLevel < DNDLevelMin):
                continue

            if (DNDLevelMax is not None) and (CharacterLevel > DNDLevelMax):
                continue

        elif CharacterRecord.GameSystem == Character.GameSystemType.Traveller2ndEdition:
            CharacterCareer     = str(SummaryData.get("Career", ""))
            CharacterHomeworld  = str(SummaryData.get("Homeworld", ""))
            RawTermsValue       = SummaryData.get("Terms")
            CharacterTerms      = int(RawTermsValue) if (RawTermsValue is not None) else 1
            LevelSortValue      = CharacterTerms

            if TravellerCareer and TravellerCareer.strip() and (CharacterCareer != TravellerCareer):
                continue

            if TravellerHomeworld and TravellerHomeworld.strip() and (CharacterHomeworld != TravellerHomeworld):
                continue

            if (TravellerTermsMin is not None) and (CharacterTerms < TravellerTermsMin):
                continue

            if (TravellerTermsMax is not None) and (CharacterTerms > TravellerTermsMax):
                continue

        PortraitURL            : Typing.Optional[str] = SummaryData.get("PortraitURL")
        PortraitFileID         : Typing.Optional[str] = SummaryData.get("PortraitFileID")
        ModifiedDateText       : str                  = CharacterRecord.UpdatedAt.strftime("%Y-%m-%d %H:%M") if CharacterRecord.UpdatedAt else ""

        CharacterEntry: dict[str, Typing.Any] = {
            "Character"         : CharacterRecord,
            "GameSystemName"    : GameSystemName,
            "CharacterClass"    : CharacterClass,
            "CharacterSpecies"  : CharacterSpecies,
            "CharacterLevel"    : CharacterLevel,
            "CharacterCareer"   : CharacterCareer,
            "CharacterHomeworld": CharacterHomeworld,
            "CharacterTerms"    : CharacterTerms,
            "PortraitURL"       : PortraitURL,
            "PortraitFileID"    : PortraitFileID,
            "ModifiedDateText"  : ModifiedDateText,
            "LevelSortValue"    : LevelSortValue
        }
        FilteredCharacters.append(CharacterEntry)

    IsDescending: bool = (SortOrder == "Descending")
    if SortBy == "Level":
        FilteredCharacters.sort(key = lambda Entry: Entry["LevelSortValue"], reverse = IsDescending)

    elif SortBy == "ModifiedAt":
        FilteredCharacters.sort(key = lambda Entry: Entry["Character"].UpdatedAt or Entry["Character"].CreatedAt or DateTime.datetime.min.replace(tzinfo = DateTime.timezone.utc), reverse = IsDescending)

    else:
        FilteredCharacters.sort(key = lambda Entry: (Entry["Character"].Name or "").lower(), reverse = IsDescending)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Search Characters: {len(FilteredCharacters)} Matches of {len(AllCharacters)}")
    TemplateContext: Typing.Dict[str, Typing.Any] = {
        "Characters": FilteredCharacters
    }
    return TemplateRenderer.RenderPartialResponse("Characters/SearchCharactersResultsPartial.html", TemplateContext)

@Router.post("/{CharacterID}/Pin/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterPinPartial(CharacterID: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Pin Failed: Character \"{CharacterID[:8]}…\" Not Found")
        Headers: Typing.Dict[str, str] = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Pin Forbidden for Character: \"{CharacterID[:8]}…\"")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if TargetCharacter.IsArchived and not TargetCharacter.IsPinned:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Pin Rejected: Character \"{CharacterID[:8]}…\" Is Archived")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Archived characters cannot be pinned."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not TargetCharacter.IsPinned:
        CountStatement = SQLAlchemy.select(SQLAlchemy.func.count(Character.Character.ID)).where(Character.Character.OwnerID == TargetCharacter.OwnerID, Character.Character.IsPinned == True)
        CountResult = await DatabaseSession.execute(CountStatement)
        PinnedCount: int = CountResult.scalar() or 0
        if PinnedCount >= 6:
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Pin Limit Exceeded: {PinnedCount} of 6 Characters Pinned")
            Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Maximum of six pinned characters allowed."}), "HX-Reswap": "none"}
            return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

        TargetCharacter.IsPinned = True

    else:
        TargetCharacter.IsPinned = False

    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Character Pin: ID=\"{CharacterID[:8]}…\", Pinned={TargetCharacter.IsPinned}")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.post("/{CharacterID}/Visibility/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterVisibilityPartial(CharacterID: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Visibility Toggle Failed: Character \"{CharacterID[:8]}…\" Not Found")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Visibility Toggle Forbidden for Character: \"{CharacterID[:8]}…\"")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    TargetCharacter.IsPublic = not TargetCharacter.IsPublic
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Character Visibility: ID=\"{CharacterID[:8]}…\", Public={TargetCharacter.IsPublic}")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.post("/{CharacterID}/Archive/Partial", response_class = Responses.HTMLResponse)
async def ArchiveCharacterPartial(CharacterID: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Archive Failed: Character \"{CharacterID[:8]}…\" Not Found")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, TargetCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Archive Forbidden for Character: \"{CharacterID[:8]}…\"")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to archive this character."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if TargetCharacter.IsPinned and not TargetCharacter.IsArchived:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Archive Rejected: Character \"{CharacterID[:8]}…\" Is Pinned")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Pinned characters cannot be archived. Unpin the character first."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    TargetCharacter.IsArchived = not TargetCharacter.IsArchived
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Character Archive: ID=\"{CharacterID[:8]}…\", Archived={TargetCharacter.IsArchived}")
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
            CreatedAtString: str = Char.CreatedAt.isoformat() if Char.CreatedAt else ""
            UpdatedAtString: str = Char.UpdatedAt.isoformat() if Char.UpdatedAt else CreatedAtString
            VisibleCharacters.append({"ID": Char.ID, "OwnerID": Char.OwnerID, "Name": Char.Name, "GameSystem": Char.GameSystem.value, "IsPublic": Char.IsPublic, "IsArchived": Char.IsArchived, "IsPinned": Char.IsPinned, "IsAccepted": Char.IsAccepted, "IsProtected": Char.IsProtected, "IsOverridden": Char.IsOverridden, "ImportSource": Char.ImportSource, "SummaryData": Char.SummaryData, "DetailData": Char.DetailData, "CanModify": RoleBasedAccessControl.CanModifyCharacter(CurrentUser, Char), "CanArchive": RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, Char), "CreatedAt": CreatedAtString, "UpdatedAt": UpdatedAtString})

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Listed Characters: {len(VisibleCharacters)} Visible of {len(AllCharacters)}")
    return VisibleCharacters

@Router.post("")
async def CreateCharacter(RequestPayload: CharacterCreateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Character Creation Forbidden: System=\"{RequestPayload.GameSystem.value}\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to create characters")

    OwnerID: str = RequestPayload.TargetOwnerID if (RequestPayload.TargetOwnerID and CurrentUser.Role in (User.UserRole.GameMaster, User.UserRole.Administrator)) else CurrentUser.ID
    IsProtectedValue: bool = True if ((RequestPayload.ImportSource == "DicecloudV1") or RequestPayload.IsProtected) else False
    NowTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.timezone.utc)
    NewCharacter = Character.Character(OwnerID = OwnerID, Name = RequestPayload.Name, GameSystem = RequestPayload.GameSystem, IsPublic = RequestPayload.IsPublic, IsAccepted = RequestPayload.IsAccepted, IsProtected = IsProtectedValue, IsOverridden = RequestPayload.IsOverridden, ImportSource = RequestPayload.ImportSource, SummaryData = RequestPayload.SummaryData, DetailData = RequestPayload.DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
    DatabaseSession.add(NewCharacter)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewCharacter)
    if not NewCharacter.IsAccepted:
        await MailService.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = NewCharacter.OwnerID, Subject = f"Character '{NewCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour character '{NewCharacter.Name}' ({NewCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = NewCharacter.ID)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created Character: \"{NewCharacter.Name}\" (ID=\"{NewCharacter.ID[:8]}…\")")
    ResultDictionary: Typing.Dict[str, Typing.Any] = {
        "ID"          : NewCharacter.ID,
        "OwnerID"     : NewCharacter.OwnerID,
        "Name"        : NewCharacter.Name,
        "GameSystem"  : NewCharacter.GameSystem.value,
        "IsPublic"    : NewCharacter.IsPublic,
        "IsArchived"  : NewCharacter.IsArchived,
        "IsAccepted"  : NewCharacter.IsAccepted,
        "IsProtected" : NewCharacter.IsProtected,
        "IsOverridden": NewCharacter.IsOverridden,
        "ImportSource": NewCharacter.ImportSource,
        "SummaryData" : NewCharacter.SummaryData,
        "DetailData"  : NewCharacter.DetailData
    }
    return ResultDictionary

@Router.post("/Portrait/Upload/Partial", response_class = Responses.HTMLResponse)
async def UploadCharacterPortraitPartial(File: FastAPI.UploadFile = FastAPI.File(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not RoleBasedAccessControl.IsUserInGuild(CurrentUser):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Portrait Upload Rejected: User \"{CurrentUser.ID[:8]}…\" Not in Guild")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Discord server membership required")

    RawBytes: bytes = await File.read()
    SanitizedBytes, ContentType = ImageProcessingService.GLOBAL_IMAGE_PROCESSING_SERVICE.SanitizeAndOptimizeImage(RawBytes, File.filename or "portrait.jpg")
    FileSizeBytes: int = len(SanitizedBytes)
    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Portrait Upload Rejected: Quota Exceeded ({FileSizeBytes}B Needed)")
        raise FastAPI.HTTPException(status_code = 400, detail = "Storage quota exceeded")

    OriginalFileName: str = File.filename or "portrait.jpg"
    ObjectKey: Typing.Optional[str] = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, OriginalFileName, ContentType, SanitizedBytes)
    if not ObjectKey:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Portrait Storage Failed with Provider Error")
        raise FastAPI.HTTPException(status_code = 500, detail = "Storage provider error during portrait upload")

    NewStorageFile = StorageFile.StorageFile(OwnerID = CurrentUser.ID, FileName = OriginalFileName, ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey)
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewStorageFile)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Portrait Upload Succeeded: FileID=\"{NewStorageFile.ID[:8]}…\", Size={FileSizeBytes}B")

    Context: Typing.Dict[str, Typing.Any] = {
        "PortraitFileID": NewStorageFile.ID
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterPortraitPartial.html", Context, Headers = {"HX-Trigger": "portraitSelected"})

@Router.post("/Portrait/Select/Partial", response_class = Responses.HTMLResponse)
async def SelectCharacterPortraitPartial(FileID: str = FastAPI.Form(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.ID == FileID, StorageFile.StorageFile.OwnerID == CurrentUser.ID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Portrait Selection Failed: File \"{FileID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Selected Character Portrait: FileID=\"{TargetFile.ID[:8]}…\"")
    Context: Typing.Dict[str, Typing.Any] = {
        "PortraitFileID": TargetFile.ID
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterPortraitPartial.html", Context, Headers = {"HX-Trigger": "portraitSelected"})

@Router.post("/Manual/Partial", response_class = Responses.HTMLResponse)
async def CreateCharacterManualPartial(Request: FastAPI.Request, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    FormData = await Request.form()
    GameSystemValue: str = str(FormData.get("GameSystem") or "DND5thEdition")
    try:
        GameSystem: Character.GameSystemType = Character.GameSystemType(GameSystemValue)

    except ValueError:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Manual Character Creation Rejected: Invalid System \"{GameSystemValue}\"")
        Context: Typing.Dict[str, Typing.Any] = {
            "IsSuccess"   : False,
            "ErrorMessage": f"Unrecognized game system: {GameSystemValue}"
        }
        ResponseHeaders: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"characterSaveError": {"ErrorMessage": f"Unrecognized game system: {GameSystemValue}"}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

    Name: str = str(FormData.get("Name") or "").strip()
    if (len(Name) == 0):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Manual Character Creation Rejected: Empty Name")
        Context = {
            "IsSuccess"   : False,
            "ErrorMessage": "Character name cannot be blank."
        }
        ResponseHeaders = {
            "HX-Trigger": JSON.dumps({"characterSaveError": {"ErrorMessage": "Character name cannot be blank."}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser, GameSystem):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Manual Character Creation Forbidden: System=\"{GameSystem.value}\"")
        Context = {
            "IsSuccess"   : False,
            "ErrorMessage": "Your role does not have permission to create characters."
        }
        ResponseHeaders = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to create characters."})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

    PlayerName: Typing.Optional[str] = FormData.get("PlayerName")
    PortraitFileID: Typing.Optional[str] = FormData.get("PortraitFileID")
    IsPublic: bool = str(FormData.get("IsPublic", "true")).lower() in ["true", "1", "on"]

    try:
        if GameSystem == Character.GameSystemType.DND5thEdition:
            UnifiedSheet = Services.GLOBAL_CHARACTER_MAPPER.MapManualFormData(dict(FormData))
            DetailData = UnifiedSheet.model_dump()
            PrimaryClassName: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "Adventurer"
            SummaryData = {
                "Class"         : PrimaryClassName,
                "Level"         : UnifiedSheet.TotalLevel,
                "HitPoints"     : UnifiedSheet.HitPoints.MaxHitPoints,
                "Species"       : UnifiedSheet.Species.FullName,
                "PortraitFileID": PortraitFileID
            }

        else:
            CareerName: str = str(FormData.get("ClassOrCareer") or "Citizen").strip()
            TermsCount: int = int(FormData.get("LevelOrTerms", 1) or 1)
            SummaryData = {
                "Career"        : CareerName,
                "Terms"         : TermsCount,
                "Homeworld"     : "Core",
                "PortraitFileID": PortraitFileID
            }
            DetailData = {
                "Name"          : Name,
                "GameSystem"    : GameSystem.value,
                "Career"        : CareerName,
                "Terms"         : TermsCount,
                "PortraitFileID": PortraitFileID
            }

        IsProtectedState: bool = str(FormData.get("IsProtectedState", "false")).lower() in ("true", "1", "on")
        IsOverriddenState: bool = str(FormData.get("IsOverriddenState", "false")).lower() in ("true", "1", "on")
        CharacterID: Typing.Optional[str] = str(FormData.get("CharacterID") or "").strip() or None
        NowTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.timezone.utc)
        SavedCharacter: Character.Character
        if (CharacterID is not None) and (CharacterID not in ("Current", "Draft", "New")):
            QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
            QueryResult = await DatabaseSession.execute(QueryStatement)
            ExistingCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
            if (ExistingCharacter is not None):
                if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, ExistingCharacter):
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Manual Character Update Forbidden: ID=\"{CharacterID[:8]}…\"")
                    Context = {
                        "IsSuccess"   : False,
                        "ErrorMessage": "Your role does not have permission to modify this character."
                    }
                    ResponseHeaders = {
                        "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."})
                    }
                    return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

                ExistingCharacter.Name = Name
                ExistingCharacter.GameSystem = GameSystem
                ExistingCharacter.IsPublic = IsPublic
                ExistingCharacter.IsProtected = IsProtectedState
                ExistingCharacter.IsOverridden = IsOverriddenState
                ExistingCharacter.SummaryData = SummaryData
                ExistingCharacter.DetailData = DetailData
                ExistingCharacter.UpdatedAt = NowTimestamp
                await DatabaseSession.commit()
                await DatabaseSession.refresh(ExistingCharacter)
                SavedCharacter = ExistingCharacter
                DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Manual Character Updated: \"{SavedCharacter.Name}\" (ID=\"{SavedCharacter.ID[:8]}…\")")

            else:
                NewCharacter = Character.Character(OwnerID = CurrentUser.ID, Name = Name, GameSystem = GameSystem, IsPublic = IsPublic, IsAccepted = False, IsProtected = IsProtectedState, IsOverridden = IsOverriddenState, SummaryData = SummaryData, DetailData = DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
                DatabaseSession.add(NewCharacter)
                await DatabaseSession.commit()
                await DatabaseSession.refresh(NewCharacter)
                SavedCharacter = NewCharacter
                await MailService.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = SavedCharacter.OwnerID, Subject = f"Character '{SavedCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour character '{SavedCharacter.Name}' ({SavedCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = SavedCharacter.ID)
                DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Manual Character Created: \"{SavedCharacter.Name}\" (ID=\"{SavedCharacter.ID[:8]}…\")")

        else:
            NewCharacter = Character.Character(OwnerID = CurrentUser.ID, Name = Name, GameSystem = GameSystem, IsPublic = IsPublic, IsAccepted = False, IsProtected = IsProtectedState, IsOverridden = IsOverriddenState, SummaryData = SummaryData, DetailData = DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
            DatabaseSession.add(NewCharacter)
            await DatabaseSession.commit()
            await DatabaseSession.refresh(NewCharacter)
            SavedCharacter = NewCharacter
            await MailService.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = SavedCharacter.OwnerID, Subject = f"Character '{SavedCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour character '{SavedCharacter.Name}' ({SavedCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = SavedCharacter.ID)
            DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Manual Character Created: \"{SavedCharacter.Name}\" (ID=\"{SavedCharacter.ID[:8]}…\")")

    except Exception as SaveException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Manual Character Save Error: {type(SaveException).__name__}")
        Context = {
            "IsSuccess"   : False,
            "ErrorMessage": f"Failed to save character: {str(SaveException)}"
        }
        ResponseHeaders = {
            "HX-Trigger": JSON.dumps({"characterSaveError": {"ErrorMessage": str(SaveException)}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

    Context = {
        "IsSuccess"    : True,
        "CharacterName": SavedCharacter.Name,
        "GameSystem"   : SavedCharacter.GameSystem.value
    }
    ResponseHeaders = {
        "HX-Trigger": JSON.dumps({"characterSaved": {"CharacterName": SavedCharacter.Name, "CharacterID": SavedCharacter.ID}})
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

@Router.post("/{CharacterID}/Protect/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterProtectionPartial(CharacterID: str, Request: FastAPI.Request, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not CurrentUser:
        Headers: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "You do not have the permission to use this feature."}),
            "HX-Reswap" : "none"
        }
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    TargetCharacter: Typing.Optional[Character.Character] = None
    IsDraft: bool = bool(CharacterID in ("Current", "Draft", "New", ""))
    if (not IsDraft):
        QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
        QueryResult = await DatabaseSession.execute(QueryStatement)
        TargetCharacter = QueryResult.scalars().first()
        if (not TargetCharacter):
            Headers = {
                "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}),
                "HX-Reswap" : "none"
            }
            return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if (not RoleBasedAccessControl.CanProtectCharacter(CurrentUser, TargetCharacter)):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Protect Character Forbidden: ID=\"{CharacterID[:8]}…\"")
        Headers = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "You do not have the permission to use this feature."}),
            "HX-Reswap" : "none"
        }
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    FormData = await Request.form()
    ActiveTab: str = str(FormData.get("ActiveTab") or "CharacterSheetOverviewTab").strip()
    if (ActiveTab not in ("CharacterSheetOverviewTab", "CharacterSheetAbilitiesTab", "CharacterSheetInventoryTab", "CharacterSheetDescriptionTab")):
        ActiveTab = "CharacterSheetOverviewTab"

    CurrentOverridden: bool = str(FormData.get("IsOverriddenState", "false")).lower() in ("true", "1", "on")
    if (((TargetCharacter is not None) and TargetCharacter.IsOverridden) or ((TargetCharacter is None) and CurrentOverridden)):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Protect Character Rejected: Override Active (ID=\"{CharacterID[:8]}…\")")
        Headers = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Override is active and takes precedence. Disable override before enabling protection."}),
            "HX-Reswap" : "none"
        }
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if (TargetCharacter is not None):
        TargetCharacter.IsProtected = not TargetCharacter.IsProtected
        TargetCharacter.IsOverridden = False

        if (not TargetCharacter.IsProtected) and (CurrentUser is not None):
            ExistingFileID: Typing.Optional[str] = (TargetCharacter.SummaryData or {}).get("PortraitFileID") or (TargetCharacter.DetailData or {}).get("PortraitFileID")
            ExistingPortraitURL: Typing.Optional[str] = (TargetCharacter.SummaryData or {}).get("PortraitURL") or (TargetCharacter.DetailData or {}).get("PortraitURL")
            if ((not ExistingFileID) and (ExistingPortraitURL is not None)):
                StoredFileID: Typing.Optional[str] = await CharacterImportService.GLOBAL_CHARACTER_IMPORTER.DownloadAndStorePortrait(CurrentUser, ExistingPortraitURL, DatabaseSession)
                if (StoredFileID is not None):
                    NewSummaryData: Typing.Dict[str, Typing.Any] = dict(TargetCharacter.SummaryData or {})
                    NewSummaryData["PortraitFileID"] = StoredFileID
                    TargetCharacter.SummaryData = NewSummaryData
                    NewDetailData: Typing.Dict[str, Typing.Any] = dict(TargetCharacter.DetailData or {})
                    NewDetailData["PortraitFileID"] = StoredFileID
                    if (("PhysicalAppearance" in NewDetailData) and isinstance(NewDetailData["PhysicalAppearance"], dict)):
                        NewPhysicalAppearance: Typing.Dict[str, Typing.Any] = dict(NewDetailData["PhysicalAppearance"])
                        NewPhysicalAppearance["PortraitFileID"] = StoredFileID
                        NewDetailData["PhysicalAppearance"] = NewPhysicalAppearance

                    TargetCharacter.DetailData = NewDetailData
                    Attributes.flag_modified(TargetCharacter, "SummaryData")
                    Attributes.flag_modified(TargetCharacter, "DetailData")

        await DatabaseSession.commit()
        await DatabaseSession.refresh(TargetCharacter)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Character Protection: ID=\"{CharacterID[:8]}…\", Protected={TargetCharacter.IsProtected}")
        Context: Typing.Dict[str, Typing.Any] = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = TargetCharacter, IsAllowed = True, IsProtected = TargetCharacter.IsProtected, IsOverridden = TargetCharacter.IsOverridden, ActiveTab = ActiveTab)

    else:
        CurrentProtected: bool = str(FormData.get("IsProtectedState", "false")).lower() in ("true", "1", "on")
        NewProtectedState: bool = not CurrentProtected
        GameSystemValue: str = str(FormData.get("GameSystem") or "DND5thEdition")
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Draft Protection: Protected={NewProtectedState}")
        Context = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = None, DetailDataOverride = dict(FormData), IsAllowed = True, IsProtected = NewProtectedState, IsOverridden = False, ActiveTab = ActiveTab)
        Context["GameSystem"] = GameSystemValue

    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterSheetWindow.html", Context)

@Router.post("/{CharacterID}/Override/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterOverridePartial(CharacterID: str, Request: FastAPI.Request, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if ((not CurrentUser) or (not RoleBasedAccessControl.CanOverrideCharacter(CurrentUser))):
        UserID: str = CurrentUser.ID if (CurrentUser is not None) else "AnonymousUser"
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Override Character Forbidden: ID=\"{CharacterID[:8]}…\"")
        Headers: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "You do not have the permission to use this feature."}),
            "HX-Reswap" : "none"
        }
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    TargetCharacter: Typing.Optional[Character.Character] = None
    IsDraft: bool = bool(CharacterID in ("Current", "Draft", "New", ""))
    if (not IsDraft):
        QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
        QueryResult = await DatabaseSession.execute(QueryStatement)
        TargetCharacter = QueryResult.scalars().first()
        if (not TargetCharacter):
            Headers = {
                "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}),
                "HX-Reswap" : "none"
            }
            return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    FormData = await Request.form()
    ActiveTab: str = str(FormData.get("ActiveTab") or "CharacterSheetOverviewTab").strip()
    if (ActiveTab not in ("CharacterSheetOverviewTab", "CharacterSheetAbilitiesTab", "CharacterSheetInventoryTab", "CharacterSheetDescriptionTab")):
        ActiveTab = "CharacterSheetOverviewTab"

    if (TargetCharacter is not None):
        NewOverriddenValue: bool = not TargetCharacter.IsOverridden
        TargetCharacter.IsOverridden = NewOverriddenValue
        if (NewOverriddenValue):
            TargetCharacter.IsProtected = False

        await DatabaseSession.commit()
        await DatabaseSession.refresh(TargetCharacter)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Character Override: ID=\"{CharacterID[:8]}…\", Overridden={TargetCharacter.IsOverridden}")
        Context = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = TargetCharacter, IsAllowed = True, IsProtected = TargetCharacter.IsProtected, IsOverridden = TargetCharacter.IsOverridden, ActiveTab = ActiveTab)

    else:
        CurrentProtected: bool = str(FormData.get("IsProtectedState", "false")).lower() in ("true", "1", "on")
        CurrentOverridden: bool = str(FormData.get("IsOverriddenState", "false")).lower() in ("true", "1", "on")
        NewOverriddenState: bool = not CurrentOverridden
        NewProtectedState: bool = False if (NewOverriddenState) else (CurrentProtected)
        GameSystemValue: str = str(FormData.get("GameSystem") or "DND5thEdition")
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Toggled Draft Override: Overridden={NewOverriddenState}")
        Context = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = None, DetailDataOverride = dict(FormData), IsAllowed = True, IsProtected = NewProtectedState, IsOverridden = NewOverriddenState, ActiveTab = ActiveTab)
        Context["GameSystem"] = GameSystemValue

    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterSheetWindow.html", Context)

class CharacterImportExternalRequest(Pydantic.BaseModel):
    ImportURL: str
    DiscordID: str

@Router.post("/Import", response_class = Responses.JSONResponse, status_code = FastAPI.status.HTTP_201_CREATED)
async def ImportCharacterFromExternalSource(RequestPayload: CharacterImportExternalRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), TokenPayload: dict[str, Typing.Any] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceToken)) -> Responses.JSONResponse:
    TargetDiscordID: str = str(RequestPayload.DiscordID).strip()
    UserQueryStatement = SQLAlchemy.select(User.User).where(User.User.DiscordID == TargetDiscordID)
    UserQueryResult    = await DatabaseSession.execute(UserQueryStatement)
    TargetUser         = UserQueryResult.scalars().first()
    if (TargetUser is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"External Character Import Rejected: DiscordID=\"{TargetDiscordID}\" Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"User with DiscordID '{TargetDiscordID}' not found")

    try:
        NewCharacter: Character.Character = await CharacterImportService.GLOBAL_CHARACTER_IMPORTER.ImportCharacterFromURL(RequestPayload.ImportURL, TargetUser.ID, DatabaseSession)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"External Character Imported: Name=\"{NewCharacter.Name}\", ID={NewCharacter.ID}, Owner={TargetUser.DisplayName}")
        ResponseData: dict[str, Typing.Any] = {
            "ID"         : str(NewCharacter.ID),
            "Name"       : str(NewCharacter.Name),
            "GameSystem" : str(NewCharacter.GameSystem.value if hasattr(NewCharacter.GameSystem, "value") else NewCharacter.GameSystem),
            "SummaryData": dict(NewCharacter.SummaryData or {}),
            "DetailData" : dict(NewCharacter.DetailData or {})
        }
        return Responses.JSONResponse(status_code = FastAPI.status.HTTP_201_CREATED, content = ResponseData)

    except ValueError as ValidationError:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"External Character Import Invalid URL: {str(ValidationError)}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = str(ValidationError))

    except Exception as ImportException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"External Character Import Failed: {type(ImportException).__name__} - {str(ImportException)}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Character import failed: {str(ImportException)}")

@Router.post("/Import/Partial", response_class = Responses.HTMLResponse)
@Router.post("/Import/Partial/", response_class = Responses.HTMLResponse)
@Router.post("/import/partial", response_class = Responses.HTMLResponse)
async def ImportCharacterPartial(Request: FastAPI.Request, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if ((CurrentUser.Role == User.UserRole.Visitor) or (not RoleBasedAccessControl.IsUserInGuild(CurrentUser)) or (not RoleBasedAccessControl.CanCreateCharacter(CurrentUser, Character.GameSystemType.DND5thEdition))):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Character Import Denied: User \"{CurrentUser.ID[:8]}…\" Unauthorized")
        ErrorMessage: str = "Discord server membership required to import characters." if ((CurrentUser.Role == User.UserRole.Visitor) or (not RoleBasedAccessControl.IsUserInGuild(CurrentUser))) else "Your role does not have permission to import characters."
        Context: Typing.Dict[str, Typing.Any] = {
            "IsSuccess"   : False,
            "ErrorMessage": ErrorMessage
        }
        ResponseHeaders: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"characterImportError": {"ErrorMessage": ErrorMessage}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportResultPartial.html", Context, 200, ResponseHeaders)

    FormData: FastAPI.datastructures.FormData = await Request.form()
    ImportURL: str = str(FormData.get("ImportURL") or FormData.get("URL") or "").strip()
    if not ImportURL:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Character Import Rejected: Empty URL Provided")
        ErrorMessage: str = "Please enter a valid character sheet URL."
        Context: Typing.Dict[str, Typing.Any] = {
            "IsSuccess"   : False,
            "ErrorMessage": ErrorMessage
        }
        ResponseHeaders: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"characterImportError": {"ErrorMessage": ErrorMessage}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportResultPartial.html", Context, 200, ResponseHeaders)

    try:
        NewCharacter: Character.Character = await CharacterImportService.GLOBAL_CHARACTER_IMPORTER.ImportCharacterFromURL(ImportURL, CurrentUser.ID, DatabaseSession)
        UtilityName: str = "Dicecloud v1" if (NewCharacter.ImportSource == "DicecloudV1") else "D&D Beyond"
        Context: Typing.Dict[str, Typing.Any] = {
            "IsSuccess"  : True,
            "Character"  : NewCharacter,
            "GameSystem" : NewCharacter.GameSystem.value,
            "UtilityName": UtilityName
        }
        ResponseHeaders: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"characterSaved": {"CharacterName": NewCharacter.Name, "CharacterID": NewCharacter.ID}, "characterImportSuccess": {"CharacterName": NewCharacter.Name, "CharacterID": NewCharacter.ID, "GameSystem": NewCharacter.GameSystem.value}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportResultPartial.html", Context, 200, ResponseHeaders)

    except Exception as ImportException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Character Import Error: {type(ImportException).__name__}")
        ErrorMessage: str = str(ImportException)
        Context: Typing.Dict[str, Typing.Any] = {
            "IsSuccess"   : False,
            "ErrorMessage": ErrorMessage
        }
        ResponseHeaders: Typing.Dict[str, str] = {
            "HX-Trigger": JSON.dumps({"characterImportError": {"ErrorMessage": ErrorMessage}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportResultPartial.html", Context, 200, ResponseHeaders)

@Router.get("/Import/Overview/Partial", response_class = Responses.HTMLResponse)
@Router.get("/Import/Overview/Partial/", response_class = Responses.HTMLResponse)
@Router.get("/import/overview/partial", response_class = Responses.HTMLResponse)
@Router.get("/import/overview/partial/", response_class = Responses.HTMLResponse)
@Router.post("/Import/Overview/Partial", response_class = Responses.HTMLResponse)
@Router.post("/Import/Overview/Partial/", response_class = Responses.HTMLResponse)
@Router.post("/import/overview/partial", response_class = Responses.HTMLResponse)
@Router.post("/import/overview/partial/", response_class = Responses.HTMLResponse)
async def GetCharacterImportOverviewPartial(Request: FastAPI.Request, URL: Typing.Optional[str] = None, ImportURL: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    TargetURL: str = (URL or ImportURL or "").strip()
    if not TargetURL:
        if (Request.method == "POST"):
            FormData: FastAPI.datastructures.FormData = await Request.form()
            TargetURL = str(FormData.get("ImportURL") or FormData.get("URL") or "").strip()

    if not TargetURL:
        Context: Typing.Dict[str, Typing.Any] = {
            "IsReady"     : False,
            "ErrorMessage": None,
            "Overview"    : None
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportOverviewPartial.html", Context, 200)

    SourceType, CharacterID, UtilityName = CharacterImportService.GLOBAL_CHARACTER_IMPORTER.DetectImportSource(TargetURL)
    if ((SourceType is None) or (CharacterID is None)):
        Context: Typing.Dict[str, Typing.Any] = {
            "IsReady"     : False,
            "ErrorMessage": "Awaiting a valid Dicecloud v1 or D&D Beyond character URL.",
            "Overview"    : None
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportOverviewPartial.html", Context, 200)

    try:
        Overview: Typing.Dict[str, Typing.Any] = await CharacterImportService.GLOBAL_CHARACTER_IMPORTER.GetCharacterOverview(TargetURL)
        Context: Typing.Dict[str, Typing.Any] = {
            "IsReady"     : True,
            "ErrorMessage": None,
            "Overview"    : Overview
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportOverviewPartial.html", Context, 200)

    except Exception as OverviewException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Character Overview Error: {type(OverviewException).__name__}")
        Context: Typing.Dict[str, Typing.Any] = {
            "IsReady"     : False,
            "ErrorMessage": str(OverviewException),
            "Overview"    : None
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportOverviewPartial.html", Context, 200)

@Router.get("/{CharacterID}/Actions", response_model = Typing.List[AutomationModels.UnifiedActionEntry])
async def GetCharacterActions(CharacterID: str, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.List[AutomationModels.UnifiedActionEntry]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Get Character Actions Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanViewCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Get Character Actions Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to view this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any]                  = FoundCharacter.DetailData or {}
    UnifiedActionsList  : Typing.List[AutomationModels.UnifiedActionEntry] = []

    StandardAttacksList = DetailDataDictionary.get("Attacks", [])
    if isinstance(StandardAttacksList, list):
        for AttackItem in StandardAttacksList:
            if isinstance(AttackItem, dict):
                UnifiedActionsList.append(AutomationModels.UnifiedActionEntry(
                    ID               = str(AttackItem.get("ID") or UUID.uuid4()),
                    Name             = str(AttackItem.get("Name", "Standard Attack")),
                    SourceType       = "StandardAttack",
                    ActivationType   = "Action",
                    AttackBonus      = int(AttackItem.get("AttackBonus", 0)) if (AttackItem.get("AttackBonus") is not None) else None,
                    DamageExpression = str(AttackItem.get("DamageExpression", "")) if AttackItem.get("DamageExpression") else None,
                    DamageType       = str(AttackItem.get("DamageType", "")) if AttackItem.get("DamageType") else None,
                    RangeDescription = str(AttackItem.get("RangeDescription", "")) if AttackItem.get("RangeDescription") else None,
                    Phrase           = None,
                    ThumbnailURL     = None,
                    Automation       = []
                ))

    CustomAttacksList = DetailDataDictionary.get("CustomAttacks", [])
    if isinstance(CustomAttacksList, list):
        for CustomItem in CustomAttacksList:
            if isinstance(CustomItem, dict):
                RawActivationType: str                                    = str(CustomItem.get("ActivationType") or "Action")
                RawAutomation                                             = CustomItem.get("Automation", [])
                ParsedAutomation : Typing.List[AutomationModels.EffectNode] = []
                if isinstance(RawAutomation, list):
                    for RawNode in RawAutomation:
                        if isinstance(RawNode, dict):
                            ParsedAutomation.append(AutomationModels.EffectNode.model_validate(RawNode))

                UnifiedActionsList.append(AutomationModels.UnifiedActionEntry(
                    ID               = str(CustomItem.get("ID") or UUID.uuid4()),
                    Name             = str(CustomItem.get("Name", "Custom Action")),
                    SourceType       = "CustomAutomation",
                    ActivationType   = RawActivationType,
                    AttackBonus      = None,
                    DamageExpression = None,
                    DamageType       = None,
                    RangeDescription = None,
                    Phrase           = CustomItem.get("Phrase"),
                    ThumbnailURL     = CustomItem.get("ThumbnailURL"),
                    Automation       = ParsedAutomation
                ))

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Unified Actions: Character=\"{CharacterID[:8]}…\", Count={len(UnifiedActionsList)}")
    return UnifiedActionsList

@Router.post("/{CharacterID}/Actions", status_code = 201, response_model = AutomationModels.CustomAttackEntry)
async def CreateCharacterAction(CharacterID: str, RequestPayload: AutomationModels.CustomAttackCreateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> AutomationModels.CustomAttackEntry:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Create Character Action Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Create Character Action Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    ValidationResult = AutomationService.GLOBAL_AUTOMATION_SERVICE.ValidateAutomation(RequestPayload.Automation)
    if not ValidationResult.IsValid:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Create Character Action Rejected: Invalid Automation Tree for \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 400, detail = {"Message": "Invalid automation specification", "Errors": ValidationResult.Errors})

    ActionID: str = RequestPayload.ID if ((RequestPayload.ID is not None) and (RequestPayload.ID.strip() != "")) else str(UUID.uuid4())
    NewAction = AutomationModels.CustomAttackEntry(
        ID             = ActionID,
        Name           = RequestPayload.Name.strip(),
        ActivationType = RequestPayload.ActivationType,
        Phrase         = RequestPayload.Phrase,
        ThumbnailURL   = RequestPayload.ThumbnailURL,
        Automation     = RequestPayload.Automation,
        IsDirty        = False
    )

    DetailDataDictionary : Typing.Dict[str, Typing.Any]              = dict(FoundCharacter.DetailData or {})
    ExistingCustomAttacks: Typing.List[Typing.Dict[str, Typing.Any]] = list(DetailDataDictionary.get("CustomAttacks") or [])
    ExistingCustomAttacks.append(NewAction.model_dump())
    DetailDataDictionary["CustomAttacks"] = ExistingCustomAttacks
    FoundCharacter.DetailData             = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created Character Action: ActionID=\"{NewAction.ID[:8]}…\", Character=\"{CharacterID[:8]}…\"")
    return NewAction

@Router.patch("/{CharacterID}/Actions/{ActionID}", response_model = AutomationModels.CustomAttackEntry)
async def UpdateCharacterAction(CharacterID: str, ActionID: str, RequestPayload: AutomationModels.CustomAttackUpdateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> AutomationModels.CustomAttackEntry:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Update Character Action Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Update Character Action Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary  : Typing.Dict[str, Typing.Any]              = dict(FoundCharacter.DetailData or {})
    ExistingCustomAttacks : Typing.List[Typing.Dict[str, Typing.Any]] = list(DetailDataDictionary.get("CustomAttacks") or [])
    TargetIndex           : Typing.Optional[int]                     = None
    TargetActionDictionary: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    for ActionIndex, ActionItem in enumerate(ExistingCustomAttacks):
        if (str(ActionItem.get("ID")) == ActionID):
            TargetIndex            = ActionIndex
            TargetActionDictionary = dict(ActionItem)
            break

    if (TargetIndex is None) or (TargetActionDictionary is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Update Character Action Failed: Action \"{ActionID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Action not found")

    if (RequestPayload.Automation is not None):
        ValidationResult = AutomationService.GLOBAL_AUTOMATION_SERVICE.ValidateAutomation(RequestPayload.Automation)
        if not ValidationResult.IsValid:
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Update Character Action Rejected: Invalid Automation Tree for \"{ActionID[:8]}…\"")
            raise FastAPI.HTTPException(status_code = 400, detail = {"Message": "Invalid automation specification", "Errors": ValidationResult.Errors})

        TargetActionDictionary["Automation"] = [Node.model_dump() for Node in RequestPayload.Automation]

    if (RequestPayload.Name is not None):
        TargetActionDictionary["Name"] = RequestPayload.Name.strip()

    if (RequestPayload.ActivationType is not None):
        TargetActionDictionary["ActivationType"] = RequestPayload.ActivationType.value

    if (RequestPayload.Phrase is not None):
        TargetActionDictionary["Phrase"] = RequestPayload.Phrase

    if (RequestPayload.ThumbnailURL is not None):
        TargetActionDictionary["ThumbnailURL"] = RequestPayload.ThumbnailURL

    UpdatedActionModel = AutomationModels.CustomAttackEntry.model_validate(TargetActionDictionary)
    ExistingCustomAttacks[TargetIndex]    = UpdatedActionModel.model_dump()
    DetailDataDictionary["CustomAttacks"] = ExistingCustomAttacks
    FoundCharacter.DetailData             = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Updated Character Action: ActionID=\"{ActionID[:8]}…\", Character=\"{CharacterID[:8]}…\"")
    return UpdatedActionModel

@Router.delete("/{CharacterID}/Actions/{ActionID}")
async def DeleteCharacterAction(CharacterID: str, ActionID: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Delete Character Action Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Delete Character Action Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary : Typing.Dict[str, Typing.Any]              = dict(FoundCharacter.DetailData or {})
    ExistingCustomAttacks: Typing.List[Typing.Dict[str, Typing.Any]] = list(DetailDataDictionary.get("CustomAttacks") or [])
    OriginalLength       : int                                       = len(ExistingCustomAttacks)
    FilteredCustomAttacks = [ActionItem for ActionItem in ExistingCustomAttacks if str(ActionItem.get("ID")) != ActionID]
    if (len(FilteredCustomAttacks) == OriginalLength):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Delete Character Action Failed: Action \"{ActionID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Action not found")

    DetailDataDictionary["CustomAttacks"] = FilteredCustomAttacks
    FoundCharacter.DetailData             = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Deleted Character Action: ActionID=\"{ActionID[:8]}…\", Character=\"{CharacterID[:8]}…\"")
    return {"IsSuccess": True, "RemovedActionID": ActionID}

@Router.post("/{CharacterID}/Counters")
async def CreateOrUpdateCharacterCounter(CharacterID: str, RequestPayload: AutomationModels.CounterCreateOrUpdateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Set Counter Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Set Counter Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any] = dict(FoundCharacter.DetailData or {})
    CountersDictionary  : Typing.Dict[str, Typing.Any] = dict(DetailDataDictionary.get("CustomCounters") or {})
    CounterModel = AutomationModels.CounterData(
        Value         = RequestPayload.Value,
        MaxValue      = RequestPayload.MaxValue,
        MinValue      = RequestPayload.MinValue,
        ResetSchedule = RequestPayload.ResetSchedule,
        Description   = RequestPayload.Description
    )
    CountersDictionary[RequestPayload.Name] = CounterModel.model_dump()
    DetailDataDictionary["CustomCounters"]  = CountersDictionary
    FoundCharacter.DetailData               = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Set Counter: Name=\"{RequestPayload.Name}\", Character=\"{CharacterID[:8]}…\"")
    return {"CounterName": RequestPayload.Name, "Counter": CounterModel.model_dump()}

@Router.patch("/{CharacterID}/Counters/{CounterName}")
async def MutateCharacterCounter(CharacterID: str, CounterName: str, RequestPayload: AutomationModels.CounterMutationRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Mutate Counter Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Mutate Counter Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any] = dict(FoundCharacter.DetailData or {})
    CountersDictionary  : Typing.Dict[str, Typing.Any] = dict(DetailDataDictionary.get("CustomCounters") or {})
    ExistingCounterRaw  = CountersDictionary.get(CounterName)
    if (ExistingCounterRaw is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Mutate Counter Failed: Counter \"{CounterName}\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = f"Counter '{CounterName}' not found")

    CounterModel: AutomationModels.CounterData = AutomationModels.CounterData.model_validate(ExistingCounterRaw)
    CurrentValue: int                          = CounterModel.Value
    NewValue    : int                          = CurrentValue
    if (RequestPayload.Value is not None):
        NewValue = RequestPayload.Value

    elif (RequestPayload.Delta is not None):
        NewValue = CurrentValue + RequestPayload.Delta

    elif (RequestPayload.Operation is not None):
        OperationLower: str = RequestPayload.Operation.lower()
        if (OperationLower == "increment"):
            NewValue = CurrentValue + 1

        elif (OperationLower == "decrement"):
            NewValue = CurrentValue - 1

        elif (OperationLower == "reset"):
            NewValue = CounterModel.MaxValue if (CounterModel.MaxValue is not None) else (CounterModel.MinValue if (CounterModel.MinValue is not None) else 0)

        else:
            raise FastAPI.HTTPException(status_code = 400, detail = f"Unrecognized counter operation '{RequestPayload.Operation}'")

    else:
        raise FastAPI.HTTPException(status_code = 400, detail = "Either Value, Delta, or Operation must be provided")

    if (CounterModel.MinValue is not None) and (NewValue < CounterModel.MinValue):
        NewValue = CounterModel.MinValue

    if (CounterModel.MaxValue is not None) and (NewValue > CounterModel.MaxValue):
        NewValue = CounterModel.MaxValue

    CounterModel.Value                     = NewValue
    CountersDictionary[CounterName]        = CounterModel.model_dump()
    DetailDataDictionary["CustomCounters"] = CountersDictionary
    FoundCharacter.DetailData              = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Mutated Counter: Name=\"{CounterName}\", Value={NewValue}, Character=\"{CharacterID[:8]}…\"")
    return {"CounterName": CounterName, "Counter": CounterModel.model_dump()}

@Router.post("/{CharacterID}/Variables")
async def SetCharacterVariables(CharacterID: str, RequestPayload: AutomationModels.VariableSetRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Set Variables Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Set Variables Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any] = dict(FoundCharacter.DetailData or {})
    VariablesDictionary : Typing.Dict[str, Typing.Any] = dict(DetailDataDictionary.get("Variables") or {})
    HasMutated          : bool                         = False
    if (RequestPayload.Variables is not None):
        VariablesDictionary.update(RequestPayload.Variables)
        HasMutated = True

    if (RequestPayload.Name is not None) and (RequestPayload.Value is not None):
        VariablesDictionary[RequestPayload.Name] = RequestPayload.Value
        HasMutated = True

    if not HasMutated:
        raise FastAPI.HTTPException(status_code = 400, detail = "Either 'Variables' dictionary or 'Name' and 'Value' pair must be supplied")

    DetailDataDictionary["Variables"] = VariablesDictionary
    FoundCharacter.DetailData         = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Set Variables: Character=\"{CharacterID[:8]}…\", VariableCount={len(VariablesDictionary)}")
    return {"Variables": VariablesDictionary}


