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
import sqlalchemy.orm                            as ORM
import sqlalchemy.orm.attributes                 as Attributes
import Server.Auth.RoleBasedAccessControl        as RoleBasedAccessControl
import Server.Database                           as Database
import Server.Models.AutomationModels            as AutomationModels
import Server.Models.Character                   as Character
import Server.Models.Mail                        as Mail
import Server.Models.StorageFile                 as StorageFile
import Server.Models.User                        as User
import Server.Services                           as Services
import Server.Services.AutomationService         as Automation
import Server.Services.CharacterGeneratorService as CharacterGenerator
import Server.Services.CharacterImportService    as CharacterImport
import Server.Services.CharacterMappingService   as CharacterMapping
import Server.Services.DebugService              as Debug
import Server.Services.ImageProcessingService    as ImageProcessing
import Server.Services.MailboxService            as Mailbox
import Server.Services.OracleStorageService      as OracleStorage
import Server.Services.TemplateRendererService   as TemplateRenderer
import Server.Services.External5ETools           as External5ETools

Router = FastAPI.APIRouter(prefix = "/API/Characters", tags = ["Characters"])
External5EToolsService: External5ETools.External5ETools = External5ETools.GLOBAL_EXTERNAL_5ETOOLS

@Router.get("/Rules/Classes", response_class = Responses.JSONResponse)
async def GetClassRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    RulesSummary: Typing.Dict[str, Typing.Any] = External5EToolsService.GetClassRulesSummary()
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Class Rules: Count={len(RulesSummary)}")
    return Responses.JSONResponse(content = RulesSummary)

@Router.get("/Rules/SpellcastingAbility", response_class = Responses.JSONResponse)
async def GetClassSpellcastingAbilityRule(ClassName: str, SubclassName: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ResolvedAbility: Typing.Optional[str] = External5EToolsService.GetCanonicalSpellcastingAbility(ClassName, SubclassName)
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Spellcasting Rule: Class=\"{ClassName}\", Ability=\"{ResolvedAbility}\"")
    return Responses.JSONResponse(content = {"ClassName": ClassName, "SubclassName": SubclassName, "SpellcastingAbility": ResolvedAbility})

@Router.get("/Rules/DataStore", response_class = Responses.JSONResponse)
async def GetRulesDataStore(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    DataStoreDictionary: Typing.Dict[str, Typing.Any] = External5EToolsService.GetRulesDataStore()
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Rules Data Store: System=\"{DataStoreDictionary.get("GameSystem")}\"")
    return Responses.JSONResponse(content = DataStoreDictionary)

@Router.get("/Rules/Cantrips", response_class = Responses.JSONResponse)
async def GetCantripsRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    CantripsList: Typing.List[str] = External5EToolsService.GetCantripsList()
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Cantrips Rules: Count={len(CantripsList)}")
    return Responses.JSONResponse(content = CantripsList)

@Router.get("/Rules/EquipmentData", response_class = Responses.JSONResponse)
async def GetEquipmentRules(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    EquipmentData: Typing.Dict[str, Typing.Any] = External5EToolsService.GetEquipmentRulesData()
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Equipment Rules: Items={len(EquipmentData.get("Weights", {}))}, Armors={len(EquipmentData.get("Armors", {}))}")
    return Responses.JSONResponse(content = EquipmentData)

@Router.get("/Rules/Spells/{SpellName:path}", response_class = Responses.JSONResponse)
async def GetSpellRule(SpellName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    SpellRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetSpellData(SpellName, Source = Source)
    if (SpellRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Spell Rule: Name=\"{SpellName}\"")
        return Responses.JSONResponse(content = SpellRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Spell not found")

@Router.get("/Rules/Monsters/{MonsterName:path}", response_class = Responses.JSONResponse)
async def GetMonsterRule(MonsterName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    MonsterRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetMonsterData(MonsterName, Source = Source)
    if (MonsterRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Monster Rule: Name=\"{MonsterName}\"")
        return Responses.JSONResponse(content = MonsterRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Monster not found")

@Router.get("/Rules/Items/{ItemName:path}", response_class = Responses.JSONResponse)
async def GetItemRule(ItemName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ItemRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetItemData(ItemName, Source = Source)
    if (ItemRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Item Rule: Name=\"{ItemName}\"")
        return Responses.JSONResponse(content = ItemRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Item not found")

@Router.get("/Rules/Feats/{FeatName:path}", response_class = Responses.JSONResponse)
async def GetFeatRule(FeatName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    FeatRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetFeatData(FeatName, Source = Source)
    if (FeatRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Feat Rule: Name=\"{FeatName}\"")
        return Responses.JSONResponse(content = FeatRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Feat not found")

@Router.get("/Rules/Options/{OptionName:path}", response_class = Responses.JSONResponse)
async def GetOptionRule(OptionName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    OptionRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetOptionData(OptionName, Source = Source)
    if (OptionRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Option Rule: Name=\"{OptionName}\"")
        return Responses.JSONResponse(content = OptionRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Option not found")

@Router.get("/Rules/Rules/{RuleName:path}", response_class = Responses.JSONResponse)
async def GetRuleDefinition(RuleName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    RuleRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetRuleData(RuleName, Source = Source)
    if (RuleRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Rule Definition: Name=\"{RuleName}\"")
        return Responses.JSONResponse(content = RuleRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Rule not found")

@Router.get("/Rules/Backgrounds/{BackgroundName:path}", response_class = Responses.JSONResponse)
async def GetBackgroundRule(BackgroundName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    BackgroundRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetBackgroundData(BackgroundName, Source = Source)
    if (BackgroundRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Background Rule: Name=\"{BackgroundName}\"")
        return Responses.JSONResponse(content = BackgroundRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Background not found")

@Router.get("/Rules/Species/{SpeciesName:path}", response_class = Responses.JSONResponse)
async def GetSpeciesRule(SpeciesName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    SpeciesRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetSpeciesData(SpeciesName, Source = Source)
    if (SpeciesRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Species Rule: Name=\"{SpeciesName}\"")
        return Responses.JSONResponse(content = SpeciesRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Species not found")

@Router.get("/Rules/Conditions/{ConditionName:path}", response_class = Responses.JSONResponse)
async def GetConditionRule(ConditionName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ConditionRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetConditionData(ConditionName, Source = Source)
    if (ConditionRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Condition Rule: Name=\"{ConditionName}\"")
        return Responses.JSONResponse(content = ConditionRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Condition not found")

@Router.get("/Rules/Deities/{DeityName:path}", response_class = Responses.JSONResponse)
async def GetDeityRule(DeityName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    DeityRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetDeityData(DeityName, Source = Source)
    if (DeityRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Deity Rule: Name=\"{DeityName}\"")
        return Responses.JSONResponse(content = DeityRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Deity not found")

@Router.get("/Rules/Vehicles/{VehicleName:path}", response_class = Responses.JSONResponse)
async def GetVehicleRule(VehicleName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    VehicleRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetVehicleData(VehicleName, Source = Source)
    if (VehicleRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Vehicle Rule: Name=\"{VehicleName}\"")
        return Responses.JSONResponse(content = VehicleRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Vehicle not found")

@Router.get("/Rules/Classes/{ClassName:path}", response_class = Responses.JSONResponse)
async def GetClassDetailRule(ClassName: str, Source: Typing.Optional[str] = FastAPI.Query(default = None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    ClassRecord: Typing.Optional[Typing.Dict[str, Typing.Any]] = External5EToolsService.GetClassDetailData(ClassName, Source = Source)
    if (ClassRecord is not None):
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Class Detail Rule: Name=\"{ClassName}\"")
        return Responses.JSONResponse(content = ClassRecord)

    raise FastAPI.HTTPException(status_code = 404, detail = "Class not found")

@Router.get("/Rules/Compendium/Search", response_class = Responses.JSONResponse)
async def SearchCompendiumRules(Query: str, Category: Typing.Optional[str] = FastAPI.Query(default = None), Limit: int = FastAPI.Query(default = 5), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.JSONResponse:
    SearchResults: Typing.Dict[str, Typing.Any] = External5EToolsService.SearchCompendium(QueryText = Query, CategoryFilter = Category, ResultLimit = Limit)
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Compendium Search: Query=\"{Query}\", Category=\"{Category}\"")
    return Responses.JSONResponse(content = SearchResults)

class CharacterCreateRequest(Pydantic.BaseModel):
    Name             : str
    GameSystem       : Character.GameSystemType
    EntityType       : Character.EntityType         = Character.EntityType.Character
    ParentCharacterID: Typing.Optional[str]         = None
    IsPublic         : bool                         = True
    IsAccepted       : bool                         = False
    IsProtected      : bool                         = False
    IsOverridden     : bool                         = False
    ImportSource     : Typing.Optional[str]         = None
    SummaryData      : Typing.Dict[str, Typing.Any] = Pydantic.Field(default_factory = dict)
    DetailData       : Typing.Dict[str, Typing.Any] = Pydantic.Field(default_factory = dict)
    TargetOwnerID    : Typing.Optional[str]         = None

class CharacterUpdateRequest(Pydantic.BaseModel):
    Name             : Typing.Optional[str]                          = None
    EntityType       : Typing.Optional[Character.EntityType]         = None
    ParentCharacterID: Typing.Optional[str]                          = None
    IsPublic         : Typing.Optional[bool]                         = None
    IsAccepted       : Typing.Optional[bool]                         = None
    IsProtected      : Typing.Optional[bool]                         = None
    IsOverridden     : Typing.Optional[bool]                         = None
    ImportSource     : Typing.Optional[str]                          = None
    SummaryData      : Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    DetailData       : Typing.Optional[Typing.Dict[str, Typing.Any]] = None

class CharacterStatePatchRequest(Pydantic.BaseModel):
    DetailData : Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    SummaryData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None

class CharacterCompanionLinkOrCreateRequest(Pydantic.BaseModel):
    CompanionID: Typing.Optional[str]                          = None
    Name       : Typing.Optional[str]                          = None
    EntityType : Character.EntityType                          = Character.EntityType.Companion
    IsPublic   : bool                                          = True
    SummaryData: Typing.Dict[str, Typing.Any]                  = Pydantic.Field(default_factory = dict)
    DetailData : Typing.Dict[str, Typing.Any]                  = Pydantic.Field(default_factory = dict)

class CharacterTransferRequest(Pydantic.BaseModel):
    OwnerID          : Typing.Optional[str] = None
    ParentCharacterID: Typing.Optional[str] = None

def DeepMergeDictionaries(BaseDictionary: Typing.Dict[str, Typing.Any], PatchDictionary: Typing.Dict[str, Typing.Any]) -> Typing.Dict[str, Typing.Any]:
    MergedDictionary: Typing.Dict[str, Typing.Any] = dict(BaseDictionary)
    for PatchKey, PatchValue in PatchDictionary.items():
        ExistingValue: Typing.Any = MergedDictionary.get(PatchKey)
        if isinstance(ExistingValue, dict) and isinstance(PatchValue, dict):
            MergedDictionary[PatchKey] = DeepMergeDictionaries(ExistingValue, PatchValue)

        else:
            MergedDictionary[PatchKey] = PatchValue

    return MergedDictionary

def SerializeCharacterRecord(TargetCharacter: Character.Character, CallerContext: Typing.Any = None) -> Typing.Dict[str, Typing.Any]:
    IsService  : bool                     = RoleBasedAccessControl.IsServiceContext(CallerContext)
    CurrentUser: Typing.Optional[User.User] = CallerContext if isinstance(CallerContext, User.User) else None
    CreatedAtString: str                  = TargetCharacter.CreatedAt.isoformat() if TargetCharacter.CreatedAt else ""
    UpdatedAtString: str                  = TargetCharacter.UpdatedAt.isoformat() if TargetCharacter.UpdatedAt else CreatedAtString
    EntityTypeValue: str                  = TargetCharacter.EntityType.value if hasattr(TargetCharacter.EntityType, "value") else str(TargetCharacter.EntityType)
    GameSystemValue: str                  = TargetCharacter.GameSystem.value if hasattr(TargetCharacter.GameSystem, "value") else str(TargetCharacter.GameSystem)

    OwnerPayload: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
    if (TargetCharacter.Owner is not None):
        if IsService or (CurrentUser is not None):
            OwnerPayload = {
                "ID"         : TargetCharacter.Owner.ID,
                "DiscordID"  : TargetCharacter.Owner.DiscordID,
                "Username"   : TargetCharacter.Owner.Username,
                "DisplayName": TargetCharacter.Owner.DisplayName
            }

        else:
            OwnerPayload = {
                "Username"   : TargetCharacter.Owner.Username,
                "DisplayName": TargetCharacter.Owner.DisplayName
            }

    return {
        "ID"               : TargetCharacter.ID,
        "OwnerID"          : TargetCharacter.OwnerID,
        "Name"             : TargetCharacter.Name,
        "GameSystem"       : GameSystemValue,
        "EntityType"       : EntityTypeValue,
        "ParentCharacterID": TargetCharacter.ParentCharacterID,
        "IsPublic"         : TargetCharacter.IsPublic,
        "IsArchived"       : TargetCharacter.IsArchived,
        "IsPinned"         : TargetCharacter.IsPinned,
        "IsAccepted"       : TargetCharacter.IsAccepted,
        "IsProtected"      : TargetCharacter.IsProtected,
        "IsOverridden"     : TargetCharacter.IsOverridden,
        "ImportSource"     : TargetCharacter.ImportSource,
        "SummaryData"      : dict(TargetCharacter.SummaryData or {}),
        "DetailData"       : dict(TargetCharacter.DetailData or {}),
        "Owner"            : OwnerPayload,
        "CanModify"        : True if IsService else RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter),
        "CanArchive"       : True if IsService else RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, TargetCharacter),
        "CreatedAt"        : CreatedAtString,
        "UpdatedAt"        : UpdatedAtString
    }

def ParseEntityTypeParameter(RawEntityType: Typing.Optional[str], DefaultType: Character.EntityType = Character.EntityType.Character) -> Character.EntityType:
    if (RawEntityType is None) or (not RawEntityType.strip()):
        return DefaultType

    Cleaned: str = RawEntityType.strip()
    for Candidate in Character.EntityType:
        if (Candidate.value.lower() == Cleaned.lower()):
            return Candidate

    return DefaultType

def BuildCharacterDisplayEntry(CharacterRecord: Character.Character, CurrentUser: Typing.Optional[User.User] = None) -> Typing.Dict[str, Typing.Any]:
    SummaryData   : Typing.Dict[str, Typing.Any] = CharacterRecord.SummaryData or {}
    DetailData    : Typing.Dict[str, Typing.Any] = CharacterRecord.DetailData or {}
    GameSystemName: str                          = CharacterRecord.GameSystem.value if hasattr(CharacterRecord.GameSystem, "value") else str(CharacterRecord.GameSystem)
    EntityTypeName: str                          = CharacterRecord.EntityType.value if hasattr(CharacterRecord.EntityType, "value") else str(CharacterRecord.EntityType)
    FirstName     : str                          = CharacterRecord.Name.strip().split()[0] if (CharacterRecord.Name and CharacterRecord.Name.strip()) else ""

    CharacterClass    : str = ""
    CharacterSpecies  : str = ""
    CharacterLevel    : int = 1
    CharacterCareer   : str = ""
    CharacterHomeworld: str = ""
    CharacterTerms    : int = 1
    VehicleType       : str = str(DetailData.get("VehicleType") or SummaryData.get("VehicleType") or "Vehicle")
    VehicleHullPoints : int = int(DetailData.get("HullPoints") or SummaryData.get("HullPoints") or 0)
    VehicleMaxHull    : int = int(DetailData.get("MaxHullPoints") or SummaryData.get("MaxHullPoints") or VehicleHullPoints)
    RawMGT2EArmor     : Typing.Any = DetailData.get("Armor")
    VehicleArmor      : int = int(RawMGT2EArmor.get("Protection", 0)) if isinstance(RawMGT2EArmor, dict) else int(RawMGT2EArmor or 0)
    RawDNDAC          : Typing.Any = DetailData.get("ArmorClass")
    VehicleArmorClass : int = int(RawDNDAC.get("TotalArmorClass", 15)) if isinstance(RawDNDAC, dict) else int(RawDNDAC or 15)
    LevelSortValue    : int = 1

    if CharacterRecord.GameSystem == Character.GameSystemType.DND5E:
        CharacterClass   = str(SummaryData.get("Class", ""))
        CharacterSpecies = str(SummaryData.get("Species", ""))
        RawLevelValue    = SummaryData.get("Level")
        CharacterLevel   = int(RawLevelValue) if (RawLevelValue is not None) else 1
        LevelSortValue   = VehicleHullPoints if (EntityTypeName == "Vehicle") else CharacterLevel

    elif CharacterRecord.GameSystem == Character.GameSystemType.MGT2E:
        CharacterCareer    = str(SummaryData.get("Career", ""))
        CharacterHomeworld = str(SummaryData.get("Homeworld", ""))
        RawTermsValue      = SummaryData.get("Terms")
        CharacterTerms     = int(RawTermsValue) if (RawTermsValue is not None) else 1
        LevelSortValue     = VehicleHullPoints if (EntityTypeName == "Vehicle") else CharacterTerms

    PortraitURL     : Typing.Optional[str] = SummaryData.get("PortraitURL")
    PortraitFileID  : Typing.Optional[str] = SummaryData.get("PortraitFileID")
    ClassDisplay    : str                  = CharacterClass or "Adventurer"
    CareerDisplay   : str                  = CharacterCareer or "Citizen"
    HomeworldDisplay: str                  = CharacterHomeworld or "Core"
    HitPointsValue  : int                  = int(SummaryData.get("HitPoints", 10) or 10)
    ModifiedDateText: str                  = CharacterRecord.UpdatedAt.strftime("%Y-%m-%d %H:%M") if CharacterRecord.UpdatedAt else ""

    if (EntityTypeName == "Vehicle"):
        DetailsText: str = f"{VehicleType} | Hull: {VehicleHullPoints}/{VehicleMaxHull} | " + (f"Armor: {VehicleArmor}" if (GameSystemName == "MGT2E") else f"AC: {VehicleArmorClass}")

    elif (CharacterRecord.GameSystem == Character.GameSystemType.DND5E):
        DetailsText = f"Class: {ClassDisplay} | Level {CharacterLevel} | HP: {HitPointsValue}"

    else:
        DetailsText = f"Career: {CareerDisplay} | Terms: {CharacterTerms} | Homeworld: {HomeworldDisplay}"

    return {
        "Character"         : CharacterRecord,
        "GameSystemName"    : GameSystemName,
        "EntityTypeName"    : EntityTypeName,
        "FirstName"         : FirstName,
        "CharacterClass"    : CharacterClass,
        "CharacterSpecies"  : CharacterSpecies,
        "CharacterLevel"    : CharacterLevel,
        "CharacterCareer"   : CharacterCareer,
        "CharacterHomeworld": CharacterHomeworld,
        "CharacterTerms"    : CharacterTerms,
        "VehicleType"       : VehicleType,
        "VehicleHullPoints" : VehicleHullPoints,
        "VehicleMaxHull"    : VehicleMaxHull,
        "VehicleArmor"      : VehicleArmor,
        "VehicleArmorClass" : VehicleArmorClass,
        "PortraitURL"       : PortraitURL,
        "PortraitFileID"    : PortraitFileID,
        "DetailsText"       : DetailsText,
        "ModifiedDateText"  : ModifiedDateText,
        "LevelSortValue"    : LevelSortValue,
        "CanModify"         : RoleBasedAccessControl.CanModifyCharacter(CurrentUser, CharacterRecord),
        "CanArchive"        : RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, CharacterRecord)
    }

def ParseIntField(FormData: Typing.Any, Key: str, Default: int = 0) -> int:
    RawValue = FormData.get(Key)
    if (RawValue is None) or (str(RawValue).strip() == ""):
        return Default

    return int(float(str(RawValue).strip()))

def ParseMGT2ESkillsText(RawSkillsText: str) -> Typing.Dict[str, int]:
    SkillsDictionary: Typing.Dict[str, int] = {}
    for RawLine in RegularExpressions.split(r"[\n,;]+", RawSkillsText or ""):
        CleanedLine: str = RawLine.strip()
        if not CleanedLine:
            continue

        if (":" in CleanedLine):
            SkillPart, LevelPart = CleanedLine.split(":", 1)
            SkillName: str = SkillPart.strip().lower()
            if SkillName:
                try:
                    SkillsDictionary[SkillName] = int(LevelPart.strip())

                except ValueError:
                    SkillsDictionary[SkillName] = 0

        else:
            SkillsDictionary[CleanedLine.lower()] = 0

    return SkillsDictionary

def ParseManualMGT2EAndVehicleData(FormData: Typing.Any, Name: str, GameSystem: Character.GameSystemType, EntityTypeValue: Character.EntityType, PortraitFileID: Typing.Optional[str]) -> Typing.Tuple[Typing.Dict[str, Typing.Any], Typing.Dict[str, Typing.Any]]:
    if (EntityTypeValue == Character.EntityType.Vehicle):
        VehicleType  : str = str(FormData.get("VehicleType") or ("Type-S Scout/Courier" if (GameSystem == Character.GameSystemType.MGT2E) else "Sailing Ship")).strip()
        HullPoints   : int = ParseIntField(FormData, "HullPoints", 40 if (GameSystem == Character.GameSystemType.MGT2E) else 100)
        MaxHullPoints: int = ParseIntField(FormData, "MaxHullPoints", HullPoints)
        CrewCapacity : int = ParseIntField(FormData, "CrewCapacity", 4)

        if (GameSystem == Character.GameSystemType.MGT2E):
            VehicleArmorRating: int = ParseIntField(FormData, "VehicleArmor", ParseIntField(FormData, "Armor", 4))
            ThrustValue       : int = ParseIntField(FormData, "Thrust", 2)
            JumpRatingValue   : int = ParseIntField(FormData, "JumpRating", 0)
            PowerPointsValue  : int = ParseIntField(FormData, "PowerPoints", 20)
            FuelValue         : int = ParseIntField(FormData, "Fuel", 20)
            MaxFuelValue      : int = ParseIntField(FormData, "MaxFuel", FuelValue)
            WeaponsList       : Typing.List[Typing.Dict[str, str]] = []
            for RawWeaponLine in str(FormData.get("VehicleWeapons") or "").splitlines():
                CleanedLine: str = RawWeaponLine.strip()
                if not CleanedLine:
                    continue

                Parts: Typing.List[str] = [Part.strip() for Part in CleanedLine.split("|")]
                WeaponsList.append({"Name": Parts[0], "Damage": Parts[1] if (len(Parts) > 1 and Parts[1]) else "2D"})

            SummaryData: Typing.Dict[str, Typing.Any] = {
                "System"        : GameSystem.value,
                "EntityType"    : EntityTypeValue.value,
                "VehicleType"   : VehicleType,
                "HullPoints"    : HullPoints,
                "MaxHullPoints" : MaxHullPoints,
                "PortraitFileID": PortraitFileID
            }
            DetailData: Typing.Dict[str, Typing.Any] = {
                "Name"          : Name,
                "GameSystem"    : GameSystem.value,
                "VehicleType"   : VehicleType,
                "HullPoints"    : HullPoints,
                "MaxHullPoints" : MaxHullPoints,
                "Armor"         : VehicleArmorRating,
                "Thrust"        : ThrustValue,
                "JumpRating"    : JumpRatingValue,
                "PowerPoints"   : PowerPointsValue,
                "Fuel"          : FuelValue,
                "MaxFuel"       : MaxFuelValue,
                "CrewCapacity"  : CrewCapacity,
                "Weapons"       : WeaponsList,
                "PortraitFileID": PortraitFileID
            }
            return (SummaryData, DetailData)

        VehicleArmorClass: int = ParseIntField(FormData, "VehicleArmorClass", 15)
        DamageThreshold  : int = ParseIntField(FormData, "DamageThreshold", 0)
        VehicleSpeedText : str = str(FormData.get("VehicleSpeed") or "30 ft").strip()
        AttacksList      : Typing.List[Typing.Dict[str, Typing.Any]] = []
        for RawAttackLine in str(FormData.get("VehicleAttacks") or "").splitlines():
            CleanedLine = RawAttackLine.strip()
            if not CleanedLine:
                continue

            Parts = [Part.strip() for Part in CleanedLine.split("|")]
            AttackBonusVal: int = 0
            if (len(Parts) > 1) and Parts[1]:
                try:
                    AttackBonusVal = int(Parts[1])

                except ValueError:
                    AttackBonusVal = 0

            AttacksList.append({"Name": Parts[0], "AttackBonus": AttackBonusVal, "DamageExpression": Parts[2] if (len(Parts) > 2 and Parts[2]) else "1d10", "DamageType": Parts[3] if (len(Parts) > 3 and Parts[3]) else "Bludgeoning"})

        SummaryData = {
            "System"        : GameSystem.value,
            "EntityType"    : EntityTypeValue.value,
            "VehicleType"   : VehicleType,
            "HullPoints"    : HullPoints,
            "MaxHullPoints" : MaxHullPoints,
            "ArmorClass"    : VehicleArmorClass,
            "PortraitFileID": PortraitFileID
        }
        DetailData = {
            "Name"           : Name,
            "GameSystem"     : GameSystem.value,
            "VehicleType"    : VehicleType,
            "HullPoints"     : HullPoints,
            "MaxHullPoints"  : MaxHullPoints,
            "ArmorClass"     : VehicleArmorClass,
            "DamageThreshold": DamageThreshold,
            "Speed"          : VehicleSpeedText,
            "CrewCapacity"   : CrewCapacity,
            "Attacks"        : AttacksList,
            "PortraitFileID" : PortraitFileID
        }
        return (SummaryData, DetailData)

    CareerName   : str = str(FormData.get("Career") or FormData.get("ClassOrCareer") or "Citizen").strip()
    TermsCount   : int = ParseIntField(FormData, "Terms", ParseIntField(FormData, "LevelOrTerms", 1))
    AgeValue     : int = ParseIntField(FormData, "MGT2EAge", 18 + (TermsCount * 4))
    HomeworldName: str = str(FormData.get("Homeworld") or "Core").strip()
    TitleName    : str = str(FormData.get("Title") or "").strip()

    Characteristics   : Typing.Dict[str, int] = {}
    MaxCharacteristics: Typing.Dict[str, int] = {}
    for CharacteristicName in ["Strength", "Dexterity", "Endurance", "Intelligence", "Education", "SocialStanding"]:
        CurrentScore: int = ParseIntField(FormData, f"MGT2E{CharacteristicName}", ParseIntField(FormData, CharacteristicName, 7))
        MaxScore    : int = ParseIntField(FormData, f"MGT2EMax{CharacteristicName}", CurrentScore)
        Characteristics[CharacteristicName]    = max(0, CurrentScore)
        MaxCharacteristics[CharacteristicName] = max(0, MaxScore)

    SkillsDictionary: Typing.Dict[str, int]   = ParseMGT2ESkillsText(str(FormData.get("MGT2ESkills") or ""))
    ArmorName       : str                     = str(FormData.get("MGT2EArmorName") or "Cloth Armor").strip()
    ArmorProtection : int                     = ParseIntField(FormData, "MGT2EArmorProtection", 0)
    CreditsAmount   : int                     = ParseIntField(FormData, "MGT2ECredits", 0)
    InventoryItems  : Typing.List[str]        = [Item.strip() for Item in RegularExpressions.split(r"[\n,]+", str(FormData.get("MGT2EInventory") or "")) if Item.strip()]

    SummaryData = {
        "System"        : GameSystem.value,
        "EntityType"    : EntityTypeValue.value,
        "Career"        : CareerName,
        "Terms"         : TermsCount,
        "Age"           : AgeValue,
        "Homeworld"     : HomeworldName,
        "Title"         : TitleName or ("Citizen" if (Characteristics["SocialStanding"] < 10) else "Noble"),
        "PortraitFileID": PortraitFileID
    }
    DetailData = {
        "Name"              : Name,
        "GameSystem"        : GameSystem.value,
        "Career"            : CareerName,
        "Terms"             : TermsCount,
        "Age"               : AgeValue,
        "Homeworld"         : HomeworldName,
        "Title"             : SummaryData["Title"],
        "Characteristics"   : Characteristics,
        "MaxCharacteristics": MaxCharacteristics,
        "Skills"            : SkillsDictionary,
        "Armor"             : {
            "Name"      : ArmorName,
            "Protection": ArmorProtection
        },
        "Inventory"         : InventoryItems,
        "Currency"          : {
            "Credits": CreditsAmount
        },
        "PortraitFileID"    : PortraitFileID
    }
    return (SummaryData, DetailData)

@Router.get("/Partial", response_class = Responses.HTMLResponse)
async def ListCharactersPartial(SearchQuery: Typing.Optional[str] = None, EntityType: Typing.Optional[str] = "All", CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character)
    if SearchQuery and SearchQuery.strip():
        NormalizedSearchTerm: str = f"%{SearchQuery.strip()}%"
        QueryStatement = QueryStatement.where(Character.Character.Name.ilike(NormalizedSearchTerm))

    if EntityType and (EntityType != "All"):
        ResolvedFilterType: Character.EntityType = ParseEntityTypeParameter(EntityType)
        QueryStatement = QueryStatement.where(Character.Character.EntityType == ResolvedFilterType)

    QueryStatement = QueryStatement.order_by(Character.Character.IsPinned.desc(), Character.Character.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    AllCharacters = QueryResult.scalars().all()
    AccessibleCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for CharacterRecord in AllCharacters:
        if RoleBasedAccessControl.CanViewCharacter(CurrentUser, CharacterRecord):
            AccessibleCharacters.append(BuildCharacterDisplayEntry(CharacterRecord, CurrentUser))

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Rendered Characters Partial: {len(AccessibleCharacters)} of {len(AllCharacters)}")
    TemplateContext: Typing.Dict[str, Typing.Any] = {
        "Characters"        : AccessibleCharacters,
        "SearchQuery"       : SearchQuery or "",
        "SelectedEntityType": EntityType or "All"
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterListPartial.html", TemplateContext)

@Router.get("/Search/Partial", response_class = Responses.HTMLResponse)
async def SearchCharactersPartial(SearchQuery: Typing.Optional[str] = None, SortBy: Typing.Optional[str] = "Name", SortOrder: Typing.Optional[str] = "Ascending", GameSystem: Typing.Optional[str] = "DND5E", EntityType: Typing.Optional[str] = "All", DNDClass: Typing.Optional[str] = None, DNDSpecies: Typing.Optional[str] = None, DNDLevelMin: Typing.Optional[int] = 1, DNDLevelMax: Typing.Optional[int] = 20, TravellerCareer: Typing.Optional[str] = None, TravellerHomeworld: Typing.Optional[str] = None, TravellerTermsMin: Typing.Optional[int] = 1, TravellerTermsMax: Typing.Optional[int] = 10, IncludePrivate: Typing.Optional[bool] = False, IncludeArchived: Typing.Optional[bool] = False, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character)
    if SearchQuery and SearchQuery.strip():
        NormalizedTerm: str = f"%{SearchQuery.strip()}%"
        QueryStatement = QueryStatement.where(Character.Character.Name.ilike(NormalizedTerm))

    if GameSystem and (GameSystem != "All"):
        QueryStatement = QueryStatement.where(Character.Character.GameSystem == GameSystem)

    if EntityType and (EntityType != "All"):
        ResolvedFilterType: Character.EntityType = ParseEntityTypeParameter(EntityType)
        QueryStatement = QueryStatement.where(Character.Character.EntityType == ResolvedFilterType)

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

        DisplayEntry: Typing.Dict[str, Typing.Any] = BuildCharacterDisplayEntry(CharacterRecord, CurrentUser)
        if CharacterRecord.GameSystem == Character.GameSystemType.DND5E:
            CharacterClass  : str = DisplayEntry["CharacterClass"]
            CharacterSpecies: str = DisplayEntry["CharacterSpecies"]
            CharacterLevel  : int = DisplayEntry["CharacterLevel"]

            if DNDClass and DNDClass.strip() and (CharacterClass != DNDClass):
                continue

            if DNDSpecies and DNDSpecies.strip() and (CharacterSpecies != DNDSpecies):
                continue

            if (DisplayEntry["EntityTypeName"] != "Vehicle"):
                if (DNDLevelMin is not None) and (CharacterLevel < DNDLevelMin):
                    continue

                if (DNDLevelMax is not None) and (CharacterLevel > DNDLevelMax):
                    continue

        elif CharacterRecord.GameSystem == Character.GameSystemType.MGT2E:
            CharacterCareer   : str = DisplayEntry["CharacterCareer"]
            CharacterHomeworld: str = DisplayEntry["CharacterHomeworld"]
            CharacterTerms    : int = DisplayEntry["CharacterTerms"]

            if TravellerCareer and TravellerCareer.strip() and (CharacterCareer != TravellerCareer):
                continue

            if TravellerHomeworld and TravellerHomeworld.strip() and (CharacterHomeworld != TravellerHomeworld):
                continue

            if (DisplayEntry["EntityTypeName"] != "Vehicle"):
                if (TravellerTermsMin is not None) and (CharacterTerms < TravellerTermsMin):
                    continue

                if (TravellerTermsMax is not None) and (CharacterTerms > TravellerTermsMax):
                    continue

        FilteredCharacters.append(DisplayEntry)

    IsDescending: bool = (SortOrder == "Descending")
    if SortBy == "Level":
        FilteredCharacters.sort(key = lambda Entry: Entry["LevelSortValue"], reverse = IsDescending)

    elif SortBy == "ModifiedAt":
        FilteredCharacters.sort(key = lambda Entry: Entry["Character"].UpdatedAt or Entry["Character"].CreatedAt or DateTime.datetime.min.replace(tzinfo = DateTime.timezone.utc), reverse = IsDescending)

    else:
        FilteredCharacters.sort(key = lambda Entry: (Entry["Character"].Name or "").lower(), reverse = IsDescending)

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Rendered Search Characters: {len(FilteredCharacters)} Matches of {len(AllCharacters)}")
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Pin Failed: Character \"{CharacterID[:8]}…\" Not Found")
        Headers: Typing.Dict[str, str] = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Pin Forbidden for Character: \"{CharacterID[:8]}…\"")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if TargetCharacter.IsArchived and not TargetCharacter.IsPinned:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Pin Rejected: Character \"{CharacterID[:8]}…\" Is Archived")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Archived characters cannot be pinned."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not TargetCharacter.IsPinned:
        CountStatement = SQLAlchemy.select(SQLAlchemy.func.count(Character.Character.ID)).where(Character.Character.OwnerID == TargetCharacter.OwnerID, Character.Character.IsPinned == True)
        CountResult = await DatabaseSession.execute(CountStatement)
        PinnedCount: int = CountResult.scalar() or 0
        if PinnedCount >= 6:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Pin Limit Exceeded: {PinnedCount} of 6 Characters Pinned")
            Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Maximum of six pinned characters allowed."}), "HX-Reswap": "none"}
            return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

        TargetCharacter.IsPinned = True

    else:
        TargetCharacter.IsPinned = False

    await DatabaseSession.commit()
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Character Pin: ID=\"{CharacterID[:8]}…\", Pinned={TargetCharacter.IsPinned}")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.post("/{CharacterID}/Visibility/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterVisibilityPartial(CharacterID: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Visibility Toggle Failed: Character \"{CharacterID[:8]}…\" Not Found")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Visibility Toggle Forbidden for Character: \"{CharacterID[:8]}…\"")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    TargetCharacter.IsPublic = not TargetCharacter.IsPublic
    await DatabaseSession.commit()
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Character Visibility: ID=\"{CharacterID[:8]}…\", Public={TargetCharacter.IsPublic}")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.post("/{CharacterID}/Archive/Partial", response_class = Responses.HTMLResponse)
async def ArchiveCharacterPartial(CharacterID: str, SearchQuery: Typing.Optional[str] = None, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetCharacter: Typing.Optional[Character.Character] = QueryResult.scalars().first()
    if not TargetCharacter:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Archive Failed: Character \"{CharacterID[:8]}…\" Not Found")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Character not found."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if not RoleBasedAccessControl.CanArchiveCharacter(CurrentUser, TargetCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Archive Forbidden for Character: \"{CharacterID[:8]}…\"")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to archive this character."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    if TargetCharacter.IsPinned and not TargetCharacter.IsArchived:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Archive Rejected: Character \"{CharacterID[:8]}…\" Is Pinned")
        Headers = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Pinned characters cannot be archived. Unpin the character first."}), "HX-Reswap": "none"}
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    TargetCharacter.IsArchived = not TargetCharacter.IsArchived
    await DatabaseSession.commit()
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Character Archive: ID=\"{CharacterID[:8]}…\", Archived={TargetCharacter.IsArchived}")
    return await ListCharactersPartial(SearchQuery = SearchQuery, CurrentUser = CurrentUser, DatabaseSession = DatabaseSession)

@Router.get("")
async def ListCharacters(GameSystem: Typing.Optional[Character.GameSystemType] = None, EntityType: Typing.Optional[Character.EntityType] = None, ShowArchived: bool = False, CallerContext: Typing.Union[User.User, Typing.Dict[str, Typing.Any], None] = FastAPI.Depends(RoleBasedAccessControl.GetOptionalServiceOrUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.List[Typing.Dict[str, Typing.Any]]:
    IsService  : bool                     = RoleBasedAccessControl.IsServiceContext(CallerContext)
    CurrentUser: Typing.Optional[User.User] = CallerContext if isinstance(CallerContext, User.User) else None
    QueryStatement = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner))
    if GameSystem:
        QueryStatement = QueryStatement.where(Character.Character.GameSystem == GameSystem)

    if EntityType:
        QueryStatement = QueryStatement.where(Character.Character.EntityType == EntityType)

    if (not ShowArchived) or (not IsService and (CurrentUser is None)):
        QueryStatement = QueryStatement.where(Character.Character.IsArchived == False)

    QueryStatement = QueryStatement.order_by(Character.Character.IsPinned.desc(), Character.Character.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    AllCharacters = QueryResult.scalars().all()
    VisibleCharacters: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for Char in AllCharacters:
        if IsService or RoleBasedAccessControl.CanViewCharacter(CurrentUser, Char):
            VisibleCharacters.append(SerializeCharacterRecord(Char, CallerContext))

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Listed Characters: {len(VisibleCharacters)} Visible of {len(AllCharacters)}")
    return VisibleCharacters

@Router.post("")
async def CreateCharacter(RequestPayload: CharacterCreateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Character Creation Forbidden: System=\"{RequestPayload.GameSystem.value}\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role is not permitted to create characters")

    OwnerID: str = RequestPayload.TargetOwnerID if (RequestPayload.TargetOwnerID and CurrentUser.Role in (User.UserRole.GameMaster, User.UserRole.Administrator)) else CurrentUser.ID
    IsProtectedValue: bool = True if ((RequestPayload.ImportSource in ("DC1", "DC2")) or RequestPayload.IsProtected) else False
    NowTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.timezone.utc)
    NewCharacter = Character.Character(OwnerID = OwnerID, Name = RequestPayload.Name, GameSystem = RequestPayload.GameSystem, EntityType = RequestPayload.EntityType, ParentCharacterID = RequestPayload.ParentCharacterID, IsPublic = RequestPayload.IsPublic, IsAccepted = RequestPayload.IsAccepted, IsProtected = IsProtectedValue, IsOverridden = RequestPayload.IsOverridden, ImportSource = RequestPayload.ImportSource, SummaryData = RequestPayload.SummaryData, DetailData = RequestPayload.DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
    DatabaseSession.add(NewCharacter)
    await DatabaseSession.commit()
    QueryStatement = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ID == NewCharacter.ID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    NewCharacter   = QueryResult.scalars().first() or NewCharacter
    if not NewCharacter.IsAccepted:
        await Mailbox.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = NewCharacter.OwnerID, Subject = f"Character '{NewCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour character '{NewCharacter.Name}' ({NewCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = NewCharacter.ID)

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created Character: \"{NewCharacter.Name}\" (ID=\"{NewCharacter.ID[:8]}…\")")
    return SerializeCharacterRecord(NewCharacter, CurrentUser)

@Router.post("/Portrait/Upload/Partial", response_class = Responses.HTMLResponse)
async def UploadCharacterPortraitPartial(File: FastAPI.UploadFile = FastAPI.File(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not RoleBasedAccessControl.IsUserInGuild(CurrentUser):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Portrait Upload Rejected: User \"{CurrentUser.ID[:8]}…\" Not in Guild")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Discord server membership required")

    RawBytes: bytes = await File.read()
    SanitizedBytes, ContentType = ImageProcessing.GLOBAL_IMAGE_PROCESSING_SERVICE.SanitizeAndOptimizeImage(RawBytes, File.filename or "portrait.jpg")
    FileSizeBytes: int = len(SanitizedBytes)
    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Portrait Upload Rejected: Quota Exceeded ({FileSizeBytes}B Needed)")
        raise FastAPI.HTTPException(status_code = 400, detail = "Storage quota exceeded")

    OriginalFileName: str = File.filename or "portrait.jpg"
    ObjectKey: Typing.Optional[str] = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, OriginalFileName, ContentType, SanitizedBytes)
    if not ObjectKey:
        Debug.LogMessage(Level = Debug.LogLevel.Error, Message = "Portrait Storage Failed with Provider Error")
        raise FastAPI.HTTPException(status_code = 500, detail = "Storage provider error during portrait upload")

    NewStorageFile = StorageFile.StorageFile(OwnerID = CurrentUser.ID, FileName = OriginalFileName, ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey)
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewStorageFile)
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Portrait Upload Succeeded: FileID=\"{NewStorageFile.ID[:8]}…\", Size={FileSizeBytes}B")

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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Portrait Selection Failed: File \"{FileID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Selected Character Portrait: FileID=\"{TargetFile.ID[:8]}…\"")
    Context: Typing.Dict[str, Typing.Any] = {
        "PortraitFileID": TargetFile.ID
    }
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterPortraitPartial.html", Context, Headers = {"HX-Trigger": "portraitSelected"})

@Router.post("/Manual/Partial", response_class = Responses.HTMLResponse)
async def CreateCharacterManualPartial(Request: FastAPI.Request, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    FormData = await Request.form()
    GameSystemValue: str = str(FormData.get("GameSystem") or "DND5E")
    try:
        GameSystem: Character.GameSystemType = Character.GameSystemType(GameSystemValue)

    except ValueError:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Manual Character Creation Rejected: Invalid System \"{GameSystemValue}\"")
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Manual Character Creation Rejected: Empty Name")
        Context = {
            "IsSuccess"   : False,
            "ErrorMessage": "Character name cannot be blank."
        }
        ResponseHeaders = {
            "HX-Trigger": JSON.dumps({"characterSaveError": {"ErrorMessage": "Character name cannot be blank."}})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

    if not RoleBasedAccessControl.CanCreateCharacter(CurrentUser, GameSystem):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Manual Character Creation Forbidden: System=\"{GameSystem.value}\"")
        Context = {
            "IsSuccess"   : False,
            "ErrorMessage": "Your role does not have permission to create characters."
        }
        ResponseHeaders = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to create characters."})
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterManualCreationResultPartial.html", Context, 200, ResponseHeaders)

    PlayerName     : Typing.Optional[str]  = FormData.get("PlayerName")
    PortraitFileID : Typing.Optional[str]  = FormData.get("PortraitFileID")
    IsPublic       : bool                  = str(FormData.get("IsPublic", "true")).lower() in ["true", "1", "on"]
    EntityTypeValue: Character.EntityType  = ParseEntityTypeParameter(str(FormData.get("EntityType") or "Character"))
    RawParentID    : Typing.Optional[str]  = str(FormData.get("ParentCharacterID") or "").strip() or None
    ParentCharID   : Typing.Optional[str]  = RawParentID if (EntityTypeValue in (Character.EntityType.Companion, Character.EntityType.Vehicle)) else None

    try:
        if (GameSystem == Character.GameSystemType.DND5E) and (EntityTypeValue != Character.EntityType.Vehicle):
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
            SummaryData, DetailData = ParseManualMGT2EAndVehicleData(FormData = FormData, Name = Name, GameSystem = GameSystem, EntityTypeValue = EntityTypeValue, PortraitFileID = PortraitFileID)

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
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Manual Character Update Forbidden: ID=\"{CharacterID[:8]}…\"")
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
                ExistingCharacter.EntityType = EntityTypeValue
                if (ParentCharID is not None) and (ParentCharID != ExistingCharacter.ID):
                    ExistingCharacter.ParentCharacterID = ParentCharID

                elif (EntityTypeValue not in (Character.EntityType.Companion, Character.EntityType.Vehicle)):
                    ExistingCharacter.ParentCharacterID = None

                ExistingCharacter.IsPublic = IsPublic
                ExistingCharacter.IsProtected = IsProtectedState
                ExistingCharacter.IsOverridden = IsOverriddenState
                ExistingCharacter.SummaryData = SummaryData
                ExistingCharacter.DetailData = DetailData
                Attributes.flag_modified(ExistingCharacter, "SummaryData")
                Attributes.flag_modified(ExistingCharacter, "DetailData")
                ExistingCharacter.UpdatedAt = NowTimestamp
                await DatabaseSession.commit()
                await DatabaseSession.refresh(ExistingCharacter)
                SavedCharacter = ExistingCharacter
                Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Manual Character Updated: \"{SavedCharacter.Name}\" (ID=\"{SavedCharacter.ID[:8]}…\")")

            else:
                NewCharacter = Character.Character(OwnerID = CurrentUser.ID, Name = Name, GameSystem = GameSystem, EntityType = EntityTypeValue, ParentCharacterID = ParentCharID, IsPublic = IsPublic, IsAccepted = False, IsProtected = IsProtectedState, IsOverridden = IsOverriddenState, SummaryData = SummaryData, DetailData = DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
                DatabaseSession.add(NewCharacter)
                await DatabaseSession.commit()
                await DatabaseSession.refresh(NewCharacter)
                SavedCharacter = NewCharacter
                await Mailbox.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = SavedCharacter.OwnerID, Subject = f"Character '{SavedCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour character '{SavedCharacter.Name}' ({SavedCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = SavedCharacter.ID)
                Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Manual Character Created: \"{SavedCharacter.Name}\" (ID=\"{SavedCharacter.ID[:8]}…\")")

        else:
            NewCharacter = Character.Character(OwnerID = CurrentUser.ID, Name = Name, GameSystem = GameSystem, EntityType = EntityTypeValue, ParentCharacterID = ParentCharID, IsPublic = IsPublic, IsAccepted = False, IsProtected = IsProtectedState, IsOverridden = IsOverriddenState, SummaryData = SummaryData, DetailData = DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
            DatabaseSession.add(NewCharacter)
            await DatabaseSession.commit()
            await DatabaseSession.refresh(NewCharacter)
            SavedCharacter = NewCharacter
            await Mailbox.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = SavedCharacter.OwnerID, Subject = f"Character '{SavedCharacter.Name}' Submitted for Review", Body = f"Greetings.\n\nYour character '{SavedCharacter.Name}' ({SavedCharacter.GameSystem.value}) has been placed into the queue for review by a character checker.\n\nYou will receive a notification once the review is completed.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = SavedCharacter.ID)
            Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Manual Character Created: \"{SavedCharacter.Name}\" (ID=\"{SavedCharacter.ID[:8]}…\")")

    except Exception as SaveException:
        Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Manual Character Save Error: {type(SaveException).__name__}")
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Protect Character Forbidden: ID=\"{CharacterID[:8]}…\"")
        Headers = {
            "HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "You do not have the permission to use this feature."}),
            "HX-Reswap" : "none"
        }
        return Responses.HTMLResponse(content = "", status_code = 200, headers = Headers)

    FormData = await Request.form()
    ActiveTab: str = str(FormData.get("ActiveTab") or "CharacterSheetOverviewTab").strip()
    if (ActiveTab not in ("CharacterSheetOverviewTab", "CharacterSheetAbilitiesTab", "CharacterSheetInventoryTab", "CharacterSheetDescriptionTab", "CharacterSheetCompanionsTab")):
        ActiveTab = "CharacterSheetOverviewTab"

    EntityTypeOverride       : Typing.Optional[str] = str(FormData.get("EntityType") or "").strip() or None
    ParentCharacterIDOverride: Typing.Optional[str] = str(FormData.get("ParentCharacterID") or "").strip() or None

    CurrentOverridden: bool = str(FormData.get("IsOverriddenState", "false")).lower() in ("true", "1", "on")
    if (((TargetCharacter is not None) and TargetCharacter.IsOverridden) or ((TargetCharacter is None) and CurrentOverridden)):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Protect Character Rejected: Override Active (ID=\"{CharacterID[:8]}…\")")
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
                StoredFileID: Typing.Optional[str] = await CharacterImport.GLOBAL_CHARACTER_IMPORTER.DownloadAndStorePortrait(CurrentUser, ExistingPortraitURL, DatabaseSession)
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
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Character Protection: ID=\"{CharacterID[:8]}…\", Protected={TargetCharacter.IsProtected}")
        Context: Typing.Dict[str, Typing.Any] = CharacterMapping.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = TargetCharacter, IsAllowed = True, IsProtected = TargetCharacter.IsProtected, IsOverridden = TargetCharacter.IsOverridden, ActiveTab = ActiveTab, EntityTypeOverride = EntityTypeOverride, ParentCharacterIDOverride = ParentCharacterIDOverride)

    else:
        CurrentProtected: bool = str(FormData.get("IsProtectedState", "false")).lower() in ("true", "1", "on")
        NewProtectedState: bool = not CurrentProtected
        GameSystemValue: str = str(FormData.get("GameSystem") or "DND5E")
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Draft Protection: Protected={NewProtectedState}")
        Context = CharacterMapping.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = None, DetailDataOverride = dict(FormData), IsAllowed = True, IsProtected = NewProtectedState, IsOverridden = False, ActiveTab = ActiveTab, EntityTypeOverride = EntityTypeOverride, ParentCharacterIDOverride = ParentCharacterIDOverride)
        Context["GameSystem"] = GameSystemValue

    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterSheetWindow.html", Context)

@Router.post("/{CharacterID}/Override/Partial", response_class = Responses.HTMLResponse)
async def ToggleCharacterOverridePartial(CharacterID: str, Request: FastAPI.Request, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if ((not CurrentUser) or (not RoleBasedAccessControl.CanOverrideCharacter(CurrentUser))):
        UserID: str = CurrentUser.ID if (CurrentUser is not None) else "AnonymousUser"
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Override Character Forbidden: ID=\"{CharacterID[:8]}…\"")
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
    if (ActiveTab not in ("CharacterSheetOverviewTab", "CharacterSheetAbilitiesTab", "CharacterSheetInventoryTab", "CharacterSheetDescriptionTab", "CharacterSheetCompanionsTab")):
        ActiveTab = "CharacterSheetOverviewTab"

    EntityTypeOverride       : Typing.Optional[str] = str(FormData.get("EntityType") or "").strip() or None
    ParentCharacterIDOverride: Typing.Optional[str] = str(FormData.get("ParentCharacterID") or "").strip() or None

    if (TargetCharacter is not None):
        NewOverriddenValue: bool = not TargetCharacter.IsOverridden
        TargetCharacter.IsOverridden = NewOverriddenValue
        if (NewOverriddenValue):
            TargetCharacter.IsProtected = False

        await DatabaseSession.commit()
        await DatabaseSession.refresh(TargetCharacter)
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Character Override: ID=\"{CharacterID[:8]}…\", Overridden={TargetCharacter.IsOverridden}")
        Context = CharacterMapping.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = TargetCharacter, IsAllowed = True, IsProtected = TargetCharacter.IsProtected, IsOverridden = TargetCharacter.IsOverridden, ActiveTab = ActiveTab, EntityTypeOverride = EntityTypeOverride, ParentCharacterIDOverride = ParentCharacterIDOverride)

    else:
        CurrentProtected: bool = str(FormData.get("IsProtectedState", "false")).lower() in ("true", "1", "on")
        CurrentOverridden: bool = str(FormData.get("IsOverriddenState", "false")).lower() in ("true", "1", "on")
        NewOverriddenState: bool = not CurrentOverridden
        NewProtectedState: bool = False if (NewOverriddenState) else (CurrentProtected)
        GameSystemValue: str = str(FormData.get("GameSystem") or "DND5E")
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Toggled Draft Override: Overridden={NewOverriddenState}")
        Context = CharacterMapping.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = None, DetailDataOverride = dict(FormData), IsAllowed = True, IsProtected = NewProtectedState, IsOverridden = NewOverriddenState, ActiveTab = ActiveTab, EntityTypeOverride = EntityTypeOverride, ParentCharacterIDOverride = ParentCharacterIDOverride)
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"External Character Import Rejected: DiscordID=\"{TargetDiscordID}\" Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"User with DiscordID '{TargetDiscordID}' not found")

    try:
        NewCharacter: Character.Character = await CharacterImport.GLOBAL_CHARACTER_IMPORTER.ImportCharacterFromURL(RequestPayload.ImportURL, TargetUser.ID, DatabaseSession)
        QueryStatement = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ID == NewCharacter.ID)
        QueryResult    = await DatabaseSession.execute(QueryStatement)
        NewCharacter   = QueryResult.scalars().first() or NewCharacter
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"External Character Imported: Name=\"{NewCharacter.Name}\", ID={NewCharacter.ID}, Owner={TargetUser.DisplayName}")
        return Responses.JSONResponse(status_code = FastAPI.status.HTTP_201_CREATED, content = SerializeCharacterRecord(NewCharacter, TokenPayload))

    except ValueError as ValidationError:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"External Character Import Invalid URL: {str(ValidationError)}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = str(ValidationError))

    except Exception as ImportException:
        Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"External Character Import Failed: {type(ImportException).__name__} - {str(ImportException)}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_500_INTERNAL_SERVER_ERROR, detail = f"Character import failed: {str(ImportException)}")

@Router.post("/Import/Partial", response_class = Responses.HTMLResponse)
@Router.post("/Import/Partial/", response_class = Responses.HTMLResponse)
@Router.post("/import/partial", response_class = Responses.HTMLResponse)
async def ImportCharacterPartial(Request: FastAPI.Request, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if ((CurrentUser.Role == User.UserRole.Visitor) or (not RoleBasedAccessControl.IsUserInGuild(CurrentUser)) or (not RoleBasedAccessControl.CanCreateCharacter(CurrentUser, Character.GameSystemType.DND5E))):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Character Import Denied: User \"{CurrentUser.ID[:8]}…\" Unauthorized")
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Character Import Rejected: Empty URL Provided")
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
        NewCharacter: Character.Character = await CharacterImport.GLOBAL_CHARACTER_IMPORTER.ImportCharacterFromURL(ImportURL, CurrentUser.ID, DatabaseSession)
        UtilityName: str = "Dicecloud v1" if (NewCharacter.ImportSource == "DC1") else ("Dicecloud v2" if (NewCharacter.ImportSource == "DC2") else "D&D Beyond")
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
        Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Character Import Error: {type(ImportException).__name__}")
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

    SourceType, CharacterID, UtilityName = CharacterImport.GLOBAL_CHARACTER_IMPORTER.DetectImportSource(TargetURL)
    if ((SourceType is None) or (CharacterID is None)):
        Context: Typing.Dict[str, Typing.Any] = {
            "IsReady"     : False,
            "ErrorMessage": "Awaiting a valid Dicecloud v1 or D&D Beyond character URL.",
            "Overview"    : None
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportOverviewPartial.html", Context, 200)

    try:
        Overview: Typing.Dict[str, Typing.Any] = await CharacterImport.GLOBAL_CHARACTER_IMPORTER.GetCharacterOverview(TargetURL)
        Context: Typing.Dict[str, Typing.Any] = {
            "IsReady"     : True,
            "ErrorMessage": None,
            "Overview"    : Overview
        }
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterImportOverviewPartial.html", Context, 200)

    except Exception as OverviewException:
        Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Character Overview Error: {type(OverviewException).__name__}")
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Get Character Actions Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanViewCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Get Character Actions Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to view this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any]                  = FoundCharacter.DetailData or {}
    UnifiedActionsList  : Typing.List[AutomationModels.UnifiedActionEntry] = []

    StandardAttacksList = DetailDataDictionary.get("Attacks", [])
    if isinstance(StandardAttacksList, list):
        for AttackItem in StandardAttacksList:
            if isinstance(AttackItem, dict):
                UnifiedActionsList.append(AutomationModels.UnifiedActionEntry(ID = str(AttackItem.get("ID") or UUID.uuid4()), Name = str(AttackItem.get("Name", "Standard Attack")), SourceType = "StandardAttack", ActivationType = "Action", AttackBonus = int(AttackItem.get("AttackBonus", 0)) if (AttackItem.get("AttackBonus") is not None) else None, DamageExpression = str(AttackItem.get("DamageExpression", "")) if AttackItem.get("DamageExpression") else None, DamageType = str(AttackItem.get("DamageType", "")) if AttackItem.get("DamageType") else None, RangeDescription = str(AttackItem.get("RangeDescription", "")) if AttackItem.get("RangeDescription") else None, Phrase = None, ThumbnailURL = None, Automation = []))

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

                UnifiedActionsList.append(AutomationModels.UnifiedActionEntry(ID = str(CustomItem.get("ID") or UUID.uuid4()), Name = str(CustomItem.get("Name", "Custom Action")), SourceType = "CustomAutomation", ActivationType = RawActivationType, AttackBonus = None, DamageExpression = None, DamageType = None, RangeDescription = None, Phrase = CustomItem.get("Phrase"), ThumbnailURL = CustomItem.get("ThumbnailURL"), Automation = ParsedAutomation))

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Unified Actions: Character=\"{CharacterID[:8]}…\", Count={len(UnifiedActionsList)}")
    return UnifiedActionsList

@Router.post("/{CharacterID}/Actions", status_code = 201, response_model = AutomationModels.CustomAttackEntry)
async def CreateCharacterAction(CharacterID: str, RequestPayload: AutomationModels.CustomAttackCreateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> AutomationModels.CustomAttackEntry:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Create Character Action Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Create Character Action Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    ValidationResult = Automation.GLOBAL_AUTOMATION_SERVICE.ValidateAutomation(RequestPayload.Automation)
    if not ValidationResult.IsValid:
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Create Character Action Rejected: Invalid Automation Tree for \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 400, detail = {"Message": "Invalid automation specification", "Errors": ValidationResult.Errors})

    ActionID: str = RequestPayload.ID if ((RequestPayload.ID is not None) and (RequestPayload.ID.strip() != "")) else str(UUID.uuid4())
    NewAction = AutomationModels.CustomAttackEntry(ID = ActionID, Name = RequestPayload.Name.strip(), ActivationType = RequestPayload.ActivationType, Phrase = RequestPayload.Phrase, ThumbnailURL = RequestPayload.ThumbnailURL, Automation = RequestPayload.Automation, IsDirty = False)

    DetailDataDictionary : Typing.Dict[str, Typing.Any]              = dict(FoundCharacter.DetailData or {})
    ExistingCustomAttacks: Typing.List[Typing.Dict[str, Typing.Any]] = list(DetailDataDictionary.get("CustomAttacks") or [])
    ExistingCustomAttacks.append(NewAction.model_dump())
    DetailDataDictionary["CustomAttacks"] = ExistingCustomAttacks
    FoundCharacter.DetailData             = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created Character Action: ActionID=\"{NewAction.ID[:8]}…\", Character=\"{CharacterID[:8]}…\"")
    return NewAction

@Router.patch("/{CharacterID}/Actions/{ActionID}", response_model = AutomationModels.CustomAttackEntry)
async def UpdateCharacterAction(CharacterID: str, ActionID: str, RequestPayload: AutomationModels.CustomAttackUpdateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> AutomationModels.CustomAttackEntry:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Update Character Action Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Update Character Action Forbidden: Character \"{CharacterID[:8]}…\"")
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
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Update Character Action Failed: Action \"{ActionID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Action not found")

    if (RequestPayload.Automation is not None):
        ValidationResult = Automation.GLOBAL_AUTOMATION_SERVICE.ValidateAutomation(RequestPayload.Automation)
        if not ValidationResult.IsValid:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Update Character Action Rejected: Invalid Automation Tree for \"{ActionID[:8]}…\"")
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

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Updated Character Action: ActionID=\"{ActionID[:8]}…\", Character=\"{CharacterID[:8]}…\"")
    return UpdatedActionModel

@Router.delete("/{CharacterID}/Actions/{ActionID}")
async def DeleteCharacterAction(CharacterID: str, ActionID: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Delete Character Action Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Delete Character Action Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary : Typing.Dict[str, Typing.Any]              = dict(FoundCharacter.DetailData or {})
    ExistingCustomAttacks: Typing.List[Typing.Dict[str, Typing.Any]] = list(DetailDataDictionary.get("CustomAttacks") or [])
    OriginalLength       : int                                       = len(ExistingCustomAttacks)
    FilteredCustomAttacks = [ActionItem for ActionItem in ExistingCustomAttacks if str(ActionItem.get("ID")) != ActionID]
    if (len(FilteredCustomAttacks) == OriginalLength):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Delete Character Action Failed: Action \"{ActionID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Action not found")

    DetailDataDictionary["CustomAttacks"] = FilteredCustomAttacks
    FoundCharacter.DetailData             = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Deleted Character Action: ActionID=\"{ActionID[:8]}…\", Character=\"{CharacterID[:8]}…\"")
    return {"IsSuccess": True, "RemovedActionID": ActionID}

@Router.post("/{CharacterID}/Counters")
async def CreateOrUpdateCharacterCounter(CharacterID: str, RequestPayload: AutomationModels.CounterCreateOrUpdateRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Set Counter Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Set Counter Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any] = dict(FoundCharacter.DetailData or {})
    CountersDictionary  : Typing.Dict[str, Typing.Any] = dict(DetailDataDictionary.get("CustomCounters") or {})
    CounterModel = AutomationModels.CounterData(Value = RequestPayload.Value, MaxValue = RequestPayload.MaxValue, MinValue = RequestPayload.MinValue, ResetSchedule = RequestPayload.ResetSchedule, Description = RequestPayload.Description)
    CountersDictionary[RequestPayload.Name] = CounterModel.model_dump()
    DetailDataDictionary["CustomCounters"]  = CountersDictionary
    FoundCharacter.DetailData               = DetailDataDictionary
    Attributes.flag_modified(FoundCharacter, "DetailData")
    FoundCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(FoundCharacter)

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Set Counter: Name=\"{RequestPayload.Name}\", Character=\"{CharacterID[:8]}…\"")
    return {"CounterName": RequestPayload.Name, "Counter": CounterModel.model_dump()}

@Router.patch("/{CharacterID}/Counters/{CounterName}")
async def MutateCharacterCounter(CharacterID: str, CounterName: str, RequestPayload: AutomationModels.CounterMutationRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Mutate Counter Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Mutate Counter Forbidden: Character \"{CharacterID[:8]}…\"")
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    DetailDataDictionary: Typing.Dict[str, Typing.Any] = dict(FoundCharacter.DetailData or {})
    CountersDictionary  : Typing.Dict[str, Typing.Any] = dict(DetailDataDictionary.get("CustomCounters") or {})
    ExistingCounterRaw  = CountersDictionary.get(CounterName)
    if (ExistingCounterRaw is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Mutate Counter Failed: Counter \"{CounterName}\" Not Found")
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

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Mutated Counter: Name=\"{CounterName}\", Value={NewValue}, Character=\"{CharacterID[:8]}…\"")
    return {"CounterName": CounterName, "Counter": CounterModel.model_dump()}

@Router.post("/{CharacterID}/Variables")
async def SetCharacterVariables(CharacterID: str, RequestPayload: AutomationModels.VariableSetRequest, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.Dict[str, Typing.Any]:
    QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundCharacter = QueryResult.scalars().first()
    if (FoundCharacter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Set Variables Failed: Character \"{CharacterID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, FoundCharacter):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Set Variables Forbidden: Character \"{CharacterID[:8]}…\"")
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

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Set Variables: Character=\"{CharacterID[:8]}…\", VariableCount={len(VariablesDictionary)}")
    return {"Variables": VariablesDictionary}

async def BuildCompanionsPartialContext(CharacterID: str, CurrentUser: Typing.Optional[User.User], DatabaseSession: AsyncIO.AsyncSession) -> Typing.Dict[str, Typing.Any]:
    ParentStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    ParentResult    = await DatabaseSession.execute(ParentStatement)
    ParentRecord    = ParentResult.scalars().first()
    if (ParentRecord is None):
        return {
            "ParentCharacter"  : None,
            "LinkedCompanions" : [],
            "LinkableEntities" : [],
            "CanModify"        : False
        }

    CanModifyParent: bool = RoleBasedAccessControl.CanModifyCharacter(CurrentUser, ParentRecord)
    LinkedStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ParentCharacterID == CharacterID, Character.Character.EntityType.in_([Character.EntityType.Companion, Character.EntityType.Vehicle]), Character.Character.IsArchived == False).order_by(Character.Character.Name.asc())
    LinkedResult    = await DatabaseSession.execute(LinkedStatement)
    LinkedRecords   = [BuildCharacterDisplayEntry(Entry, CurrentUser) for Entry in LinkedResult.scalars().all() if RoleBasedAccessControl.CanViewCharacter(CurrentUser, Entry)]

    CandidateStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID != CharacterID, Character.Character.GameSystem == ParentRecord.GameSystem, Character.Character.EntityType.in_([Character.EntityType.Companion, Character.EntityType.Vehicle]), Character.Character.IsArchived == False, SQLAlchemy.or_(Character.Character.ParentCharacterID.is_(None), Character.Character.ParentCharacterID != CharacterID)).order_by(Character.Character.Name.asc())
    CandidateResult    = await DatabaseSession.execute(CandidateStatement)
    LinkableRecords    = [Entry for Entry in CandidateResult.scalars().all() if RoleBasedAccessControl.CanModifyCharacter(CurrentUser, Entry)]

    return {
        "ParentCharacter" : ParentRecord,
        "LinkedCompanions": LinkedRecords,
        "LinkableEntities": LinkableRecords,
        "CanModify"       : CanModifyParent
    }

@Router.get("/{CharacterID}/Companions", response_class = Responses.JSONResponse)
async def GetCharacterCompanions(CharacterID: str, CallerContext: Typing.Union[User.User, Typing.Dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.JSONResponse:
    IsService  : bool                     = RoleBasedAccessControl.IsServiceContext(CallerContext)
    CurrentUser: Typing.Optional[User.User] = CallerContext if isinstance(CallerContext, User.User) else None

    ParentStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    ParentResult    = await DatabaseSession.execute(ParentStatement)
    ParentCharacter = ParentResult.scalars().first()
    if (ParentCharacter is None):
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if (not IsService) and (not RoleBasedAccessControl.CanViewCharacter(CurrentUser, ParentCharacter)):
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to view this character")

    QueryStatement = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ParentCharacterID == CharacterID, Character.Character.EntityType.in_([Character.EntityType.Companion, Character.EntityType.Vehicle]), Character.Character.IsArchived == False).order_by(Character.Character.Name.asc())
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    CompanionsList = QueryResult.scalars().all()

    SerializedCompanions: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for CompanionRecord in CompanionsList:
        if IsService or RoleBasedAccessControl.CanViewCharacter(CurrentUser, CompanionRecord):
            SerializedCompanions.append(SerializeCharacterRecord(CompanionRecord, CallerContext))

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Listed Companions: ParentID=\"{CharacterID[:8]}…\", Count={len(SerializedCompanions)}")
    return Responses.JSONResponse(content = SerializedCompanions)

@Router.post("/{CharacterID}/Companions", response_class = Responses.JSONResponse)
async def CreateOrLinkCharacterCompanion(CharacterID: str, RequestPayload: CharacterCompanionLinkOrCreateRequest, CallerContext: Typing.Union[User.User, Typing.Dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.JSONResponse:
    IsService  : bool                     = RoleBasedAccessControl.IsServiceContext(CallerContext)
    CurrentUser: Typing.Optional[User.User] = CallerContext if isinstance(CallerContext, User.User) else None

    ParentStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    ParentResult    = await DatabaseSession.execute(ParentStatement)
    ParentCharacter = ParentResult.scalars().first()
    if (ParentCharacter is None):
        raise FastAPI.HTTPException(status_code = 404, detail = "Parent character not found")

    if (not IsService) and (not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, ParentCharacter)):
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to modify this character")

    if RequestPayload.CompanionID:
        if (RequestPayload.CompanionID == CharacterID):
            raise FastAPI.HTTPException(status_code = 400, detail = "Character cannot be linked to itself")

        CompanionStatement = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ID == RequestPayload.CompanionID)
        CompanionResult    = await DatabaseSession.execute(CompanionStatement)
        TargetCompanion    = CompanionResult.scalars().first()
        if (TargetCompanion is None):
            raise FastAPI.HTTPException(status_code = 404, detail = "Companion or vehicle not found")

        if TargetCompanion.EntityType not in (Character.EntityType.Companion, Character.EntityType.Vehicle):
            raise FastAPI.HTTPException(status_code = 400, detail = "Only Companion or Vehicle entities can be linked")

        if (TargetCompanion.GameSystem != ParentCharacter.GameSystem):
            raise FastAPI.HTTPException(status_code = 400, detail = "Linked entity must share the parent character's game system")

        if (not IsService) and (not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCompanion)) and (not RoleBasedAccessControl.IsGameMaster(CurrentUser)):
            raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to link this entity")

        TargetCompanion.ParentCharacterID = CharacterID
        TargetCompanion.UpdatedAt         = DateTime.datetime.now(DateTime.timezone.utc)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(TargetCompanion)
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Linked Companion: ChildID=\"{TargetCompanion.ID[:8]}…\", ParentID=\"{CharacterID[:8]}…\"")
        return Responses.JSONResponse(status_code = 200, content = SerializeCharacterRecord(TargetCompanion, CallerContext))

    if (not RequestPayload.Name) or (not RequestPayload.Name.strip()):
        raise FastAPI.HTTPException(status_code = 400, detail = "Either CompanionID or Name must be provided")

    if RequestPayload.EntityType not in (Character.EntityType.Companion, Character.EntityType.Vehicle):
        raise FastAPI.HTTPException(status_code = 400, detail = "EntityType must be Companion or Vehicle")

    NowTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.timezone.utc)
    NewCompanion = Character.Character(OwnerID = ParentCharacter.OwnerID, Name = RequestPayload.Name.strip(), GameSystem = ParentCharacter.GameSystem, EntityType = RequestPayload.EntityType, ParentCharacterID = CharacterID, IsPublic = RequestPayload.IsPublic, IsAccepted = True, SummaryData = RequestPayload.SummaryData, DetailData = RequestPayload.DetailData, CreatedAt = NowTimestamp, UpdatedAt = NowTimestamp)
    DatabaseSession.add(NewCompanion)
    await DatabaseSession.commit()

    ReloadStatement = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ID == NewCompanion.ID)
    ReloadResult    = await DatabaseSession.execute(ReloadStatement)
    NewCompanion    = ReloadResult.scalars().first() or NewCompanion
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created Linked Companion: ChildID=\"{NewCompanion.ID[:8]}…\", ParentID=\"{CharacterID[:8]}…\"")
    return Responses.JSONResponse(status_code = 201, content = SerializeCharacterRecord(NewCompanion, CallerContext))

@Router.post("/{CharacterID}/Transfer", response_class = Responses.JSONResponse)
async def TransferCharacter(CharacterID: str, RequestPayload: CharacterTransferRequest, CallerContext: Typing.Union[User.User, Typing.Dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.JSONResponse:
    IsService  : bool                     = RoleBasedAccessControl.IsServiceContext(CallerContext)
    CurrentUser: Typing.Optional[User.User] = CallerContext if isinstance(CallerContext, User.User) else None

    QueryStatement  = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ID == CharacterID)
    QueryResult     = await DatabaseSession.execute(QueryStatement)
    TargetCharacter = QueryResult.scalars().first()
    if (TargetCharacter is None):
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    FieldsSet      : set[str] = set(RequestPayload.model_fields_set)
    IsOwnerChange  : bool     = ("OwnerID" in FieldsSet) and (RequestPayload.OwnerID is not None) and (RequestPayload.OwnerID != TargetCharacter.OwnerID)
    IsParentChange : bool     = ("ParentCharacterID" in FieldsSet)
    if (not IsOwnerChange) and (not IsParentChange):
        raise FastAPI.HTTPException(status_code = 400, detail = "OwnerID or ParentCharacterID must be supplied")

    if (not IsService) and (not RoleBasedAccessControl.CanTransferCharacter(CurrentUser, TargetCharacter, IsOwnerChange)):
        raise FastAPI.HTTPException(status_code = 403, detail = "Your role does not have permission to transfer this character")

    if IsOwnerChange and (RequestPayload.OwnerID is not None):
        UserStatement = SQLAlchemy.select(User.User).where(User.User.ID == RequestPayload.OwnerID)
        UserResult    = await DatabaseSession.execute(UserStatement)
        NewOwner      = UserResult.scalars().first()
        if (NewOwner is None):
            raise FastAPI.HTTPException(status_code = 404, detail = "Target owner user not found")

        TargetCharacter.OwnerID = NewOwner.ID

    if IsParentChange:
        if (RequestPayload.ParentCharacterID is None) or (not RequestPayload.ParentCharacterID.strip()):
            TargetCharacter.ParentCharacterID = None

        else:
            CleanParentID: str = RequestPayload.ParentCharacterID.strip()
            if (CleanParentID == TargetCharacter.ID):
                raise FastAPI.HTTPException(status_code = 400, detail = "Character cannot be its own parent")

            ParentStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CleanParentID)
            ParentResult    = await DatabaseSession.execute(ParentStatement)
            ParentCharacter = ParentResult.scalars().first()
            if (ParentCharacter is None):
                raise FastAPI.HTTPException(status_code = 404, detail = "Target parent character not found")

            if (ParentCharacter.GameSystem != TargetCharacter.GameSystem):
                raise FastAPI.HTTPException(status_code = 400, detail = "Parent character must share the same game system")

            TargetCharacter.ParentCharacterID = ParentCharacter.ID

    TargetCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    ReloadResult    = await DatabaseSession.execute(QueryStatement)
    TargetCharacter = ReloadResult.scalars().first() or TargetCharacter
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Transferred Character: ID=\"{CharacterID[:8]}…\", OwnerID=\"{TargetCharacter.OwnerID[:8]}…\", ParentID=\"{TargetCharacter.ParentCharacterID}\"")
    return Responses.JSONResponse(status_code = 200, content = SerializeCharacterRecord(TargetCharacter, CallerContext))

@Router.patch("/{CharacterID}/State", response_class = Responses.JSONResponse)
async def UpdateCharacterState(CharacterID: str, RequestPayload: CharacterStatePatchRequest, CallerContext: Typing.Union[User.User, Typing.Dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.JSONResponse:
    IsService  : bool                     = RoleBasedAccessControl.IsServiceContext(CallerContext)
    CurrentUser: Typing.Optional[User.User] = CallerContext if isinstance(CallerContext, User.User) else None

    QueryStatement  = SQLAlchemy.select(Character.Character).options(ORM.selectinload(Character.Character.Owner)).where(Character.Character.ID == CharacterID)
    QueryResult     = await DatabaseSession.execute(QueryStatement)
    TargetCharacter = QueryResult.scalars().first()
    if (TargetCharacter is None):
        raise FastAPI.HTTPException(status_code = 404, detail = "Character not found")

    if (not IsService) and (not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter)) and (not RoleBasedAccessControl.IsGameMaster(CurrentUser)):
        raise FastAPI.HTTPException(status_code = 403, detail = "You do not have permission to update this character state")

    if (RequestPayload.DetailData is None) and (RequestPayload.SummaryData is None):
        raise FastAPI.HTTPException(status_code = 400, detail = "DetailData or SummaryData must be provided")

    if (RequestPayload.DetailData is not None):
        TargetCharacter.DetailData = DeepMergeDictionaries(dict(TargetCharacter.DetailData or {}), RequestPayload.DetailData)
        Attributes.flag_modified(TargetCharacter, "DetailData")

    if (RequestPayload.SummaryData is not None):
        TargetCharacter.SummaryData = DeepMergeDictionaries(dict(TargetCharacter.SummaryData or {}), RequestPayload.SummaryData)
        Attributes.flag_modified(TargetCharacter, "SummaryData")

    TargetCharacter.UpdatedAt = DateTime.datetime.now(DateTime.timezone.utc)
    await DatabaseSession.commit()
    ReloadResult    = await DatabaseSession.execute(QueryStatement)
    TargetCharacter = ReloadResult.scalars().first() or TargetCharacter
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Patched Character State: ID=\"{CharacterID[:8]}…\"")
    return Responses.JSONResponse(status_code = 200, content = SerializeCharacterRecord(TargetCharacter, CallerContext))

@Router.get("/{CharacterID}/Companions/Partial", response_class = Responses.HTMLResponse)
async def GetCharacterCompanionsPartial(CharacterID: str, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    Context: Typing.Dict[str, Typing.Any] = await BuildCompanionsPartialContext(CharacterID, CurrentUser, DatabaseSession)
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterCompanionsPartial.html", Context)

@Router.post("/{CharacterID}/Companions/Link/Partial", response_class = Responses.HTMLResponse)
async def LinkCharacterCompanionPartial(CharacterID: str, Request: FastAPI.Request, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    FormData   = await Request.form()
    CompanionID: str = str(FormData.get("CompanionID") or "").strip()

    ParentStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    ParentResult    = await DatabaseSession.execute(ParentStatement)
    ParentCharacter = ParentResult.scalars().first()
    if (ParentCharacter is None) or (not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, ParentCharacter)):
        Headers: Typing.Dict[str, str] = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."})}
        Context = await BuildCompanionsPartialContext(CharacterID, CurrentUser, DatabaseSession)
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterCompanionsPartial.html", Context, 200, Headers)

    if CompanionID and (CompanionID != CharacterID):
        ChildStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CompanionID)
        ChildResult    = await DatabaseSession.execute(ChildStatement)
        TargetChild    = ChildResult.scalars().first()
        if (TargetChild is not None) and (TargetChild.EntityType in (Character.EntityType.Companion, Character.EntityType.Vehicle)) and (TargetChild.GameSystem == ParentCharacter.GameSystem) and (RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetChild) or RoleBasedAccessControl.IsGameMaster(CurrentUser)):
            TargetChild.ParentCharacterID = CharacterID
            TargetChild.UpdatedAt         = DateTime.datetime.now(DateTime.timezone.utc)
            await DatabaseSession.commit()

    Context = await BuildCompanionsPartialContext(CharacterID, CurrentUser, DatabaseSession)
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterCompanionsPartial.html", Context)

@Router.post("/{CharacterID}/Companions/{CompanionID}/Unlink/Partial", response_class = Responses.HTMLResponse)
async def UnlinkCharacterCompanionPartial(CharacterID: str, CompanionID: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    ParentStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
    ParentResult    = await DatabaseSession.execute(ParentStatement)
    ParentCharacter = ParentResult.scalars().first()
    if (ParentCharacter is None) or (not RoleBasedAccessControl.CanModifyCharacter(CurrentUser, ParentCharacter)):
        Headers: Typing.Dict[str, str] = {"HX-Trigger": JSON.dumps({"ShowPermissionDeniedAlert": "Your role does not have permission to modify this character."})}
        Context = await BuildCompanionsPartialContext(CharacterID, CurrentUser, DatabaseSession)
        return TemplateRenderer.RenderPartialResponse("Characters/CharacterCompanionsPartial.html", Context, 200, Headers)

    ChildStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CompanionID, Character.Character.ParentCharacterID == CharacterID)
    ChildResult    = await DatabaseSession.execute(ChildStatement)
    TargetChild    = ChildResult.scalars().first()
    if (TargetChild is not None):
        TargetChild.ParentCharacterID = None
        TargetChild.UpdatedAt         = DateTime.datetime.now(DateTime.timezone.utc)
        await DatabaseSession.commit()

    Context = await BuildCompanionsPartialContext(CharacterID, CurrentUser, DatabaseSession)
    return TemplateRenderer.RenderPartialResponse("Characters/CharacterCompanionsPartial.html", Context)


