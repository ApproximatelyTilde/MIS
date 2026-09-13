import typing                              as Typing
import pytest                              as Pytest
import Server.Models.Character             as Character
import Server.Services.DiceRollerService   as DiceRollerService

class TestDiceRollerService:
    def TestRollStandardDiceValidRange(self) -> None:
        RollerService: DiceRollerService.DiceRollerService = DiceRollerService.DiceRollerService()
        RollResults  : Typing.List[int]                    = RollerService.RollStandardDice(DieCount = 4, DieSides = 6)

        assert (len(RollResults) == 4)
        for RollValue in RollResults:
            assert ((RollValue >= 1) and (RollValue <= 6))

    def TestRollStandardDiceInvalidParametersRaiseValueError(self) -> None:
        RollerService: DiceRollerService.DiceRollerService = DiceRollerService.DiceRollerService()

        with Pytest.raises(ValueError):
            RollerService.RollStandardDice(DieCount = 0, DieSides = 6)

        with Pytest.raises(ValueError):
            RollerService.RollStandardDice(DieCount = 5, DieSides = 0)

        with Pytest.raises(ValueError):
            RollerService.RollStandardDice(DieCount = 101, DieSides = 20)

    def TestRollDND5EStandardExpression(self) -> None:
        RollerService: DiceRollerService.DiceRollerService = DiceRollerService.DiceRollerService()
        RollResult   : DiceRollerService.DiceRollResult    = RollerService.RollDND5E(Expression = "1d20+5")

        assert (RollResult.Expression == "1d20+5")
        assert (RollResult.Modifier == 5)
        assert (len(RollResult.IndividualRolls) == 1)
        assert (RollResult.Total == (RollResult.IndividualRolls[0] + 5))
        assert (RollResult.GameSystem == Character.GameSystemType.DND5E)

    def TestRollDND5EAdvantageAndDisadvantage(self) -> None:
        RollerService     : DiceRollerService.DiceRollerService = DiceRollerService.DiceRollerService()
        AdvantageResult   : DiceRollerService.DiceRollResult    = RollerService.RollDND5E(Expression = "1d20+3", Advantage = True, Difficulty = 15)

        assert (len(AdvantageResult.IndividualRolls) == 2)
        assert ("Advantage" in AdvantageResult.Description)
        assert (AdvantageResult.Effect is not None)

        DisadvantageResult: DiceRollerService.DiceRollResult    = RollerService.RollDND5E(Expression = "1d20+3", Disadvantage = True, Difficulty = 15)
        assert (len(DisadvantageResult.IndividualRolls) == 2)
        assert ("Disadvantage" in DisadvantageResult.Description)

    def TestRollMGT2EStandard(self) -> None:
        RollerService: DiceRollerService.DiceRollerService = DiceRollerService.DiceRollerService()
        RollResult   : DiceRollerService.DiceRollResult    = RollerService.RollMGT2E(Modifier = 2, TargetDifficulty = 8)

        assert (RollResult.Modifier == 2)
        assert (len(RollResult.IndividualRolls) == 2)
        assert (RollResult.Total == (RollResult.IndividualRolls[0] + RollResult.IndividualRolls[1] + 2))
        assert (RollResult.GameSystem == Character.GameSystemType.MGT2E)
