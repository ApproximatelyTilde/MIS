import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import Server.Services.DebugService             as DebugService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Desktop/Windows", tags = ["DesktopWindows"])

@Router.get("/ApplicationLauncher", response_class = Responses.HTMLResponse)
@Router.get("/application-launcher", response_class = Responses.HTMLResponse)
async def GetApplicationLauncherWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Application Launcher Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/ApplicationLauncherWindow.html")

@Router.get("/AccountCentre", response_class = Responses.HTMLResponse)
async def GetAccountCentreWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Account Centre Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/AccountCentreWindow.html")

@Router.get("/DiceRoller", response_class = Responses.HTMLResponse)
async def GetDiceRollerWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Dice Roller Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/DiceRollerWindow.html")

@Router.get("/CharacterGenerator", response_class = Responses.HTMLResponse)
async def GetCharacterGeneratorWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Character Generator Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterGeneratorWindow.html")

@Router.get("/Calendar", response_class = Responses.HTMLResponse)
async def GetCalendarWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Calendar Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CalendarWindow.html")

@Router.get("/Storage", response_class = Responses.HTMLResponse)
async def GetStorageWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Storage Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/StorageWindow.html")

@Router.get("/RoleSwitcher", response_class = Responses.HTMLResponse)
async def GetRoleSwitcherWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Role Switcher Window Content")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/RoleSwitcherWindow.html")
