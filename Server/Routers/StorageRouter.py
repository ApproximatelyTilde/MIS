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
import Server.Services.DebugService            as DebugService
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
async def ListStorageFilesPartial(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if not CurrentUser:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Storage Files Rejected for Unauthenticated User")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "Please authenticate to access cloud object storage."})

    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.OwnerID == CurrentUser.ID).order_by(StorageFile.StorageFile.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Files = QueryResult.scalars().all()
    if not Files:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Storage Files Empty for User: \"{CurrentUser.ID[:8]}…\"")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"InfoMessage": "No files uploaded yet."})

    FormattedFiles: list[dict[str, Typing.Any]] = []
    for FileRecord in Files:
        SizeKB: float = round(FileRecord.FileSizeBytes / 1000, 1)
        Category: str = GetMIMETypeCategory(FileRecord.ContentType)
        FileEntry: dict[str, Typing.Any] = {
            "ID"         : FileRecord.ID,
            "FileName"   : FileRecord.FileName,
            "ContentType": FileRecord.ContentType,
            "Category"   : Category,
            "SizeKB"     : SizeKB,
            "IsAudio"    : FileRecord.ContentType.startswith("audio/"),
            "IsImage"    : FileRecord.ContentType.startswith("image/"),
            "IsVideo"    : FileRecord.ContentType.startswith("video/"),
            "IsPublic"   : FileRecord.IsPublic
        }
        FormattedFiles.append(FileEntry)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Storage Files: Count={len(FormattedFiles)}")
    return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"Files": FormattedFiles})

@Router.get("/Images/Picker/Partial", response_class = Responses.HTMLResponse)
async def ListStorageImagesPickerPartial(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if not CurrentUser:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Image Picker Rejected for Unauthenticated User")
        return TemplateRenderer.RenderPartialResponse("Storage/ImagePickerGridPartial.html", {"InfoMessage": "Please authenticate to access cloud object storage."})

    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.OwnerID == CurrentUser.ID, StorageFile.StorageFile.ContentType.like("image/%")).order_by(StorageFile.StorageFile.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    ImageFiles = QueryResult.scalars().all()
    if not ImageFiles:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Image Picker Empty for User: \"{CurrentUser.ID[:8]}…\"")
        return TemplateRenderer.RenderPartialResponse("Storage/ImagePickerGridPartial.html", {"InfoMessage": "No image assets found in object storage."})

    FormattedImages: list[dict[str, Typing.Any]] = []
    for FileRecord in ImageFiles:
        SizeKB: float = round(FileRecord.FileSizeBytes / 1000, 1)
        ImageEntry: dict[str, Typing.Any] = {
            "ID"         : FileRecord.ID,
            "FileName"   : FileRecord.FileName,
            "ContentType": FileRecord.ContentType,
            "SizeKB"     : SizeKB
        }
        FormattedImages.append(ImageEntry)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Image Picker: Count={len(FormattedImages)}")
    return TemplateRenderer.RenderPartialResponse("Storage/ImagePickerGridPartial.html", {"Images": FormattedImages})

@Router.get("/Gauge/Partial", response_class = Responses.HTMLResponse)
async def GetStorageGaugePartial(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.HTMLResponse:
    if not CurrentUser:
        return TemplateRenderer.RenderPartialResponse("Storage/StorageGaugePartial.html", {"IsAuthenticated": False})

    TotalBytes: int = Config.GLOBAL_SETTINGS.USER_STORAGE_QUOTA_BYTES
    UsedBytes: int = CurrentUser.StorageUsedBytes
    FreeBytes: int = max(0, TotalBytes - UsedBytes)
    FreeMB: int = int(round(FreeBytes / 1000000))
    UsedPercentage: int = min(100, int(round((UsedBytes / TotalBytes) * 100)))
    QuotaInteger: int = UsedPercentage
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Storage Gauge: Used={UsedPercentage}%, Free={FreeMB}MB")
    Context: dict[str, Typing.Any] = {
        "IsAuthenticated": True,
        "FreeMB"         : FreeMB,
        "UsedPercentage" : UsedPercentage,
        "QuotaInteger"   : QuotaInteger
    }
    return TemplateRenderer.RenderPartialResponse("Storage/StorageGaugePartial.html", Context)

@Router.post("/Upload/Partial", response_class = Responses.HTMLResponse)
async def UploadUserFilePartial(File: FastAPI.UploadFile = FastAPI.File(...), CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if not RoleBasedAccessControl.IsUserInGuild(CurrentUser):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Storage Upload Rejected: User \"{CurrentUser.ID[:8]}…\" Not in Guild")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Upload rejected: Discord server membership required!"})

    FileContent: bytes = await File.read()
    FileSizeBytes: int = len(FileContent)
    if FileSizeBytes == 0:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Storage Upload Rejected: File Is Empty")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Upload rejected: File is empty."})

    if not OracleStorage.GLOBAL_STORAGE_SERVICE.CheckQuotaAvailable(CurrentUser, FileSizeBytes):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Storage Upload Rejected: Quota Exceeded ({FileSizeBytes}B Needed)")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Upload rejected: 100 MB per-user quota exceeded!"})

    ContentType: str = File.content_type if File.content_type else "application/octet-stream"
    FileHash: str = HashLib.sha256(FileContent).hexdigest().upper()[:8]
    HashedFileName: str = FileHash
    ObjectKey = await OracleStorage.GLOBAL_STORAGE_SERVICE.UploadFile(CurrentUser, HashedFileName, ContentType, FileContent)
    if not ObjectKey:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Storage Upload Failed: Provider Error on File \"{HashedFileName}\"")
        return TemplateRenderer.RenderPartialResponse("Storage/FilesTableRowsPartial.html", {"ErrorMessage": "Cloud object storage service is unavailable."})

    NewStorageFile = StorageFile.StorageFile(OwnerID = CurrentUser.ID, FileName = HashedFileName, ContentType = ContentType, FileSizeBytes = FileSizeBytes, ObjectKey = ObjectKey, IsPublic = False)
    DatabaseSession.add(NewStorageFile)
    CurrentUser.StorageUsedBytes += FileSizeBytes
    await DatabaseSession.commit()
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Storage Upload Succeeded: File=\"{HashedFileName}\", Size={FileSizeBytes}B")
    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.post("/Files/{FileID}/Share/Partial", response_class = Responses.Response)
async def ShareStorageFilePartial(FileID: str, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.ID == FileID, StorageFile.StorageFile.OwnerID == CurrentUser.ID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: StorageFile.StorageFile | None = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Storage Share Failed: File \"{FileID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    if not TargetFile.IsPublic:
        TargetFile.IsPublic = True
        await DatabaseSession.commit()
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Storage File Shared: FileID=\"{TargetFile.ID[:8]}…\", Name=\"{TargetFile.FileName}\"")

    TriggerPayload: str = JSON.dumps({"FileShared": {"FileID": TargetFile.ID, "FileName": TargetFile.FileName}})
    HeadersDictionary: dict[str, str] = {
        "HX-Trigger": TriggerPayload
    }
    return Responses.Response(status_code = 200, headers = HeadersDictionary)

@Router.delete("/Files/{FileID}/Delete/Partial", response_class = Responses.HTMLResponse)
async def DeleteUserFilePartial(FileID: str, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.ID == FileID, StorageFile.StorageFile.OwnerID == CurrentUser.ID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: StorageFile.StorageFile | None = QueryResult.scalars().first()
    if TargetFile:
        await OracleStorage.GLOBAL_STORAGE_SERVICE.DeleteFile(TargetFile.ObjectKey)
        CurrentUser.StorageUsedBytes = max(0, CurrentUser.StorageUsedBytes - TargetFile.FileSizeBytes)
        await DatabaseSession.delete(TargetFile)
        await DatabaseSession.commit()
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Storage File Deleted: FileID=\"{TargetFile.ID[:8]}…\", Size={TargetFile.FileSizeBytes}B")

    else:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Storage Deletion Failed: File \"{FileID[:8]}…\" Not Found")

    return await ListStorageFilesPartial(CurrentUser, DatabaseSession)

@Router.get("/Files/{FileID}/Stream")
async def StreamUserFile(FileID: str, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.ID == FileID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: StorageFile.StorageFile | None = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Storage Stream Failed: File \"{FileID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if FileBytes is None:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Storage Stream Failed: Object Data Missing in Storage")
        raise FastAPI.HTTPException(status_code = 404, detail = "File data not found in cloud storage")

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Storage Stream Served: FileID=\"{TargetFile.ID[:8]}…\", Size={len(FileBytes)}B")
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType)

@Router.get("/Files/{FileID}/Download")
async def DownloadUserFile(FileID: str, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.ID == FileID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: StorageFile.StorageFile | None = QueryResult.scalars().first()
    if not TargetFile:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Storage Download Failed: File \"{FileID[:8]}…\" Not Found")
        raise FastAPI.HTTPException(status_code = 404, detail = "File not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if FileBytes is None:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Storage Download Failed: Object Data Missing in Storage")
        raise FastAPI.HTTPException(status_code = 404, detail = "File data not found in cloud storage")

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Storage Download Served: File=\"{TargetFile.FileName}\", Size={len(FileBytes)}B")
    HeadersDictionary: dict[str, str] = {
        "Content-Disposition": f"attachment; filename=\"{TargetFile.FileName}\""
    }
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType, headers = HeadersDictionary)

@PublicObjectRouter.get("/{FileID}")
@PublicObjectRouter.get("/{FileID}/{FileName}")
async def RetrievePublicObject(FileID: str, FileName: Typing.Annotated[str | None, None] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.Response:
    QueryStatement = SQLAlchemy.select(StorageFile.StorageFile).where(StorageFile.StorageFile.ID == FileID)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetFile: StorageFile.StorageFile | None = QueryResult.scalars().first()
    if not TargetFile or not TargetFile.IsPublic:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Public Object Failed: File \"{FileID[:8]}…\" Not Found or Private")
        raise FastAPI.HTTPException(status_code = 404, detail = "Object not found")

    FileBytes = await OracleStorage.GLOBAL_STORAGE_SERVICE.RetrieveFileBytes(TargetFile.ObjectKey)
    if FileBytes is None:
        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = "Public Object Failed: Object Data Missing in Storage")
        raise FastAPI.HTTPException(status_code = 404, detail = "Object data not found in cloud storage")

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Public Object Served: File=\"{TargetFile.FileName}\", Size={len(FileBytes)}B")
    HeadersDictionary: dict[str, str] = {
        "Content-Disposition": f"inline; filename=\"{TargetFile.FileName}\"",
        "Cache-Control"      : "public, max-age=31536000, immutable"
    }
    return Responses.Response(content = FileBytes, media_type = TargetFile.ContentType, headers = HeadersDictionary)
