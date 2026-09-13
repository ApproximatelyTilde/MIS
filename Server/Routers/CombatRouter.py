import datetime                                  as DateTime
import typing                                    as Typing
import fastapi                                   as FastAPI
import fastapi.responses                         as Responses
import pydantic                                  as Pydantic
import sqlalchemy                                as SQLAlchemy
import sqlalchemy.ext.asyncio                    as AsyncIO
import sqlalchemy.orm.attributes                 as Attributes
import Server.Auth.RoleBasedAccessControl        as RoleBasedAccessControl
import Server.Database                           as Database
import Server.Models.CombatEncounter              as CombatEncounter
import Server.Models.Mail                        as Mail
import Server.Models.User                        as User
import Server.Services.DebugService              as DebugService
import Server.Services.MailService               as MailService

Router: FastAPI.APIRouter = FastAPI.APIRouter(prefix = "/API/Combat", tags = ["Combat"])

class CombatEncounterSaveRequest(Pydantic.BaseModel):
    RoundNumber         : int                                 = 1
    ActiveCombatantIndex: int                                 = 0
    Combatants          : list[dict[str, Typing.Any]]         = Pydantic.Field(default_factory = list)
    ActiveEffects       : list[dict[str, Typing.Any]]         = Pydantic.Field(default_factory = list)
    GuildID             : Typing.Optional[str]                = None

def SerializeCombatEncounter(EncounterRecord: CombatEncounter.CombatEncounter) -> dict[str, Typing.Any]:
    return {
        "ID"                  : EncounterRecord.ID,
        "ChannelID"           : EncounterRecord.ChannelID,
        "GuildID"             : EncounterRecord.GuildID,
        "RoundNumber"         : EncounterRecord.RoundNumber,
        "ActiveCombatantIndex": EncounterRecord.ActiveCombatantIndex,
        "Combatants"          : EncounterRecord.Combatants,
        "ActiveEffects"       : EncounterRecord.ActiveEffects,
        "IsActive"            : EncounterRecord.IsActive,
        "CreatedAt"           : EncounterRecord.CreatedAt.isoformat(),
        "UpdatedAt"           : EncounterRecord.UpdatedAt.isoformat()
    }

def BuildCombatEncounterLog(EncounterRecord: CombatEncounter.CombatEncounter) -> str:
    GuildDisplayString: str = EncounterRecord.GuildID if (EncounterRecord.GuildID is not None) else "Direct Message / Unspecified"
    LogLines: list[str] = [
        "# Combat Encounter Concluded",
        f"- **Channel ID**: {EncounterRecord.ChannelID}",
        f"- **Guild ID**: {GuildDisplayString}",
        f"- **Total Rounds Concluded**: {EncounterRecord.RoundNumber}",
        f"- **Final Active Combatant Index**: {EncounterRecord.ActiveCombatantIndex}",
        "",
        "## Combatants Roster"
    ]
    if EncounterRecord.Combatants:
        for Combatant in EncounterRecord.Combatants:
            CombatantName       : str = str(Combatant.get("Name", "Unknown Combatant"))
            InitiativeValue     : str = str(Combatant.get("Initiative", 0))
            CurrentHP           : str = str(Combatant.get("CurrentHitPoints", 0))
            MaxHP               : str = str(Combatant.get("MaxHitPoints", 0))
            ArmorClassValue     : str = str(Combatant.get("ArmorClass", 10))
            ConditionsList      : list[str] = Combatant.get("Conditions", [])
            ConditionsText      : str = f" | Conditions: {', '.join(ConditionsList)}" if ConditionsList else ""
            LogLines.append(f"- **{CombatantName}** (Init {InitiativeValue}) — {CurrentHP}/{MaxHP} HP | AC {ArmorClassValue}{ConditionsText}")

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
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Combat Encounter Not Found: ChannelID={ChannelID}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Active combat encounter for channel '{ChannelID}' not found")

    EncounterPayload = SerializeCombatEncounter(FoundEncounter)
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Combat Encounter: ChannelID={ChannelID}, Round={FoundEncounter.RoundNumber}")
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
        TargetEncounter.Combatants           = RequestPayload.Combatants
        TargetEncounter.ActiveEffects        = RequestPayload.ActiveEffects
        if (RequestPayload.GuildID is not None):
            TargetEncounter.GuildID = RequestPayload.GuildID

        TargetEncounter.UpdatedAt = CurrentTimestamp
        Attributes.flag_modified(TargetEncounter, "Combatants")
        Attributes.flag_modified(TargetEncounter, "ActiveEffects")
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Updated Combat Encounter: ChannelID={ChannelID}, Round={TargetEncounter.RoundNumber}")

    else:
        TargetEncounter = CombatEncounter.CombatEncounter(
            ChannelID            = ChannelID,
            GuildID              = RequestPayload.GuildID,
            RoundNumber          = RequestPayload.RoundNumber,
            ActiveCombatantIndex = RequestPayload.ActiveCombatantIndex,
            Combatants           = RequestPayload.Combatants,
            ActiveEffects        = RequestPayload.ActiveEffects,
            IsActive             = True,
            CreatedAt            = CurrentTimestamp,
            UpdatedAt            = CurrentTimestamp
        )
        DatabaseSession.add(TargetEncounter)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created New Combat Encounter: ChannelID={ChannelID}, Round={TargetEncounter.RoundNumber}")

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
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Delete Combat Encounter Failed: ChannelID={ChannelID} Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Active combat encounter for channel '{ChannelID}' not found")

    LogContent: str = BuildCombatEncounterLog(FoundEncounter)
    ControllerDiscordIDs: list[str] = [str(Combatant.get("ControllerDiscordID")) for Combatant in FoundEncounter.Combatants if Combatant.get("ControllerDiscordID")]
    GMQueryStatement = SQLAlchemy.select(User.User).where(SQLAlchemy.or_(User.User.Role.in_([User.UserRole.GameMaster, User.UserRole.Administrator]), User.User.DiscordID.in_(ControllerDiscordIDs)))
    GMQueryResult    = await DatabaseSession.execute(GMQueryStatement)
    IdentifiedGMs    = list(GMQueryResult.scalars().all())

    MailedCount: int = 0
    for GMRecord in IdentifiedGMs:
        await MailService.DispatchAutomatedMail(
            DatabaseSession   = DatabaseSession,
            RecipientUserID   = GMRecord.ID,
            Subject           = f"Combat Concluded: Channel {FoundEncounter.ChannelID}",
            Body              = LogContent,
            Category          = Mail.MailCategory.StoryNotice,
            RelatedEntityType = "CombatEncounter",
            RelatedEntityID   = FoundEncounter.ID
        )
        MailedCount += 1

    EncounterID: str = FoundEncounter.ID
    await DatabaseSession.delete(FoundEncounter)
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Hard-Deleted Combat Encounter: ChannelID={ChannelID}, ID={EncounterID}, MailedTo={MailedCount} GMs")
    return Responses.JSONResponse(content = {"IsSuccess": True, "ChannelID": ChannelID, "DeletedEncounterID": EncounterID, "MailedRecipientsCount": MailedCount})
