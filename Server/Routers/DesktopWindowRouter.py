import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Desktop/Windows", tags = ["DesktopWindows"])

@Router.get("/ApplicationLauncher", response_class = Responses.HTMLResponse)
@Router.get("/application-launcher", response_class = Responses.HTMLResponse)
async def GetApplicationLauncherWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/ApplicationLauncherWindow.html")

@Router.get("/AccountCentre", response_class = Responses.HTMLResponse)
async def GetAccountCentreWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/AccountCentreWindow.html")

@Router.get("/DiceRoller", response_class = Responses.HTMLResponse)
async def GetDiceRollerWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/DiceRollerWindow.html")

@Router.get("/CharacterGenerator", response_class = Responses.HTMLResponse)
async def GetCharacterGeneratorWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterGeneratorWindow.html")

@Router.get("/Calendar", response_class = Responses.HTMLResponse)
async def GetCalendarWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CalendarWindow.html")

@Router.get("/Storage", response_class = Responses.HTMLResponse)
async def GetStorageWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/StorageWindow.html")

@Router.get("/RoleSwitcher", response_class = Responses.HTMLResponse)
async def GetRoleSwitcherWindowContent() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/RoleSwitcherWindow.html")
