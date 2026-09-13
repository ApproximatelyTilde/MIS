import hashlib                                 as HashLib
import json                                    as JSON
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
PublicObjectRouter = FastAPI.APIRouter(prefix = "/Objects", tags = ["Objects"])

def GetMIMETypeCategory(ContentType: str) -> str:
    LowerContentType: str = ContentType.lower()
    if LowerContentType.startswith("image/"):
        return "Image"
    if LowerContentType.startswith("audio/"):
        return "Audio"
    if LowerContentType.startswith("video/"):
        return "Video"
    if LowerContentType.startswith("text/") or LowerContentType == "application/pdf":
        return "Document"
    if "zip" in LowerContentType or "tar" in LowerContentType or "gzip" in LowerContentType:
        return "Archive"
    return "Binary"

@Router.get("/Files/Partial", response_class = Responses.HTMLResponse)
async def ListStorageFilesPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not CurrentUser:
        DebugService.LogDebugMessage("Storage Files Partial: Rejected Unauthenticated")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "Please authenticate to access cloud object storage."})

    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier).order_by(StorageFile.StorageFile.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Files = QueryResult.scalars().all()
    if not Files:
        DebugService.LogDebugMessage(f"Storage Files Partial: Empty (User='{CurrentUser.Identifier}')")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "No files uploaded yet."})

    FormattedFiles: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for FileRecord in Files:
        SizeKB: float = round(FileRecord.FileSizeBytes / 1000, 1)
        Category: str = GetMIMETypeCategory(FileRecord.ContentType)
        FormattedFiles.append({
            "Identifier" : FileRecord.Identifier,
            "FileName"   : FileRecord.FileName,
            "ContentType": FileRecord.ContentType,
            "Category"   : Category,
            "SizeKB"     : SizeKB,
            "IsAudio"    : FileRecord.ContentType.startswith("audio/"),
            "IsImage"    : FileRecord.ContentType.startswith("image/"),
            "IsVideo"    : FileRecord.ContentType.startswith("video/"),
            "IsPublic"   : FileRecord.IsPublic
        })

    DebugService.LogDebugMessage(f"Storage Files Partial Rendered: {len(FormattedFiles)} Files (User='{CurrentUser.Identifier}')")
    return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"Files": FormattedFiles})

@Router.get("/Images/Picker/Partial", response_class = Responses.HTMLResponse)
async def ListStorageImagesPickerPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not CurrentUser:
        DebugService.LogDebugMessage("Storage Images Picker: Rejected Unauthenticated")
        return TemplateRenderer.RenderPartialResponse("Storage/ImagePickerGridPartial.html", {"InfoMessage": "Please authenticate to access cloud object storage."})

    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(
        StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier,
        StorageFile.StorageFile.ContentType.like("image/%")
    ).order_by(StorageFile.StorageFile.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    ImageFiles = QueryResult.scalars().all()
    if not ImageFiles:
        DebugService.LogDebugMessage(f"Storage Images Picker: Empty (User='{CurrentUser.Identifier}')")
        return TemplateRenderer.RenderPartialResponse("Storage/ImagePickerGridPartial.html", {"InfoMessage": "No image assets found in object storage."})

    FormattedImages: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for FileRecord in ImageFiles:
        SizeKB: float = round(FileRecord.FileSizeBytes / 1000, 1)
        FormattedImages.append({
            "Identifier": FileRecord.Identifier,
            "FileName": FileRecord.FileName,
            "ContentType": FileRecord.ContentType,
            "SizeKB": SizeKB
        })

    DebugService.LogDebugMessage(f"Storage Images Picker Rendered: {len(FormattedImages)} Images (User='{CurrentUser.Identifier}')")
    return TemplateRenderer.RenderPartialResponse("Storage/ImagePickerGridPartial.html", {"Images": FormattedImages})

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
    DebugService.LogDebugMessage(f"Storage Gauge Rendered: User='{CurrentUser.Identifier}', Used={UsedPercentage}%, Free={FreeMB}MB")
    Context: Typing.Dict[str, Typing.Any] = {
        "IsAuthenticated": True,
        "FreeMB"         : FreeMB,
        "UsedPercentage" : UsedPercentage,
        "QuotaInteger"   : QuotaInteger
    }
    return TemplateRenderer.RenderPartialResponse("Storage/StorageGaugePartial.html", Context)

@Router.post("/Upload/Partial", response_class = Responses.HTMLResponse)
async def UploadUserFilePartial(File: FastAPI.UploadFile = FastAPI.File(...), CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    if not RoleBasedAccessControl.IsUserInGuild(CurrentUser):
        DebugService.LogDebugMessage(f"Storage Upload Rejected: User '{CurrentUser.Identifier}' Not In Guild")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {
            "ErrorMessage": "Upload rejected: Discord server membership required!"
        })

    FileContent: bytes = await File.read()
    FileSizeBytes: int = len(FileContent)
    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        DebugService.LogDebugMessage(f"Storage Upload Rejected: Quota Exceeded For User '{CurrentUser.Identifier}' ({FileSizeBytes}B Needed)")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Upload rejected: 100 MB per-user quota exceeded!"})

    ContentType: str = File.content_type if File.content_type else "application/octet-stream"
    FileHash: str = HashLib.sha256(FileContent).hexdigest().upper()[:8]
    HashedFileName: str = FileHash
    ObjectKey = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, HashedFileName, ContentType, FileContent)
    if not ObjectKey:
        DebugService.LogDebugMessage(f"Storage Upload Failed: Provider Error (User='{CurrentUser.Identifier}', Name='{HashedFileName}')")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Storage provider error during upload."})

    NewStorageFile = StorageFile.StorageFile(OwnerIdentifier = CurrentUser.Identifier, FileName = HashedFileName, ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey, IsPublic = False)
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    DebugService.LogDebugMessage(f"Storage Upload Succeeded: Key='{ObjectKey}', File='{HashedFileName}', Size={FileSizeBytes}B, User='{CurrentUser.Identifier}'")
    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.post("/Files/{FileIdentifier}/Share/Partial", response_class = Responses.Response)
async def ShareStorageFilePartial(FileIdentifier: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier, StorageFile.StorageFile.OwnerIdentifier == CurrentUser.Identifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogDebugMessage(f"Storage Share Failed: File '{FileIdentifier}' Not Found Or Unauthorized (User='{CurrentUser.Identifier}')")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    if not TargetFile.IsPublic:
        TargetFile.IsPublic = True
        await DatabaseSession.commit()
        DebugService.LogDebugMessage(f"Storage File Shared: File='{TargetFile.Identifier}', Name='{TargetFile.FileName}', User='{CurrentUser.Identifier}'")

    TriggerPayload: str = JSON.dumps({"fileShared": {"FileIdentifier": TargetFile.Identifier, "FileName": TargetFile.FileName}})
    HeadersDictionary: Typing.Dict[str, str] = {
        "HX-Trigger": TriggerPayload
    }
    return Responses.Response(status_code = 200, headers = HeadersDictionary)

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
        DebugService.LogDebugMessage(f"Storage File Deleted: ID='{TargetFile.Identifier}', Key='{TargetFile.ObjectKey}', Size={TargetFile.FileSizeBytes}B, User='{CurrentUser.Identifier}'")
    else:
        DebugService.LogDebugMessage(f"Storage File Deletion Failed: ID='{FileIdentifier}' Not Found (User='{CurrentUser.Identifier}')")

    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.get("/Files/{FileIdentifier}/Stream")
async def StreamUserFile(FileIdentifier: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogDebugMessage(f"Storage Stream Failed: File '{FileIdentifier}' Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    DebugService.LogDebugMessage(f"Storage Stream Served: File='{TargetFile.Identifier}', Size={len(FileBytes)}B, Type='{TargetFile.ContentType}'")
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType)

@Router.get("/Files/{FileIdentifier}/Download")
async def DownloadUserFile(FileIdentifier: str, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogDebugMessage(f"Storage Download Failed: File '{FileIdentifier}' Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    DebugService.LogDebugMessage(f"Storage Download Served: File='{TargetFile.FileName}', Size={len(FileBytes)}B, Type='{TargetFile.ContentType}'")
    HeadersDictionary: Typing.Dict[str, str] = {
        "Content-Disposition": f'attachment; filename="{TargetFile.FileName}"'
    }
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType, headers = HeadersDictionary)

@PublicObjectRouter.get("/{FileIdentifier}")
@PublicObjectRouter.get("/{FileIdentifier}/{FileName}")
async def RetrievePublicObject(FileIdentifier: str, FileName: Typing.Optional[str] = None, DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.Identifier == FileIdentifier)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: Typing.Optional[StorageFile.StorageFile] = QueryResult.scalars().first()
    if not TargetFile or not TargetFile.IsPublic:
        DebugService.LogDebugMessage(f"Public Object Failed: File '{FileIdentifier}' Not Found Or Private")
        raise FastAPI.HTTPException(status_code = 404, detail = "Object not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if not FileBytes:
        FileBytes = b""

    DebugService.LogDebugMessage(f"Public Object Served: Key='{TargetFile.ObjectKey}', File='{TargetFile.FileName}', Size={len(FileBytes)}B")
    HeadersDictionary: Typing.Dict[str, str] = {
        "Content-Disposition": f'inline; filename="{TargetFile.FileName}"',
        "Cache-Control": "public, max-age=31536000, immutable"
    }
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType, headers = HeadersDictionary)
