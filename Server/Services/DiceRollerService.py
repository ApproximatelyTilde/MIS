import random as Random
import re as RegularExpressions
import typing as Typing
import Server.Models.Character as Character

class DiceRollResult:
    def __init__(self, Expression: str, IndividualRolls: Typing.List[int], Modifier: int, Total: int, Description: str = "", GameSystem: Character.GameSystemType = Character.GameSystemType.DND5thEdition, Effect: Typing.Optional[int] = None) -> None:
        self.Expression: str = Expression
        self.IndividualRolls: Typing.List[int] = IndividualRolls
        self.Modifier: int = Modifier
        self.Total: int = Total
        self.Description: str = Description
        self.GameSystem: Character.GameSystemType = GameSystem
        self.Effect: Typing.Optional[int] = Effect

    def ToDictionary(self) -> Typing.Dict[str, Typing.Any]:
        ResultDictionary: Typing.Dict[str, Typing.Any] = {
            "Expression": self.Expression,
            "IndividualRolls": self.IndividualRolls,
            "Modifier": self.Modifier,
            "Total": self.Total,
            "Description": self.Description,
            "GameSystem": self.GameSystem.value,
            "Effect": self.Effect
        }
        return ResultDictionary

class DiceRollerService:
    def __init__(self) -> None:
        self.DicePattern: RegularExpressions.Pattern[str] = RegularExpressions.compile(r"^(\d+)?d(\d+)([+-]\d+)?$", RegularExpressions.IGNORECASE)

    def RollStandardDice(self, DieCount: int, DieSides: int) -> Typing.List[int]:
        Rolls: Typing.List[int] = [Random.randint(1, DieSides) for _ in range(DieCount)]
        return Rolls

    def RollDND5thEdition(self, Expression: str, Advantage: bool = False, Disadvantage: bool = False, Difficulty: Typing.Optional[int] = None) -> DiceRollResult:
        CleanExpression: str = Expression.strip().replace(" ", "")
        Effect: Typing.Optional[int] = None
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
            return DiceRollResult(CleanExpression, [FirstRoll, SecondRoll], Modifier, Total, DescriptionText, Character.GameSystemType.DND5thEdition, Effect)

        Match = self.DicePattern.match(CleanExpression)
        if not Match:
            SingleRoll: int = Random.randint(1, 20)
            if Difficulty is not None:
                Effect = SingleRoll - Difficulty
                OutcomeText = "Success" if (Effect >= 0) else "Failure"
                DescriptionText = f"Default d20 Roll vs DC {Difficulty} ({OutcomeText})"
            else:
                DescriptionText = "Default d20 Roll"
            return DiceRollResult(CleanExpression, [SingleRoll], 0, SingleRoll, DescriptionText, Character.GameSystemType.DND5thEdition, Effect)

        DieCountString, DieSidesString, ModifierString = Match.groups()
        DieCount: int = int(DieCountString) if DieCountString else 1
        DieSides: int = int(DieSidesString)
        Modifier = int(ModifierString) if ModifierString else 0
        Rolls: Typing.List[int] = self.RollStandardDice(DieCount, DieSides)
        Total = sum(Rolls) + Modifier
        if Difficulty is not None:
            Effect = Total - Difficulty
            OutcomeText = "Success" if (Effect >= 0) else "Failure"
            DescriptionText = f"Standard Roll vs DC {Difficulty} ({OutcomeText})"
        else:
            DescriptionText = "Standard Roll"
        return DiceRollResult(CleanExpression, Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.DND5thEdition, Effect)

    def RollTraveller2ndEdition(self, Modifier: int = 0, HasBoon: bool = False, HasBane: bool = False, TargetDifficulty: int = 8) -> DiceRollResult:
        ExpressionText: str = "2d6"
        if HasBoon and not HasBane:
            Rolls: Typing.List[int] = self.RollStandardDice(3, 6)
            SortedRolls: Typing.List[int] = sorted(Rolls, reverse = True)
            KeptRolls: Typing.List[int] = SortedRolls[:2]
            Total: int = sum(KeptRolls) + Modifier
            Effect: int = Total - TargetDifficulty
            DescriptionText: str = f"Boon (3d6 drop lowest): [{Rolls[0]}, {Rolls[1]}, {Rolls[2]}] -> Kept [{KeptRolls[0]}, {KeptRolls[1]}] vs Diff {TargetDifficulty}"
            return DiceRollResult("3d6 (Boon)", Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.Traveller2ndEdition, Effect)

        if HasBane and not HasBoon:
            Rolls = self.RollStandardDice(3, 6)
            SortedRolls = sorted(Rolls)
            KeptRolls = SortedRolls[:2]
            Total = sum(KeptRolls) + Modifier
            Effect = Total - TargetDifficulty
            DescriptionText = f"Bane (3d6 drop highest): [{Rolls[0]}, {Rolls[1]}, {Rolls[2]}] -> Kept [{KeptRolls[0]}, {KeptRolls[1]}] vs Diff {TargetDifficulty}"
            return DiceRollResult("3d6 (Bane)", Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.Traveller2ndEdition, Effect)

        Rolls = self.RollStandardDice(2, 6)
        Total = sum(Rolls) + Modifier
        Effect = Total - TargetDifficulty
        DescriptionText = f"2d6 Check vs Target {TargetDifficulty}"
        return DiceRollResult(ExpressionText, Rolls, Modifier, Total, DescriptionText, Character.GameSystemType.Traveller2ndEdition, Effect)

    def ExtractModifier(self, Expression: str) -> int:
        PlusIndex: int = Expression.find("+")
        MinusIndex: int = Expression.find("-")
        if PlusIndex != -1:
            try:
                return int(Expression[PlusIndex + 1:])
            except ValueError:
                return 0

        if MinusIndex != -1:
            try:
                return -int(Expression[MinusIndex + 1:])
            except ValueError:
                return 0

        return 0

GLOBAL_DICE_ROLLER: DiceRollerService = DiceRollerService()
