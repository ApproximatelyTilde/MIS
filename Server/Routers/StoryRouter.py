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
import Server.Services.TemplateRendererService as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Stories", tags = ["Stories"])

class StoryCreateRequest(Pydantic.BaseModel):
    Title      : str
    Description: str = ""
    GameSystem : Character.GameSystemType
    IsPublic   : bool = True

@Router.get("/Partial", response_class = Responses.HTMLResponse)
async def ListStoriesPartial(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
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

    return TemplateRenderer.RenderPartialResponse("Stories/StoryListPartial.html", {"Stories": StoryEntries})

@Router.post("/{StoryIdentifier}/JoinRequest/Partial", response_class = Responses.HTMLResponse)
async def RequestToJoinStoryPartial(StoryIdentifier: str, CurrentUser: User.User = FastAPI.Depends(RoleBasedAccessControl.RequireAuthenticatedUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    ExistingMemberQuery = SQLAlchemy.select(Story.StoryMember).where(Story.StoryMember.StoryIdentifier == StoryIdentifier, Story.StoryMember.UserIdentifier == CurrentUser.Identifier)
    ExistingResult = await DatabaseSession.execute(ExistingMemberQuery)
    ExistingMember = ExistingResult.scalars().first()
    if not ExistingMember:
        NewMember = Story.StoryMember(StoryIdentifier = StoryIdentifier, UserIdentifier = CurrentUser.Identifier, MembershipStatus = Story.StoryMembershipStatus.Requested)
        DatabaseSession.add(NewMember)
        await DatabaseSession.commit()

    return await ListStoriesPartial(CurrentUser, DatabaseSession)

@Router.get("")
async def ListStories(CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Typing.List[Typing.Dict[str, Typing.Any]]:
    QueryStatement = SQLAlchemy.select(Story.Story)
    QueryResult = await DatabaseSession.execute(QueryStatement)
    Stories = QueryResult.scalars().all()
    VisibleStories: Typing.List[Typing.Dict[str, Typing.Any]] = []
    for SingleStory in Stories:
        if RoleBasedAccessControl.CanViewStory(CurrentUser, SingleStory, False):
            VisibleStories.append({"Identifier": SingleStory.Identifier, "Title": SingleStory.Title, "GameSystem": SingleStory.GameSystem.value, "IsPublic": SingleStory.IsPublic})

    return VisibleStories
