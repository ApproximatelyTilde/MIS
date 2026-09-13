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
import Server.Models.Aliasing                     as Aliasing
import Server.Models.User                        as User
import Server.Services.DebugService              as DebugService

Router: FastAPI.APIRouter = FastAPI.APIRouter(tags = ["Aliases and Snippets"])

class AliasCreateRequest(Pydantic.BaseModel):
    Name           : str
    Content        : str
    Scope          : str
    OwnerID        : str
    ServerID       : Typing.Optional[str] = None
    CollaboratorIDs: list[str]            = Pydantic.Field(default_factory = list)

class AliasUpdateRequest(Pydantic.BaseModel):
    Name           : Typing.Optional[str]       = None
    Content        : Typing.Optional[str]       = None
    CollaboratorIDs: Typing.Optional[list[str]] = None

def SerializeAlias(AliasRecord: Aliasing.Alias) -> dict[str, Typing.Any]:
    return {
        "ID"             : AliasRecord.ID,
        "Name"           : AliasRecord.Name,
        "Content"        : AliasRecord.Content,
        "Scope"          : AliasRecord.Scope,
        "OwnerID"        : AliasRecord.OwnerID,
        "ServerID"       : AliasRecord.ServerID,
        "CollaboratorIDs": AliasRecord.CollaboratorIDs,
        "CreatedAt"      : AliasRecord.CreatedAt.isoformat(),
        "UpdatedAt"      : AliasRecord.UpdatedAt.isoformat()
    }

def SerializeSnippet(SnippetRecord: Aliasing.Snippet) -> dict[str, Typing.Any]:
    return {
        "ID"             : SnippetRecord.ID,
        "Name"           : SnippetRecord.Name,
        "Content"        : SnippetRecord.Content,
        "Scope"          : SnippetRecord.Scope,
        "OwnerID"        : SnippetRecord.OwnerID,
        "ServerID"       : SnippetRecord.ServerID,
        "CollaboratorIDs": SnippetRecord.CollaboratorIDs,
        "CreatedAt"      : SnippetRecord.CreatedAt.isoformat(),
        "UpdatedAt"      : SnippetRecord.UpdatedAt.isoformat()
    }

@Router.get("/API/Aliases", response_class = Responses.JSONResponse)
async def GetAliases(Scope: str = FastAPI.Query(...), OwnerID: Typing.Optional[str] = FastAPI.Query(None), ServerID: Typing.Optional[str] = FastAPI.Query(None), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    NormalizedScope: str = Scope.capitalize()
    if (NormalizedScope == "User"):
        if (OwnerID is None):
            raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = "OwnerID is required when Scope is User")

        QueryStatement = SQLAlchemy.select(Aliasing.Alias).where(Aliasing.Alias.Scope == "User", Aliasing.Alias.OwnerID == OwnerID)

    elif (NormalizedScope == "Server"):
        if (ServerID is None):
            raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = "ServerID is required when Scope is Server")

        QueryStatement = SQLAlchemy.select(Aliasing.Alias).where(Aliasing.Alias.Scope == "Server", Aliasing.Alias.ServerID == ServerID)

    else:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = f"Invalid Scope '{Scope}'. Expected 'User' or 'Server'")

    QueryResult = await DatabaseSession.execute(QueryStatement)
    FoundAliases = list(QueryResult.scalars().all())
    ResultsList  = [SerializeAlias(Record) for Record in FoundAliases]
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Aliases: Scope={NormalizedScope}, Count={len(ResultsList)}")
    return Responses.JSONResponse(content = ResultsList)

@Router.post("/API/Aliases", response_class = Responses.JSONResponse, status_code = FastAPI.status.HTTP_201_CREATED)
async def CreateAlias(RequestPayload: AliasCreateRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    NormalizedScope: str                = RequestPayload.Scope.capitalize()
    CleanName      : str                = RequestPayload.Name.strip().lower()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    NewAlias = Aliasing.Alias(
        Name            = CleanName,
        Content         = RequestPayload.Content,
        Scope           = NormalizedScope,
        OwnerID         = RequestPayload.OwnerID,
        ServerID        = RequestPayload.ServerID if (NormalizedScope == "Server") else None,
        CollaboratorIDs = RequestPayload.CollaboratorIDs,
        CreatedAt       = CurrentTime,
        UpdatedAt       = CurrentTime
    )
    DatabaseSession.add(NewAlias)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewAlias)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created Alias: ID={NewAlias.ID}, Name=\"{CleanName}\", Scope={NormalizedScope}")
    return Responses.JSONResponse(status_code = FastAPI.status.HTTP_201_CREATED, content = SerializeAlias(NewAlias))

@Router.patch("/API/Aliases/{AliasID}", response_class = Responses.JSONResponse)
async def UpdateAlias(AliasID: str, RequestPayload: AliasUpdateRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Aliasing.Alias).where(Aliasing.Alias.ID == AliasID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetAlias    = QueryResult.scalars().first()
    if (TargetAlias is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Update Alias Failed: ID={AliasID} Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Alias '{AliasID}' not found")

    if (RequestPayload.Name is not None):
        TargetAlias.Name = RequestPayload.Name.strip().lower()

    if (RequestPayload.Content is not None):
        TargetAlias.Content = RequestPayload.Content

    if (RequestPayload.CollaboratorIDs is not None):
        TargetAlias.CollaboratorIDs = RequestPayload.CollaboratorIDs
        Attributes.flag_modified(TargetAlias, "CollaboratorIDs")

    TargetAlias.UpdatedAt = DateTime.datetime.now(DateTime.UTC)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetAlias)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Updated Alias: ID={AliasID}, Name=\"{TargetAlias.Name}\"")
    return Responses.JSONResponse(content = SerializeAlias(TargetAlias))

@Router.delete("/API/Aliases/{AliasID}", response_class = Responses.JSONResponse)
async def DeleteAlias(AliasID: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Aliasing.Alias).where(Aliasing.Alias.ID == AliasID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetAlias    = QueryResult.scalars().first()
    if (TargetAlias is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Delete Alias Failed: ID={AliasID} Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Alias '{AliasID}' not found")

    await DatabaseSession.delete(TargetAlias)
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Deleted Alias: ID={AliasID}")
    return Responses.JSONResponse(content = {"IsSuccess": True, "DeletedAliasID": AliasID})

@Router.get("/API/Snippets", response_class = Responses.JSONResponse)
async def GetSnippets(Scope: str = FastAPI.Query(...), OwnerID: Typing.Optional[str] = FastAPI.Query(None), ServerID: Typing.Optional[str] = FastAPI.Query(None), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    NormalizedScope: str = Scope.capitalize()
    if (NormalizedScope == "User"):
        if (OwnerID is None):
            raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = "OwnerID is required when Scope is User")

        QueryStatement = SQLAlchemy.select(Aliasing.Snippet).where(Aliasing.Snippet.Scope == "User", Aliasing.Snippet.OwnerID == OwnerID)

    elif (NormalizedScope == "Server"):
        if (ServerID is None):
            raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = "ServerID is required when Scope is Server")

        QueryStatement = SQLAlchemy.select(Aliasing.Snippet).where(Aliasing.Snippet.Scope == "Server", Aliasing.Snippet.ServerID == ServerID)

    else:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = f"Invalid Scope '{Scope}'. Expected 'User' or 'Server'")

    QueryResult  = await DatabaseSession.execute(QueryStatement)
    FoundSnippets = list(QueryResult.scalars().all())
    ResultsList   = [SerializeSnippet(Record) for Record in FoundSnippets]
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Snippets: Scope={NormalizedScope}, Count={len(ResultsList)}")
    return Responses.JSONResponse(content = ResultsList)

@Router.post("/API/Snippets", response_class = Responses.JSONResponse, status_code = FastAPI.status.HTTP_201_CREATED)
async def CreateSnippet(RequestPayload: AliasCreateRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    NormalizedScope: str                = RequestPayload.Scope.capitalize()
    CleanName      : str                = RequestPayload.Name.strip().lower()
    CurrentTime    : DateTime.datetime = DateTime.datetime.now(DateTime.UTC)

    NewSnippet = Aliasing.Snippet(
        Name            = CleanName,
        Content         = RequestPayload.Content,
        Scope           = NormalizedScope,
        OwnerID         = RequestPayload.OwnerID,
        ServerID        = RequestPayload.ServerID if (NormalizedScope == "Server") else None,
        CollaboratorIDs = RequestPayload.CollaboratorIDs,
        CreatedAt       = CurrentTime,
        UpdatedAt       = CurrentTime
    )
    DatabaseSession.add(NewSnippet)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewSnippet)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Created Snippet: ID={NewSnippet.ID}, Name=\"{CleanName}\", Scope={NormalizedScope}")
    return Responses.JSONResponse(status_code = FastAPI.status.HTTP_201_CREATED, content = SerializeSnippet(NewSnippet))

@Router.patch("/API/Snippets/{SnippetID}", response_class = Responses.JSONResponse)
async def UpdateSnippet(SnippetID: str, RequestPayload: AliasUpdateRequest, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Aliasing.Snippet).where(Aliasing.Snippet.ID == SnippetID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetSnippet  = QueryResult.scalars().first()
    if (TargetSnippet is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Update Snippet Failed: ID={SnippetID} Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Snippet '{SnippetID}' not found")

    if (RequestPayload.Name is not None):
        TargetSnippet.Name = RequestPayload.Name.strip().lower()

    if (RequestPayload.Content is not None):
        TargetSnippet.Content = RequestPayload.Content

    if (RequestPayload.CollaboratorIDs is not None):
        TargetSnippet.CollaboratorIDs = RequestPayload.CollaboratorIDs
        Attributes.flag_modified(TargetSnippet, "CollaboratorIDs")

    TargetSnippet.UpdatedAt = DateTime.datetime.now(DateTime.UTC)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(TargetSnippet)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Updated Snippet: ID={SnippetID}, Name=\"{TargetSnippet.Name}\"")
    return Responses.JSONResponse(content = SerializeSnippet(TargetSnippet))

@Router.delete("/API/Snippets/{SnippetID}", response_class = Responses.JSONResponse)
async def DeleteSnippet(SnippetID: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession), CallerContext: Typing.Union[User.User, dict[str, Typing.Any]] = FastAPI.Depends(RoleBasedAccessControl.RequireServiceOrAuthenticatedUser)) -> Responses.JSONResponse:
    QueryStatement = SQLAlchemy.select(Aliasing.Snippet).where(Aliasing.Snippet.ID == SnippetID)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    TargetSnippet  = QueryResult.scalars().first()
    if (TargetSnippet is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Delete Snippet Failed: ID={SnippetID} Not Found")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = f"Snippet '{SnippetID}' not found")

    await DatabaseSession.delete(TargetSnippet)
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Deleted Snippet: ID={SnippetID}")
    return Responses.JSONResponse(content = {"IsSuccess": True, "DeletedSnippetID": SnippetID})
