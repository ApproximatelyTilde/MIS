import random                                    as Random
import typing                                    as Typing
import Server.Models.Character                   as Character
import Server.Services.CharacterMappingService   as CharacterMapping
import Server.Services.DebugService              as DebugService

class CharacterGeneratorService:
    DND5thEditionClasses: Typing.List[str] = ["Fighter", "Wizard", "Rogue", "Cleric", "Paladin", "Ranger", "Barbarian", "Bard", "Druid", "Monk", "Sorcerer", "Warlock"]
    DND5thEditionSpecies: Typing.List[str] = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn", "Gnome", "Half-Elf", "Half-Orc", "Tiefling"]
    DND5thEditionBackgrounds: Typing.List[str] = ["Acolyte", "Criminal", "Folk Hero", "Noble", "Sage", "Soldier", "Outlander", "Urchin"]
    Traveller2ndEditionCareers: Typing.List[str] = ["Navy", "Scout", "Marine", "Army", "Merchant", "Agent", "Scholar", "Noble", "Rogue", "Citizen", "Drifter", "Entertainer"]
    Traveller2ndEditionHomeworlds: Typing.List[str] = ["High Technology World", "Agricultural World", "Industrial World", "Asteroid Belt", "Water World", "Desert World", "Core Capital"]

    def Roll4D6DropLowest(self) -> int:
        Rolls: Typing.List[int] = [Random.randint(1, 6) for _ in range(4)]
        ResultScore: int = sum(sorted(Rolls)[1:])
        DebugService.LogDebugMessage(f"4d6 Drop Lowest: {Rolls} -> {ResultScore}")
        return ResultScore

    def GenerateDND5thEditionQuickCharacter(self, Name: str, PreferredClass: Typing.Optional[str] = None) -> Typing.Dict[str, Typing.Any]:
        SelectedClass: str = PreferredClass if (PreferredClass in self.DND5thEditionClasses) else Random.choice(self.DND5thEditionClasses)
        SelectedSpecies: str = Random.choice(self.DND5thEditionSpecies)
        SelectedBackground: str = Random.choice(self.DND5thEditionBackgrounds)
        AbilityScores: Typing.Dict[str, int] = {
            "Strength": self.Roll4D6DropLowest(),
            "Dexterity": self.Roll4D6DropLowest(),
            "Constitution": self.Roll4D6DropLowest(),
            "Intelligence": self.Roll4D6DropLowest(),
            "Wisdom": self.Roll4D6DropLowest(),
            "Charisma": self.Roll4D6DropLowest()
        }
        ConstitutionModifier: int = (AbilityScores["Constitution"] - 10) // 2
        BaseHitPoints: int = max(1, 10 + ConstitutionModifier)
        Summary: Typing.Dict[str, Typing.Any] = {
            "System": Character.GameSystemType.DND5thEdition.value,
            "Class": SelectedClass,
            "Level": 1,
            "Species": SelectedSpecies,
            "Background": SelectedBackground,
            "HitPoints": BaseHitPoints,
            "ArmorClass": 10 + ((AbilityScores["Dexterity"] - 10) // 2)
        }
        CurrencyDictionary: Typing.Dict[str, int] = {
            "GoldPieces": 15,
            "SilverPieces": 0,
            "CopperPieces": 0
        }
        Detail: Typing.Dict[str, Typing.Any] = {
            "AbilityScores": AbilityScores,
            "ProficiencyBonus": 2,
            "PassivePerception": 10 + ((AbilityScores["Wisdom"] - 10) // 2),
            "Inventory": ["Backpack", "Bedroll", "Rations (5 days)", "Waterskin", "50ft Rope"],
            "Currency": CurrencyDictionary
        }
        CharacterPayload: Typing.Dict[str, Typing.Any] = {
            "Name": Name,
            "GameSystem": Character.GameSystemType.DND5thEdition.value,
            "SummaryData": Summary,
            "DetailData": Detail
        }
        DebugService.LogDebugMessage(f"Generated DND5thEdition Character: '{Name}' ({SelectedSpecies} {SelectedClass}, HP={BaseHitPoints}, AC={Summary['ArmorClass']})")
        return CharacterPayload

    def GenerateTraveller2ndEditionQuickCharacter(self, Name: str, PreferredCareer: Typing.Optional[str] = None) -> Typing.Dict[str, Typing.Any]:
        SelectedCareer: str = PreferredCareer if (PreferredCareer in self.Traveller2ndEditionCareers) else Random.choice(self.Traveller2ndEditionCareers)
        SelectedHomeworld: str = Random.choice(self.Traveller2ndEditionHomeworlds)
        Characteristics: Typing.Dict[str, int] = {
            "Strength": Random.randint(1, 6) + Random.randint(1, 6),
            "Dexterity": Random.randint(1, 6) + Random.randint(1, 6),
            "Endurance": Random.randint(1, 6) + Random.randint(1, 6),
            "Intelligence": Random.randint(1, 6) + Random.randint(1, 6),
            "Education": Random.randint(1, 6) + Random.randint(1, 6),
            "SocialStanding": Random.randint(1, 6) + Random.randint(1, 6)
        }
        StartingTerms: int = Random.randint(1, 4)
        StartingAge: int = 18 + (StartingTerms * 4)
        StartingCredits: int = Random.randint(1, 6) * 1000 * StartingTerms
        Summary: Typing.Dict[str, Typing.Any] = {
            "System": Character.GameSystemType.Traveller2ndEdition.value,
            "Career": SelectedCareer,
            "Terms": StartingTerms,
            "Age": StartingAge,
            "Homeworld": SelectedHomeworld,
            "Title": "Citizen" if (Characteristics["SocialStanding"] < 10) else "Noble"
        }
        SkillsDictionary: Typing.Dict[str, int] = {
            "GunCombat": 1,
            "Athletics": 1,
            "Pilot": 0,
            "VaccSuit": 0,
            "Electronics": 0
        }
        CurrencyDictionary: Typing.Dict[str, int] = {
            "Credits": StartingCredits
        }
        Detail: Typing.Dict[str, Typing.Any] = {
            "Characteristics": Characteristics,
            "Skills": SkillsDictionary,
            "Inventory": ["Standard Vacc Suit", "Commdot", "Hand Computer", "Slug Pistol"],
            "Currency": CurrencyDictionary
        }
        CharacterPayload: Typing.Dict[str, Typing.Any] = {
            "Name": Name,
            "GameSystem": Character.GameSystemType.Traveller2ndEdition.value,
            "SummaryData": Summary,
            "DetailData": Detail
        }
        DebugService.LogDebugMessage(f"Generated Traveller2ndEdition Character: '{Name}' (Career={SelectedCareer}, Terms={StartingTerms}, Age={StartingAge}, World='{SelectedHomeworld}')")
        return CharacterPayload

    def IngestExternalDNDBeyondData(self, RawJSON: Typing.Dict[str, Typing.Any]) -> Typing.Dict[str, Typing.Any]:
        MappedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDNDBeyondCharacter(RawJSON)
        ExportedPayload = CharacterMapping.GLOBAL_CHARACTER_MAPPER.ExportToDatabasePayload(MappedSheet, RawImportData = RawJSON)
        DebugService.LogDebugMessage(f"Ingested External DNDBeyond Character: '{MappedSheet.Name}' (Lvl={MappedSheet.TotalLevel}, Keys={len(RawJSON)})")
        return ExportedPayload

    def IngestExternalDicecloudData(self, RawJSON: Typing.Dict[str, Typing.Any]) -> Typing.Dict[str, Typing.Any]:
        MappedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDicecloudCharacter(RawJSON)
        ExportedPayload = CharacterMapping.GLOBAL_CHARACTER_MAPPER.ExportToDatabasePayload(MappedSheet, RawImportData = RawJSON)
        DebugService.LogDebugMessage(f"Ingested External Dicecloud Character: '{MappedSheet.Name}' (Lvl={MappedSheet.TotalLevel}, Keys={len(RawJSON)})")
        return ExportedPayload

GLOBAL_CHARACTER_GENERATOR_SERVICE: CharacterGeneratorService = CharacterGeneratorService()
