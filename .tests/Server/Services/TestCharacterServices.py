import typing                                    as Typing
import Server.Models.Character                   as Character
import Server.Services.CharacterGeneratorService as CharacterGeneratorService
import Server.Services.CharacterImportService    as CharacterImportService
import Server.Services.CharacterMappingService   as CharacterMappingService

class TestCharacterServices:
    def TestRoll4D6DropLowestRange(self) -> None:
        GeneratorService: CharacterGeneratorService.CharacterGeneratorService = CharacterGeneratorService.CharacterGeneratorService()
        for EvaluationIndex in range(10):
            ScoreValue: int = GeneratorService.Roll4D6DropLowest()
            assert ((ScoreValue >= 3) and (ScoreValue <= 18))

    def TestGenerateDND5EQuickCharacterStructure(self) -> None:
        GeneratorService: CharacterGeneratorService.CharacterGeneratorService = CharacterGeneratorService.CharacterGeneratorService()
        CharacterPayload: Typing.Dict[str, Typing.Any]                        = GeneratorService.GenerateDND5EQuickCharacter(Name = "Theron", PreferredClass = "Fighter")

        assert (CharacterPayload.get("Name") == "Theron")
        assert (CharacterPayload.get("GameSystem") == "DND5E")
        assert ("SummaryData" in CharacterPayload)
        assert ("DetailData" in CharacterPayload)

        SummaryData     : Typing.Dict[str, Typing.Any]                        = CharacterPayload["SummaryData"]
        assert (isinstance(SummaryData, dict))
        assert (SummaryData.get("Class") == "Fighter")
        assert (SummaryData.get("Level") == 1)

    def TestDetectImportSourceDicecloudV1RealURL(self) -> None:
        ImportService: CharacterImportService.CharacterImportService                                   = CharacterImportService.CharacterImportService()
        TargetURL    : str                                                                             = "https://v1.dicecloud.com/character/ZSywPvEfx7bQdXMvu/"
        ImportResult : Typing.Tuple[Typing.Optional[str], Typing.Optional[str], Typing.Optional[str]]  = ImportService.DetectImportSource(TargetURL = TargetURL)
        SourceType, CharacterID, SourceName                                                            = ImportResult

        assert (SourceType == "DC1")
        assert (CharacterID == "ZSywPvEfx7bQdXMvu")
        assert (SourceName == "Dicecloud v1")

    def TestDetectImportSourceDNDBeyondRealURL(self) -> None:
        ImportService: CharacterImportService.CharacterImportService                                   = CharacterImportService.CharacterImportService()
        TargetURL    : str                                                                             = "https://www.dndbeyond.com/characters/168802324/O1VFol"
        ImportResult : Typing.Tuple[Typing.Optional[str], Typing.Optional[str], Typing.Optional[str]]  = ImportService.DetectImportSource(TargetURL = TargetURL)
        SourceType, CharacterID, SourceName                                                            = ImportResult

        assert (SourceType == "DDB")
        assert (CharacterID == "168802324")
        assert (SourceName == "D&D Beyond")

    def TestDetectImportSourceDNDBeyondShortlink(self) -> None:
        ImportService: CharacterImportService.CharacterImportService                                   = CharacterImportService.CharacterImportService()
        TargetURL    : str                                                                             = "https://ddb.ac/characters/168802324"
        ImportResult : Typing.Tuple[Typing.Optional[str], Typing.Optional[str], Typing.Optional[str]]  = ImportService.DetectImportSource(TargetURL = TargetURL)
        SourceType, CharacterID, SourceName                                                            = ImportResult

        assert (SourceType == "DDB")
        assert (CharacterID == "168802324")
        assert (SourceName == "D&D Beyond")

    def TestDetectImportSourceInvalidURL(self) -> None:
        ImportService: CharacterImportService.CharacterImportService                                   = CharacterImportService.CharacterImportService()
        TargetURL    : str                                                                             = "https://unknownservice.com/character/999"
        ImportResult : Typing.Tuple[Typing.Optional[str], Typing.Optional[str], Typing.Optional[str]]  = ImportService.DetectImportSource(TargetURL = TargetURL)
        SourceType, CharacterID, SourceName                                                            = ImportResult

        assert (SourceType is None)
        assert (CharacterID is None)
        assert (SourceName is None)
