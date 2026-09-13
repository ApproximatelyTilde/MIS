import json                                as JavaScriptObjectNotation
import pathlib                             as PathLibrary
import re                                 as RegularExpressions
import time                               as TimeLibrary
import typing                             as Typing
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
                except Exception:
                    pass

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
            except Exception:
                pass

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
            except Exception:
                pass

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
                                "Value": BaseItemEntry.get("value", 0.0)
                            }
                            if ItemType.startswith("M") or ItemType.startswith("R"):
                                self.WeaponsData[ItemName] = self.ItemsData[ItemName]
            except Exception:
                pass

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
                                "Value": ItemEntry.get("value", 0.0)
                            }
            except Exception:
                pass

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
            SingleClassName, SingleLevel, SingleSubclassName, _ = CastingClasses[0]
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
        for _, Level, _, ProgressionType in CastingClasses:
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
