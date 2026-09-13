import contextlib                   as ContextLibrary
import fastapi                      as FastAPI
import fastapi.responses            as Responses
import fastapi.staticfiles          as StaticFiles
import os                           as OperatingSystem
import typing                       as Typing
import uvicorn                      as Uvicorn
import Server.Config                as Config
import Server.Database              as Database
import Server.Routers               as Routers
import Server.Services.DebugService as Debug

@ContextLibrary.asynccontextmanager
async def ApplicationLifespan(AppInstance: FastAPI.FastAPI) -> Typing.AsyncGenerator[None, None]:
    Debug.ConfigureUvicornAccessLogging()
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Synchronizing Database Tables: Environment={Config.GLOBAL_SETTINGS.ENVIRONMENT}")
    async with Database.ASYNC_ENGINE.begin() as DatabaseConnection:
        await DatabaseConnection.run_sync(Database.Base.metadata.create_all)

    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = "Database Schema Initialized and Ready")

    yield
    Debug.LogMessage(Level = Debug.LogLevel.Info, Message = "Database Engine Disposed on Shutdown")
    await Database.ASYNC_ENGINE.dispose()

APPLICATION_SERVICE: FastAPI.FastAPI = FastAPI.FastAPI(title = "zibell Application Service", version = "1.0.0", lifespan = ApplicationLifespan)
APPLICATION_SERVICE.include_router(Routers.AuthAPIRouter)
APPLICATION_SERVICE.include_router(Routers.AuthenticationCallbackAPIRouter)
APPLICATION_SERVICE.include_router(Routers.AutomationAPIRouter)
APPLICATION_SERVICE.include_router(Routers.CharacterAPIRouter)
APPLICATION_SERVICE.include_router(Routers.StoryAPIRouter)
APPLICATION_SERVICE.include_router(Routers.EconomyAPIRouter)
APPLICATION_SERVICE.include_router(Routers.StorageAPIRouter)
APPLICATION_SERVICE.include_router(Routers.MailAPIRouter)
APPLICATION_SERVICE.include_router(Routers.PublicObjectAPIRouter)
APPLICATION_SERVICE.include_router(Routers.ToolsAPIRouter)
APPLICATION_SERVICE.include_router(Routers.DesktopWindowAPIRouter)
APPLICATION_SERVICE.include_router(Routers.CombatAPIRouter)
APPLICATION_SERVICE.include_router(Routers.AliasingAPIRouter)
APPLICATION_SERVICE.include_router(Routers.VariableAPIRouter)
APPLICATION_SERVICE.include_router(Routers.ServerSettingsAPIRouter)
if OperatingSystem.path.exists("Client/Resources"):
    APPLICATION_SERVICE.mount("/Resources", StaticFiles.StaticFiles(directory = "Client/Resources"), name = "Resources")

if OperatingSystem.path.exists("Client/External"):
    APPLICATION_SERVICE.mount("/External", StaticFiles.StaticFiles(directory = "Client/External"), name = "External")

@APPLICATION_SERVICE.get("/", response_class = Responses.HTMLResponse)
async def ServeClientDesktop(Request: FastAPI.Request) -> Responses.HTMLResponse:
    IndexPath = OperatingSystem.path.join("Client", "Index.html")
    if OperatingSystem.path.exists(IndexPath):
        with open(IndexPath, "r", encoding = "utf-8") as FileHandle:
            HTMLContent: str = FileHandle.read()

        Environment: str = Config.GLOBAL_SETTINGS.ENVIRONMENT
        HTMLContent = HTMLContent.replace("<head>", f"<head>\n    <meta name=\"Environment\" content=\"{Environment}\">")

        CacheControl: str = Request.headers.get("cache-control", "").lower()
        Pragma: str = Request.headers.get("pragma", "").lower()
        IsHardReload: bool = ("no-cache" in CacheControl) or ("no-cache" in Pragma)
        if IsHardReload:
            HTMLContent = HTMLContent.replace("<head>", "<head>\n  <meta name=\"ClientHardReload\" content=\"true\">")

        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Client Desktop Served: HardReload={IsHardReload}, Environment={Environment}")
        return Responses.HTMLResponse(content = HTMLContent)

    Debug.LogMessage(Level = Debug.LogLevel.Error, Message = f"Client Desktop Missing: Path=\"{IndexPath}\"")
    raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = "Client Index File Not Found")

@APPLICATION_SERVICE.get("/favicon.ico", include_in_schema = False)
async def ServeFavicon() -> Responses.FileResponse:
    FaviconPath: str = OperatingSystem.path.join("Client", "Resources", "favicon.ico")
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = "Favicon Asset Served to Client")
    return Responses.FileResponse(FaviconPath)

@APPLICATION_SERVICE.get("/apple-touch-icon.png", include_in_schema = False)
async def ServeAppleTouchIcon() -> Responses.FileResponse:
    AppleTouchIconPath: str = OperatingSystem.path.join("Client", "Resources", "apple-touch-icon.png")
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = "Apple Touch Icon Asset Served to Client")
    return Responses.FileResponse(AppleTouchIconPath)

@APPLICATION_SERVICE.get("/site.webmanifest", include_in_schema = False)
async def ServeSiteWebManifest() -> Responses.FileResponse:
    ManifestPath: str = OperatingSystem.path.join("Client", "Resources", "site.webmanifest")
    Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = "Web Manifest Asset Served to Client")
    return Responses.FileResponse(ManifestPath, media_type = "application/manifest+json")

if (__name__ == "__main__"):
    Uvicorn.run("Main:APPLICATION_SERVICE", host = Config.GLOBAL_SETTINGS.HOST, port = Config.GLOBAL_SETTINGS.PORT, reload = (Config.GLOBAL_SETTINGS.ENVIRONMENT.lower() == "development"))

