import typing                                  as Typing
import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import pydantic                                as Pydantic
import sqlalchemy                              as SQLAlchemy
import sqlalchemy.ext.asyncio                  as AsyncIO
import Server.Auth.RoleBasedAccessControl      as RoleBasedAccessControl
import Server.Database                         as Database
import Server.Models.Character                 as Character
import Server.Models.Mail                      as Mail
import Server.Models.Story                     as Story
import Server.Models.User                      as User
import Server.Services.DebugService            as DebugService
import Server.Services.MailService             as MailService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Stories", tags = ["Stories"])

class StoryCreateRequest(Pydantic.BaseModel):
    Title      : str
    Description: str = ""
    GameSystem : Character.GameSystemType
    IsPublic   : bool = True

@Router.get("/Partial", response_class = Responses.HTMLResponse)
async def ListStoriesPartial(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    QueryStatement = SQLAlchemy.select(Story.Story)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Stories = QueryResult.scalars().all()
    UserMembershipStoryIDs: set[str] = set()
    if CurrentUser:
        MembershipQuery = SQLAlchemy.select(Story.StoryMember.StoryID).where(Story.StoryMember.UserID == CurrentUser.ID, Story.StoryMember.MembershipStatus.in_([Story.StoryMembershipStatus.Active, Story.StoryMembershipStatus.Invited]))
        MembershipResult = await DatabaseSession.execute(MembershipQuery)
        UserMembershipStoryIDs = set(MembershipResult.scalars().all())

    StoryEntries: list[dict[str, Typing.Any]] = []
    for SingleStory in Stories:
        IsMember: bool = (SingleStory.ID in UserMembershipStoryIDs)
        if RoleBasedAccessControl.CanViewStory(CurrentUser, SingleStory, IsMember):
            GameSystemName: str = SingleStory.GameSystem.value if hasattr(SingleStory.GameSystem, "value") else str(SingleStory.GameSystem)
            StoryEntry: dict[str, Typing.Any] = {
                "Story"         : SingleStory,
                "GameSystemName": GameSystemName,
                "IsMember"      : IsMember,
                "CanRequestJoin": (SingleStory.IsPublic and (not IsMember) and (CurrentUser is not None))
            }
            StoryEntries.append(StoryEntry)

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rendered Stories Partial: {len(StoryEntries)} of {len(Stories)}")
    return TemplateRenderer.RenderPartialResponse("Stories/StoryListPartial.html", {"Stories": StoryEntries})

@Router.post("/{StoryID}/JoinRequest/Partial", response_class = Responses.HTMLResponse)
async def RequestToJoinStoryPartial(StoryID: str, CurrentUser: Typing.Annotated[User.User, FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> Responses.HTMLResponse:
    StoryQuery = SQLAlchemy.select(Story.Story).where(Story.Story.ID == StoryID)
    StoryResult = await DatabaseSession.execute(StoryQuery)
    TargetStory: Story.Story | None = StoryResult.scalars().first()
    if (TargetStory is None):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Story Join Rejected: Story \"{StoryID[:8]}…\" Not Found")
        return TemplateRenderer.RenderPartialResponse("Stories/StoryNotFoundPartial.html")

    if TargetStory.IsArchived or (not TargetStory.IsPublic) or (not RoleBasedAccessControl.CanViewStory(CurrentUser, TargetStory, False)):
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Story Join Access Denied: ID=\"{StoryID[:8]}…\"")
        return TemplateRenderer.RenderPartialResponse("Stories/StoryAccessDeniedPartial.html")

    ExistingMemberQuery = SQLAlchemy.select(Story.StoryMember).where(Story.StoryMember.StoryID == StoryID, Story.StoryMember.UserID == CurrentUser.ID)
    ExistingResult = await DatabaseSession.execute(ExistingMemberQuery)
    ExistingMember = ExistingResult.scalars().first()
    if not ExistingMember:
        NewMember = Story.StoryMember(StoryID = StoryID, UserID = CurrentUser.ID, MembershipStatus = Story.StoryMembershipStatus.Requested)
        DatabaseSession.add(NewMember)
        await DatabaseSession.commit()
        await MailService.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = TargetStory.GameMasterID, Subject = f"Story Application: '{TargetStory.Title}'", Body = f"Greetings Game Master.\n\nUser '{CurrentUser.DisplayName}' has requested to join your story '{TargetStory.Title}'.\n\nYou may use the Electronic Mail Dispatch system to coordinate with this applicant regarding campaign schedules and party requirements.", Category = Mail.MailCategory.StoryNotice, RelatedEntityType = "Story", RelatedEntityID = TargetStory.ID)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Requested to Join Story: StoryID=\"{StoryID[:8]}…\", UserID=\"{CurrentUser.ID[:8]}…\"")

    else:
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Story Join Skipped: Status=\"{ExistingMember.MembershipStatus.value}\"")

    return await ListStoriesPartial(CurrentUser, DatabaseSession)

@Router.get("")
async def ListStories(CurrentUser: Typing.Annotated[User.User | None, FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser)] = None, DatabaseSession: Typing.Annotated[AsyncIO.AsyncSession, FastAPI.Depends(Database.GetDatabaseSession)] = None) -> list[dict[str, Typing.Any]]:
    QueryStatement = SQLAlchemy.select(Story.Story)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Stories = QueryResult.scalars().all()
    VisibleStories: list[dict[str, Typing.Any]] = []
    for SingleStory in Stories:
        if RoleBasedAccessControl.CanViewStory(CurrentUser, SingleStory, False):
            VisibleStories.append({"ID": SingleStory.ID, "Title": SingleStory.Title, "GameSystem": SingleStory.GameSystem.value, "IsPublic": SingleStory.IsPublic})

    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Listed Stories: {len(VisibleStories)} Visible of {len(Stories)}")
    return VisibleStories
