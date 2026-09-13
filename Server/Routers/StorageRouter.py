import typing                                  as Typing
import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import sqlalchemy                              as SQLAlchemy
import sqlalchemy.ext.asyncio                  as AsyncIO
import Server.Auth.RoleBasedAccessControl      as RoleBasedAccessControl
import Server.Config                           as Config
import Server.Database                         as Database
import Server.Models.StorageFile               as StorageFile
import Server.Models.User                      as User
import Server.Services.OracleStorageService    as OracleStorage
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Storage", tags = ["Storage"])

@Router.get("/Files/Partial", response_class = Responses.HTMLResponse)
async def ListStorageFilesPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not CurrentUser:
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "Please authenticate to access cloud object storage."})

    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier).order_by(StorageFile.StorageFile.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Files = QueryResult.scalars().all()
    if not Files:
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "No files uploaded yet."})

    FormattedFiles: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for FileRecord in Files:
        SizeKB: float = round(FileRecord.FileSizeBytes / 1000, 1)
        FormattedFiles.append({
            "Identifier" : FileRecord.Identifier,
            "FileName"   : FileRecord.FileName,
            "ContentType": FileRecord.ContentType,
            "SizeKB"     : SizeKB,
            "IsAudio"    : FileRecord.ContentType.startswith("audio"),
            "IsImage"    : FileRecord.ContentType.startswith("image")
        })

    return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"Files": FormattedFiles})

@Router.get("/Gauge/Partial", response_class = Responses.HTMLResponse)
async def GetStorageGaugePartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    if not CurrentUser:
        return TemplateRenderer.RenderPartialResponse("Storage/StorageGaugePartial.html", {"IsAuthenticated": False})

    TotalBytes: int = Config.GLOBAL_SETTINGS.USER_STORAGE_QUOTA_BYTES
    UsedBytes: int = CurrentUser.StorageUsedBytes
    FreeBytes: int = max(0, TotalBytes - UsedBytes)
    FreeMB: int = int(round(FreeBytes / 1000000))
    UsedPercentage: int = min(100, int(round((UsedBytes / TotalBytes) * 100)))
    QuotaInteger: int = UsedPercentage
    Context: Typing.Dict[str, Typing.Any] = {
        "IsAuthenticated": True,
        "FreeMB"         : FreeMB,
        "UsedPercentage" : UsedPercentage,
        "QuotaInteger"   : QuotaInteger
    }
    return TemplateRenderer.RenderPartialResponse("Storage/StorageGaugePartial.html", Context)

@Router.post("/Upload/Partial", response_class = Responses.HTMLResponse)
async def UploadUserFilePartial(File: FastAPI.UploadFile = FastAPI.File(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    FileContent: bytes = await File.read()
    FileSizeBytes: int = len(FileContent)
    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Upload rejected: 100 MB per-user quota exceeded!"})

    ContentType: str = File.content_type if File.content_type else "application/octet-stream"
    ObjectKey = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, File.filename if File.filename else "unnamed_file", ContentType, FileContent)
    if not ObjectKey:
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Storage provider error during upload."})

    NewStorageFile = StorageFile.StorageFile(OwnerIdentifier = CurrentUser.Identifier, FileName = File.filename if File.filename else "unnamed_file", ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey)
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.delete("/Files/{FileIdentifier}/Delete/Partial", response_class = Responses.HTMLResponse)
async def DeleteUserFilePartial(FileIdentifier: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier, StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if TargetFile:
        await OracleStorage.GLOBAL_STORAGE_SERVICE.DeleteFile(TargetFile.ObjectKey)
        CurrentUser.StorageUsedBytes = max(0, CurrentUser.StorageUsedBytes - TargetFile.FileSizeBytes)
        await DatabaseSession.delete(TargetFile)
        await DatabaseSession.commit()

    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.get("/Files/{FileIdentifier}/Stream")
async def StreamUserFile(FileIdentifier: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType)

@Router.get("/Files/{FileIdentifier}/Download")
async def DownloadUserFile(FileIdentifier: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    HeadersDictionary: Typing.Dict[str, str] = {
        "Content-Disposition": f'attachment; filename="{TargetFile.FileName}"'
    }
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType, headers = HeadersDictionary)
