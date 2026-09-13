import typing                             as Typing
import Server.Services.FuzzySearchService as FuzzySearchService

class TestFuzzySearchService:
    def TestNormalizeString(self) -> None:
        assert (FuzzySearchService.FuzzySearchService.NormalizeString("Longsword +1") == "longsword1")
        assert (FuzzySearchService.FuzzySearchService.NormalizeString("  Potion-Of-Healing! ") == "potionofhealing")
        assert (FuzzySearchService.FuzzySearchService.NormalizeString("D&D 5E") == "dd5e")

    def TestFindBestMatchExact(self) -> None:
        CandidateOptions: Typing.List[str]     = ["Fighter", "Wizard", "Rogue", "Cleric"]
        BestMatch       : Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(Query = "wizard", Candidates = CandidateOptions)
        assert (BestMatch == "Wizard")

    def TestFindBestMatchFuzzy(self) -> None:
        CandidateOptions: Typing.List[str]     = ["Barbarian", "Bard", "Paladin", "Sorcerer"]
        BestMatch       : Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(Query = "barbarian", Candidates = CandidateOptions)
        assert (BestMatch == "Barbarian")

    def TestFindBestMatchEmptyReturnsNone(self) -> None:
        assert (FuzzySearchService.FuzzySearchService.FindBestMatch(Query = "", Candidates = ["Fighter"]) is None)
        assert (FuzzySearchService.FuzzySearchService.FindBestMatch(Query = "Fighter", Candidates = []) is None)

    def TestFindMatchesRanking(self) -> None:
        CandidateOptions: Typing.List[str] = ["Cure Wounds", "Inflict Wounds", "Healing Word", "Mass Cure Wounds"]
        MatchesList     : Typing.List[str] = FuzzySearchService.FuzzySearchService.FindMatches(Query = "Wounds", Candidates = CandidateOptions, Limit = 3)
        assert (len(MatchesList) > 0)
