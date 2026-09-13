import contextlib                               as ContextLibrary
import fastapi                                  as FastAPI
import fastapi.responses                        as Responses
import fastapi.staticfiles                      as StaticFiles
import os                                       as OperatingSystem
import typing                                   as Typing
import Server.Config                            as Config
import Server.Database                          as Database
import Server.Routers                           as Routers
import Server.Services.DebugService             as DebugService

@ContextLibrary.asynccontextmanager
async def ApplicationLifespan(AppInstance: FastAPI.FastAPI) -> Typing.AsyncGenerator[None, None]:
    DebugService.LogDebugMessage(f"Lifespan Startup: Synchronizing Database Tables ({Config.GLOBAL_SETTINGS.ENVIRONMENT})")
    async with Database.ASYNC_ENGINE.begin() as DatabaseConnection:
        await DatabaseConnection.run_sync(Database.Base.metadata.create_all)
    DebugService.LogDebugMessage("Lifespan Startup: Database Schema Ready")

    yield
    DebugService.LogDebugMessage("Lifespan Shutdown: Database Engine Disposed")
    await Database.ASYNC_ENGINE.dispose()

APPLICATION_SERVICE: FastAPI.FastAPI = FastAPI.FastAPI(title = "MIS In-Universe Simulated Desktop", version = "1.0.0", lifespan = ApplicationLifespan)
Service: FastAPI.FastAPI = APPLICATION_SERVICE
APPLICATION_SERVICE.include_router(Routers.AuthAPIRouter)
APPLICATION_SERVICE.include_router(Routers.AuthenticationCallbackAPIRouter)
APPLICATION_SERVICE.include_router(Routers.CharacterAPIRouter)
APPLICATION_SERVICE.include_router(Routers.StoryAPIRouter)
APPLICATION_SERVICE.include_router(Routers.EconomyAPIRouter)
APPLICATION_SERVICE.include_router(Routers.StorageAPIRouter)
APPLICATION_SERVICE.include_router(Routers.PublicObjectAPIRouter)
APPLICATION_SERVICE.include_router(Routers.ToolsAPIRouter)
APPLICATION_SERVICE.include_router(Routers.DesktopWindowAPIRouter)
if OperatingSystem.path.exists("Client/Resources"):
    APPLICATION_SERVICE.mount("/Resources", StaticFiles.StaticFiles(directory = "Client/Resources"), name = "Resources")

@APPLICATION_SERVICE.get("/", response_class = Responses.HTMLResponse)
async def ServeClientDesktop(Request: FastAPI.Request) -> Responses.HTMLResponse:
    IndexPath = OperatingSystem.path.join("Client", "Index.html")
    if OperatingSystem.path.exists(IndexPath):
        with open(IndexPath, "r", encoding = "utf-8") as FileHandle:
            HTMLContent: str = FileHandle.read()

        Environment: str = Config.GLOBAL_SETTINGS.ENVIRONMENT
        HTMLContent = HTMLContent.replace("<head>", '<head>\n    <meta name="Environment" content="' + Environment + '">')

        CacheControl: str = Request.headers.get("cache-control", "").lower()
        Pragma: str = Request.headers.get("pragma", "").lower()
        IsHardReload: bool = ("no-cache" in CacheControl) or ("no-cache" in Pragma)
        if IsHardReload:
            HTMLContent = HTMLContent.replace("<head>", '<head>\n  <meta name="ClientHardReload" content="true">')

        DebugService.LogDebugMessage(f"Desktop Served: HardReload={IsHardReload}, Env={Environment}")
        return Responses.HTMLResponse(content = HTMLContent)

    DebugService.LogDebugMessage(f"Desktop Missing: Path='{IndexPath}' Not Found")
    raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = "Client Index File Not Found")

@APPLICATION_SERVICE.get("/favicon.ico", include_in_schema = False)
async def ServeFavicon() -> Responses.FileResponse:
    FaviconPath: str = OperatingSystem.path.join("Client", "Resources", "favicon.ico")
    DebugService.LogDebugMessage(f"Asset Served: Favicon='{FaviconPath}'")
    return Responses.FileResponse(FaviconPath)

@APPLICATION_SERVICE.get("/apple-touch-icon.png", include_in_schema = False)
async def ServeAppleTouchIcon() -> Responses.FileResponse:
    AppleTouchIconPath: str = OperatingSystem.path.join("Client", "Resources", "apple-touch-icon.png")
    DebugService.LogDebugMessage(f"Asset Served: AppleTouchIcon='{AppleTouchIconPath}'")
    return Responses.FileResponse(AppleTouchIconPath)

@APPLICATION_SERVICE.get("/site.webmanifest", include_in_schema = False)
async def ServeSiteWebManifest() -> Responses.FileResponse:
    ManifestPath: str = OperatingSystem.path.join("Client", "Resources", "site.webmanifest")
    DebugService.LogDebugMessage(f"Asset Served: WebManifest='{ManifestPath}'")
    return Responses.FileResponse(ManifestPath, media_type = "application/manifest+json")

