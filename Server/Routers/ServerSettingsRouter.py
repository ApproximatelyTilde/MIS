import datetime                                  as DateTime
import typing                                    as Typing
import fastapi                                   as FastAPI
import fastapi.responses                         as Responses
import pydantic                                  as Pydantic
import sqlalchemy                                as SQLAlchemy
import sqlalchemy.ext.asyncio                    as AsyncIO
import Server.Auth.RoleBasedAccessControl        as RoleBasedAccessControl
import Server.Database                           as Database
import Server.Models.ServerSettings               as ServerSettings
import Server.Models.User                        as User
import Server.Services.DebugService              as DebugService

Router: FastAPI.APIRouter = FastAPI.APIRouter(prefix = "/API/Servers", tags = ["Server Settings"])

class ServerSettingsSaveRequest(Pydantic.BaseModel):
    CommandPrefixDND      : str
    CommandPrefixTraveller: str
    RuleSetEnforcementMode: str
    MacroMasterRoleID     : Typing.Optional[str] = None

def SerializeServerSettings(SettingsRecord: ServerSettings.ServerSettings) -> dict[str, Typing.Any]:
    return {
        "GuildID"               : SettingsRecord.GuildID,
        "CommandPrefixDND"      : SettingsRecord.CommandPrefixDND,
        "CommandPrefixTraveller": SettingsRecord.CommandPrefixTraveller,
        "RuleSetEnforcementMode": SettingsRecord.RuleSetEnforcementMode,
        "MacroMasterRoleID"     : SettingsRecord.MacroMasterRoleID
    }

@Router.get("/{GuildID}/Settings", response_class = Responses.JSONResponse)
async def GetServerSettings(GuildID: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(ServerSettings.ServerSettings).where(ServerSettings.ServerSettings.GuildID == GuildID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetSettings = QueryResult.scalars().first()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    if (TargetSettings is None):
        TargetSettings = ServerSettings.ServerSettings(
            GuildID                = GuildID,
            CommandPrefixDND       = "&",
            CommandPrefixTraveller = "!",
            RuleSetEnforcementMode = "Standard",
            MacroMasterRoleID      = None,
            CreatedAt              = CurrentTime,
            UpdatedAt              = CurrentTime
        )
        DatabaseSession.add(TargetSettings)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(TargetSettings)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Initialized Default Server Settings: GuildID={GuildID}")

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Server Settings: GuildID={GuildID}")
    return Responses.JSONResponse(content = SerializeServerSettings(TargetSettings))

@Router.put("/{GuildID}/Settings", response_class = Responses.JSONResponse)
async def SaveServerSettings(GuildID: str, RequestPayload: ServerSettingsSaveRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(ServerSettings.ServerSettings).where(ServerSettings.ServerSettings.GuildID == GuildID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetSettings = QueryResult.scalars().first()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    if (TargetSettings is not None):
        TargetSettings.CommandPrefixDND       = RequestPayload.CommandPrefixDND
        TargetSettings.CommandPrefixTraveller = RequestPayload.CommandPrefixTraveller
        TargetSettings.RuleSetEnforcementMode = RequestPayload.RuleSetEnforcementMode
        TargetSettings.MacroMasterRoleID      = RequestPayload.MacroMasterRoleID
        TargetSettings.UpdatedAt              = CurrentTime
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Updated Server Settings: GuildID={GuildID}")

    else:
        TargetSettings = ServerSettings.ServerSettings(
            GuildID                = GuildID,
            CommandPrefixDND       = RequestPayload.CommandPrefixDND,
            CommandPrefixTraveller = RequestPayload.CommandPrefixTraveller,
            RuleSetEnforcementMode = RequestPayload.RuleSetEnforcementMode,
            MacroMasterRoleID      = RequestPayload.MacroMasterRoleID,
            CreatedAt              = CurrentTime,
            UpdatedAt              = CurrentTime
        )
        DatabaseSession.add(TargetSettings)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created Server Settings: GuildID={GuildID}")

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetSettings)
    return Responses.JSONResponse(content = SerializeServerSettings(TargetSettings))
