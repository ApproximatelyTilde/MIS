import random                                  as Random
import typing                                  as Typing
import Server.Models.Character                 as Character
import Server.Services.CharacterMappingService as CharacterMapping
import Server.Services.DebugService            as Debug

class CharacterGeneratorService:
    DND5EClasses    : Typing.List[str] = ["Fighter", "Wizard", "Rogue", "Cleric", "Paladin", "Ranger", "Barbarian", "Bard", "Druid", "Monk", "Sorcerer", "Warlock"]
    DND5ESpecies    : Typing.List[str] = ["Human", "Elf", "Dwarf", "Halfling", "Dragonborn", "Gnome", "Half-Elf", "Half-Orc", "Tiefling"]
    DND5EBackgrounds: Typing.List[str] = ["Acolyte", "Criminal", "Folk Hero", "Noble", "Sage", "Soldier", "Outlander", "Urchin"]
    MGT2ECareers    : Typing.List[str] = ["Navy", "Scout", "Marine", "Army", "Merchant", "Agent", "Scholar", "Noble", "Rogue", "Citizen", "Drifter", "Entertainer"]
    MGT2EHomeworlds : Typing.List[str] = ["High Technology World", "Agricultural World", "Industrial World", "Asteroid Belt", "Water World", "Desert World", "Core Capital"]

    def Roll4D6DropLowest(self) -> int:
        Rolls: Typing.List[int] = [Random.randint(1, 6) for RollIndex in range(4)]
        ResultScore: int = sum(sorted(Rolls)[1:])
        Debug.LogMessage(Level = Debug.LogLevel.Debug, Message = f"Evaluated Ability Score: Rolls={Rolls}, Score={ResultScore}")
        return ResultScore

    def GenerateDND5EQuickCharacter(self, Name: str, PreferredClass: Typing.Optional[str] = None) -> Typing.Dict[str, Typing.Any]:
        SelectedClass: str = PreferredClass if (PreferredClass in self.DND5EClasses) else Random.choice(self.DND5EClasses)
        SelectedSpecies: str = Random.choice(self.DND5ESpecies)
        SelectedBackground: str = Random.choice(self.DND5EBackgrounds)
        AbilityScores: Typing.Dict[str, int] = {
            "Strength"    : self.Roll4D6DropLowest(),
            "Dexterity"   : self.Roll4D6DropLowest(),
            "Constitution": self.Roll4D6DropLowest(),
            "Intelligence": self.Roll4D6DropLowest(),
            "Wisdom"      : self.Roll4D6DropLowest(),
            "Charisma"    : self.Roll4D6DropLowest()
        }
        ConstitutionModifier: int = (AbilityScores["Constitution"] - 10) // 2
        BaseHitPoints: int = max(1, 10 + ConstitutionModifier)
        Summary: Typing.Dict[str, Typing.Any] = {
            "System"    : Character.GameSystemType.DND5E.value,
            "Class"     : SelectedClass,
            "Level"     : 1,
            "Species"   : SelectedSpecies,
            "Background": SelectedBackground,
            "HitPoints" : BaseHitPoints,
            "ArmorClass": 10 + ((AbilityScores["Dexterity"] - 10) // 2)
        }
        CurrencyDictionary: Typing.Dict[str, int] = {
            "GoldPieces"  : 15,
            "SilverPieces": 0,
            "CopperPieces": 0
        }
        Detail: Typing.Dict[str, Typing.Any] = {
            "AbilityScores"    : AbilityScores,
            "ProficiencyBonus" : 2,
            "PassivePerception": 10 + ((AbilityScores["Wisdom"] - 10) // 2),
            "Inventory"        : ["Backpack", "Bedroll", "Rations (5 days)", "Waterskin", "50ft Rope"],
            "Currency"         : CurrencyDictionary
        }
        CharacterPayload: Typing.Dict[str, Typing.Any] = {
            "Name"       : Name,
            "GameSystem" : Character.GameSystemType.DND5E.value,
            "SummaryData": Summary,
            "DetailData" : Detail
        }
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created Character: \"{Name}\" ({SelectedSpecies} {SelectedClass}, HP={BaseHitPoints})")
        return CharacterPayload

    def GenerateMGT2EQuickCharacter(self, Name: str, PreferredCareer: Typing.Optional[str] = None) -> Typing.Dict[str, Typing.Any]:
        SelectedCareer: str = PreferredCareer if (PreferredCareer in self.MGT2ECareers) else Random.choice(self.MGT2ECareers)
        SelectedHomeworld: str = Random.choice(self.MGT2EHomeworlds)
        Characteristics: Typing.Dict[str, int] = {
            "Strength"      : Random.randint(1, 6) + Random.randint(1, 6),
            "Dexterity"     : Random.randint(1, 6) + Random.randint(1, 6),
            "Endurance"     : Random.randint(1, 6) + Random.randint(1, 6),
            "Intelligence"  : Random.randint(1, 6) + Random.randint(1, 6),
            "Education"     : Random.randint(1, 6) + Random.randint(1, 6),
            "SocialStanding": Random.randint(1, 6) + Random.randint(1, 6)
        }
        StartingTerms: int = Random.randint(1, 4)
        StartingAge: int = 18 + (StartingTerms * 4)
        StartingCredits: int = Random.randint(1, 6) * 1000 * StartingTerms
        Summary: Typing.Dict[str, Typing.Any] = {
            "System"   : Character.GameSystemType.MGT2E.value,
            "Career"   : SelectedCareer,
            "Terms"    : StartingTerms,
            "Age"      : StartingAge,
            "Homeworld": SelectedHomeworld,
            "Title"    : "Citizen" if (Characteristics["SocialStanding"] < 10) else "Noble"
        }
        SkillsDictionary: Typing.Dict[str, int] = {
            "GunCombat"  : 1,
            "Athletics"  : 1,
            "Pilot"      : 0,
            "VaccSuit"   : 0,
            "Electronics": 0
        }
        CurrencyDictionary: Typing.Dict[str, int] = {
            "Credits": StartingCredits
        }
        Detail: Typing.Dict[str, Typing.Any] = {
            "Characteristics": Characteristics,
            "Skills"         : SkillsDictionary,
            "Inventory"      : ["Standard Vacc Suit", "Commdot", "Hand Computer", "Slug Pistol"],
            "Currency"       : CurrencyDictionary
        }
        CharacterPayload: Typing.Dict[str, Typing.Any] = {
            "Name"       : Name,
            "GameSystem" : Character.GameSystemType.MGT2E.value,
            "SummaryData": Summary,
            "DetailData" : Detail
        }
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Created Character: \"{Name}\" ({SelectedCareer}, Terms={StartingTerms}, Age={StartingAge})")
        return CharacterPayload

    def IngestExternalDDBData(self, RawJSON: Typing.Dict[str, Typing.Any]) -> Typing.Dict[str, Typing.Any]:
        MappedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDDBCharacter(RawJSON)
        ExportedPayload = CharacterMapping.GLOBAL_CHARACTER_MAPPER.ExportToDatabasePayload(MappedSheet, RawImportData = RawJSON)
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Ingested DDB Character: \"{MappedSheet.Name}\" (Level={MappedSheet.TotalLevel})")
        return ExportedPayload

    def IngestExternalDC1Data(self, RawJSON: Typing.Dict[str, Typing.Any]) -> Typing.Dict[str, Typing.Any]:
        MappedSheet = CharacterMapping.GLOBAL_CHARACTER_MAPPER.MapDC1Character(RawJSON)
        ExportedPayload = CharacterMapping.GLOBAL_CHARACTER_MAPPER.ExportToDatabasePayload(MappedSheet, RawImportData = RawJSON)
        ExportedPayload["IsProtected"] = True
        ExportedPayload["ImportSource"] = "DC1"
        Debug.LogMessage(Level = Debug.LogLevel.Info, Message = f"Ingested DC1 Character: \"{MappedSheet.Name}\" (Level={MappedSheet.TotalLevel})")

        return ExportedPayload

GLOBAL_CHARACTER_GENERATOR_SERVICE: CharacterGeneratorService = CharacterGeneratorService()
