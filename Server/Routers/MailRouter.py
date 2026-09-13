import datetime                             as DateTime
import typing                               as Typing
import fastapi                              as FastAPI
import fastapi.responses                    as Responses
import sqlalchemy                           as SQLAlchemy
import sqlalchemy.ext.asyncio               as AsyncIO
import Server.Auth.RoleBasedAccessControl   as RoleBasedAccessControl
import Server.Database                      as Database
import Server.Models.Mail                   as Mail
import Server.Models.User                   as User
import Server.Services.DebugService         as DebugService
import Server.Services.MailService          as MailService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Mail", tags = ["Mail"])

@Router.get("/Status", response_class = Responses.JSONResponse)
async def GetMailStatus(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.JSONResponse:
    if (CurrentUser is None) or (CurrentUser.Role == User.UserRole.Visitor):
        return Responses.JSONResponse(content = {"HasUnread": False, "UnreadCount": 0})

    if RoleBasedAccessControl.HasUserRole(CurrentUser, "Sheet Checker (DND5thEdition)") or RoleBasedAccessControl.HasUserRole(CurrentUser, "Sheet Checker (Traveller2ndEdition)") or (CurrentUser.Role in (User.UserRole.Checker, User.UserRole.Administrator)):
        await MailService.CheckOverdueCharacterReviews(DatabaseSession = DatabaseSession)

    UnreadCount: int = await MailService.GetUnreadMailCount(DatabaseSession = DatabaseSession, RecipientUserID = CurrentUser.ID)
    StatusData: dict[str, Typing.Any] = {
        "HasUnread"  : bool(UnreadCount > 0),
        "UnreadCount": UnreadCount
    }
    return Responses.JSONResponse(content = StatusData)

@Router.get("/Recipients", response_class = Responses.JSONResponse)
async def GetEligibleRecipientsEndpoint(CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.JSONResponse:
    Recipients: list[dict[str, str]] = await MailService.GetEligibleRecipients(DatabaseSession = DatabaseSession, CurrentUserID = CurrentUser.ID)
    return Responses.JSONResponse(content = Recipients)

@Router.post("/Preview/Partial", response_class = Responses.HTMLResponse)
async def GetMailPreviewPartial(Body: Typing.Annotated[str, FastAPI.Form()] = "") -> Responses.HTMLResponse:
    RenderedHTML: str = MailService.RenderMarkdown(Body)
    return TemplateRenderer.RenderPartialResponse("Mail/MailPreviewPartial.html", {"RenderedHTML": RenderedHTML})

@Router.get("/List/Partial", response_class = Responses.HTMLResponse)
async def GetMailListPartial(Filter: str = "All", SelectedMessageID: str | None = None, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if CurrentUser.Role == User.UserRole.Visitor:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Guests are not allowed to access Mail")

    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    FilterUnreadOnly: bool = (Filter == "Unread")
    Messages: list[Mail.MailMessage] = await MailService.GetInboxMessages(DatabaseSession = DatabaseSession, RecipientUserID = CurrentUser.ID, FilterUnreadOnly = FilterUnreadOnly)

    FormattedMessages: list[dict[str, Typing.Any]] = []
    for MessageItem in Messages:
        SenderName        : str               = MailService.SYSTEM_SENDER_NAME if MessageItem.IsAutomated else (MessageItem.Sender.DisplayName if MessageItem.Sender else "Unknown")
        SenderPortraitURL : str               = MailService.ResolveSenderPortraitURL(SenderUser = MessageItem.Sender, IsAutomated = MessageItem.IsAutomated)
        CreatedAtUTC      : DateTime.datetime = MessageItem.CreatedAt
        FormattedTimestamp: str               = CreatedAtUTC.strftime("%I:%M %p")
        FormattedMessages.append({
            "ID"                  : MessageItem.ID,
            "SenderName"          : SenderName,
            "SenderPortraitURL"   : SenderPortraitURL,
            "Subject"             : MessageItem.Subject,
            "Category"            : MessageItem.Category.value,
            "CategoryDisplayLabel": MailService.GetCategoryDisplayLabel(MessageItem.Category),
            "IsAutomated"         : MessageItem.IsAutomated,
            "IsRead"              : MessageItem.IsRead,
            "FormattedTimestamp"  : FormattedTimestamp,
            "CreatedAt"           : MessageItem.CreatedAt,
            "CreatedAtISO"        : MessageItem.CreatedAt.isoformat(),
            "IsSelected"          : (MessageItem.ID == SelectedMessageID)
        })

    Context: dict[str, Typing.Any] = {
        "Messages"         : FormattedMessages,
        "ActiveFilter"     : Filter,
        "SelectedMessageID": SelectedMessageID,
        "IsGameMaster"     : RoleBasedAccessControl.IsGameMaster(CurrentUser)
    }
    return TemplateRenderer.RenderPartialResponse("Mail/MailListPartial.html", Context)

@Router.get("/Message/{MessageID}/Partial", response_class = Responses.HTMLResponse)
async def GetMailMessageViewPartial(MessageID: str, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if CurrentUser.Role == User.UserRole.Visitor:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Guests are not allowed to access Mail")

    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    TargetMessage: Mail.MailMessage | None = await MailService.GetMessageByID(DatabaseSession = DatabaseSession, MessageID = MessageID, UserID = CurrentUser.ID)
    if TargetMessage is None:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = "Message not found")

    if (not TargetMessage.IsRead) and (TargetMessage.RecipientUserID == CurrentUser.ID):
        await MailService.MarkMessageAsRead(DatabaseSession = DatabaseSession, MessageID = TargetMessage.ID, RecipientUserID = CurrentUser.ID)
        TargetMessage.IsRead = True

    RenderedBodyHtml    : str                   = MailService.RenderMarkdown(TargetMessage.Body)
    CategoryDisplayLabel: str                   = MailService.GetCategoryDisplayLabel(TargetMessage.Category)
    ActivityState       : dict[str, Typing.Any] = MailService.ResolveUserActivityState(SenderUser = TargetMessage.Sender, IsAutomated = TargetMessage.IsAutomated)
    InUniverseYear      : int                   = TargetMessage.CreatedAt.year - 36
    CreatedAtFormatted  : str                   = f"{TargetMessage.CreatedAt.strftime('%d/%m')}/{InUniverseYear} {TargetMessage.CreatedAt.strftime('%I:%M %p')}"

    Context: dict[str, Typing.Any] = {
        "Message"             : TargetMessage,
        "RenderedBodyHtml"    : RenderedBodyHtml,
        "CategoryDisplayLabel": CategoryDisplayLabel,
        "ActivityState"       : ActivityState,
        "CreatedAtFormatted"  : CreatedAtFormatted,
        "CurrentUserID"       : CurrentUser.ID
    }
    Headers: dict[str, str] = {
        "HX-Trigger": "UpdateMailStatus"
    }
    return TemplateRenderer.RenderPartialResponse("Mail/MailMessageViewPartial.html", Context, Headers = Headers)

@Router.get("/Placeholder/Partial", response_class = Responses.HTMLResponse)
async def GetMailPlaceholderPartial() -> Responses.HTMLResponse:
    return TemplateRenderer.RenderPartialResponse("Mail/MailPlaceholderPartial.html")

@Router.get("/Compose/Partial", response_class = Responses.HTMLResponse)
async def GetMailComposePartial(RecipientUserID: str = "", Subject: str = "", Category: str = "GeneralMessage", RelatedEntityType: str = "", RelatedEntityID: str = "", BodyTemplate: str = "", CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if CurrentUser.Role == User.UserRole.Visitor:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Guests are not allowed to access Mail Compose")

    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    UsersQuery = SQLAlchemy.select(User.User).where(User.User.ID != CurrentUser.ID, User.User.Role != User.UserRole.Visitor, ~User.User.Username.ilike("test%")).order_by(User.User.DisplayName.asc())
    UsersResult = await DatabaseSession.execute(UsersQuery)
    AvailableUsers: list[User.User] = list(UsersResult.scalars().all())

    Categories: list[dict[str, str]] = [{"Value": Cat.value, "Label": MailService.CATEGORY_DISPLAY_MAPPING.get(Cat, Cat.value)} for Cat in Mail.MailCategory if Cat != Mail.MailCategory.SystemAlert]

    Context: dict[str, Typing.Any] = {
        "AvailableUsers"   : AvailableUsers,
        "RecipientUserID"  : RecipientUserID,
        "Subject"          : Subject,
        "Category"         : Category,
        "Categories"       : Categories,
        "RelatedEntityType": RelatedEntityType,
        "RelatedEntityID"  : RelatedEntityID,
        "BodyTemplate"     : BodyTemplate
    }
    return TemplateRenderer.RenderPartialResponse("Mail/MailComposePartial.html", Context)

@Router.post("/Send", response_class = Responses.HTMLResponse)
async def TransmitMailDispatch(Request: FastAPI.Request, Subject: Typing.Annotated[str, FastAPI.Form()], Body: Typing.Annotated[str, FastAPI.Form()], RecipientUsernames: Typing.Annotated[str, FastAPI.Form()] = "", RecipientUserID: Typing.Annotated[str, FastAPI.Form()] = "", Category: Typing.Annotated[str, FastAPI.Form()] = "GeneralMessage", RelatedEntityType: Typing.Annotated[str, FastAPI.Form()] = "", RelatedEntityID: Typing.Annotated[str, FastAPI.Form()] = "", CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if CurrentUser.Role == User.UserRole.Visitor:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Guests are not allowed to send Mail")

    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    ResolvedRecipientIDs: list[str] = []
    if RecipientUserID and RecipientUserID.strip():
        ResolvedRecipientIDs.append(RecipientUserID.strip())

    if RecipientUsernames and RecipientUsernames.strip():
        RawUsernames: list[str] = [Token.strip().lstrip("@").strip() for Token in RecipientUsernames.replace(",", " ").split() if Token.strip()]
        if RawUsernames:
            UserQuery = SQLAlchemy.select(User.User).where(User.User.Username.in_(RawUsernames), User.User.Role != User.UserRole.Visitor)
            UserResult = await DatabaseSession.execute(UserQuery)
            FoundUsers: list[User.User] = list(UserResult.scalars().all())
            for FoundUser in FoundUsers:
                if FoundUser.ID not in ResolvedRecipientIDs:
                    ResolvedRecipientIDs.append(FoundUser.ID)

    if not ResolvedRecipientIDs:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = "At least one valid recipient must be specified")

    ResolvedCategory: Mail.MailCategory = Mail.MailCategory.GeneralMessage
    try:
        ResolvedCategory = Mail.MailCategory(Category)
    except ValueError:
        ResolvedCategory = Mail.MailCategory.GeneralMessage

    CreatedMessages: list[Mail.MailMessage] = await MailService.DispatchMultiUserMail(DatabaseSession = DatabaseSession, SenderUserID = CurrentUser.ID, RecipientUserIDs = ResolvedRecipientIDs, Subject = Subject, Body = Body, Category = ResolvedCategory, RelatedEntityType = RelatedEntityType if bool(RelatedEntityType) else None, RelatedEntityID = RelatedEntityID if bool(RelatedEntityID) else None)
    PrimaryMessage: Mail.MailMessage = CreatedMessages[0]

    TargetContainer: str = Request.headers.get("HX-Target", "")
    if TargetContainer != "MailMessageContainer":
        SuccessContext: dict[str, Typing.Any] = {
            "SentCount": len(CreatedMessages),
            "Subject"  : Subject
        }
        Headers: dict[str, str] = {
            "HX-Trigger": "RefreshMailList"
        }
        return TemplateRenderer.RenderPartialResponse("Mail/MailComposeSuccessPartial.html", SuccessContext, Headers = Headers)

    RenderedBodyHtml    : str                   = MailService.RenderMarkdown(PrimaryMessage.Body)
    CategoryDisplayLabel: str                   = MailService.GetCategoryDisplayLabel(PrimaryMessage.Category)
    ActivityState       : dict[str, Typing.Any] = MailService.ResolveUserActivityState(SenderUser = CurrentUser, IsAutomated = False)
    InUniverseYear      : int                   = PrimaryMessage.CreatedAt.year - 36
    CreatedAtFormatted  : str                   = f"{PrimaryMessage.CreatedAt.strftime('%d/%m')}/{InUniverseYear} {PrimaryMessage.CreatedAt.strftime('%I:%M %p')}"

    Context: dict[str, Typing.Any] = {
        "Message"             : PrimaryMessage,
        "RenderedBodyHtml"    : RenderedBodyHtml,
        "CategoryDisplayLabel": CategoryDisplayLabel,
        "ActivityState"       : ActivityState,
        "CreatedAtFormatted"  : CreatedAtFormatted,
        "CurrentUserID"       : CurrentUser.ID,
        "NoticeMessage"       : f"Message successfully sent to {len(CreatedMessages)} recipient(s)."
    }
    Headers: dict[str, str] = {
        "HX-Trigger": "RefreshMailList"
    }
    return TemplateRenderer.RenderPartialResponse("Mail/MailMessageViewPartial.html", Context, Headers = Headers)

@Router.post("/Message/{MessageID}/Reply/Partial", response_class = Responses.HTMLResponse)
async def TransmitMailReply(MessageID: str, ReplyBody: Typing.Annotated[str, FastAPI.Form()], CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if CurrentUser.Role == User.UserRole.Visitor:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Guests are not allowed to reply to Mail")

    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    ParentMessage: Mail.MailMessage | None = await MailService.GetMessageByID(DatabaseSession = DatabaseSession, MessageID = MessageID, UserID = CurrentUser.ID)
    if ParentMessage is None:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_404_NOT_FOUND, detail = "Original message not found")

    if (ParentMessage.IsAutomated) or (ParentMessage.SenderUserID is None):
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_400_BAD_REQUEST, detail = "Direct replies to automated messages are prohibited")

    ReplySubject: str = ParentMessage.Subject if ParentMessage.Subject.startswith("Re: ") else f"Re: {ParentMessage.Subject}"
    ReplyMessage: Mail.MailMessage = await MailService.DispatchUserMail(DatabaseSession = DatabaseSession, SenderUserID = CurrentUser.ID, RecipientUserID = ParentMessage.SenderUserID, Subject = ReplySubject, Body = ReplyBody, Category = ParentMessage.Category, RelatedEntityType = ParentMessage.RelatedEntityType, RelatedEntityID = ParentMessage.RelatedEntityID, ParentMessageID = ParentMessage.ID)

    RenderedBodyHtml    : str                   = MailService.RenderMarkdown(ReplyMessage.Body)
    CategoryDisplayLabel: str                   = MailService.GetCategoryDisplayLabel(ParentMessage.Category)
    ActivityState       : dict[str, Typing.Any] = MailService.ResolveUserActivityState(SenderUser = ParentMessage.Sender, IsAutomated = ParentMessage.IsAutomated)
    InUniverseYear      : int                   = ParentMessage.CreatedAt.year - 36
    CreatedAtFormatted  : str                   = f"{ParentMessage.CreatedAt.strftime('%d/%m')}/{InUniverseYear} {ParentMessage.CreatedAt.strftime('%I:%M %p')}"

    Context: dict[str, Typing.Any] = {
        "Message"             : ParentMessage,
        "RenderedBodyHtml"    : RenderedBodyHtml,
        "CategoryDisplayLabel": CategoryDisplayLabel,
        "ActivityState"       : ActivityState,
        "CreatedAtFormatted"  : CreatedAtFormatted,
        "CurrentUserID"       : CurrentUser.ID,
        "NoticeMessage"       : "Reply successfully sent."
    }
    Headers: dict[str, str] = {
        "HX-Trigger": "RefreshMailList"
    }
    return TemplateRenderer.RenderPartialResponse("Mail/MailMessageViewPartial.html", Context, Headers = Headers)

@Router.post("/Message/{MessageID}/MarkRead", response_class = Responses.Response)
async def MarkMailRead(MessageID: str, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.Response:
    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    await MailService.MarkMessageAsRead(DatabaseSession = DatabaseSession, MessageID = MessageID, RecipientUserID = CurrentUser.ID)
    Headers: dict[str, str] = {
        "HX-Trigger": "UpdateMailStatus"
    }
    return Responses.Response(status_code = 200, headers = Headers)

@Router.post("/Message/{MessageID}/Delete", response_class = Responses.HTMLResponse)
async def DeleteMailMessageEndpoint(MessageID: str, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    if CurrentUser.Role == User.UserRole.Visitor:
        raise FastAPI.HTTPException(status_code = FastAPI.status.HTTP_403_FORBIDDEN, detail = "Guests are not allowed to delete Mail")

    await MailService.UpdateUserSiteActivity(DatabaseSession = DatabaseSession, UserID = CurrentUser.ID)
    await MailService.DeleteMailMessage(DatabaseSession = DatabaseSession, MessageID = MessageID, UserID = CurrentUser.ID)
    Headers: dict[str, str] = {
        "HX-Trigger": "RefreshMailList, UpdateMailStatus"
    }
    return TemplateRenderer.RenderPartialResponse("Mail/MailPlaceholderPartial.html", {}, Headers = Headers)
