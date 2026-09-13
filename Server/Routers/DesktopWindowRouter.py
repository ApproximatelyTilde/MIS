import typing                                  as Typing
import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import sqlalchemy                              as SQLAlchemy
import sqlalchemy.ext.asyncio                  as AsyncIO
import Server.Auth.RoleBasedAccessControl      as RoleBasedAccessControl
import Server.Database                         as Database
import Server.Models.Character                 as Character
import Server.Models.Mail                      as Mail
import Server.Models.User                      as User
import Server.Services.CharacterMappingService as CharacterMappingService
import Server.Services.DebugService            as DebugService
import Server.Services.MailService             as MailService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Desktop/Windows", tags = ["DesktopWindows"])

@Router.get("/ApplicationLauncher", response_class = Responses.HTMLResponse)
@Router.get("/application-launcher", response_class = Responses.HTMLResponse)
async def GetApplicationLauncherWindowContent() -> Responses.HTMLResponse:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Application Launcher Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/ApplicationLauncherWindow.html")

@Router.get("/AccountCentre", response_class = Responses.HTMLResponse)
async def GetAccountCentreWindowContent() -> Responses.HTMLResponse:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Account Centre Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/AccountCentreWindow.html")

@Router.get("/DiceRoller", response_class = Responses.HTMLResponse)
async def GetDiceRollerWindowContent() -> Responses.HTMLResponse:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Dice Roller Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/DiceRollerWindow.html")

@Router.get("/Clock", response_class = Responses.HTMLResponse)
async def GetClockWindowContent() -> Responses.HTMLResponse:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Clock Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/ClockWindow.html")

@Router.get("/NPCGenerator", response_class = Responses.HTMLResponse)
async def GetNPCGeneratorWindowContent(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.HTMLResponse:
    UserID = getattr(CurrentUser, "ID", None)
    if not RoleBasedAccessControl.IsGameMaster(CurrentUser):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Access Denied for Non Game Master User: \"{str(UserID)[:8]}…\"")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Game Master role required")

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Non Player Character Generator Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/NPCGeneratorWindow.html")

@Router.get("/CharacterSheet", response_class = Responses.HTMLResponse)
async def GetCharacterSheetWindowContent(GameSystem: str | None = None, CharacterID: str | None = None, CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    IsAllowed: bool = RoleBasedAccessControl.CanCreateCharacter(CurrentUser)
    ResolvedSystem: str = GameSystem or "DND5thEdition"
    TargetCharacter: Character.Character | None = None
    IsSpecificCharacterRequested: bool = (CharacterID is not None) and (CharacterID not in ("Current", "Draft", "New", ""))
    if IsSpecificCharacterRequested:
        QueryStatement = SQLAlchemy.select(Character.Character).where(Character.Character.ID == CharacterID)
        QueryResult = await DatabaseSession.execute(QueryStatement)
        TargetCharacter = QueryResult.scalars().first()
        if (TargetCharacter is None):
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Character Not Found: ID=\"{CharacterID[:8]}…\"")
            return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterNotFoundWindow.html", StatusCode = 404)

        if not RoleBasedAccessControl.CanViewCharacter(CurrentUser, TargetCharacter):
            CharID: str | None = TargetCharacter.ID
            UserID: str | None = CurrentUser.ID if (CurrentUser is not None) else None
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"View Access Denied for Character: ID=\"{str(CharID)[:8]}…\"")
            return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterAccessDeniedWindow.html", StatusCode = 403)

    CanModify     : bool                 = RoleBasedAccessControl.CanModifyCharacter(CurrentUser, TargetCharacter) if (TargetCharacter is not None) else RoleBasedAccessControl.CanCreateCharacter(CurrentUser)
    IsAllowed     : bool                 = True if (TargetCharacter is not None) else RoleBasedAccessControl.CanCreateCharacter(CurrentUser)
    ResolvedSystem: str                  = GameSystem or "DND5thEdition"
    IsProtected   : bool                 = True if (not CanModify) else (TargetCharacter.IsProtected if (TargetCharacter is not None) else False)
    IsOverridden  : bool                 = TargetCharacter.IsOverridden if (TargetCharacter is not None) else False
    UserID        : str | None           = CurrentUser.ID if (CurrentUser is not None) else None
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Character Sheet: System=\"{ResolvedSystem}\", Allowed={IsAllowed}")
    Context: dict[str, Typing.Any] = CharacterMappingService.GLOBAL_CHARACTER_MAPPER.BuildCharacterSheetContext(TargetCharacter = TargetCharacter, IsAllowed = IsAllowed, IsProtected = IsProtected, IsOverridden = IsOverridden, ActiveTab = "CharacterSheetOverviewTab")
    Context["GameSystem"] = ResolvedSystem

    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterSheetWindow.html", Context)

@Router.get("/Calendar", response_class = Responses.HTMLResponse)
async def GetCalendarWindowContent() -> Responses.HTMLResponse:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Calendar Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CalendarWindow.html")

@Router.get("/Storage", response_class = Responses.HTMLResponse)
async def GetStorageWindowContent(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.HTMLResponse:
    IsInGuild: bool = RoleBasedAccessControl.IsUserInGuild(CurrentUser)
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Content for Storage Window: InGuild={IsInGuild}")
    Context: dict[str, Typing.Any] = {
        "IsInGuild": IsInGuild
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/StorageWindow.html", Context)

@Router.get("/RoleSwitcher", response_class = Responses.HTMLResponse)
async def GetRoleSwitcherWindowContent() -> Responses.HTMLResponse:
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = "Served Content for Role Switcher Window")
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/RoleSwitcherWindow.html")

@Router.get("/PortraitAssetPicker", response_class = Responses.HTMLResponse)
async def GetPortraitAssetPickerWindowContent(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.HTMLResponse:
    IsInGuild: bool = RoleBasedAccessControl.IsUserInGuild(CurrentUser)
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Content for Portrait Picker Window: InGuild={IsInGuild}")
    Context: dict[str, Typing.Any] = {
        "IsAuthenticated": CurrentUser is not None,
        "IsInGuild": IsInGuild
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/PortraitAssetPickerWindow.html", Context)

@Router.get("/CharacterImport", response_class = Responses.HTMLResponse)
@Router.get("/CharacterImport/", response_class = Responses.HTMLResponse)
@Router.get("/character-import", response_class = Responses.HTMLResponse)
async def GetCharacterImportWindowContent(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None) -> Responses.HTMLResponse:
    IsAuthenticated: bool = (CurrentUser is not None) and (CurrentUser.Role != User.UserRole.Visitor)
    IsInGuild: bool = RoleBasedAccessControl.IsUserInGuild(CurrentUser) if (IsAuthenticated) else False
    UserID: str | None = CurrentUser.ID if (CurrentUser is not None) else None
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Content for Character Import Window: InGuild={IsInGuild}")
    Context: dict[str, Typing.Any] = {
        "IsAuthenticated": IsAuthenticated,
        "IsInGuild"      : IsInGuild
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/CharacterImportWindow.html", Context)

@Router.get("/SearchCharacters", response_class = Responses.HTMLResponse)
@Router.get("/SearchCharacters/", response_class = Responses.HTMLResponse)
@Router.get("/search-characters", response_class = Responses.HTMLResponse)
async def GetSearchCharactersWindowContent(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Character.Character)
    QueryResult    = await DatabaseSession.execute(QueryStatement)
    AllCharacters  = QueryResult.scalars().all()

    DNDClasses: Typing.List[str] = sorted(list({Char.SummaryData.get("Class") for Char in AllCharacters if ((Char.GameSystem == Character.GameSystemType.DND5thEdition) and (Char.SummaryData is not None) and bool(Char.SummaryData.get("Class")))}))
    DNDSpecies: Typing.List[str] = sorted(list({Char.SummaryData.get("Species") for Char in AllCharacters if ((Char.GameSystem == Character.GameSystemType.DND5thEdition) and (Char.SummaryData is not None) and bool(Char.SummaryData.get("Species")))}))
    TravellerCareers: Typing.List[str] = sorted(list({Char.SummaryData.get("Career") for Char in AllCharacters if ((Char.GameSystem == Character.GameSystemType.Traveller2ndEdition) and (Char.SummaryData is not None) and bool(Char.SummaryData.get("Career")))}))
    TravellerHomeworlds: Typing.List[str] = sorted(list({Char.SummaryData.get("Homeworld") for Char in AllCharacters if ((Char.GameSystem == Character.GameSystemType.Traveller2ndEdition) and (Char.SummaryData is not None) and bool(Char.SummaryData.get("Homeworld")))}))

    CanViewPrivateOrArchived: bool = RoleBasedAccessControl.IsGameMaster(CurrentUser)
    UserID = CurrentUser.ID if (CurrentUser is not None) else None
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Search Window: Classes={len(DNDClasses)}, Species={len(DNDSpecies)}")
    Context: dict[str, Typing.Any] = {
        "DNDClasses"              : DNDClasses,
        "DNDSpecies"              : DNDSpecies,
        "TravellerCareers"        : TravellerCareers,
        "TravellerHomeworlds"     : TravellerHomeworlds,
        "CanViewPrivateOrArchived": CanViewPrivateOrArchived
    }

    return TemplateRenderer.RenderPartialResponse("DesktopWindows/SearchCharactersWindow.html", Context)

@Router.get("/Mail", response_class = Responses.HTMLResponse)
async def GetMailWindowContent(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    IsAuthenticated: bool = (CurrentUser is not None) and (CurrentUser.Role != User.UserRole.Visitor)
    if not IsAuthenticated:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Access Denied for Unauthenticated Visitor on Mail Window")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Authentication required to access Mail")

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Content for Mail Window: UserID=\"{CurrentUser.ID[:8]}…\"")
    Context: dict[str, Typing.Any] = {
        "IsAuthenticated": IsAuthenticated,
        "IsGameMaster"   : RoleBasedAccessControl.IsGameMaster(CurrentUser)
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/MailWindow.html", Context)

@Router.get("/MailCompose", response_class = Responses.HTMLResponse)
async def GetMailComposeWindowContent(RecipientUserID: str = "", RecipientUsername: str = "", Subject: str = "", Category: str = "GeneralMessage", RelatedEntityType: str = "", RelatedEntityID: str = "", BodyTemplate: str = "", CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    IsAuthenticated: bool = (CurrentUser is not None) and (CurrentUser.Role != User.UserRole.Visitor)
    if not IsAuthenticated:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Access Denied for Unauthenticated Visitor on Mail Compose Window")
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_401_UNAUTHORIZED, detail = "Authentication required to access Mail Compose")

    CategoryOptions: list[dict[str, str]] = [{"Value": Cat.value, "Label": MailService.CATEGORY_DISPLAY_MAPPING.get(Cat, Cat.value)} for Cat in Mail.MailCategory if Cat != Mail.MailCategory.SystemAlert]

    PrefilledRecipients: list[dict[str, str]] = []
    if RecipientUserID:
        RecipientQuery = SQLAlchemy.select(User.User).where(User.User.ID == RecipientUserID)
        RecipientResult = await DatabaseSession.execute(RecipientQuery)
        ResolvedUser = RecipientResult.scalars().first()
        if ResolvedUser:
            PrefilledRecipients.append({
                "ID"          : ResolvedUser.ID,
                "Username"    : ResolvedUser.Username,
                "DisplayName" : ResolvedUser.DisplayName,
                "FormattedTag": f"@{ResolvedUser.Username}"
            })

    elif RecipientUsername:
        CleanUser = RecipientUsername.lstrip("@").strip()
        RecipientQuery = SQLAlchemy.select(User.User).where(User.User.Username == CleanUser)
        RecipientResult = await DatabaseSession.execute(RecipientQuery)
        ResolvedUser = RecipientResult.scalars().first()
        if ResolvedUser:
            PrefilledRecipients.append({
                "ID"          : ResolvedUser.ID,
                "Username"    : ResolvedUser.Username,
                "DisplayName" : ResolvedUser.DisplayName,
                "FormattedTag": f"@{ResolvedUser.Username}"
            })

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Served Content for Mail Compose Window: UserID=\"{CurrentUser.ID[:8]}…\"")
    Context: dict[str, Typing.Any] = {
        "IsAuthenticated"    : IsAuthenticated,
        "PrefilledRecipients": PrefilledRecipients,
        "Subject"            : Subject,
        "Category"           : Category,
        "CategoryOptions"    : CategoryOptions,
        "RelatedEntityType"  : RelatedEntityType,
        "RelatedEntityID"    : RelatedEntityID,
        "BodyTemplate"       : BodyTemplate
    }
    return TemplateRenderer.RenderPartialResponse("DesktopWindows/MailComposeWindow.html", Context)



