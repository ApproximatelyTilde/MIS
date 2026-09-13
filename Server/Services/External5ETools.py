import json                               as JavaScriptObjectNotation
import pathlib                            as PathLibrary
import re                                 as RegularExpressions
import time                               as TimeLibrary
import typing                             as Typing
import Server.Services.DebugService       as DebugService
import Server.Services.FuzzySearchService as FuzzySearchService

CACHE_EXPIRATION_SECONDS: int = 1209600

class External5ETools:
    def __init__(self, DataDirectoryPath: Typing.Optional[PathLibrary.Path] = None) -> None:
        if DataDirectoryPath is None:
            self.DataDirectoryPath: PathLibrary.Path = PathLibrary.Path(__file__).resolve().parent / "External" / "5eTools" / "data"

        else:
            self.DataDirectoryPath = DataDirectoryPath

        self.ClassesData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.SubclassesData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.MulticlassSpellSlotTable: Typing.Dict[int, Typing.List[int]] = {
        }
        self.WarlockPactMagicTable: Typing.Dict[int, Typing.Tuple[int, int]] = {
        }
        self.LevelExperienceTable: Typing.Dict[int, int] = {
        }
        self.WeaponsData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ItemsData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.SpellsDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.SpellsNormalizedMap: Typing.Dict[str, str] = {
        }
        self.MonstersDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.MonstersNormalizedMap: Typing.Dict[str, str] = {
        }
        self.ItemsDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ItemsNormalizedMap: Typing.Dict[str, str] = {
        }
        self.SourcePublicationDates: Typing.Dict[str, str] = {
        }
        self.RulesDataStore: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
        self.CantripsList: Typing.Optional[Typing.List[str]] = None
        self.EquipmentRulesData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
        self.LastLoadedTimestamp: float = 0.0

    def EnsureDataLoaded(self) -> None:
        CurrentTimestamp: float = TimeLibrary.time()
        if (self.LastLoadedTimestamp > 0.0) and ((CurrentTimestamp - self.LastLoadedTimestamp) < CACHE_EXPIRATION_SECONDS):
            return

        self.InitializeData()
        self.LastLoadedTimestamp = CurrentTimestamp

    def InitializeData(self) -> None:
        self.ClassesData = {
        }
        self.SubclassesData = {
        }
        self.MulticlassSpellSlotTable = {
        }
        self.WarlockPactMagicTable = {
        }
        self.LevelExperienceTable = {
        }
        self.WeaponsData = {
        }
        self.ItemsData = {
        }
        self.SpellsDetailData = {
        }
        self.SpellsNormalizedMap = {
        }
        self.MonstersDetailData = {
        }
        self.MonstersNormalizedMap = {
        }
        self.ItemsDetailData = {
        }
        self.ItemsNormalizedMap = {
        }
        self.RulesDataStore = None
        self.CantripsList = None
        self.EquipmentRulesData = None
        self.LoadSourcePublicationDates()

        ClassDirectory: PathLibrary.Path = self.DataDirectoryPath / "class"
        if ClassDirectory.exists():
            for ClassFilePath in ClassDirectory.glob("class-*.json"):
                if "fluff" in ClassFilePath.name:
                    continue

                try:
                    with open(ClassFilePath, mode = "r", encoding = "utf-8") as ClassFile:
                        ClassJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ClassFile)
                        for ClassEntry in ClassJSON.get("class", []):
                            ClassName: Typing.Optional[str] = ClassEntry.get("name")
                            if ClassName and ClassName not in self.ClassesData:
                                ClassSpellProgression: Typing.List[Typing.List[int]] = []
                                for TableGroup in ClassEntry.get("classTableGroups", []):
                                    if "rowsSpellProgression" in TableGroup:
                                        ClassSpellProgression = TableGroup.get("rowsSpellProgression", [])

                                    if "subclasses" in TableGroup and "rowsSpellProgression" in TableGroup:
                                        SubclassSpellProgression = TableGroup.get("rowsSpellProgression", [])
                                        for GroupSubclass in TableGroup.get("subclasses", []):
                                            SubclassName: Typing.Optional[str] = GroupSubclass.get("name")
                                            if SubclassName:
                                                Key: str = f"{ClassName}:{SubclassName}"
                                                if Key not in self.SubclassesData:
                                                    self.SubclassesData[Key] = {
                                                        "CasterProgression": "1/3",
                                                        "SpellcastingAbility": None,
                                                        "RowsSpellProgression": SubclassSpellProgression,
                                                        "Raw": GroupSubclass
                                                    }

                                                else:
                                                    self.SubclassesData[Key]["RowsSpellProgression"] = SubclassSpellProgression

                                    ColumnLabelsList: Typing.List[str] = [str(LabelItem).lower() for LabelItem in TableGroup.get("colLabels", [])]
                                    if "spell slots" in ColumnLabelsList and "slot level" in ColumnLabelsList:
                                        SlotsColumnIndex: int = ColumnLabelsList.index("spell slots")
                                        LevelColumnIndex: int = ColumnLabelsList.index("slot level")
                                        for PactRowIndex, PactRowData in enumerate(TableGroup.get("rows", [])):
                                            if len(PactRowData) > max(SlotsColumnIndex, LevelColumnIndex):
                                                PactSlotCount: int = int(PactRowData[SlotsColumnIndex])
                                                RawLevelString: str = str(PactRowData[LevelColumnIndex])
                                                LevelMatches = RegularExpressions.findall(r"\d+", RawLevelString)
                                                if LevelMatches:
                                                    PactSlotLevel: int = int(LevelMatches[0])
                                                    self.WarlockPactMagicTable[PactRowIndex + 1] = (PactSlotLevel, PactSlotCount)

                                self.ClassesData[ClassName] = {
                                    "HitDie": ClassEntry.get("hd", {}).get("faces"),
                                    "CasterProgression": ClassEntry.get("casterProgression"),
                                    "SpellcastingAbility": ClassEntry.get("spellcastingAbility"),
                                    "RowsSpellProgression": ClassSpellProgression,
                                    "Raw": ClassEntry
                                }

                        for SubclassEntry in ClassJSON.get("subclass", []):
                            SubclassName: Typing.Optional[str] = SubclassEntry.get("name")
                            SubclassClassName: Typing.Optional[str] = SubclassEntry.get("className")
                            if SubclassName and SubclassClassName:
                                SubclassKey: str = f"{SubclassClassName}:{SubclassName}"
                                SubclassSpellProgression = []
                                for SubTableGroup in SubclassEntry.get("subclassTableGroups", []):
                                    if "rowsSpellProgression" in SubTableGroup:
                                        SubclassSpellProgression = SubTableGroup.get("rowsSpellProgression", [])
                                        break

                                if SubclassKey not in self.SubclassesData:
                                    self.SubclassesData[SubclassKey] = {
                                        "CasterProgression": SubclassEntry.get("casterProgression"),
                                        "SpellcastingAbility": SubclassEntry.get("spellcastingAbility"),
                                        "RowsSpellProgression": SubclassSpellProgression,
                                        "Raw": SubclassEntry
                                    }

                                else:
                                    if SubclassEntry.get("casterProgression"):
                                        self.SubclassesData[SubclassKey]["CasterProgression"] = SubclassEntry.get("casterProgression")

                                    if SubclassEntry.get("spellcastingAbility"):
                                        self.SubclassesData[SubclassKey]["SpellcastingAbility"] = SubclassEntry.get("spellcastingAbility")

                                    if SubclassSpellProgression:
                                        self.SubclassesData[SubclassKey]["RowsSpellProgression"] = SubclassSpellProgression

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Class File: {ClassFilePath.name}")

        VariantRulesFilePath: PathLibrary.Path = self.DataDirectoryPath / "variantrules.json"
        if VariantRulesFilePath.exists():
            try:
                with open(VariantRulesFilePath, mode = "r", encoding = "utf-8") as VariantRulesFile:
                    VariantRulesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(VariantRulesFile)

                    def ScanEntriesForSpellSlots(EntriesList: Typing.List[Typing.Any]) -> None:
                        for EntryItem in EntriesList:
                            if isinstance(EntryItem, dict):
                                if EntryItem.get("type") == "table" and "Multiclass Spellcaster" in str(EntryItem.get("caption", "")):
                                    for RowItem in EntryItem.get("rows", []):
                                        if len(RowItem) >= 10:
                                            LevelMatches = RegularExpressions.findall(r"\d+", str(RowItem[0]))
                                            if LevelMatches:
                                                CasterLevelValue: int = int(LevelMatches[0])
                                                SlotsList: Typing.List[int] = []
                                                for CellItem in RowItem[1:10]:
                                                    CleanCell: str = str(CellItem).strip()
                                                    if CleanCell.isdigit():
                                                        SlotsList.append(int(CleanCell))

                                                    else:
                                                        SlotsList.append(0)

                                                self.MulticlassSpellSlotTable[CasterLevelValue] = SlotsList

                                if "entries" in EntryItem and isinstance(EntryItem["entries"], list):
                                    ScanEntriesForSpellSlots(EntryItem["entries"])

                    for RuleRecord in VariantRulesJSON.get("variantrule", []):
                        if "entries" in RuleRecord and isinstance(RuleRecord["entries"], list):
                            ScanEntriesForSpellSlots(RuleRecord["entries"])

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Multiclass Spell Slots from Variant Rules")

        BookPlayerHandbookFilePath: PathLibrary.Path = self.DataDirectoryPath / "book" / "book-phb.json"
        if BookPlayerHandbookFilePath.exists():
            try:
                with open(BookPlayerHandbookFilePath, mode = "r", encoding = "utf-8") as BookPlayerHandbookFile:
                    BookPlayerHandbookJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BookPlayerHandbookFile)

                    def ScanEntriesForAdvancement(EntriesList: Typing.List[Typing.Any]) -> None:
                        for EntryItem in EntriesList:
                            if isinstance(EntryItem, dict):
                                if EntryItem.get("type") == "table" and EntryItem.get("caption") == "Character Advancement":
                                    for RowItem in EntryItem.get("rows", []):
                                        if len(RowItem) >= 2:
                                            ExperiencePointsString: str = str(RowItem[0]).replace(",", "").strip()
                                            LevelString: str = str(RowItem[1]).strip()
                                            if ExperiencePointsString.isdigit() and LevelString.isdigit():
                                                self.LevelExperienceTable[int(LevelString)] = int(ExperiencePointsString)

                                if "entries" in EntryItem and isinstance(EntryItem["entries"], list):
                                    ScanEntriesForAdvancement(EntryItem["entries"])

                    if "data" in BookPlayerHandbookJSON and isinstance(BookPlayerHandbookJSON["data"], list):
                        ScanEntriesForAdvancement(BookPlayerHandbookJSON["data"])

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Advancement Table from Handbook")

        BaseItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items-base.json"
        if BaseItemsFilePath.exists():
            try:
                with open(BaseItemsFilePath, mode = "r", encoding = "utf-8") as BaseItemsFile:
                    BaseItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BaseItemsFile)
                    for BaseItemEntry in BaseItemsJSON.get("baseitem", []):
                        ItemName: Typing.Optional[str] = BaseItemEntry.get("name")
                        ItemType: str = str(BaseItemEntry.get("type", ""))
                        if ItemName and ItemName not in self.ItemsData:
                            self.ItemsData[ItemName] = {
                                "Type": ItemType,
                                "Properties": BaseItemEntry.get("property", []),
                                "DamageExpression": BaseItemEntry.get("dmg1"),
                                "DamageType": BaseItemEntry.get("dmgType"),
                                "Weight": BaseItemEntry.get("weight", 0.0),
                                "Value": BaseItemEntry.get("value", 0.0),
                                "AC": BaseItemEntry.get("ac")
                            }
                            if ItemType.startswith("M") or ItemType.startswith("R"):
                                self.WeaponsData[ItemName] = self.ItemsData[ItemName]

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Base Items from Dataset")

        ItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items.json"
        if ItemsFilePath.exists():
            try:
                with open(ItemsFilePath, mode = "r", encoding = "utf-8") as ItemsFile:
                    ItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ItemsFile)
                    for ItemEntry in ItemsJSON.get("item", []):
                        ItemName: Typing.Optional[str] = ItemEntry.get("name")
                        if ItemName and ItemName not in self.ItemsData:
                            ItemType: str = str(ItemEntry.get("type", ""))
                            BaseItemReference: Typing.Optional[str] = ItemEntry.get("baseItem")
                            self.ItemsData[ItemName] = {
                                "Type": ItemType,
                                "BaseItem": BaseItemReference,
                                "Properties": ItemEntry.get("property", []),
                                "DamageExpression": ItemEntry.get("dmg1"),
                                "DamageType": ItemEntry.get("dmgType"),
                                "Weight": ItemEntry.get("weight", 0.0),
                                "Value": ItemEntry.get("value", 0.0),
                                "AC": ItemEntry.get("ac")
                            }

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Standard Items from Dataset")

    def FindCanonicalClassName(self, ClassNameQuery: str) -> Typing.Optional[str]:
        self.EnsureDataLoaded()
        KnownClassNames: Typing.List[str] = list(self.ClassesData.keys())
        CanonicalName: Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(ClassNameQuery, KnownClassNames, Cutoff = 0.5)
        return CanonicalName

    def GetClassData(self, ClassName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureDataLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if CanonicalName:
            return self.ClassesData.get(CanonicalName)

        return None

    def GetClassHitDie(self, ClassName: str) -> Typing.Optional[int]:
        self.EnsureDataLoaded()
        ClassInformation: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.GetClassData(ClassName)
        if ClassInformation:
            HitDieValue: Typing.Optional[int] = ClassInformation.get("HitDie")
            if HitDieValue is not None:
                return int(HitDieValue)

        return None

    def GetClassSpellcastingAbility(self, ClassName: str, SubclassName: Typing.Optional[str] = None) -> Typing.Optional[str]:
        self.EnsureDataLoaded()
        CanonicalClassName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if not CanonicalClassName:
            return None

        if SubclassName:
            SubclassKey: str = f"{CanonicalClassName}:{SubclassName}"
            for KnownKey, SubclassInformation in self.SubclassesData.items():
                if KnownKey.lower() == SubclassKey.lower() or SubclassKey.lower() in KnownKey.lower():
                    SubclassAbility: Typing.Optional[str] = SubclassInformation.get("SpellcastingAbility")
                    if SubclassAbility:
                        return SubclassAbility

        ClassInformation: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.ClassesData.get(CanonicalClassName)
        if ClassInformation:
            ClassAbility: Typing.Optional[str] = ClassInformation.get("SpellcastingAbility")
            if ClassAbility:
                return ClassAbility

        return None

    def GetCanonicalSpellcastingAbility(self, ClassName: str, SubclassName: Typing.Optional[str] = None) -> Typing.Optional[str]:
        RawAbility: Typing.Optional[str] = self.GetClassSpellcastingAbility(ClassName, SubclassName)
        if not RawAbility:
            return None

        AbilityMapping: Typing.Dict[str, str] = {
            "int": "Intelligence",
            "intelligence": "Intelligence",
            "wis": "Wisdom",
            "wisdom": "Wisdom",
            "cha": "Charisma",
            "charisma": "Charisma",
            "str": "Strength",
            "strength": "Strength",
            "dex": "Dexterity",
            "dexterity": "Dexterity",
            "con": "Constitution",
            "constitution": "Constitution"
        }
        return AbilityMapping.get(RawAbility.lower().strip())

    def GetClassRulesSummary(self) -> Typing.Dict[str, Typing.Any]:
        self.EnsureDataLoaded()
        AbilityMapping: Typing.Dict[str, str] = {
            "int": "Intelligence",
            "intelligence": "Intelligence",
            "wis": "Wisdom",
            "wisdom": "Wisdom",
            "cha": "Charisma",
            "charisma": "Charisma",
            "str": "Strength",
            "strength": "Strength",
            "dex": "Dexterity",
            "dexterity": "Dexterity",
            "con": "Constitution",
            "constitution": "Constitution"
        }

        ClassesSummary: Typing.Dict[str, Typing.Any] = {
        }
        for ClassName, ClassInformation in self.ClassesData.items():
            RawAbility: Typing.Optional[str] = ClassInformation.get("SpellcastingAbility")
            CanonicalAbility: Typing.Optional[str] = AbilityMapping.get(RawAbility.lower().strip()) if RawAbility else None
            ClassesSummary[ClassName] = {
                "SpellcastingAbility": CanonicalAbility,
                "CasterProgression": ClassInformation.get("CasterProgression"),
                "HitDie": ClassInformation.get("HitDie")
            }

        SubclassesSummary: Typing.Dict[str, Typing.Any] = {
        }
        for SubclassKey, SubclassInformation in self.SubclassesData.items():
            RawAbility = SubclassInformation.get("SpellcastingAbility")
            CanonicalAbility = AbilityMapping.get(RawAbility.lower().strip()) if RawAbility else None
            SubclassesSummary[SubclassKey] = {
                "SpellcastingAbility": CanonicalAbility,
                "CasterProgression": SubclassInformation.get("CasterProgression")
            }

        return {
            "Classes": ClassesSummary,
            "Subclasses": SubclassesSummary
        }

    def GetClassCasterProgression(self, ClassName: str, SubclassName: Typing.Optional[str] = None) -> Typing.Optional[str]:
        self.EnsureDataLoaded()
        CanonicalClassName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if not CanonicalClassName:
            return None

        if SubclassName:
            SubclassKey: str = f"{CanonicalClassName}:{SubclassName}"
            for KnownKey, SubclassInformation in self.SubclassesData.items():
                if KnownKey.lower() == SubclassKey.lower() or SubclassKey.lower() in KnownKey.lower():
                    SubclassProgression: Typing.Optional[str] = SubclassInformation.get("CasterProgression")
                    if SubclassProgression:
                        return SubclassProgression

        ClassInformation: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.ClassesData.get(CanonicalClassName)
        if ClassInformation:
            ClassProgression: Typing.Optional[str] = ClassInformation.get("CasterProgression")
            if ClassProgression:
                return ClassProgression

        return None

    def CalculateHitPoints(self, ClassLevels: Typing.List[Typing.Tuple[str, int, bool]], ConstitutionModifier: int) -> Typing.Tuple[int, bool]:
        self.EnsureDataLoaded()
        TotalHitPoints: int = 0
        IsDirty: bool = False

        for ClassName, Level, IsStartingClass in ClassLevels:
            HitDie: Typing.Optional[int] = self.GetClassHitDie(ClassName)
            if HitDie is None:
                HitDie = 8
                IsDirty = True

            AverageHitDie: int = (HitDie // 2) + 1
            if IsStartingClass:
                FirstLevelHitPoints: int = max(1, HitDie + ConstitutionModifier)
                RemainingLevelsHitPoints: int = max(0, Level - 1) * max(1, AverageHitDie + ConstitutionModifier)
                TotalHitPoints += FirstLevelHitPoints + RemainingLevelsHitPoints

            else:
                SubsequentClassHitPoints: int = Level * max(1, AverageHitDie + ConstitutionModifier)
                TotalHitPoints += SubsequentClassHitPoints

        return (TotalHitPoints, IsDirty)

    def CalculateMulticlassSpellSlots(self, ClassProgressionList: Typing.List[Typing.Tuple[str, int, Typing.Optional[str]]]) -> Typing.List[Typing.Tuple[int, int]]:
        self.EnsureDataLoaded()
        CastingClasses: Typing.List[Typing.Tuple[str, int, Typing.Optional[str], str]] = []

        for ClassName, Level, SubclassName in ClassProgressionList:
            CasterProgression: Typing.Optional[str] = self.GetClassCasterProgression(ClassName, SubclassName)
            if CasterProgression and CasterProgression != "pact":
                CastingClasses.append((ClassName, Level, SubclassName, CasterProgression))

        if not CastingClasses:
            return []

        if len(CastingClasses) == 1:
            SingleClassName, SingleLevel, SingleSubclassName, SingleProgressionType = CastingClasses[0]
            CanonicalClassName: Typing.Optional[str] = self.FindCanonicalClassName(SingleClassName)
            if CanonicalClassName:
                if SingleSubclassName:
                    SubclassKey: str = f"{CanonicalClassName}:{SingleSubclassName}"
                    for KnownKey, SubclassInformation in self.SubclassesData.items():
                        if KnownKey.lower() == SubclassKey.lower() or SubclassKey.lower() in KnownKey.lower():
                            SubRows: Typing.List[Typing.List[int]] = SubclassInformation.get("RowsSpellProgression", [])
                            if SubRows and len(SubRows) >= SingleLevel and SingleLevel > 0:
                                SlotRow: Typing.List[int] = SubRows[SingleLevel - 1]
                                return [(SlotIndex + 1, Count) for SlotIndex, Count in enumerate(SlotRow) if Count > 0]

                ClassInformation: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.ClassesData.get(CanonicalClassName)
                if ClassInformation:
                    ClassRows: Typing.List[Typing.List[int]] = ClassInformation.get("RowsSpellProgression", [])
                    if ClassRows and len(ClassRows) >= SingleLevel and SingleLevel > 0:
                        SlotRow = ClassRows[SingleLevel - 1]
                        return [(SlotIndex + 1, Count) for SlotIndex, Count in enumerate(SlotRow) if Count > 0]

        TotalEffectiveCasterLevel: int = 0
        for CasterClassName, Level, CasterSubclassName, ProgressionType in CastingClasses:
            if ProgressionType == "full":
                TotalEffectiveCasterLevel += Level

            elif ProgressionType == "1/2":
                TotalEffectiveCasterLevel += Level // 2

            elif ProgressionType == "artificer":
                if len(CastingClasses) == 1:
                    TotalEffectiveCasterLevel += (Level + 1) // 2

                else:
                    TotalEffectiveCasterLevel += Level // 2

            elif ProgressionType == "1/3":
                TotalEffectiveCasterLevel += Level // 3

        if TotalEffectiveCasterLevel <= 0:
            return []

        ClampedLevel: int = min(20, max(1, TotalEffectiveCasterLevel))
        SlotCounts: Typing.List[int] = self.MulticlassSpellSlotTable.get(ClampedLevel, [0] * 9)
        SpellSlotEntries: Typing.List[Typing.Tuple[int, int]] = []

        for SlotIndex, Count in enumerate(SlotCounts):
            SlotLevel: int = SlotIndex + 1
            if Count > 0:
                SpellSlotEntries.append((SlotLevel, Count))

        return SpellSlotEntries

    def CalculatePactMagicSlots(self, WarlockLevel: int) -> Typing.Optional[Typing.Tuple[int, int]]:
        self.EnsureDataLoaded()
        if WarlockLevel <= 0:
            return None

        ClampedLevel: int = min(20, max(1, WarlockLevel))
        PactData: Typing.Optional[Typing.Tuple[int, int]] = self.WarlockPactMagicTable.get(ClampedLevel)
        return PactData

    def FindCanonicalWeaponName(self, WeaponNameQuery: str) -> Typing.Optional[str]:
        self.EnsureDataLoaded()
        KnownWeaponNames: Typing.List[str] = list(self.WeaponsData.keys())
        CanonicalName: Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(WeaponNameQuery, KnownWeaponNames, Cutoff = 0.5)
        return CanonicalName

    def GetWeaponData(self, WeaponName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureDataLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalWeaponName(WeaponName)
        if CanonicalName:
            return self.WeaponsData.get(CanonicalName)

        ItemMatch: Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(WeaponName, list(self.ItemsData.keys()), Cutoff = 0.5)
        if ItemMatch:
            ItemEntry: Typing.Dict[str, Typing.Any] = self.ItemsData[ItemMatch]
            BaseItemReference: Typing.Optional[str] = ItemEntry.get("BaseItem")
            if BaseItemReference:
                CleanBaseItemReference: str = BaseItemReference.split("|")[0]
                BaseCanonicalName: Typing.Optional[str] = self.FindCanonicalWeaponName(CleanBaseItemReference)
                if BaseCanonicalName:
                    return self.WeaponsData.get(BaseCanonicalName)

            return ItemEntry

        return None

    def IsWeaponRanged(self, WeaponName: str) -> Typing.Optional[bool]:
        self.EnsureDataLoaded()
        WeaponInformation: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.GetWeaponData(WeaponName)
        if WeaponInformation:
            ItemType: str = WeaponInformation.get("Type", "")
            if ItemType.startswith("R"):
                return True

            if ItemType.startswith("M"):
                return False

        return None

    def IsWeaponFinesse(self, WeaponName: str) -> bool:
        self.EnsureDataLoaded()
        WeaponInformation: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.GetWeaponData(WeaponName)
        if WeaponInformation:
            Properties: Typing.List[str] = WeaponInformation.get("Properties", [])
            for PropertyItem in Properties:
                if PropertyItem == "F" or PropertyItem.startswith("F|"):
                    return True

        return False

    def LoadSourcePublicationDates(self) -> None:
        self.SourcePublicationDates = {
        }
        BooksFilePath: PathLibrary.Path = self.DataDirectoryPath / "books.json"
        if BooksFilePath.exists():
            try:
                with open(BooksFilePath, mode = "r", encoding = "utf-8") as BooksFile:
                    BooksJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BooksFile)
                    for BookEntry in BooksJSON.get("book", []):
                        BookID: str = str(BookEntry.get("id") or BookEntry.get("source") or "").upper().strip()
                        PublishedDate: str = str(BookEntry.get("published") or "").strip()
                        if BookID and PublishedDate:
                            self.SourcePublicationDates[BookID] = PublishedDate

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Publication Dates from Books Dataset")

        AdventuresFilePath: PathLibrary.Path = self.DataDirectoryPath / "adventures.json"
        if AdventuresFilePath.exists():
            try:
                with open(AdventuresFilePath, mode = "r", encoding = "utf-8") as AdventuresFile:
                    AdventuresJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(AdventuresFile)
                    for AdventureEntry in AdventuresJSON.get("adventure", []):
                        AdventureID: str = str(AdventureEntry.get("id") or AdventureEntry.get("source") or "").upper().strip()
                        PublishedDate: str = str(AdventureEntry.get("published") or "").strip()
                        if AdventureID and PublishedDate and AdventureID not in self.SourcePublicationDates:
                            self.SourcePublicationDates[AdventureID] = PublishedDate

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Publication Dates from Adventures Dataset")

        if "XPHB" not in self.SourcePublicationDates:
            self.SourcePublicationDates["XPHB"] = "2024-09-17"

        if "XDMG" not in self.SourcePublicationDates:
            self.SourcePublicationDates["XDMG"] = "2024-11-12"

        if "XMM" not in self.SourcePublicationDates:
            self.SourcePublicationDates["XMM"] = "2025-02-18"

    def GetSourcePublicationDate(self, SourceCode: str) -> str:
        NormalizedSource: str = str(SourceCode or "").upper().strip()
        if NormalizedSource in self.SourcePublicationDates:
            return self.SourcePublicationDates[NormalizedSource]

        if NormalizedSource.startswith("X"):
            return "2024-09-17"

        return "1970-01-01"

    def IsSourceNewerOrEqual(self, CandidateSource: str, ExistingSource: str) -> bool:
        CandidateDate: str = self.GetSourcePublicationDate(CandidateSource)
        ExistingDate: str = self.GetSourcePublicationDate(ExistingSource)
        return CandidateDate >= ExistingDate

    def ExtractDamageTypes(self) -> Typing.List[str]:
        FoundDamageTypes: Typing.Set[str] = set()
        TablesFilePath: PathLibrary.Path = self.DataDirectoryPath / "tables.json"
        if TablesFilePath.exists():
            try:
                with open(TablesFilePath, mode = "r", encoding = "utf-8") as TablesFile:
                    TablesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(TablesFile)
                    for TableEntry in TablesJSON.get("table", []):
                        TableName: str = str(TableEntry.get("name") or "").strip().lower()
                        if TableName == "damage types":
                            for RowItem in TableEntry.get("rows", []):
                                if isinstance(RowItem, list) and len(RowItem) > 0:
                                    RawDamageName: str = str(RowItem[0]).strip()
                                    if RawDamageName:
                                        FoundDamageTypes.add(RawDamageName.capitalize())

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Damage Types from Tables Dataset")

        VariantRulesFilePath: PathLibrary.Path = self.DataDirectoryPath / "variantrules.json"
        if VariantRulesFilePath.exists():
            try:
                with open(VariantRulesFilePath, mode = "r", encoding = "utf-8") as VariantRulesFile:
                    VariantRulesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(VariantRulesFile)

                    def ScanVariantRuleEntries(EntriesList: Typing.List[Typing.Any]) -> None:
                        for EntryItem in EntriesList:
                            if isinstance(EntryItem, dict):
                                Caption: str = str(EntryItem.get("caption") or "").lower()
                                if EntryItem.get("type") == "table" and "damage types" in Caption:
                                    for RowItem in EntryItem.get("rows", []):
                                        if isinstance(RowItem, list) and len(RowItem) > 0:
                                            RawDamageName: str = str(RowItem[0]).strip()
                                            if RawDamageName:
                                                FoundDamageTypes.add(RawDamageName.capitalize())

                                if "entries" in EntryItem and isinstance(EntryItem["entries"], list):
                                    ScanVariantRuleEntries(EntryItem["entries"])

                    for RuleRecord in VariantRulesJSON.get("variantrule", []):
                        if "entries" in RuleRecord and isinstance(RuleRecord["entries"], list):
                            ScanVariantRuleEntries(RuleRecord["entries"])

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Damage Types from Variant Rules")

        SpellsDirectory: PathLibrary.Path = self.DataDirectoryPath / "spells"
        if SpellsDirectory.exists():
            for SpellFilePath in SpellsDirectory.glob("spells-*.json"):
                try:
                    with open(SpellFilePath, mode = "r", encoding = "utf-8") as SpellFile:
                        SpellJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(SpellFile)
                        for SpellEntry in SpellJSON.get("spell", []):
                            for DamageItem in SpellEntry.get("damageInflict", []):
                                if DamageItem and isinstance(DamageItem, str):
                                    FoundDamageTypes.add(DamageItem.capitalize())

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Damage Types from Spell File: {SpellFilePath.name}")

        return sorted(list(FoundDamageTypes))

    def ExtractSpecies(self) -> Typing.List[str]:
        SpeciesMap: Typing.Dict[str, Typing.Tuple[str, str]] = {
        }
        RacesFilePath: PathLibrary.Path = self.DataDirectoryPath / "races.json"
        if RacesFilePath.exists():
            try:
                with open(RacesFilePath, mode = "r", encoding = "utf-8") as RacesFile:
                    RacesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(RacesFile)
                    for RaceEntry in RacesJSON.get("race", []):
                        RaceName: Typing.Optional[str] = RaceEntry.get("name")
                        RaceSource: str = str(RaceEntry.get("source") or "PHB")
                        if RaceName and not RaceName.startswith("_"):
                            CleanName: str = RaceName.strip()
                            NormalizedKey: str = CleanName.lower()
                            if NormalizedKey in SpeciesMap:
                                ExistingSource: str = SpeciesMap[NormalizedKey][1]
                                if self.IsSourceNewerOrEqual(RaceSource, ExistingSource):
                                    SpeciesMap[NormalizedKey] = (CleanName, RaceSource)

                            else:
                                SpeciesMap[NormalizedKey] = (CleanName, RaceSource)

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Species from Races Dataset")

        return sorted([Entry[0] for Entry in SpeciesMap.values()])

    def ExtractBackgrounds(self) -> Typing.List[str]:
        BackgroundsMap: Typing.Dict[str, Typing.Tuple[str, str]] = {
        }
        BackgroundsFilePath: PathLibrary.Path = self.DataDirectoryPath / "backgrounds.json"
        if BackgroundsFilePath.exists():
            try:
                with open(BackgroundsFilePath, mode = "r", encoding = "utf-8") as BackgroundsFile:
                    BackgroundsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BackgroundsFile)
                    for BackgroundEntry in BackgroundsJSON.get("background", []):
                        BackgroundName: Typing.Optional[str] = BackgroundEntry.get("name")
                        BackgroundSource: str = str(BackgroundEntry.get("source") or "PHB")
                        if BackgroundName and not BackgroundName.startswith("_"):
                            CleanName: str = BackgroundName.strip()
                            NormalizedKey: str = CleanName.lower()
                            if NormalizedKey in BackgroundsMap:
                                ExistingSource: str = BackgroundsMap[NormalizedKey][1]
                                if self.IsSourceNewerOrEqual(BackgroundSource, ExistingSource):
                                    BackgroundsMap[NormalizedKey] = (CleanName, BackgroundSource)

                            else:
                                BackgroundsMap[NormalizedKey] = (CleanName, BackgroundSource)

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Backgrounds from Dataset")

        return sorted([Entry[0] for Entry in BackgroundsMap.values()])

    def ExtractClassesAndSubclasses(self) -> Typing.Tuple[Typing.List[str], Typing.List[str]]:
        ClassesMap: Typing.Dict[str, Typing.Tuple[str, str]] = {
        }
        SubclassesMap: Typing.Dict[str, Typing.Tuple[str, str]] = {
        }
        ClassDirectory: PathLibrary.Path = self.DataDirectoryPath / "class"
        if ClassDirectory.exists():
            for ClassFilePath in ClassDirectory.glob("class-*.json"):
                if "fluff" in ClassFilePath.name:
                    continue

                try:
                    with open(ClassFilePath, mode = "r", encoding = "utf-8") as ClassFile:
                        ClassJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ClassFile)
                        for ClassEntry in ClassJSON.get("class", []):
                            ClassName: Typing.Optional[str] = ClassEntry.get("name")
                            ClassSource: str = str(ClassEntry.get("source") or "PHB")
                            if ClassName and not ClassName.startswith("_"):
                                CleanName: str = ClassName.strip()
                                NormalizedKey: str = CleanName.lower()
                                if NormalizedKey in ClassesMap:
                                    ExistingSource: str = ClassesMap[NormalizedKey][1]
                                    if self.IsSourceNewerOrEqual(ClassSource, ExistingSource):
                                        ClassesMap[NormalizedKey] = (CleanName, ClassSource)

                                else:
                                    ClassesMap[NormalizedKey] = (CleanName, ClassSource)

                        for SubclassEntry in ClassJSON.get("subclass", []):
                            SubclassName: Typing.Optional[str] = SubclassEntry.get("name")
                            SubclassSource: str = str(SubclassEntry.get("classSource") or SubclassEntry.get("source") or "PHB")
                            if SubclassName and not SubclassName.startswith("_"):
                                CleanName: str = SubclassName.strip()
                                NormalizedKey: str = CleanName.lower()
                                if NormalizedKey in SubclassesMap:
                                    ExistingSource: str = SubclassesMap[NormalizedKey][1]
                                    if self.IsSourceNewerOrEqual(SubclassSource, ExistingSource):
                                        SubclassesMap[NormalizedKey] = (CleanName, SubclassSource)

                                else:
                                    SubclassesMap[NormalizedKey] = (CleanName, SubclassSource)

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Class and Subclass File: {ClassFilePath.name}")

        SortedClasses: Typing.List[str] = sorted([Entry[0] for Entry in ClassesMap.values()])
        SortedSubclasses: Typing.List[str] = sorted([Entry[0] for Entry in SubclassesMap.values()])
        return (SortedClasses, SortedSubclasses)

    def ExtractSpells(self) -> Typing.List[str]:
        SpellsMap: Typing.Dict[str, Typing.Tuple[str, str]] = {
        }
        SpellsDirectory: PathLibrary.Path = self.DataDirectoryPath / "spells"
        if SpellsDirectory.exists():
            for SpellFilePath in SpellsDirectory.glob("spells-*.json"):
                if "fluff" in SpellFilePath.name:
                    continue

                try:
                    with open(SpellFilePath, mode = "r", encoding = "utf-8") as SpellFile:
                        SpellJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(SpellFile)
                        for SpellEntry in SpellJSON.get("spell", []):
                            SpellName: Typing.Optional[str] = SpellEntry.get("name")
                            SpellSource: str = str(SpellEntry.get("source") or "PHB")
                            if SpellName and not SpellName.startswith("_"):
                                CleanName: str = SpellName.strip()
                                NormalizedKey: str = CleanName.lower()
                                if NormalizedKey in SpellsMap:
                                    ExistingSource: str = SpellsMap[NormalizedKey][1]
                                    if self.IsSourceNewerOrEqual(SpellSource, ExistingSource):
                                        SpellsMap[NormalizedKey] = (CleanName, SpellSource)

                                else:
                                    SpellsMap[NormalizedKey] = (CleanName, SpellSource)

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Spells File: {SpellFilePath.name}")

        return sorted([Entry[0] for Entry in SpellsMap.values()])

    def ExtractAllItemsAndProficiencies(self) -> Typing.Tuple[Typing.List[str], Typing.List[str], Typing.List[str], Typing.List[str]]:
        ItemsMap: Typing.Dict[str, Typing.Tuple[str, str, str]] = {
        }
        BaseItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items-base.json"
        if BaseItemsFilePath.exists():
            try:
                with open(BaseItemsFilePath, mode = "r", encoding = "utf-8") as BaseItemsFile:
                    BaseItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BaseItemsFile)
                    for BaseItemEntry in BaseItemsJSON.get("baseitem", []):
                        ItemName: Typing.Optional[str] = BaseItemEntry.get("name")
                        ItemSource: str = str(BaseItemEntry.get("source") or "PHB")
                        ItemType: str = str(BaseItemEntry.get("type") or "")
                        if ItemName and not ItemName.startswith("_"):
                            CleanName: str = ItemName.strip()
                            NormalizedKey: str = CleanName.lower()
                            if NormalizedKey in ItemsMap:
                                ExistingSource: str = ItemsMap[NormalizedKey][1]
                                if self.IsSourceNewerOrEqual(ItemSource, ExistingSource):
                                    ItemsMap[NormalizedKey] = (CleanName, ItemSource, ItemType)

                            else:
                                ItemsMap[NormalizedKey] = (CleanName, ItemSource, ItemType)

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Base Items for Proficiencies")

        ItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items.json"
        if ItemsFilePath.exists():
            try:
                with open(ItemsFilePath, mode = "r", encoding = "utf-8") as ItemsFile:
                    ItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ItemsFile)
                    for ItemEntry in ItemsJSON.get("item", []):
                        ItemName: Typing.Optional[str] = ItemEntry.get("name")
                        ItemSource: str = str(ItemEntry.get("source") or "PHB")
                        ItemType: str = str(ItemEntry.get("type") or "")
                        if ItemName and not ItemName.startswith("_"):
                            CleanName: str = ItemName.strip()
                            NormalizedKey: str = CleanName.lower()
                            if NormalizedKey in ItemsMap:
                                ExistingSource: str = ItemsMap[NormalizedKey][1]
                                if self.IsSourceNewerOrEqual(ItemSource, ExistingSource):
                                    ItemsMap[NormalizedKey] = (CleanName, ItemSource, ItemType)

                            else:
                                ItemsMap[NormalizedKey] = (CleanName, ItemSource, ItemType)

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Standard Items for Proficiencies")

        AllItemsList: Typing.List[str] = sorted([Entry[0] for Entry in ItemsMap.values()])
        WeaponProficienciesSet: Typing.Set[str] = {
            "Simple Weapons",
            "Martial Weapons"
        }
        ArmorProficienciesSet: Typing.Set[str] = {
            "Light Armor",
            "Medium Armor",
            "Heavy Armor",
            "Shields"
        }
        ToolProficienciesSet: Typing.Set[str] = set()

        for ItemTuple in ItemsMap.values():
            NameString: str = ItemTuple[0]
            TypeString: str = ItemTuple[2]
            if TypeString.startswith("M") or TypeString.startswith("R"):
                WeaponProficienciesSet.add(NameString)

            if TypeString in ["LA", "MA", "HA", "S"]:
                ArmorProficienciesSet.add(NameString)

            if TypeString == "T" or "tool" in NameString.lower() or "kit" in NameString.lower() or "supplies" in NameString.lower() or "set" in NameString.lower() or "instrument" in NameString.lower():
                ToolProficienciesSet.add(NameString)

        return (AllItemsList, sorted(list(WeaponProficienciesSet)), sorted(list(ArmorProficienciesSet)), sorted(list(ToolProficienciesSet)))

    def ExtractLanguages(self) -> Typing.List[str]:
        LanguagesMap: Typing.Dict[str, Typing.Tuple[str, str]] = {
        }
        LanguagesFilePath: PathLibrary.Path = self.DataDirectoryPath / "languages.json"
        if LanguagesFilePath.exists():
            try:
                with open(LanguagesFilePath, mode = "r", encoding = "utf-8") as LanguagesFile:
                    LanguagesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(LanguagesFile)
                    for LanguageEntry in LanguagesJSON.get("language", []):
                        LanguageName: Typing.Optional[str] = LanguageEntry.get("name")
                        LanguageSource: str = str(LanguageEntry.get("source") or "PHB")
                        if LanguageName and not LanguageName.startswith("_"):
                            CleanName: str = LanguageName.strip()
                            NormalizedKey: str = CleanName.lower()
                            if NormalizedKey in LanguagesMap:
                                ExistingSource: str = LanguagesMap[NormalizedKey][1]
                                if self.IsSourceNewerOrEqual(LanguageSource, ExistingSource):
                                    LanguagesMap[NormalizedKey] = (CleanName, LanguageSource)

                            else:
                                LanguagesMap[NormalizedKey] = (CleanName, LanguageSource)

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Languages from Dataset")

        return sorted([Entry[0] for Entry in LanguagesMap.values()])

    def ExtractConditions(self) -> Typing.List[str]:
        ConditionsSet: Typing.Set[str] = set()
        ConditionsFilePath: PathLibrary.Path = self.DataDirectoryPath / "conditionsdiseases.json"
        if ConditionsFilePath.exists():
            try:
                with open(ConditionsFilePath, mode = "r", encoding = "utf-8") as ConditionsFile:
                    ConditionsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ConditionsFile)
                    for ConditionEntry in ConditionsJSON.get("condition", []):
                        ConditionName: Typing.Optional[str] = ConditionEntry.get("name")
                        if ConditionName and not ConditionName.startswith("_"):
                            ConditionsSet.add(ConditionName.strip().capitalize())

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Conditions from Dataset")

        return sorted(list(ConditionsSet))

    def BuildRulesDataStore(self) -> Typing.Dict[str, Typing.Any]:
        DamageTypesList: Typing.List[str] = self.ExtractDamageTypes()
        SpeciesList: Typing.List[str] = self.ExtractSpecies()
        BackgroundsList: Typing.List[str] = self.ExtractBackgrounds()
        ClassesList, SubclassesList = self.ExtractClassesAndSubclasses()
        SpellsList: Typing.List[str] = self.ExtractSpells()
        AllItemsList, WeaponsList, ArmorList, ToolsList = self.ExtractAllItemsAndProficiencies()
        LanguagesList: Typing.List[str] = self.ExtractLanguages()
        ConditionsList: Typing.List[str] = self.ExtractConditions()

        DataStore: Typing.Dict[str, Typing.Any] = {
            "GameSystem": "DND5thEdition",
            "Timestamp": TimeLibrary.time(),
            "Species": SpeciesList,
            "Backgrounds": BackgroundsList,
            "Classes": ClassesList,
            "Subclasses": SubclassesList,
            "Spells": SpellsList,
            "Items": AllItemsList,
            "WeaponProficiencies": WeaponsList,
            "ArmorProficiencies": ArmorList,
            "ToolProficiencies": ToolsList,
            "Languages": LanguagesList,
            "DamageTypes": DamageTypesList,
            "Conditions": ConditionsList
        }
        return DataStore

    def GetRulesDataStore(self) -> Typing.Dict[str, Typing.Any]:
        self.EnsureDataLoaded()
        if self.RulesDataStore is None:
            self.RulesDataStore = self.BuildRulesDataStore()

        return self.RulesDataStore

    def GetCantripsList(self) -> Typing.List[str]:
        self.EnsureDataLoaded()
        if self.CantripsList is not None:
            return self.CantripsList

        CantripsSet: Typing.Set[str] = set()
        SpellsDirectory: PathLibrary.Path = self.DataDirectoryPath / "spells"
        if SpellsDirectory.exists():
            for SpellFilePath in SpellsDirectory.glob("spells-*.json"):
                if "fluff" in SpellFilePath.name:
                    continue

                try:
                    with open(SpellFilePath, mode = "r", encoding = "utf-8") as SpellFile:
                        SpellJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(SpellFile)
                        for SpellEntry in SpellJSON.get("spell", []):
                            SpellLevel: Typing.Any = SpellEntry.get("level")
                            if (SpellLevel == 0) or (SpellLevel == "0"):
                                SpellName: Typing.Optional[str] = SpellEntry.get("name")
                                if SpellName and not SpellName.startswith("_"):
                                    CantripsSet.add(SpellName.strip().lower())

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Cantrips: {SpellFilePath.name}")

        self.CantripsList = sorted(list(CantripsSet))
        return self.CantripsList

    def GetEquipmentRulesData(self) -> Typing.Dict[str, Typing.Any]:
        self.EnsureDataLoaded()
        if self.EquipmentRulesData is not None:
            return self.EquipmentRulesData

        ItemWeights: Typing.Dict[str, float] = {
        }
        ArmorData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        for ItemName, ItemInformation in self.ItemsData.items():
            CleanName: str = ItemName.lower().strip()
            ItemWeight: float = float(ItemInformation.get("Weight") or 0.0)
            if ItemWeight > 0.0:
                ItemWeights[CleanName] = ItemWeight

            ItemType: str = str(ItemInformation.get("Type") or "").upper()
            ItemAC: Typing.Optional[int] = ItemInformation.get("AC")
            if (ItemAC is not None) or (ItemType in ("HA", "MA", "LA", "S")):
                ArmorCategory: str = "light"
                if ItemType == "HA":
                    ArmorCategory = "heavy"

                elif ItemType == "MA":
                    ArmorCategory = "medium"

                elif ItemType == "LA":
                    ArmorCategory = "light"

                elif ItemType == "S":
                    ArmorCategory = "shield"

                ResolvedAC: int = int(ItemAC) if (ItemAC is not None) else (2 if (ArmorCategory == "shield") else 11)
                ArmorData[CleanName] = {
                    "BaseAC": ResolvedAC,
                    "ArmorType": ArmorCategory
                }

        self.EquipmentRulesData = {
            "Weights": ItemWeights,
            "Armors": ArmorData
        }
        return self.EquipmentRulesData

    def EnsureSpellsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.SpellsDetailData:
            return

        SpellsDirectory: PathLibrary.Path = self.DataDirectoryPath / "spells"
        if SpellsDirectory.exists():
            for SpellFilePath in SpellsDirectory.glob("spells-*.json"):
                if "fluff" in SpellFilePath.name:
                    continue

                try:
                    with open(SpellFilePath, mode = "r", encoding = "utf-8") as SpellFile:
                        SpellJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(SpellFile)
                        for SpellEntry in SpellJSON.get("spell", []):
                            SpellName: Typing.Optional[str] = SpellEntry.get("name")
                            SpellSource: str = str(SpellEntry.get("source") or "PHB")
                            if SpellName and not SpellName.startswith("_"):
                                CleanName: str = SpellName.strip()
                                if CleanName in self.SpellsDetailData:
                                    ExistingSource: str = str(self.SpellsDetailData[CleanName].get("source") or "PHB")
                                    if self.IsSourceNewerOrEqual(SpellSource, ExistingSource):
                                        self.SpellsDetailData[CleanName] = SpellEntry

                                else:
                                    self.SpellsDetailData[CleanName] = SpellEntry

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Spells File for Statblocks: {SpellFilePath.name}")

            for CanonicalSpellName in self.SpellsDetailData.keys():
                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalSpellName).lower()
                self.SpellsNormalizedMap[NormalizedKey] = CanonicalSpellName

    def FindCanonicalSpellName(self, SpellNameQuery: str) -> Typing.Optional[str]:
        self.EnsureSpellsLoaded()
        CleanQuery: str = SpellNameQuery.strip()
        if CleanQuery in self.SpellsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.SpellsNormalizedMap:
            return self.SpellsNormalizedMap[NormalizedQuery]

        return None

    def GetSpellData(self, SpellName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureSpellsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalSpellName(SpellName)
        if CanonicalName:
            return self.SpellsDetailData.get(CanonicalName)

        return None

    def EnsureMonstersLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.MonstersDetailData:
            return

        BestiaryDirectory: PathLibrary.Path = self.DataDirectoryPath / "bestiary"
        if BestiaryDirectory.exists():
            for BestiaryFilePath in BestiaryDirectory.glob("bestiary-*.json"):
                if "fluff" in BestiaryFilePath.name:
                    continue

                try:
                    with open(BestiaryFilePath, mode = "r", encoding = "utf-8") as BestiaryFile:
                        BestiaryJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BestiaryFile)
                        for MonsterEntry in BestiaryJSON.get("monster", []):
                            MonsterName: Typing.Optional[str] = MonsterEntry.get("name")
                            MonsterSource: str = str(MonsterEntry.get("source") or "MM")
                            if MonsterName and not MonsterName.startswith("_"):
                                CleanName: str = MonsterName.strip()
                                if CleanName in self.MonstersDetailData:
                                    ExistingSource: str = str(self.MonstersDetailData[CleanName].get("source") or "MM")
                                    if self.IsSourceNewerOrEqual(MonsterSource, ExistingSource):
                                        self.MonstersDetailData[CleanName] = MonsterEntry

                                else:
                                    self.MonstersDetailData[CleanName] = MonsterEntry

                except Exception as ParsingException:
                    DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Failed to Parse Bestiary File for Statblocks: {BestiaryFilePath.name}")

            for CanonicalMonsterName in self.MonstersDetailData.keys():
                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalMonsterName).lower()
                self.MonstersNormalizedMap[NormalizedKey] = CanonicalMonsterName

    def FindCanonicalMonsterName(self, MonsterNameQuery: str) -> Typing.Optional[str]:
        self.EnsureMonstersLoaded()
        CleanQuery: str = MonsterNameQuery.strip()
        if CleanQuery in self.MonstersDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.MonstersNormalizedMap:
            return self.MonstersNormalizedMap[NormalizedQuery]

        return None

    def GetMonsterData(self, MonsterName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureMonstersLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalMonsterName(MonsterName)
        if CanonicalName:
            return self.MonstersDetailData.get(CanonicalName)

        return None

    def EnsureItemsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.ItemsDetailData:
            return

        BaseItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items-base.json"
        if BaseItemsFilePath.exists():
            try:
                with open(BaseItemsFilePath, mode = "r", encoding = "utf-8") as BaseItemsFile:
                    BaseItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BaseItemsFile)
                    for BaseItemEntry in BaseItemsJSON.get("baseitem", []):
                        ItemName: Typing.Optional[str] = BaseItemEntry.get("name")
                        ItemSource: str = str(BaseItemEntry.get("source") or "PHB")
                        if ItemName and not ItemName.startswith("_"):
                            CleanName: str = ItemName.strip()
                            if CleanName in self.ItemsDetailData:
                                ExistingSource: str = str(self.ItemsDetailData[CleanName].get("source") or "PHB")
                                if self.IsSourceNewerOrEqual(ItemSource, ExistingSource):
                                    self.ItemsDetailData[CleanName] = BaseItemEntry

                            else:
                                self.ItemsDetailData[CleanName] = BaseItemEntry

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Base Items for Statblocks")

        ItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items.json"
        if ItemsFilePath.exists():
            try:
                with open(ItemsFilePath, mode = "r", encoding = "utf-8") as ItemsFile:
                    ItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ItemsFile)
                    for ItemEntry in ItemsJSON.get("item", []):
                        ItemName: Typing.Optional[str] = ItemEntry.get("name")
                        ItemSource: str = str(ItemEntry.get("source") or "PHB")
                        if ItemName and not ItemName.startswith("_"):
                            CleanName: str = ItemName.strip()
                            if CleanName in self.ItemsDetailData:
                                ExistingSource: str = str(self.ItemsDetailData[CleanName].get("source") or "PHB")
                                if self.IsSourceNewerOrEqual(ItemSource, ExistingSource):
                                    self.ItemsDetailData[CleanName] = ItemEntry

                            else:
                                self.ItemsDetailData[CleanName] = ItemEntry

            except Exception as ParsingException:
                DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = "Failed to Parse Standard Items for Statblocks")

        for CanonicalItemName in self.ItemsDetailData.keys():
            NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalItemName).lower()
            self.ItemsNormalizedMap[NormalizedKey] = CanonicalItemName

    def FindCanonicalItemName(self, ItemNameQuery: str) -> Typing.Optional[str]:
        self.EnsureItemsLoaded()
        CleanQuery: str = ItemNameQuery.strip()
        if CleanQuery in self.ItemsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.ItemsNormalizedMap:
            return self.ItemsNormalizedMap[NormalizedQuery]

        return None

    def GetItemData(self, ItemName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureItemsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalItemName(ItemName)
        if CanonicalName:
            return self.ItemsDetailData.get(CanonicalName)

        return None
