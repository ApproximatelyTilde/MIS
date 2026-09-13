import typing                                  as Typing
import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import Server.Auth.RoleBasedAccessControl      as RoleBasedAccessControl
import Server.Models.User                      as User
import Server.Services.DebugService             as DebugService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Desktop/Windows", tags = ["DesktopWindows"])

@Router.get("/ApplicationLauncher", response_class = Responses.HTMLResponse)
@Router.get("/application-launcher", response_class = Responses.HTMLResponse)
async def GetApplicationLauncherWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Window Requested: ApplicationLauncher")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/ApplicationLauncherWindow.html")

@Router.get("/AccountCentre", response_class = Responses.HTMLResponse)
async def GetAccountCentreWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Window Requested: AccountCentre")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/AccountCentreWindow.html")

@Router.get("/DiceRoller", response_class = Responses.HTMLResponse)
async def GetDiceRollerWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Window Requested: DiceRoller")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/DiceRollerWindow.html")

@Router.get("/NPCGenerator", response_class = Responses.HTMLResponse)
async def GetNPCGeneratorWindowContent(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    UserIdentifier = getattr(CurrentUser, "Identifier", None)
    if not RoleBasedAccessControl.IsGameMaster(CurrentUser):
        DebugService.LogDebugMessage(f"Window Denied: NPCGenerator (User={UserIdentifier}, Reason=GameMasterRequired)")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Game Master role required")

    DebugService.LogDebugMessage(f"Window Requested: NPCGenerator (User={UserIdentifier})")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/NPCGeneratorWindow.html")

@Router.get("/CharacterSheet", response_class = Responses.HTMLResponse)
async def GetCharacterSheetWindowContent(GameSystem: Typing.Optional[str] = None, CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    IsAllowed: bool = RoleBasedAccessControl.CanCreateCharacter(CurrentUser)
    ResolvedSystem: str = GameSystem or "DND5thEdition"
    DebugService.LogDebugMessage(f"Window Requested: CharacterSheet (System='{ResolvedSystem}', User={getattr(CurrentUser, 'Identifier', None)}, CanCreate={IsAllowed})")
    Context: Typing.Dict[str, Typing.Any] = {
        "GameSystem": ResolvedSystem,
        "IsAllowed" : IsAllowed
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterSheetWindow.html", Context)

@Router.get("/Calendar", response_class = Responses.HTMLResponse)
async def GetCalendarWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Window Requested: Calendar")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CalendarWindow.html")

@Router.get("/Storage", response_class = Responses.HTMLResponse)
async def GetStorageWindowContent(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    IsInGuild: bool = RoleBasedAccessControl.IsUserInGuild(CurrentUser)
    DebugService.LogDebugMessage(f"Window Requested: Storage (User={getattr(CurrentUser, 'Identifier', None)}, InGuild={IsInGuild})")
    Context: Typing.Dict[str, Typing.Any] = {
        "IsInGuild": IsInGuild
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/StorageWindow.html", Context)

@Router.get("/RoleSwitcher", response_class = Responses.HTMLResponse)
async def GetRoleSwitcherWindowContent() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Window Requested: RoleSwitcher")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/RoleSwitcherWindow.html")

@Router.get("/PortraitAssetPicker", response_class = Responses.HTMLResponse)
async def GetPortraitAssetPickerWindowContent(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)) -> Responses.HTMLResponse:
    IsInGuild: bool = RoleBasedAccessControl.IsUserInGuild(CurrentUser)
    DebugService.LogDebugMessage(f"Window Requested: PortraitAssetPicker (User={getattr(CurrentUser, 'Identifier', None)}, Auth={CurrentUser is not None}, InGuild={IsInGuild})")
    Context: Typing.Dict[str, Typing.Any] = {
        "IsAuthenticated": CurrentUser is not None,
        "IsInGuild": IsInGuild
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/PortraitAssetPickerWindow.html", Context)

