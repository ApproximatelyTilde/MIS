import dataclasses                  as Dataclasses
import random                       as Random
import re                           as RegularExpressions
import typing                       as Typing
import Server.Models.Character      as Character
import Server.Services.DebugService as DebugService

@Dataclasses.dataclass(slots = True)
class DiceRollResult:
    Expression      : str
    IndividualRolls : list[int]
    Modifier        : int
    Total           : int
    Description     : str                          = ""
    GameSystem      : Character.GameSystemType      = Dataclasses.field(default = Character.GameSystemType.DND5thEdition)
    Effect          : int | None                    = None

    def ToDictionary(self) -> dict[str, Typing.Any]:
        return {
            "Expression"     : self.Expression,
            "IndividualRolls": self.IndividualRolls,
            "Modifier"       : self.Modifier,
            "Total"          : self.Total,
            "Description"    : self.Description,
            "GameSystem"     : self.GameSystem.value,
            "Effect"         : self.Effect
        }

class DiceRollerService:
    def __init__(self) -> None:
        self.DicePattern: RegularExpressions.Pattern[str] = RegularExpressions.compile(r"^(\d+)?d(\d+)([+-]\d+)?$", RegularExpressions.IGNORECASE)

    def RollStandardDice(self, DieCount: int, DieSides: int) -> list[int]:
        if (DieSides < 1) or (DieCount < 1) or (DieCount > 100):
            raise ValueError(f"Invalid die configuration: count={DieCount}, sides={DieSides}")

        Rolls: list[int] = [Random.randint(1, DieSides) for DieIndex in range(DieCount)]
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Rolled {DieCount}d{DieSides} Yielding {Rolls} Totaling {sum(Rolls)}")
        return Rolls

    def RollDND5thEdition(self, Expression: str, Advantage: bool = False, Disadvantage: bool = False, Difficulty: int | None = None) -> DiceRollResult:
        CleanExpression: str = Expression.strip().replace(" ", "")
        Effect: int | None = None
        if Advantage and not Disadvantage:
            FirstRoll: int = Random.randint(1, 20)
            SecondRoll: int = Random.randint(1, 20)
            ChosenRoll: int = max(FirstRoll, SecondRoll)
            Modifier: int = self.ExtractModifier(CleanExpression)
            Total: int = ChosenRoll + Modifier
            if Difficulty is not None:
                Effect = Total - Difficulty
                OutcomeText: str = "Success" if (Effect >= 0) else "Failure"
                DescriptionText: str = f"Advantage: [{FirstRoll}, {SecondRoll}] -> {ChosenRoll} vs DC {Difficulty} ({OutcomeText})"

            else:
                DescriptionText = f"Advantage: [{FirstRoll}, {SecondRoll}] -> {ChosenRoll}"

            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Advantage for {CleanExpression} Keeping {ChosenRoll} Totaling {Total}")
            return DiceRollResult(CleanExpression, [FirstRoll, SecondRoll], Modifier, Total, DescriptionText, Character.GameSystemType.DND5thEdition, Effect)

        if Disadvantage and not Advantage:
            FirstRoll = Random.randint(1, 20)
            SecondRoll = Random.randint(1, 20)
            ChosenRoll = min(FirstRoll, SecondRoll)
            Modifier = self.ExtractModifier(CleanExpression)
            Total = ChosenRoll + Modifier
            if Difficulty is not None:
                Effect = Total - Difficulty
                OutcomeText = "Success" if (Effect >= 0) else "Failure"
                DescriptionText = f"Disadvantage: [{FirstRoll}, {SecondRoll}] -> {ChosenRoll} vs DC {Difficulty} ({OutcomeText})"

            else:
                DescriptionText = f"Disadvantage: [{FirstRoll}, {SecondRoll}] -> {ChosenRoll}"

            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Disadvantage for {CleanExpression} Keeping {ChosenRoll} Totaling {Total}")
            return DiceRollResult(CleanExpression, [FirstRoll, SecondRoll], Modifier, Total, DescriptionText, Character.GameSystemType.DND5thEdition, Effect)

        Match = self.DicePattern.match(CleanExpression)
        if not Match:
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Dice Expression: \"{CleanExpression}\"")
            raise ValueError(f"Invalid Dice Expression Provided: {CleanExpression}")

        DieCountString, DieSidesString, ModifierString = Match.groups()
        DieCount: int = int(DieCountString) if DieCountString else 1
        DieSides: int = int(DieSidesString)
        Modifier = int(ModifierString) if ModifierString else 0
        Rolls: list[int] = self.RollStandardDice(DieCount, DieSides)
        Total = sum(Rolls) + Modifier
        if Difficulty is not None:
            Effect = Total - Difficulty
            OutcomeText = "Success" if (Effect >= 0) else "Failure"
            DescriptionText = f"Standard Roll vs DC {Difficulty} ({OutcomeText})"

        else:
            DescriptionText = "Standard Roll"

        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Roll for {CleanExpression} with {Rolls} Totaling {Total}")
        return DiceRollResult(CleanExpression, Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.DND5thEdition, Effect)

    def RollTraveller2ndEdition(self, Modifier: int = 0, HasBoon: bool = False, HasBane: bool = False, TargetDifficulty: int = 8) -> DiceRollResult:
        ExpressionText: str = "2d6"
        if HasBoon and not HasBane:
            Rolls: list[int] = self.RollStandardDice(3, 6)
            SortedRolls: list[int] = sorted(Rolls, reverse = True)
            KeptRolls: list[int] = SortedRolls[:2]
            Total: int = sum(KeptRolls) + Modifier
            Effect: int = Total - TargetDifficulty
            DescriptionText: str = f"Boon (3d6 drop lowest): [{Rolls[0]}, {Rolls[1]}, {Rolls[2]}] -> Kept [{KeptRolls[0]}, {KeptRolls[1]}] vs Diff {TargetDifficulty}"
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Boon with Kept Rolls {KeptRolls} Totaling {Total} and Effect {Effect}")
            return DiceRollResult("3d6 (Boon)", Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.Traveller2ndEdition, Effect)

        if HasBane and not HasBoon:
            Rolls = self.RollStandardDice(3, 6)
            SortedRolls = sorted(Rolls)
            KeptRolls = SortedRolls[:2]
            Total = sum(KeptRolls) + Modifier
            Effect = Total - TargetDifficulty
            DescriptionText = f"Bane (3d6 drop highest): [{Rolls[0]}, {Rolls[1]}, {Rolls[2]}] -> Kept [{KeptRolls[0]}, {KeptRolls[1]}] vs Diff {TargetDifficulty}"
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Bane with Kept Rolls {KeptRolls} Totaling {Total} and Effect {Effect}")
            return DiceRollResult("3d6 (Bane)", Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.Traveller2ndEdition, Effect)

        Rolls = self.RollStandardDice(2, 6)
        Total = sum(Rolls) + Modifier
        Effect = Total - TargetDifficulty
        DescriptionText = f"2d6 Check vs Target {TargetDifficulty}"
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Standard Roll with {Rolls} Totaling {Total} and Effect {Effect}")
        return DiceRollResult(ExpressionText, Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.Traveller2ndEdition, Effect)

    def ExtractModifier(self, Expression: str) -> int:
        PlusIndex: int = Expression.find("+")
        MinusIndex: int = Expression.find("-")
        if PlusIndex != -1:
            try:
                return int(Expression[PlusIndex + 1:])

            except ValueError:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Positive Modifier in Expression: \"{Expression}\"")
                return 0

        if MinusIndex != -1:
            try:
                return -int(Expression[MinusIndex + 1:])

            except ValueError:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Negative Modifier in Expression: \"{Expression}\"")
                return 0

        return 0

GLOBAL_DICE_ROLLER: DiceRollerService = DiceRollerService()
