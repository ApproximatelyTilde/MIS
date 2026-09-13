import datetime                                  as DateTime
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
import Server.Models.User                        as User
import Server.Models.Variable                    as Variable
import Server.Services.DebugService              as DebugService

Router: FastAPI.APIRouter = FastAPI.APIRouter(prefix = "/API/Variables", tags = ["Variables"])

class VariableMutationRequest(Pydantic.BaseModel):
    Name : str
    Value: Typing.Optional[Typing.Any] = None

class GlobalVariableCreateRequest(Pydantic.BaseModel):
    Content: str
    Name   : Typing.Optional[str] = None
    OwnerID: Typing.Optional[str] = None
    ID     : Typing.Optional[str] = None

@Router.get("/User/{UserID}", response_class = Responses.JSONResponse)
async def GetUserVariables(UserID: str, Name: Typing.Optional[str] = FastAPI.Query(None), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Variable.UserVariable).where(Variable.UserVariable.UserID == UserID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    UserRecord     = QueryResult.scalars().first()
    VariablesMap   : dict[str, Typing.Any] = dict(UserRecord.Variables) if (UserRecord is not None) else {}

    if (Name is not None):
        if Name not in VariablesMap:
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"User Variable Not Found: UserID={UserID}, Name=\"{Name}\"")
            raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Variable '{Name}' not found for user '{UserID}'")

        return Responses.JSONResponse(content = {"UserID": UserID, "Name": Name, "Value": VariablesMap[Name]})

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served User Variables: UserID={UserID}, Count={len(VariablesMap)}")
    return Responses.JSONResponse(content = {"UserID": UserID, "Variables": VariablesMap})

@Router.post("/User/{UserID}", response_class = Responses.JSONResponse)
async def SaveUserVariable(UserID: str, RequestPayload: VariableMutationRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Variable.UserVariable).where(Variable.UserVariable.UserID == UserID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    UserRecord     = QueryResult.scalars().first()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    if (UserRecord is None):
        UserRecord = Variable.UserVariable(UserID = UserID, Variables = {}, UpdatedAt = CurrentTime)
        DatabaseSession.add(UserRecord)

    VariablesMap: dict[str, Typing.Any] = dict(UserRecord.Variables or {})
    if (RequestPayload.Value is None):
        if RequestPayload.Name in VariablesMap:
            del VariablesMap[RequestPayload.Name]

    else:
        VariablesMap[RequestPayload.Name] = RequestPayload.Value

    UserRecord.Variables = VariablesMap
    UserRecord.UpdatedAt = CurrentTime
    Attributes.flag_modified(UserRecord, "Variables")
    await DatabaseSession.commit()
    await DatabaseSession.refresh(UserRecord)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Saved User Variable: UserID={UserID}, Name=\"{RequestPayload.Name}\"")
    return Responses.JSONResponse(content = {"UserID": UserID, "Name": RequestPayload.Name, "Value": RequestPayload.Value})

@Router.get("/Server/{GuildID}", response_class = Responses.JSONResponse)
async def GetServerVariables(GuildID: str, Name: Typing.Optional[str] = FastAPI.Query(None), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Variable.ServerVariable).where(Variable.ServerVariable.GuildID == GuildID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    ServerRecord   = QueryResult.scalars().first()
    VariablesMap   : dict[str, Typing.Any] = dict(ServerRecord.Variables) if (ServerRecord is not None) else {}

    if (Name is not None):
        if Name not in VariablesMap:
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Server Variable Not Found: GuildID={GuildID}, Name=\"{Name}\"")
            raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Variable '{Name}' not found for server '{GuildID}'")

        return Responses.JSONResponse(content = {"GuildID": GuildID, "Name": Name, "Value": VariablesMap[Name]})

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Server Variables: GuildID={GuildID}, Count={len(VariablesMap)}")
    return Responses.JSONResponse(content = {"GuildID": GuildID, "Variables": VariablesMap})

@Router.post("/Server/{GuildID}", response_class = Responses.JSONResponse)
async def SaveServerVariable(GuildID: str, RequestPayload: VariableMutationRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Variable.ServerVariable).where(Variable.ServerVariable.GuildID == GuildID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    ServerRecord   = QueryResult.scalars().first()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    if (ServerRecord is None):
        ServerRecord = Variable.ServerVariable(GuildID = GuildID, Variables = {}, UpdatedAt = CurrentTime)
        DatabaseSession.add(ServerRecord)

    VariablesMap: dict[str, Typing.Any] = dict(ServerRecord.Variables or {})
    if (RequestPayload.Value is None):
        if RequestPayload.Name in VariablesMap:
            del VariablesMap[RequestPayload.Name]

    else:
        VariablesMap[RequestPayload.Name] = RequestPayload.Value

    ServerRecord.Variables = VariablesMap
    ServerRecord.UpdatedAt = CurrentTime
    Attributes.flag_modified(ServerRecord, "Variables")
    await DatabaseSession.commit()
    await DatabaseSession.refresh(ServerRecord)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Saved Server Variable: GuildID={GuildID}, Name=\"{RequestPayload.Name}\"")
    return Responses.JSONResponse(content = {"GuildID": GuildID, "Name": RequestPayload.Name, "Value": RequestPayload.Value})

@Router.get("/Global/{GvarID}", response_class = Responses.JSONResponse)
async def GetGlobalVariable(GvarID: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Variable.GlobalVariable).where(Variable.GlobalVariable.ID == GvarID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    GlobalRecord   = QueryResult.scalars().first()
    if (GlobalRecord is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Global Variable Not Found: ID={GvarID}")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Global variable '{GvarID}' not found")

    Payload = {
        "ID"       : GlobalRecord.ID,
        "Content"  : GlobalRecord.Content,
        "Name"     : GlobalRecord.Name,
        "OwnerID"  : GlobalRecord.OwnerID,
        "CreatedAt": GlobalRecord.CreatedAt.isoformat(),
        "UpdatedAt": GlobalRecord.UpdatedAt.isoformat()
    }
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Global Variable: ID={GvarID}")
    return Responses.JSONResponse(content = Payload)

@Router.post("/Global", response_class = Responses.JSONResponse, status_code = FastAPI.status.HTTP_201_CREATED)
async def CreateGlobalVariable(RequestPayload: GlobalVariableCreateRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    TargetID   : str                = RequestPayload.ID if (RequestPayload.ID is not None) else str(UUID.uuid4())
    CurrentTime: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    NewGlobalVariable = Variable.GlobalVariable(
        ID        = TargetID,
        Content   = RequestPayload.Content,
        Name      = RequestPayload.Name,
        OwnerID   = RequestPayload.OwnerID,
        CreatedAt = CurrentTime,
        UpdatedAt = CurrentTime
    )
    DatabaseSession.add(NewGlobalVariable)
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created Global Variable: ID={TargetID}")
    return Responses.JSONResponse(status_code = FastAPI.status.HTTP_201_CREATED, content = {"ID": TargetID})
