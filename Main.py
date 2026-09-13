import contextlib                               as ContextLibrary
import fastapi                                  as FastAPI
import fastapi.responses                        as Responses
import fastapi.staticfiles                      as StaticFiles
import os                                       as OperatingSystem
import typing                                   as Typing
import Server.Config                            as Config
import Server.Database                          as Database
import Server.Routers                           as Routers
import Server.Services.TemplateRendererService  as TemplateRenderer

@ContextLibrary.asynccontextmanager
async def ApplicationLifespan(AppInstance: FastAPI.FastAPI) -> Typing.AsyncGenerator[None, None]:
    async with Database.ASYNC_ENGINE.begin() as DatabaseConnection:
        await DatabaseConnection.run_sync(Database.Base.metadata.create_all)

    yield
    await Database.ASYNC_ENGINE.dispose()

Service = FastAPI.FastAPI(title = "MIS In-Universe Simulated Desktop", version = "1.0.0", lifespan = ApplicationLifespan)
Service.include_router(Routers.AuthAPIRouter)
Service.include_router(Routers.AuthenticationCallbackAPIRouter)
Service.include_router(Routers.CharacterAPIRouter)
Service.include_router(Routers.StoryAPIRouter)
Service.include_router(Routers.EconomyAPIRouter)
Service.include_router(Routers.StorageAPIRouter)
Service.include_router(Routers.ToolsAPIRouter)
Service.include_router(Routers.DesktopWindowAPIRouter)
if OperatingSystem.path.exists("Client/Resources"):
    Service.mount("/Resources", StaticFiles.StaticFiles(directory = "Client/Resources"), name = "Resources")

@Service.get("/", response_class = Responses.HTMLResponse)
async def ServeClientDesktop(Request: FastAPI.Request) -> Responses.HTMLResponse:
    IndexPath = OperatingSystem.path.join("Client", "Index.html")
    if OperatingSystem.path.exists(IndexPath):
        with open(IndexPath, "r", encoding = "utf-8") as FileHandle:
            HTMLContent: str = FileHandle.read()

        CacheControl: str = Request.headers.get("cache-control", "").lower()
        Pragma: str = Request.headers.get("pragma", "").lower()
        IsHardReload: bool = ("no-cache" in CacheControl) or ("no-cache" in Pragma)
        if IsHardReload:
            HTMLContent = HTMLContent.replace("<head>", '<head>\n  <meta name="ClientHardReload" content="true">')

        return Responses.HTMLResponse(content = HTMLContent)

    return TemplateRenderer.RenderPartialResponse("Fallback/DesktopFallback.html")

@Service.get("/favicon.ico", include_in_schema = False)
async def ServeFavicon() -> Responses.FileResponse:
    FaviconPath: str = OperatingSystem.path.join("Client", "Resources", "favicon.ico")
    return Responses.FileResponse(FaviconPath)

@Service.get("/apple-touch-icon.png", include_in_schema = False)
async def ServeAppleTouchIcon() -> Responses.FileResponse:
    AppleTouchIconPath: str = OperatingSystem.path.join("Client", "Resources", "apple-touch-icon.png")
    return Responses.FileResponse(AppleTouchIconPath)

@Service.get("/site.webmanifest", include_in_schema = False)
async def ServeSiteWebManifest() -> Responses.FileResponse:
    ManifestPath: str = OperatingSystem.path.join("Client", "Resources", "site.webmanifest")
    return Responses.FileResponse(ManifestPath, media_type = "application/manifest+json")

