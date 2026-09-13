import datetime                     as DateTime
import markdown                     as MarkdownLibrary
import markdown.blockprocessors     as MarkdownBlockProcessors
import markdown.inlinepatterns      as MarkdownInlinePatterns
import markdown.preprocessors       as MarkdownPreprocessors
import typing                       as Typing
import xml.etree.ElementTree        as ElementTree
import sqlalchemy                   as SQLAlchemy
import sqlalchemy.ext.asyncio       as AsyncIO
import sqlalchemy.orm               as ORM
import Server.Database              as Database
import Server.Models.Character      as Character
import Server.Models.Mail           as Mail
import Server.Models.Story          as Story
import Server.Models.User           as User
import Server.Services.DebugService as DebugService

SYSTEM_SENDER_NAME              : str = "Marten"
SYSTEM_NOTIFICATION_PORTRAIT_URL: str = "/Resources/PNG/SystemNotification.png"

CATEGORY_DISPLAY_MAPPING: dict[Mail.MailCategory, str] = {
    Mail.MailCategory.SystemAlert    : "System Alert",
    Mail.MailCategory.CharacterReview: "Character Review",
    Mail.MailCategory.StoryNotice    : "Story Notice",
    Mail.MailCategory.Administrative : "Administrative",
    Mail.MailCategory.GeneralMessage : "General"
}

class SubtitlePreprocessor(MarkdownPreprocessors.Preprocessor):
    def run(self, Lines: list[str]) -> list[str]:
        ProcessedLines: list[str] = []
        for Line in Lines:
            StrippedLine: str = Line.strip()
            if StrippedLine.startswith("-# ") or (StrippedLine == "-#"):
                ProcessedLines.append("")
                ProcessedLines.append(StrippedLine)
                ProcessedLines.append("")
            else:
                ProcessedLines.append(Line)

        return ProcessedLines

class SubtitleBlockProcessor(MarkdownBlockProcessors.BlockProcessor):
    def test(self, Parent: ElementTree.Element, Block: str) -> bool:
        return Block.startswith("-# ") or (Block == "-#")

    def run(self, Parent: ElementTree.Element, Blocks: list[str]) -> None:
        Block = Blocks.pop(0)
        Lines = [Line[3:] if Line.startswith("-# ") else Line[2:].strip() for Line in Block.split("\n")]
        ParagraphElement = ElementTree.SubElement(Parent, "p")
        ParagraphElement.set("class", "MailSubtitle")
        ParagraphElement.text = "\n".join(Lines)

class MISMarkdownExtension(MarkdownLibrary.Extension):
    def extendMarkdown(self, MarkdownInstance: MarkdownLibrary.Markdown) -> None:
        MarkdownInstance.preprocessors.register(SubtitlePreprocessor(MarkdownInstance), "mis_subtitle_pre", 175)
        MarkdownInstance.parser.blockprocessors.register(SubtitleBlockProcessor(MarkdownInstance.parser), "mis_subtitle_block", 175)
        MarkdownInstance.inlinePatterns.register(MarkdownInlinePatterns.SimpleTagInlineProcessor(r"(__)([\s\S]+?)(__)", "u"), "mis_underline", 70)

def GetCategoryDisplayLabel(Category: Mail.MailCategory | str) -> str:
    if isinstance(Category, str):
        try:
            Category = Mail.MailCategory(Category)
        except ValueError:
            return Category

    return CATEGORY_DISPLAY_MAPPING.get(Category, Category.value if hasattr(Category, "value") else str(Category))

def RenderMarkdown(ContentText: str) -> str:
    if not ContentText:
        return ""

    Extensions = [
        MISMarkdownExtension(),
        "extra",
        "nl2br",
        "sane_lists",
        "admonition",
        "pymdownx.details",
        "pymdownx.superfences",
        "pymdownx.highlight",
        "pymdownx.inlinehilite",
        "pymdownx.magiclink",
        "pymdownx.tasklist",
        "pymdownx.tilde"
    ]
    ExtensionConfigs = {
        "pymdownx.highlight": {
            "use_pygments": False
        }
    }
    RenderedHTML: str = MarkdownLibrary.markdown(ContentText, extensions = Extensions, extension_configs = ExtensionConfigs)
    return RenderedHTML

async def GetEligibleRecipients(DatabaseSession: AsyncIO.AsyncSession, CurrentUserID: str) -> list[dict[str, str]]:
    QueryStatement = SQLAlchemy.select(User.User).where(User.User.ID != CurrentUserID, User.User.Role != User.UserRole.Visitor, User.User.DiscordID.isnot(None), ~User.User.Username.ilike("test%")).order_by(User.User.DisplayName.asc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    FoundUsers: list[User.User] = list(QueryResult.scalars().all())
    RecipientList: list[dict[str, str]] = []
    for UserRecord in FoundUsers:
        RecipientList.append({
            "ID"          : UserRecord.ID,
            "Username"    : UserRecord.Username,
            "DisplayName" : UserRecord.DisplayName,
            "FormattedTag": f"@{UserRecord.Username}"
        })

    return RecipientList

async def UpdateUserSiteActivity(DatabaseSession: AsyncIO.AsyncSession, UserID: str) -> None:
    CurrentTime: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    UpdateStatement = SQLAlchemy.update(User.User).where(User.User.ID == UserID).values(LastActiveAt = CurrentTime)
    await DatabaseSession.execute(UpdateStatement)
    await DatabaseSession.commit()

async def DispatchAutomatedMail(DatabaseSession: AsyncIO.AsyncSession, RecipientUserID: str, Subject: str, Body: str, Category: Mail.MailCategory = Mail.MailCategory.SystemAlert, RelatedEntityType: str | None = None, RelatedEntityID: str | None = None) -> Mail.MailMessage:
    CurrentTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    NewMessage: Mail.MailMessage = Mail.MailMessage(SenderUserID = None, RecipientUserID = RecipientUserID, Subject = Subject, Body = Body, Category = Category, RelatedEntityType = RelatedEntityType, RelatedEntityID = RelatedEntityID, IsAutomated = True, IsRead = False, CreatedAt = CurrentTimestamp, UpdatedAt = CurrentTimestamp)
    DatabaseSession.add(NewMessage)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewMessage)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Automated Mail Dispatched to UserID=\"{RecipientUserID[:8]}…\": Subject=\"{Subject}\"")
    return NewMessage

async def DispatchUserMail(DatabaseSession: AsyncIO.AsyncSession, SenderUserID: str, RecipientUserID: str, Subject: str, Body: str, Category: Mail.MailCategory = Mail.MailCategory.GeneralMessage, RelatedEntityType: str | None = None, RelatedEntityID: str | None = None, ParentMessageID: str | None = None) -> Mail.MailMessage:
    CurrentTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    NewMessage: Mail.MailMessage = Mail.MailMessage(SenderUserID = SenderUserID, RecipientUserID = RecipientUserID, Subject = Subject, Body = Body, Category = Category, RelatedEntityType = RelatedEntityType, RelatedEntityID = RelatedEntityID, IsAutomated = False, IsRead = False, ParentMessageID = ParentMessageID, CreatedAt = CurrentTimestamp, UpdatedAt = CurrentTimestamp)
    DatabaseSession.add(NewMessage)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewMessage)
    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"User Mail Dispatched: Sender=\"{SenderUserID[:8]}…\", Recipient=\"{RecipientUserID[:8]}…\"")
    return NewMessage

async def DispatchMultiUserMail(DatabaseSession: AsyncIO.AsyncSession, SenderUserID: str, RecipientUserIDs: list[str], Subject: str, Body: str, Category: Mail.MailCategory = Mail.MailCategory.GeneralMessage, RelatedEntityType: str | None = None, RelatedEntityID: str | None = None, ParentMessageID: str | None = None) -> list[Mail.MailMessage]:
    CurrentTimestamp: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    CreatedMessages: list[Mail.MailMessage] = []
    for TargetRecipientID in RecipientUserIDs:
        NewMessage: Mail.MailMessage = Mail.MailMessage(SenderUserID = SenderUserID, RecipientUserID = TargetRecipientID, Subject = Subject, Body = Body, Category = Category, RelatedEntityType = RelatedEntityType, RelatedEntityID = RelatedEntityID, IsAutomated = False, IsRead = False, ParentMessageID = ParentMessageID, CreatedAt = CurrentTimestamp, UpdatedAt = CurrentTimestamp)
        DatabaseSession.add(NewMessage)
        CreatedMessages.append(NewMessage)

    await DatabaseSession.commit()
    for MessageItem in CreatedMessages:
        await DatabaseSession.refresh(MessageItem)

    DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Multi-User Mail Dispatched: Sender=\"{SenderUserID[:8]}…\", RecipientsCount={len(CreatedMessages)}")
    return CreatedMessages

async def GetInboxMessages(DatabaseSession: AsyncIO.AsyncSession, RecipientUserID: str, FilterUnreadOnly: bool = False) -> list[Mail.MailMessage]:
    QueryStatement = SQLAlchemy.select(Mail.MailMessage).options(ORM.selectinload(Mail.MailMessage.Sender)).where(Mail.MailMessage.RecipientUserID == RecipientUserID)
    if FilterUnreadOnly:
        QueryStatement = QueryStatement.where(Mail.MailMessage.IsRead == False)

    QueryStatement = QueryStatement.order_by(Mail.MailMessage.CreatedAt.desc())
    QueryResult = await DatabaseSession.execute(QueryStatement)
    MessageList: list[Mail.MailMessage] = list(QueryResult.scalars().all())
    return MessageList

async def GetMessageByID(DatabaseSession: AsyncIO.AsyncSession, MessageID: str, UserID: str) -> Mail.MailMessage | None:
    QueryStatement = SQLAlchemy.select(Mail.MailMessage).options(ORM.selectinload(Mail.MailMessage.Sender)).where(Mail.MailMessage.ID == MessageID, SQLAlchemy.or_(Mail.MailMessage.RecipientUserID == UserID, Mail.MailMessage.SenderUserID == UserID))
    QueryResult = await DatabaseSession.execute(QueryStatement)
    TargetMessage: Mail.MailMessage | None = QueryResult.scalars().first()
    return TargetMessage

async def MarkMessageAsRead(DatabaseSession: AsyncIO.AsyncSession, MessageID: str, RecipientUserID: str) -> bool:
    UpdateStatement = SQLAlchemy.update(Mail.MailMessage).where(Mail.MailMessage.ID == MessageID, Mail.MailMessage.RecipientUserID == RecipientUserID).values(IsRead = True, UpdatedAt = DateTime.datetime.now(DateTime.UTC))
    Result = await DatabaseSession.execute(UpdateStatement)
    await DatabaseSession.commit()
    return bool(Result.rowcount > 0)

async def DeleteMailMessage(DatabaseSession: AsyncIO.AsyncSession, MessageID: str, UserID: str) -> bool:
    DeleteStatement = SQLAlchemy.delete(Mail.MailMessage).where(Mail.MailMessage.ID == MessageID, SQLAlchemy.or_(Mail.MailMessage.RecipientUserID == UserID, Mail.MailMessage.SenderUserID == UserID))
    DeleteResult    = await DatabaseSession.execute(DeleteStatement)
    await DatabaseSession.commit()
    return bool(DeleteResult.rowcount > 0)

async def GetUnreadMailCount(DatabaseSession: AsyncIO.AsyncSession, RecipientUserID: str) -> int:
    CountStatement = SQLAlchemy.select(SQLAlchemy.func.count(Mail.MailMessage.ID)).where(Mail.MailMessage.RecipientUserID == RecipientUserID, Mail.MailMessage.IsRead == False)
    QueryResult = await DatabaseSession.execute(CountStatement)
    UnreadCount: int = int(QueryResult.scalar_one() or 0)
    return UnreadCount

async def CheckOverdueCharacterReviews(DatabaseSession: AsyncIO.AsyncSession) -> int:
    TwoDaysAgo: DateTime.datetime = DateTime.datetime.now(DateTime.UTC) - DateTime.timedelta(days = 2)
    OverdueQuery = SQLAlchemy.select(Character.Character).where(Character.Character.IsAccepted == False, Character.Character.IsArchived == False, Character.Character.CreatedAt <= TwoDaysAgo)
    OverdueResult = await DatabaseSession.execute(OverdueQuery)
    OverdueCharacters: list[Character.Character] = list(OverdueResult.scalars().all())
    if not OverdueCharacters:
        return 0

    CheckersQuery = SQLAlchemy.select(User.User).where(SQLAlchemy.or_(User.User.Role == User.UserRole.Checker, User.User.Role == User.UserRole.Administrator))
    CheckersResult = await DatabaseSession.execute(CheckersQuery)
    Checkers: list[User.User] = list(CheckersResult.scalars().all())
    if not Checkers:
        return 0

    DispatchedCount: int = 0
    NowTime: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    OneDayAgo: DateTime.datetime = NowTime - DateTime.timedelta(days = 1)
    for OverdueCharacter in OverdueCharacters:
        RecentReminderQuery = SQLAlchemy.select(Mail.MailMessage).where(Mail.MailMessage.RelatedEntityType == "Character", Mail.MailMessage.RelatedEntityID == OverdueCharacter.ID, Mail.MailMessage.Category == Mail.MailCategory.CharacterReview, Mail.MailMessage.IsAutomated == True, Mail.MailMessage.CreatedAt >= OneDayAgo)
        RecentReminderResult = await DatabaseSession.execute(RecentReminderQuery)
        if RecentReminderResult.scalars().first() is not None:
            continue

        for CheckerUser in Checkers:
            await DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = CheckerUser.ID, Subject = f"Review Reminder: Character '{OverdueCharacter.Name}' Overdue", Body = f"Notice: Character '{OverdueCharacter.Name}' ({OverdueCharacter.GameSystem.value}) submitted by Owner ID '{OverdueCharacter.OwnerID[:8]}…' has been pending review for more than 48 hours.\n\nPlease inspect the character sheet in the review queue.", Category = Mail.MailCategory.CharacterReview, RelatedEntityType = "Character", RelatedEntityID = OverdueCharacter.ID)
            DispatchedCount += 1

    return DispatchedCount

async def DispatchStoryCalloutMail(DatabaseSession: AsyncIO.AsyncSession, GameMasterUser: User.User, StoryID: str, Subject: str, ScheduleBody: str) -> int:
    MembersQuery = SQLAlchemy.select(Story.StoryMember).where(Story.StoryMember.StoryID == StoryID, Story.StoryMember.MembershipStatus.in_([Story.StoryMembershipStatus.Requested, Story.StoryMembershipStatus.Active]))
    MembersResult = await DatabaseSession.execute(MembersQuery)
    Members: list[Story.StoryMember] = list(MembersResult.scalars().all())

    DispatchedCount: int = 0
    for MemberItem in Members:
        if MemberItem.UserID == GameMasterUser.ID:
            continue

        await DispatchUserMail(DatabaseSession = DatabaseSession, SenderUserID = GameMasterUser.ID, RecipientUserID = MemberItem.UserID, Subject = Subject, Body = ScheduleBody, Category = Mail.MailCategory.StoryNotice, RelatedEntityType = "Story", RelatedEntityID = StoryID)
        DispatchedCount += 1

    return DispatchedCount

def FormatTimeAgo(TargetTime: DateTime.datetime | None) -> str:
    if TargetTime is None:
        return "Unknown"

    NowTime: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    if TargetTime.tzinfo is None:
        TargetTime = TargetTime.replace(tzinfo = DateTime.UTC)

    DifferenceSeconds: int = max(0, int((NowTime - TargetTime).total_seconds()))
    if DifferenceSeconds < 60:
        return "Active just now"

    if DifferenceSeconds < 3600:
        MinutesCount: int = DifferenceSeconds // 60
        return f"Active {MinutesCount}m ago"

    if DifferenceSeconds < 86400:
        HoursCount: int = DifferenceSeconds // 3600
        return f"Active {HoursCount}h ago"

    DaysCount: int = DifferenceSeconds // 86400
    return f"Active {DaysCount}d ago"

def ResolveSenderPortraitURL(SenderUser: Typing.Any | None, IsAutomated: bool = False) -> str:
    if (IsAutomated) or (SenderUser is None):
        return SYSTEM_NOTIFICATION_PORTRAIT_URL

    if (hasattr(SenderUser, "PortraitURL")) and bool(getattr(SenderUser, "PortraitURL")):
        return str(getattr(SenderUser, "PortraitURL"))

    if (hasattr(SenderUser, "AvatarURL")) and bool(getattr(SenderUser, "AvatarURL")):
        return str(getattr(SenderUser, "AvatarURL"))

    AvatarHash: str | None = getattr(SenderUser, "AvatarHash", None)
    DiscordID: str | None  = getattr(SenderUser, "DiscordID", None)
    if (AvatarHash is not None) and (DiscordID is not None):
        return f"https://cdn.discordapp.com/avatars/{DiscordID}/{AvatarHash}.png?size=64"

    if (DiscordID is not None) and str(DiscordID).isdigit():
        DefaultIndex: int = (int(DiscordID) >> 22) % 6
        return f"https://cdn.discordapp.com/embed/avatars/{DefaultIndex}.png"

    return "/Resources/SVG/LoginManagerButton-LocalLogin.svg"

def ResolveUserActivityState(SenderUser: User.User | None, IsAutomated: bool = False) -> dict[str, Typing.Any]:
    if (IsAutomated) or (SenderUser is None):
        return {
            "DisplayName"         : SYSTEM_SENDER_NAME,
            "Username"            : None,
            "RoleLabel"           : "System Daemon",
            "PermissionLevel"     : "System Daemon",
            "Flair"               : None,
            "StateCode"           : "System",
            "StateLabel"          : "ALWAYS ACTIVE",
            "StateClass"          : "BadgeStatusSystem",
            "StatusIndicatorClass": None,
            "LastActiveText"      : "System Daemon",
            "PortraitURL"         : SYSTEM_NOTIFICATION_PORTRAIT_URL
        }

    NowTime: DateTime.datetime = DateTime.datetime.now(DateTime.UTC)
    LastActiveAt: DateTime.datetime | None = SenderUser.LastActiveAt
    DifferenceSeconds: int = 999999
    if LastActiveAt is not None:
        if LastActiveAt.tzinfo is None:
            LastActiveAt = LastActiveAt.replace(tzinfo = DateTime.UTC)

        DifferenceSeconds = max(0, int((NowTime - LastActiveAt).total_seconds()))

    StateCode: str = "Offline"
    StateLabel: str = "OFFLINE"
    StateClass: str = "BadgeStatusOffline"
    StatusIndicatorClass: str | None = None

    if DifferenceSeconds <= 300:
        StateCode            = "Online"
        StateLabel           = "ONLINE"
        StateClass           = "BadgeStatusOnline"
        StatusIndicatorClass = "StatusIndicatorOnline"
    elif DifferenceSeconds <= 1800:
        StateCode            = "Idle"
        StateLabel           = "IDLE"
        StateClass           = "BadgeStatusIdle"
        StatusIndicatorClass = "StatusIndicatorIdle"

    if hasattr(SenderUser, "DiscordStatus") and (SenderUser.DiscordStatus == "DoNotDisturb"):
        StateCode            = "DoNotDisturb"
        StateLabel           = "DO NOT DISTURB"
        StateClass           = "BadgeStatusDND"
        StatusIndicatorClass = "StatusIndicatorDoNotDisturb"

    Flair: str | None = None
    UserRoles = getattr(SenderUser, "Roles", None)
    if UserRoles:
        for RoleItem in UserRoles:
            if RoleItem != SenderUser.Role.value:
                Flair = RoleItem
                break

    LastActiveText: str = FormatTimeAgo(LastActiveAt)
    PortraitURL   : str = ResolveSenderPortraitURL(SenderUser = SenderUser, IsAutomated = False)

    return {
        "DisplayName"         : SenderUser.DisplayName,
        "Username"            : getattr(SenderUser, "Username", None),
        "RoleLabel"           : SenderUser.Role.value,
        "PermissionLevel"     : SenderUser.Role.value,
        "Flair"               : Flair,
        "StateCode"           : StateCode,
        "StateLabel"          : StateLabel,
        "StateClass"          : StateClass,
        "StatusIndicatorClass": StatusIndicatorClass,
        "LastActiveText"      : LastActiveText,
        "PortraitURL"         : PortraitURL
    }
