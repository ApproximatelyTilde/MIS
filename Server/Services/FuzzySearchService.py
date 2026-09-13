import difflib as DifferenceLibrary
import re      as RegularExpressions
import typing  as Typing

class FuzzySearchService:
    @staticmethod
    def NormalizeString(InputString: str) -> str:
        CleanedString: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", InputString).lower()
        return CleanedString

    @staticmethod
    def FindBestMatch(Query: str, Candidates: Typing.Sequence[str], Cutoff: float = 0.6) -> Typing.Optional[str]:
        if not Query or not Candidates:
            return None

        CandidateList: Typing.List[str] = list(Candidates)
        NormalizedQuery: str = FuzzySearchService.NormalizeString(Query)

        for Candidate in CandidateList:
            if Candidate.lower() == Query.lower():
                return Candidate

        NormalizedCandidateMap: Typing.Dict[str, str] = {
            FuzzySearchService.NormalizeString(Candidate): Candidate for Candidate in CandidateList
        }

        if NormalizedQuery in NormalizedCandidateMap:
            return NormalizedCandidateMap[NormalizedQuery]

        DirectMatches: Typing.List[str] = DifferenceLibrary.get_close_matches(Query, CandidateList, n = 1, cutoff = Cutoff)
        if DirectMatches:
            return DirectMatches[0]

        NormalizedCandidates: Typing.List[str] = list(NormalizedCandidateMap.keys())
        NormalizedMatches: Typing.List[str] = DifferenceLibrary.get_close_matches(NormalizedQuery, NormalizedCandidates, n = 1, cutoff = Cutoff)
        if NormalizedMatches:
            return NormalizedCandidateMap[NormalizedMatches[0]]

        return None

    @staticmethod
    def FindMatches(Query: str, Candidates: Typing.Sequence[str], Limit: int = 5, Cutoff: float = 0.6) -> Typing.List[str]:
        if not Query or not Candidates:
            return []

        CandidateList: Typing.List[str] = list(Candidates)
        DirectMatches: Typing.List[str] = DifferenceLibrary.get_close_matches(Query, CandidateList, n = Limit, cutoff = Cutoff)
        if DirectMatches:
            return DirectMatches

        NormalizedQuery: str = FuzzySearchService.NormalizeString(Query)
        NormalizedCandidateMap: Typing.Dict[str, str] = {
            FuzzySearchService.NormalizeString(Candidate): Candidate for Candidate in CandidateList
        }
        NormalizedMatches: Typing.List[str] = DifferenceLibrary.get_close_matches(NormalizedQuery, list(NormalizedCandidateMap.keys()), n = Limit, cutoff = Cutoff)
        return [NormalizedCandidateMap[MatchKey] for MatchKey in NormalizedMatches]
