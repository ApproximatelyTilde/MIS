import typing                                    as Typing
import fastapi                                   as FastAPI
import fastapi.responses                         as Responses
import pydantic                                  as Pydantic
import sqlalchemy.ext.asyncio                    as AsyncIO
import Server.Auth.RoleBasedAccessControl        as RoleBasedAccessControl
import Server.Database                           as Database
import Server.Models.Character                   as Character
import Server.Models.User                        as User
import Server.Services.CharacterGeneratorService as CharacterGenerator
import Server.Services.DebugService              as DebugService
import Server.Services.DiceRollerService         as DiceRoller
import Server.Services.TemplateRendererService  as TemplateRenderer

Router = FastAPI.APIRouter(prefix = "/API/Tools", tags = ["Tools"])

class DiceRollRequest(Pydantic.BaseModel):
    GameSystem      : Character.GameSystemType = Character.GameSystemType.DND5thEdition
    Expression      : str = "1d20"
    Advantage       : bool = False
    Disadvantage    : bool = False
    Modifier        : int = 0
    HasBoon         : bool = False
    HasBane         : bool = False
    TargetDifficulty: int = 8
    Difficulty      : Typing.Optional[int] = None

@Router.post("/Dice/Roll")
async def RollDice(GameSystem: Character.GameSystemType = FastAPI.Form(Character.GameSystemType.DND5thEdition), Expression: str = FastAPI.Form("1d20"), Advantage: bool = FastAPI.Form(False), Disadvantage: bool = FastAPI.Form(False), HasBoon: bool = FastAPI.Form(False), HasBane: bool = FastAPI.Form(False), TargetDifficulty: int = FastAPI.Form(8), Modifier: int = FastAPI.Form(0), Difficulty: Typing.Optional[int] = FastAPI.Form(None), Format: str = "html") -> Responses.Response:
    DebugService.LogDebugMessage(f"Rolling Dice For Game System: {GameSystem.value}, Expression: {Expression}, Format: {Format}")
    if GameSystem == Character.GameSystemType.Traveller2ndEdition:
        RollResult = DiceRoller.GLOBAL_DICE_ROLLER.RollTraveller2ndEdition(Modifier = Modifier, HasBoon = HasBoon, HasBane = HasBane, TargetDifficulty = TargetDifficulty)

    else:
        RollResult = DiceRoller.GLOBAL_DICE_ROLLER.RollDND5thEdition(Expression = Expression, Advantage = Advantage, Disadvantage = Disadvantage, Difficulty = Difficulty)

    DebugService.LogDebugMessage(f"Dice Roll Computed Successfully With Total: {RollResult.Total}")
    EffectFormatted: Typing.Optional[str] = f"{RollResult.Effect:+d}" if (RollResult.Effect is not None) else None
    Context: Typing.Dict[str, Typing.Any] = {
        "GameSystem"     : RollResult.GameSystem.value,
        "Expression"     : RollResult.Expression,
        "RollsString"    : ", ".join(str(R) for R in RollResult.IndividualRolls),
        "Total"          : RollResult.Total,
        "Effect"         : RollResult.Effect,
        "EffectFormatted": EffectFormatted,
        "Description"    : RollResult.Description
    }
    return TemplateRenderer.RenderPartialResponse("Tools/DiceRollLogEntryPartial.html", Context)

@Router.post("/CharacterGenerator/Quick/Partial", response_class = Responses.HTMLResponse)
async def QuickGenerateCharacterPartial(GameSystem: Character.GameSystemType = FastAPI.Form(Character.GameSystemType.DND5thEdition), Name: str = FastAPI.Form("New Adventurer"), ClassOrCareer: Typing.Optional[str] = FastAPI.Form(None), CurrentUser: Typing.Optional[User.User] = FastAPI.Depends(RoleBasedAccessControl.GetCurrentUser), DatabaseSession: AsyncIO.AsyncSession = FastAPI.Depends(Database.GetDatabaseSession)) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Quick Generating Character For Game System: {GameSystem.value}, Name: {Name}, Class Or Career: {ClassOrCareer}, User: {getattr(CurrentUser, 'Identifier', None)}")
    if not CurrentUser or not RoleBasedAccessControl.CanCreateCharacter(CurrentUser):
        DebugService.LogDebugMessage(f"Permission Denied For Quick Character Generation: User {getattr(CurrentUser, 'Identifier', None)}")
        return TemplateRenderer.RenderPartialResponse("Tools/CharacterGeneratorResultPartial.html", {"IsPermissionDenied": True})

    if GameSystem == Character.GameSystemType.Traveller2ndEdition:
        CharacterData = CharacterGenerator.GLOBAL_CHARGEN_SERVICE.GenerateTraveller2ndEditionQuickCharacter(Name = Name, PreferredCareer = ClassOrCareer)

    else:
        CharacterData = CharacterGenerator.GLOBAL_CHARGEN_SERVICE.GenerateDND5thEditionQuickCharacter(Name = Name, PreferredClass = ClassOrCareer)

    NewCharacter = Character.Character(OwnerIdentifier = CurrentUser.Identifier, Name = CharacterData["Name"], GameSystem = Character.GameSystemType(CharacterData["GameSystem"]), IsPublic = True, SummaryData = CharacterData["SummaryData"], DetailData = CharacterData["DetailData"])
    DatabaseSession.add(NewCharacter)
    await DatabaseSession.commit()
    await DatabaseSession.refresh(NewCharacter)
    DebugService.LogDebugMessage(f"Quick Generated Character Successfully With Identifier: {NewCharacter.Identifier}")
    Context: Typing.Dict[str, Typing.Any] = {
        "IsPermissionDenied": False,
        "CharacterName"     : NewCharacter.Name,
        "GameSystem"        : NewCharacter.GameSystem.value
    }
    return TemplateRenderer.RenderPartialResponse("Tools/CharacterGeneratorResultPartial.html", Context)

@Router.get("/Calendar/Harptos/Partial", response_class = Responses.HTMLResponse)
async def GetHarptosCalendarPartial() -> Responses.HTMLResponse:
    DebugService.LogDebugMessage("Retrieving Harptos Calendar Partial Content")
    HarptosMonths: Typing.List[Typing.Dict[str, Typing.Any]] = [
        {"Number": 1, "Name": "Hammer", "ParenthesesName": "(Deepwinter)", "Days": 30, "Special": "Midwinter Holiday follows Day 30"},
        {"Number": 2, "Name": "Alturiak", "ParenthesesName": "(The Claw of Winter)", "Days": 30, "Special": ""},
        {"Number": 3, "Name": "Ches", "ParenthesesName": "(The Claw of Sunsets)", "Days": 30, "Special": ""},
        {"Number": 4, "Name": "Tarsakh", "ParenthesesName": "(The Claw of the Storms)", "Days": 30, "Special": "Greengrass Holiday follows Day 30"},
        {"Number": 5, "Name": "Mirtul", "ParenthesesName": "(The Melting)", "Days": 30, "Special": ""},
        {"Number": 6, "Name": "Kythorn", "ParenthesesName": "(The Time of Flowers)", "Days": 30, "Special": ""},
        {"Number": 7, "Name": "Flamerule", "ParenthesesName": "(Summertide)", "Days": 30, "Special": "Midsummer Holiday follows Day 30 (Shieldmeet on Leap Years)"},
        {"Number": 8, "Name": "Eleasis", "ParenthesesName": "(Highsun)", "Days": 30, "Special": ""},
        {"Number": 9, "Name": "Eleint", "ParenthesesName": "(The Fading)", "Days": 30, "Special": "Highharvestide Holiday follows Day 30"},
        {"Number": 10, "Name": "Marpenoth", "ParenthesesName": "(Leafall)", "Days": 30, "Special": ""},
        {"Number": 11, "Name": "Uktar", "ParenthesesName": "(The Rotting)", "Days": 30, "Special": "The Feast of the Moon follows Day 30"},
        {"Number": 12, "Name": "Nightal", "ParenthesesName": "(The Drawing Down)", "Days": 30, "Special": ""}
    ]
    return TemplateRenderer.RenderPartialResponse("Tools/HarptosCalendarPartial.html", {"Months": HarptosMonths})

