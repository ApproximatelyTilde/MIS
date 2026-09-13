import datetime                           as DateTime
import typing                             as Typing
import fastapi                            as FastAPI
import fastapi.responses                  as Responses
import pydantic                           as Pydantic
import sqlalchemy                         as SQLAlchemy
import sqlalchemy.ext.asyncio             as AsyncIO
import Server.Auth.RoleBasedAccessControl as RoleBasedAccessControl
import Server.Database                    as Database
import Server.Models.ServerSettings       as ServerSettings
import Server.Models.User                 as User
import Server.Services.DebugService       as Debug

Router: FastAPI.APIRouter = FastAPI.APIRouter(prefix = "/API/Servers", tags = ["Server Settings"])

class ServerSettingsSaveRequest(Pydantic.BaseModel):
    CommandPrefixDND5E    : str                  = "&"
    CommandPrefixMGT2E    : str                  = "!"
    RuleSetEnforcementMode: str                  = "Standard"
    MacroMasterRoleID     : Typing.Optional[str] = None

def SerializeServerSettings(SettingsRecord: ServerSettings.ServerSettings) -> dict[str, Typing.Any]:
    return {
        "GuildID"               : SettingsRecord.GuildID,
        "CommandPrefixDND5E"    : SettingsRecord.CommandPrefixDND5E,
        "CommandPrefixMGT2E"    : SettingsRecord.CommandPrefixMGT2E,
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
        TargetSettings = ServerSettings.ServerSettings(GuildID = GuildID, CommandPrefixDND5E = "&", CommandPrefixMGT2E = "!", RuleSetEnforcementMode = "Standard", MacroMasterRoleID = None, CreatedAt = CurrentTime, UpdatedAt = CurrentTime)
        DatabaseSession.add(TargetSettings)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(TargetSettings)
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Initialized Default Server Settings: GuildID={GuildID}")

    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Served Server Settings: GuildID={GuildID}")
    return Responses.JSONResponse(content = SerializeServerSettings(TargetSettings))

@Router.put("/{GuildID}/Settings", response_class = Responses.JSONResponse)
async def SaveServerSettings(GuildID: str, RequestPayload: ServerSettingsSaveRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(ServerSettings.ServerSettings).where(ServerSettings.ServerSettings.GuildID == GuildID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetSettings = QueryResult.scalars().first()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    if (TargetSettings is not None):
        TargetSettings.CommandPrefixDND5E     = RequestPayload.CommandPrefixDND5E
        TargetSettings.CommandPrefixMGT2E     = RequestPayload.CommandPrefixMGT2E
        TargetSettings.RuleSetEnforcementMode = RequestPayload.RuleSetEnforcementMode
        TargetSettings.MacroMasterRoleID      = RequestPayload.MacroMasterRoleID
        TargetSettings.UpdatedAt              = CurrentTime
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Updated Server Settings: GuildID={GuildID}")

    else:
        TargetSettings = ServerSettings.ServerSettings(GuildID = GuildID, CommandPrefixDND5E = RequestPayload.CommandPrefixDND5E, CommandPrefixMGT2E = RequestPayload.CommandPrefixMGT2E, RuleSetEnforcementMode = RequestPayload.RuleSetEnforcementMode, MacroMasterRoleID = RequestPayload.MacroMasterRoleID, CreatedAt = CurrentTime, UpdatedAt = CurrentTime)
        DatabaseSession.add(TargetSettings)
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created Server Settings: GuildID={GuildID}")

    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetSettings)
    return Responses.JSONResponse(content = SerializeServerSettings(TargetSettings))
