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
import Server.Services.DebugService             as DebugService
import Server.Services.OracleStorageService    as OracleStorage
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Storage", tags = ["Storage"])

@Router.get("/Files/Partial", response_class = Responses.HTMLResponse)
async def ListStorageFilesPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Listing Storage Files Partial For User: {getattr(CurrentUser, 'Identifier', None)}")
    if not CurrentUser:
        DebugService.LogDebugMessage("Unauthenticated Storage Files Request Encountered")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "Please authenticate to access cloud object storage."})

    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier).order_by(StorageFile.StorageFile.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Files = QueryResult.scalars().all()
    if not Files:
        DebugService.LogDebugMessage(f"No Storage Files Found For User: {CurrentUser.Identifier}")
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

    DebugService.LogDebugMessage(f"Rendered {len(FormattedFiles)} Storage Files For User: {CurrentUser.Identifier}")
    return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"Files": FormattedFiles})

@Router.get("/Gauge/Partial", response_class = Responses.HTMLResponse)
async def GetStorageGaugePartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Requesting Storage Gauge Partial For User: {getattr(CurrentUser, 'Identifier', None)}")
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
    DebugService.LogDebugMessage(f"Handling File Upload {File.filename} Of Size {FileSizeBytes} Bytes For User: {CurrentUser.Identifier}")
    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        DebugService.LogDebugMessage(f"Storage Quota Exceeded For User: {CurrentUser.Identifier}")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Upload rejected: 100 MB per-user quota exceeded!"})

    ContentType: str = File.content_type if File.content_type else "application/octet-stream"
    ObjectKey = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, File.filename if File.filename else "unnamed_file", ContentType, FileContent)
    if not ObjectKey:
        DebugService.LogDebugMessage("Object Storage Provider Failed During File Upload")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Storage provider error during upload."})

    NewStorageFile = StorageFile.StorageFile(OwnerIdentifier = CurrentUser.Identifier, FileName = File.filename if File.filename else "unnamed_file", ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey)
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    DebugService.LogDebugMessage(f"File Upload Succeeded With Object Key: {ObjectKey}")
    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.delete("/Files/{FileIdentifier}/Delete/Partial", response_class = Responses.HTMLResponse)
async def DeleteUserFilePartial(FileIdentifier: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Handling File Deletion For File Identifier: {FileIdentifier}, User: {CurrentUser.Identifier}")
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier, StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if TargetFile:
        await OracleStorage.GLOBAL_STORAGE_SERVICE.DeleteFile(TargetFile.ObjectKey)
        CurrentUser.StorageUsedBytes = max(0, CurrentUser.StorageUsedBytes - TargetFile.FileSizeBytes)
        await DatabaseSession.delete(TargetFile)
        await DatabaseSession.commit()
        DebugService.LogDebugMessage(f"Deleted File Successfully: {FileIdentifier}")
    else:
        DebugService.LogDebugMessage(f"Target File Not Found For Deletion: {FileIdentifier}")

    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.get("/Files/{FileIdentifier}/Stream")
async def StreamUserFile(FileIdentifier: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    DebugService.LogDebugMessage(f"Streaming User File With Identifier: {FileIdentifier}")
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogDebugMessage(f"Stream Failed: File Not Found For Identifier: {FileIdentifier}")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType)

@Router.get("/Files/{FileIdentifier}/Download")
async def DownloadUserFile(FileIdentifier: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    DebugService.LogDebugMessage(f"Downloading User File With Identifier: {FileIdentifier}")
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogDebugMessage(f"Download Failed: File Not Found For Identifier: {FileIdentifier}")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    HeadersDictionary: Typing.Dict[str, str] = {
        "Content-Disposition": f'attachment; filename="{TargetFile.FileName}"'
    }
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType, headers = HeadersDictionary)
