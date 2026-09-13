import typing                                  as Typing
import fastapi                                 as FastAPI
import fastapi.responses                       as Responses
import pydantic                                as Pydantic
import sqlalchemy                              as SQLAlchemy
import sqlalchemy.ext.asyncio                  as AsyncIO
import Server.Auth.RoleBasedAccessControl      as RoleBasedAccessControl
import Server.Database                         as Database
import Server.Models.Character                 as Character
import Server.Models.Story                     as Story
import Server.Models.User                      as User
import Server.Services.DebugService             as DebugService
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Stories", tags = ["Stories"])

class StoryCreateRequest(Pydantic.BaseModel):
    Title      : str
    Description: str = ""
    GameSystem : Character.GameSystemType
    IsPublic   : bool = True

@Router.get("/Partial", response_class = Responses.HTMLResponse)
async def ListStoriesPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Listing Stories Partial For User: {getattr(CurrentUser, 'Identifier', None)}")
    QueryStatement = SQLAlchemy.select(Story.Story)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Stories = QueryResult.scalars().all()
    UserMembershipStoryIDs: Typing.Set[str] = set()
    if CurrentUser:
        MembershipQuery = SQLAlchemy.select(Story.StoryMember.StoryIdentifier).where(Story.StoryMember.UserIdentifier == CurrentUser.Identifier, Story.StoryMember.MembershipStatus.in_([Story.StoryMembershipStatus.Active, Story.StoryMembershipStatus.Invited]))
        MembershipResult = await DatabaseSession.execute(MembershipQuery)
        UserMembershipStoryIDs = set(MembershipResult.scalars().all())

    StoryEntries: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for SingleStory in Stories:
        IsMember: bool = SingleStory.Identifier in UserMembershipStoryIDs
        if RoleBasedAccessControl.CanViewStory(CurrentUser, SingleStory, IsMember):
            StoryEntries.append({
                "Story"         : SingleStory,
                "IsMember"      : IsMember,
                "CanRequestJoin": SingleStory.IsPublic and (not IsMember) and (CurrentUser is not None)
            })

    DebugService.LogDebugMessage(f"Rendered {len(StoryEntries)} Visible Stories In Partial")
    return TemplateRenderer.RenderPartialResponse("Stories/StoryListPartial.html", {"Stories": StoryEntries})

@Router.post("/{StoryIdentifier}/JoinRequest/Partial", response_class = Responses.HTMLResponse)
async def RequestToJoinStoryPartial(StoryIdentifier: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Processing Story Join Request For Story: {StoryIdentifier}, User: {CurrentUser.Identifier}")
    ExistingMemberQuery = SQLAlchemy.select(Story.StoryMember).where(Story.StoryMember.StoryIdentifier == StoryIdentifier, Story.StoryMember.UserIdentifier == CurrentUser.Identifier)
    ExistingResult = await DatabaseSession.execute(ExistingMemberQuery)
    ExistingMember = ExistingResult.scalars().first()
    if not ExistingMember:
        NewMember = Story.StoryMember(StoryIdentifier = StoryIdentifier, UserIdentifier = CurrentUser.Identifier, MembershipStatus = Story.StoryMembershipStatus.Requested)
        DatabaseSession.add(NewMember)
        await DatabaseSession.commit()
        DebugService.LogDebugMessage(f"Created New Story Join Request Membership For Story: {StoryIdentifier}")
    else:
        DebugService.LogDebugMessage(f"Existing Membership Already Present For Story: {StoryIdentifier}")

    return await ListStoriesPartial(CurrentUser, DatabaseSession)

@Router.get("")
async def ListStories(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.List[Typing.Dict[str, Typing.Any]]:
    DebugService.LogDebugMessage(f"Listing JSON Stories For User: {getattr(CurrentUser, 'Identifier', None)}")
    QueryStatement = SQLAlchemy.select(Story.Story)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Stories = QueryResult.scalars().all()
    VisibleStories: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for SingleStory in Stories:
        if RoleBasedAccessControl.CanViewStory(CurrentUser, SingleStory, False):
            VisibleStories.append({"Identifier": SingleStory.Identifier, "Title": SingleStory.Title, "GameSystem": SingleStory.GameSystem.value, "IsPublic": SingleStory.IsPublic})

    DebugService.LogDebugMessage(f"Returning {len(VisibleStories)} Visible Stories In JSON Response")
    return VisibleStories
