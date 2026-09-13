import datetime                           as DateTime
import typing                             as Typing
import fastapi                            as FastAPI
import fastapi.responses                  as Responses
import pydantic                           as Pydantic
import sqlalchemy                         as SQLAlchemy
import sqlalchemy.ext.asyncio             as AsyncIO
import sqlalchemy.orm.attributes          as Attributes
import Server.Auth.RoleBasedAccessControl as RoleBasedAccessControl
import Server.Database                    as Database
import Server.Models.CombatEncounter      as CombatEncounter
import Server.Models.Mail                 as Mail
import Server.Models.User                 as User
import Server.Services.DebugService       as Debug
import Server.Services.MailboxService     as Mailbox

Router: FastAPI.APIRouter = FastAPI.APIRouter(prefix = "/API/Combat", tags = ["Combat"])

class CombatEncounterSaveRequest(Pydantic.BaseModel):
    RoundNumber         : int                         = 1
    ActiveCombatantIndex: int                         = 0
    GameSystem          : str                         = "DND5E"
    InitiativeMode      : str                         = "Standard"
    RemainingInRound    : list[str]                   = Pydantic.Field(default_factory = list)
    Combatants          : list[dict[str, Typing.Any]] = Pydantic.Field(default_factory = list)
    ActiveEffects       : list[dict[str, Typing.Any]] = Pydantic.Field(default_factory = list)
    GuildID             : Typing.Optional[str]        = None

def SerializeCombatEncounter(EncounterRecord: CombatEncounter.CombatEncounter) -> dict[str, Typing.Any]:
    return {
        "ID"                  : EncounterRecord.ID,
        "ChannelID"           : EncounterRecord.ChannelID,
        "GuildID"             : EncounterRecord.GuildID,
        "GameSystem"          : EncounterRecord.GameSystem,
        "InitiativeMode"      : EncounterRecord.InitiativeMode,
        "RoundNumber"         : EncounterRecord.RoundNumber,
        "ActiveCombatantIndex": EncounterRecord.ActiveCombatantIndex,
        "Combatants"          : EncounterRecord.Combatants,
        "RemainingInRound"    : EncounterRecord.RemainingInRound,
        "ActiveEffects"       : EncounterRecord.ActiveEffects,
        "IsActive"            : EncounterRecord.IsActive,
        "CreatedAt"           : EncounterRecord.CreatedAt.isoformat(),
        "UpdatedAt"           : EncounterRecord.UpdatedAt.isoformat()
    }

def FormatCombatantVitalsForLog(Combatant: dict[str, Typing.Any], GameSystem: str) -> str:
    EntityType  : str                  = str(Combatant.get("EntityType", "Character"))
    VehicleStats: Typing.Optional[dict] = Combatant.get("VehicleStats")
    IsVehicle   : bool                 = (EntityType == "Vehicle") or (VehicleStats is not None)

    if (GameSystem == "MGT2E"):
        ArmorProtection: int = int(Combatant.get("ArmorProtection", 0) or 0)
        if IsVehicle:
            StatsDict  : dict[str, Typing.Any] = VehicleStats if isinstance(VehicleStats, dict) else {}
            CurrentHull: int                   = int(StatsDict.get("HullPoints", Combatant.get("CurrentHitPoints", 0)) or 0)
            MaxHull    : int                   = int(StatsDict.get("MaxHullPoints", Combatant.get("MaxHitPoints", 0)) or 0)
            return f"Hull {CurrentHull}/{MaxHull} | Armor {ArmorProtection}"

        Characteristics   : dict[str, Typing.Any] = Combatant.get("Characteristics") if isinstance(Combatant.get("Characteristics"), dict) else {}
        MaxCharacteristics: dict[str, Typing.Any] = Combatant.get("MaxCharacteristics") if isinstance(Combatant.get("MaxCharacteristics"), dict) else Characteristics
        CurrentEndurance  : int                   = int(Characteristics.get("Endurance", Combatant.get("CurrentHitPoints", 0)) or 0)
        MaxEndurance      : int                   = int(MaxCharacteristics.get("Endurance", Combatant.get("MaxHitPoints", 0)) or 0)
        return f"END {CurrentEndurance}/{MaxEndurance} | Armor {ArmorProtection}"

    ArmorClassValue: int = int(Combatant.get("ArmorClass", 10) or 10)
    if IsVehicle and isinstance(VehicleStats, dict):
        CurrentHull = int(VehicleStats.get("HullPoints", Combatant.get("CurrentHitPoints", 0)) or 0)
        MaxHull     = int(VehicleStats.get("MaxHullPoints", Combatant.get("MaxHitPoints", 0)) or 0)
        return f"Hull {CurrentHull}/{MaxHull} | AC {ArmorClassValue}"

    CurrentHP: int = int(Combatant.get("CurrentHitPoints", 0) or 0)
    MaxHP    : int = int(Combatant.get("MaxHitPoints", 0) or 0)
    return f"{CurrentHP}/{MaxHP} HP | AC {ArmorClassValue}"

def BuildCombatEncounterLog(EncounterRecord: CombatEncounter.CombatEncounter) -> str:
    GuildDisplayString: str = EncounterRecord.GuildID if (EncounterRecord.GuildID is not None) else "Direct Message / Unspecified"
    GameSystemValue   : str = EncounterRecord.GameSystem or "DND5E"
    InitiativeModeText: str = EncounterRecord.InitiativeMode or "Standard"
    LogLines: list[str] = [
        "# Combat Encounter Concluded",
        f"- **Channel ID**: {EncounterRecord.ChannelID}",
        f"- **Guild ID**: {GuildDisplayString}",
        f"- **Game System**: {GameSystemValue}",
        f"- **Initiative Mode**: {InitiativeModeText}",
        f"- **Total Rounds Concluded**: {EncounterRecord.RoundNumber}",
        f"- **Final Active Combatant Index**: {EncounterRecord.ActiveCombatantIndex}",
        "",
        "## Combatants Roster"
    ]
    if EncounterRecord.Combatants:
        for Combatant in EncounterRecord.Combatants:
            CombatantName  : str       = str(Combatant.get("Name", "Unknown Combatant"))
            EntityType     : str       = str(Combatant.get("EntityType", "Character"))
            EntityTag      : str       = f" [{EntityType}]" if (EntityType in ("Companion", "Vehicle", "Other")) else ""
            InitiativeValue: str       = str(Combatant.get("Initiative", 0))
            VitalsText     : str       = FormatCombatantVitalsForLog(Combatant, GameSystemValue)
            ConditionsList : list[str] = Combatant.get("Conditions", [])
            ConditionsText : str       = (f" | Conditions: {", ".join(ConditionsList)}") if (bool(ConditionsList)) else ("")
            LogLines.append(f"- **{CombatantName}**{EntityTag} (Init {InitiativeValue}) — {VitalsText}{ConditionsText}")

    else:
        LogLines.append("- No combatants were recorded in this encounter.")

    LogLines.append("")
    LogLines.append("## Active Effects")
    if EncounterRecord.ActiveEffects:
        for Effect in EncounterRecord.ActiveEffects:
            EffectName      : str = str(Effect.get("Name", "Unnamed Effect"))
            DurationRounds  : str = str(Effect.get("DurationRounds", "Indefinite"))
            IsConcentration : str = "Yes" if Effect.get("Concentration", False) else "No"
            CasterName      : str = str(Effect.get("Caster", "Unknown Caster"))
            LogLines.append(f"- **{EffectName}** (Caster: {CasterName}, Duration: {DurationRounds} rounds, Concentration: {IsConcentration})")

    else:
        LogLines.append("- No active effects recorded upon encounter conclusion.")

    return "\n".join(LogLines)

@Router.get("/Encounters/{ChannelID}", response_class = Responses.JSONResponse)
async def GetCombatEncounter(ChannelID: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(CombatEncounter.CombatEncounter).where(CombatEncounter.CombatEncounter.ChannelID == ChannelID, CombatEncounter.CombatEncounter.IsActive == True)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundEncounter = QueryResult.scalars().first()
    if (FoundEncounter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Combat Encounter Not Found: ChannelID={ChannelID}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Active combat encounter for channel '{ChannelID}' not found")

    EncounterPayload = SerializeCombatEncounter(FoundEncounter)
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Combat Encounter: ChannelID={ChannelID}, Round={FoundEncounter.RoundNumber}")
    return Responses.JSONResponse(content = EncounterPayload)

@Router.put("/Encounters/{ChannelID}", response_class = Responses.JSONResponse)
async def SaveCombatEncounter(ChannelID: str, RequestPayload: CombatEncounterSaveRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(CombatEncounter.CombatEncounter).where(CombatEncounter.CombatEncounter.ChannelID == ChannelID, CombatEncounter.CombatEncounter.IsActive == True)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetEncounter = QueryResult.scalars().first()
    CurrentTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    if (TargetEncounter is not None):
        TargetEncounter.RoundNumber          = RequestPayload.RoundNumber
        TargetEncounter.ActiveCombatantIndex = RequestPayload.ActiveCombatantIndex
        TargetEncounter.GameSystem           = RequestPayload.GameSystem
        TargetEncounter.InitiativeMode       = RequestPayload.InitiativeMode
        TargetEncounter.RemainingInRound     = RequestPayload.RemainingInRound
        TargetEncounter.Combatants           = RequestPayload.Combatants
        TargetEncounter.ActiveEffects        = RequestPayload.ActiveEffects
        if (RequestPayload.GuildID is not None):
            TargetEncounter.GuildID = RequestPayload.GuildID

        TargetEncounter.UpdatedAt = CurrentTimestamp
        Attributes.flag_modified(TargetEncounter, "RemainingInRound")
        Attributes.flag_modified(TargetEncounter, "Combatants")
        Attributes.flag_modified(TargetEncounter, "ActiveEffects")
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Updated Combat Encounter: ChannelID={ChannelID}, Round={TargetEncounter.RoundNumber}")

    else:
        TargetEncounter = CombatEncounter.CombatEncounter(ChannelID = ChannelID, GuildID = RequestPayload.GuildID, GameSystem = RequestPayload.GameSystem, InitiativeMode = RequestPayload.InitiativeMode, RoundNumber = RequestPayload.RoundNumber, ActiveCombatantIndex = RequestPayload.ActiveCombatantIndex, Combatants = RequestPayload.Combatants, RemainingInRound = RequestPayload.RemainingInRound, ActiveEffects = RequestPayload.ActiveEffects, IsActive = True, CreatedAt = CurrentTimestamp, UpdatedAt = CurrentTimestamp)
        DatabaseSession.add(TargetEncounter)
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created New Combat Encounter: ChannelID={ChannelID}, Round={TargetEncounter.RoundNumber}")

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetEncounter)
    EncounterPayload = SerializeCombatEncounter(TargetEncounter)
    return Responses.JSONResponse(content = EncounterPayload)

@Router.delete("/Encounters/{ChannelID}", response_class = Responses.JSONResponse)
async def DeleteCombatEncounter(ChannelID: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(CombatEncounter.CombatEncounter).where(CombatEncounter.CombatEncounter.ChannelID == ChannelID, CombatEncounter.CombatEncounter.IsActive == True)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    FoundEncounter = QueryResult.scalars().first()
    if (FoundEncounter is None):
        Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Delete Combat Encounter Failed: ChannelID={ChannelID} Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Active combat encounter for channel '{ChannelID}' not found")

    LogContent: str = BuildCombatEncounterLog(FoundEncounter)
    ControllerDiscordIDs: list[str] = [str(Combatant.get("ControllerDiscordID")) for Combatant in FoundEncounter.Combatants if Combatant.get("ControllerDiscordID")]
    GMQueryStatement = SQLAlchemy.select(User.User).where(SQLAlchemy.or_(User.User.Role.in_([User.UserRole.GameMaster, User.UserRole.Administrator]), User.User.DiscordID.in_(ControllerDiscordIDs)))
    GMQueryResult    = await DatabaseSession.execute(GMQueryStatement)
    IdentifiedGMs    = list(GMQueryResult.scalars().all())

    MailedCount: int = 0
    for GMRecord in IdentifiedGMs:
        await Mailbox.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = GMRecord.ID, Subject = f"Combat Concluded: Channel {FoundEncounter.ChannelID}", Body = LogContent, Category = Mail.MailCategory.StoryNotice, RelatedEntityType = "CombatEncounter", RelatedEntityID = FoundEncounter.ID)
        MailedCount += 1

    EncounterID: str = FoundEncounter.ID
    await DatabaseSession.delete(FoundEncounter)
    await DatabaseSession.commit()
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Hard-Deleted Combat Encounter: ChannelID={ChannelID}, ID={EncounterID}, MailedTo={MailedCount} GMs")
    return Responses.JSONResponse(content = {"IsSuccess": True, "ChannelID": ChannelID, "DeletedEncounterID": EncounterID, "MailedRecipientsCount": MailedCount})
