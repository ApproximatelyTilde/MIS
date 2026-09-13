import copy                               as CopyLibrary
import json                               as JavaScriptObjectNotation
import pathlib                            as PathLibrary
import re                                 as RegularExpressions
import time                               as TimeLibrary
import typing                             as Typing
import Server.Services.DebugService       as Debug
import Server.Services.FuzzySearchService as FuzzySearch

CACHE_EXPIRATION_SECONDS: int = 1209600

class External5ETools:
    def __init__(self, DataDirectoryPath: Typing.Optional[PathLibrary.Path] = None) -> None:
        if DataDirectoryPath is None:
            self.DataDirectoryPath: PathLibrary.Path = PathLibrary.Path(__file__).resolve().parent.parent / "External" / "5eTools" / "data"

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
        self.SourceDisplayNames: Typing.Dict[str, str] = {
        }
        self.FeatsDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.FeatsVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.FeatsSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.FeatsNormalizedMap: Typing.Dict[str, str] = {
        }
        self.OptionsDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.OptionsVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.OptionsSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.OptionsNormalizedMap: Typing.Dict[str, str] = {
        }
        self.RulesDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.RulesVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.RulesSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.RulesNormalizedMap: Typing.Dict[str, str] = {
        }
        self.BackgroundsDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.BackgroundsVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.BackgroundsSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.BackgroundsNormalizedMap: Typing.Dict[str, str] = {
        }
        self.SpeciesDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.SpeciesVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.SpeciesSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.SpeciesNormalizedMap: Typing.Dict[str, str] = {
        }
        self.ConditionsDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ConditionsVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.ConditionsSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ConditionsNormalizedMap: Typing.Dict[str, str] = {
        }
        self.DeitiesDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.DeitiesVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.DeitiesSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.DeitiesNormalizedMap: Typing.Dict[str, str] = {
        }
        self.VehiclesDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.VehiclesVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.VehiclesSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.VehiclesNormalizedMap: Typing.Dict[str, str] = {
        }
        self.ClassesDetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ClassesVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.ClassesSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ClassesDetailNormalizedMap: Typing.Dict[str, str] = {
        }
        self.SpellsVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.SpellsSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.MonstersVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.MonstersSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
        }
        self.ItemsVersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        self.ItemsSourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {
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
        self.FeatsDetailData = {
        }
        self.FeatsVersionsData = {
        }
        self.FeatsSourceKeyedData = {
        }
        self.FeatsNormalizedMap = {
        }
        self.OptionsDetailData = {
        }
        self.OptionsVersionsData = {
        }
        self.OptionsSourceKeyedData = {
        }
        self.OptionsNormalizedMap = {
        }
        self.RulesDetailData = {
        }
        self.RulesVersionsData = {
        }
        self.RulesSourceKeyedData = {
        }
        self.RulesNormalizedMap = {
        }
        self.BackgroundsDetailData = {
        }
        self.BackgroundsVersionsData = {
        }
        self.BackgroundsSourceKeyedData = {
        }
        self.BackgroundsNormalizedMap = {
        }
        self.SpeciesDetailData = {
        }
        self.SpeciesVersionsData = {
        }
        self.SpeciesSourceKeyedData = {
        }
        self.SpeciesNormalizedMap = {
        }
        self.ConditionsDetailData = {
        }
        self.ConditionsVersionsData = {
        }
        self.ConditionsSourceKeyedData = {
        }
        self.ConditionsNormalizedMap = {
        }
        self.DeitiesDetailData = {
        }
        self.DeitiesVersionsData = {
        }
        self.DeitiesSourceKeyedData = {
        }
        self.DeitiesNormalizedMap = {
        }
        self.VehiclesDetailData = {
        }
        self.VehiclesVersionsData = {
        }
        self.VehiclesSourceKeyedData = {
        }
        self.VehiclesNormalizedMap = {
        }
        self.ClassesDetailData = {
        }
        self.ClassesVersionsData = {
        }
        self.ClassesSourceKeyedData = {
        }
        self.ClassesDetailNormalizedMap = {
        }
        self.SpellsVersionsData = {
        }
        self.SpellsSourceKeyedData = {
        }
        self.MonstersVersionsData = {
        }
        self.MonstersSourceKeyedData = {
        }
        self.ItemsVersionsData = {
        }
        self.ItemsSourceKeyedData = {
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
                            ClassSource: str = str(ClassEntry.get("source") or "PHB")
                            if ClassName and (not ClassName.startswith("_")):
                                CleanClassName: str = ClassName.strip()
                                ShouldUpdateClass: bool = False
                                if CleanClassName not in self.ClassesData:
                                    ShouldUpdateClass = True

                                else:
                                    ExistingClassSource: str = str(self.ClassesData[CleanClassName].get("Source") or "PHB")
                                    if self.IsSourceNewerOrEqual(ClassSource, ExistingClassSource):
                                        ShouldUpdateClass = True

                                if ShouldUpdateClass:
                                    ClassSpellProgression: Typing.List[Typing.List[int]] = []
                                    for TableGroup in ClassEntry.get("classTableGroups", []):
                                        if "rowsSpellProgression" in TableGroup:
                                            ClassSpellProgression = TableGroup.get("rowsSpellProgression", [])

                                        if ("subclasses" in TableGroup) and ("rowsSpellProgression" in TableGroup):
                                            SubclassSpellProgression = TableGroup.get("rowsSpellProgression", [])
                                            for GroupSubclass in TableGroup.get("subclasses", []):
                                                SubclassName: Typing.Optional[str] = GroupSubclass.get("name")
                                                if SubclassName:
                                                    Key: str = f"{CleanClassName}:{SubclassName}"
                                                    if Key not in self.SubclassesData:
                                                        self.SubclassesData[Key] = {
                                                            "CasterProgression"   : "1/3",
                                                            "SpellcastingAbility" : None,
                                                            "RowsSpellProgression": SubclassSpellProgression,
                                                            "Raw"                 : GroupSubclass
                                                        }

                                                    else:
                                                        self.SubclassesData[Key]["RowsSpellProgression"] = SubclassSpellProgression

                                        ColumnLabelsList: Typing.List[str] = [str(LabelItem).lower() for LabelItem in TableGroup.get("colLabels", [])]
                                        if ("spell slots" in ColumnLabelsList) and ("slot level" in ColumnLabelsList):
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

                                    self.ClassesData[CleanClassName] = {
                                        "HitDie"              : ClassEntry.get("hd", {}).get("faces"),
                                        "CasterProgression"   : ClassEntry.get("casterProgression"),
                                        "SpellcastingAbility" : ClassEntry.get("spellcastingAbility"),
                                        "RowsSpellProgression": ClassSpellProgression,
                                        "Source"              : ClassSource,
                                        "Raw"                 : ClassEntry
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
                                        "CasterProgression"   : SubclassEntry.get("casterProgression"),
                                        "SpellcastingAbility" : SubclassEntry.get("spellcastingAbility"),
                                        "RowsSpellProgression": SubclassSpellProgression,
                                        "Raw"                 : SubclassEntry
                                    }

                                else:
                                    if SubclassEntry.get("casterProgression"):
                                        self.SubclassesData[SubclassKey]["CasterProgression"] = SubclassEntry.get("casterProgression")

                                    if SubclassEntry.get("spellcastingAbility"):
                                        self.SubclassesData[SubclassKey]["SpellcastingAbility"] = SubclassEntry.get("spellcastingAbility")

                                    if SubclassSpellProgression:
                                        self.SubclassesData[SubclassKey]["RowsSpellProgression"] = SubclassSpellProgression

                except Exception as ParsingException:
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Class File: {ClassFilePath.name}")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Multiclass Spell Slots from Variant Rules")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Advancement Table from Handbook")

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
                                "Type"            : ItemType,
                                "Properties"      : BaseItemEntry.get("property", []),
                                "DamageExpression": BaseItemEntry.get("dmg1"),
                                "DamageType"      : BaseItemEntry.get("dmgType"),
                                "Weight"          : BaseItemEntry.get("weight", 0.0),
                                "Value"           : BaseItemEntry.get("value", 0.0),
                                "AC"              : BaseItemEntry.get("ac")
                            }
                            if ItemType.startswith("M") or ItemType.startswith("R"):
                                self.WeaponsData[ItemName] = self.ItemsData[ItemName]

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Base Items from Dataset")

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
                                "Type"            : ItemType,
                                "BaseItem"        : BaseItemReference,
                                "Properties"      : ItemEntry.get("property", []),
                                "DamageExpression": ItemEntry.get("dmg1"),
                                "DamageType"      : ItemEntry.get("dmgType"),
                                "Weight"          : ItemEntry.get("weight", 0.0),
                                "Value"           : ItemEntry.get("value", 0.0),
                                "AC"              : ItemEntry.get("ac")
                            }

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Standard Items from Dataset")

    def FindCanonicalClassName(self, ClassNameQuery: str) -> Typing.Optional[str]:
        self.EnsureDataLoaded()
        KnownClassNames: Typing.List[str] = list(self.ClassesData.keys())
        CanonicalName: Typing.Optional[str] = FuzzySearch.FuzzySearchService.FindBestMatch(ClassNameQuery, KnownClassNames, Cutoff = 0.5)
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
            CleanSubclass: str = SubclassName.strip().lower()
            for KnownKey, SubclassInformation in self.SubclassesData.items():
                if ":" in KnownKey:
                    KnownClass, KnownSubclass = KnownKey.split(":", 1)
                    if KnownClass.strip().lower() == CanonicalClassName.lower():
                        CleanKnownSubclass: str = KnownSubclass.strip().lower()
                        IsMatch: bool = (CleanKnownSubclass == CleanSubclass) or ((len(CleanSubclass) >= 3) and (CleanKnownSubclass.endswith(f" {CleanSubclass}") or CleanKnownSubclass.startswith(f"{CleanSubclass} ")))
                        if IsMatch:
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
            "int"         : "Intelligence",
            "intelligence": "Intelligence",
            "wis"         : "Wisdom",
            "wisdom"      : "Wisdom",
            "cha"         : "Charisma",
            "charisma"    : "Charisma",
            "str"         : "Strength",
            "strength"    : "Strength",
            "dex"         : "Dexterity",
            "dexterity"   : "Dexterity",
            "con"         : "Constitution",
            "constitution": "Constitution"
        }
        return AbilityMapping.get(RawAbility.lower().strip())

    def GetClassRulesSummary(self) -> Typing.Dict[str, Typing.Any]:
        self.EnsureDataLoaded()
        AbilityMapping: Typing.Dict[str, str] = {
            "int"         : "Intelligence",
            "intelligence": "Intelligence",
            "wis"         : "Wisdom",
            "wisdom"      : "Wisdom",
            "cha"         : "Charisma",
            "charisma"    : "Charisma",
            "str"         : "Strength",
            "strength"    : "Strength",
            "dex"         : "Dexterity",
            "dexterity"   : "Dexterity",
            "con"         : "Constitution",
            "constitution": "Constitution"
        }

        ClassesSummary: Typing.Dict[str, Typing.Any] = {
        }
        for ClassName, ClassInformation in self.ClassesData.items():
            RawAbility: Typing.Optional[str] = ClassInformation.get("SpellcastingAbility")
            CanonicalAbility: Typing.Optional[str] = (AbilityMapping.get(RawAbility.lower().strip())) if (bool(RawAbility)) else (None)
            ClassesSummary[ClassName] = {
                "SpellcastingAbility": CanonicalAbility,
                "CasterProgression"  : ClassInformation.get("CasterProgression"),
                "HitDie"             : ClassInformation.get("HitDie")
            }

        SubclassesSummary: Typing.Dict[str, Typing.Any] = {
        }
        for SubclassKey, SubclassInformation in self.SubclassesData.items():
            RawAbility = SubclassInformation.get("SpellcastingAbility")
            CanonicalAbility = (AbilityMapping.get(RawAbility.lower().strip())) if (bool(RawAbility)) else (None)
            SubclassesSummary[SubclassKey] = {
                "SpellcastingAbility": CanonicalAbility,
                "CasterProgression"  : SubclassInformation.get("CasterProgression")
            }

        return {
            "Classes"   : ClassesSummary,
            "Subclasses": SubclassesSummary
        }

    def GetClassCasterProgression(self, ClassName: str, SubclassName: Typing.Optional[str] = None) -> Typing.Optional[str]:
        self.EnsureDataLoaded()
        CanonicalClassName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if not CanonicalClassName:
            return None

        if SubclassName:
            CleanSubclass: str = SubclassName.strip().lower()
            for KnownKey, SubclassInformation in self.SubclassesData.items():
                if ":" in KnownKey:
                    KnownClass, KnownSubclass = KnownKey.split(":", 1)
                    if KnownClass.strip().lower() == CanonicalClassName.lower():
                        CleanKnownSubclass: str = KnownSubclass.strip().lower()
                        IsMatch: bool = (CleanKnownSubclass == CleanSubclass) or ((len(CleanSubclass) >= 3) and (CleanKnownSubclass.endswith(f" {CleanSubclass}") or CleanKnownSubclass.startswith(f"{CleanSubclass} ")))
                        if IsMatch:
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
                return (0, True)

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
                    CleanSubclass: str = SingleSubclassName.strip().lower()
                    for KnownKey, SubclassInformation in self.SubclassesData.items():
                        if ":" in KnownKey:
                            KnownClass, KnownSubclass = KnownKey.split(":", 1)
                            if KnownClass.strip().lower() == CanonicalClassName.lower():
                                CleanKnownSubclass: str = KnownSubclass.strip().lower()
                                IsMatch: bool = (CleanKnownSubclass == CleanSubclass) or ((len(CleanSubclass) >= 3) and (CleanKnownSubclass.endswith(f" {CleanSubclass}") or CleanKnownSubclass.startswith(f"{CleanSubclass} ")))
                                if IsMatch:
                                    SubRows: Typing.List[Typing.List[int]] = SubclassInformation.get("RowsSpellProgression", [])
                                    if (SubRows) and (len(SubRows) >= SingleLevel) and (SingleLevel > 0):
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
        CanonicalName: Typing.Optional[str] = FuzzySearch.FuzzySearchService.FindBestMatch(WeaponNameQuery, KnownWeaponNames, Cutoff = 0.5)
        return CanonicalName

    def GetWeaponData(self, WeaponName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureDataLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalWeaponName(WeaponName)
        if CanonicalName:
            return self.WeaponsData.get(CanonicalName)

        ItemMatch: Typing.Optional[str] = FuzzySearch.FuzzySearchService.FindBestMatch(WeaponName, list(self.ItemsData.keys()), Cutoff = 0.5)
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
        self.SourceDisplayNames = {
        }
        BooksFilePath: PathLibrary.Path = self.DataDirectoryPath / "books.json"
        if BooksFilePath.exists():
            try:
                with open(BooksFilePath, mode = "r", encoding = "utf-8") as BooksFile:
                    BooksJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BooksFile)
                    for BookEntry in BooksJSON.get("book", []):
                        BookID: str = str(BookEntry.get("id") or BookEntry.get("source") or "").upper().strip()
                        PublishedDate: str = str(BookEntry.get("published") or "").strip()
                        BookName: str = str(BookEntry.get("name") or "").strip()
                        if BookID and PublishedDate:
                            self.SourcePublicationDates[BookID] = PublishedDate

                        if BookID and BookName:
                            self.SourceDisplayNames[BookID] = BookName

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Publication Dates from Books Dataset")

        AdventuresFilePath: PathLibrary.Path = self.DataDirectoryPath / "adventures.json"
        if AdventuresFilePath.exists():
            try:
                with open(AdventuresFilePath, mode = "r", encoding = "utf-8") as AdventuresFile:
                    AdventuresJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(AdventuresFile)
                    for AdventureEntry in AdventuresJSON.get("adventure", []):
                        AdventureID: str = str(AdventureEntry.get("id") or AdventureEntry.get("source") or "").upper().strip()
                        PublishedDate: str = str(AdventureEntry.get("published") or "").strip()
                        AdventureName: str = str(AdventureEntry.get("name") or "").strip()
                        if AdventureID and PublishedDate and (AdventureID not in self.SourcePublicationDates):
                            self.SourcePublicationDates[AdventureID] = PublishedDate

                        if AdventureID and AdventureName and (AdventureID not in self.SourceDisplayNames):
                            self.SourceDisplayNames[AdventureID] = AdventureName

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Publication Dates from Adventures Dataset")

        if "XPHB" not in self.SourcePublicationDates:
            self.SourcePublicationDates["XPHB"] = "2024-09-17"

        if "XDMG" not in self.SourcePublicationDates:
            self.SourcePublicationDates["XDMG"] = "2024-11-12"

        if "XMM" not in self.SourcePublicationDates:
            self.SourcePublicationDates["XMM"] = "2025-02-18"

        if "XPHB" not in self.SourceDisplayNames:
            self.SourceDisplayNames["XPHB"] = "Player's Handbook (2024)"

        if "XDMG" not in self.SourceDisplayNames:
            self.SourceDisplayNames["XDMG"] = "Dungeon Master's Guide (2024)"

        if "XMM" not in self.SourceDisplayNames:
            self.SourceDisplayNames["XMM"] = "Monster Manual (2025)"

    def GetSourceDisplayName(self, SourceCode: str) -> str:
        NormalizedSource: str = str(SourceCode or "").upper().strip()
        if NormalizedSource in self.SourceDisplayNames:
            return self.SourceDisplayNames[NormalizedSource]

        return NormalizedSource

    def GetSourcePublicationYear(self, SourceCode: str) -> int:
        DateString: str = self.GetSourcePublicationDate(SourceCode)
        if (DateString == "2099-01-01"):
            NormalizedSource: str = str(SourceCode or "").upper().strip()
            if (NormalizedSource == "XMM"):
                return 2025

            return 2024

        if ("-" in DateString):
            YearPart: str = DateString.split("-")[0]
            if YearPart.isdigit():
                return int(YearPart)

        return 0

    def IsSource2024(self, SourceCode: str) -> bool:
        NormalizedSource: str = str(SourceCode or "").upper().strip()
        if (NormalizedSource == "XGE"):
            return False

        if (NormalizedSource in ("XPHB", "XDMG", "XMM")):
            return True

        if NormalizedSource.startswith("X"):
            return True

        return False

    def ApplyModToEntries(self, EntriesList: Typing.List[Typing.Any], ModEntry: Typing.Dict[str, Typing.Any]) -> Typing.List[Typing.Any]:
        Mode: str = str(ModEntry.get("mode", ""))
        ReplaceTarget: Typing.Optional[str] = ModEntry.get("replace")
        ItemsPayload: Typing.Any = ModEntry.get("items")
        ResultEntries: Typing.List[Typing.Any] = []

        if (Mode == "replaceArr"):
            for Entry in EntriesList:
                IsMatch: bool = False
                if isinstance(Entry, dict) and (Entry.get("name") == ReplaceTarget):
                    IsMatch = True

                elif isinstance(Entry, str) and (Entry == ReplaceTarget):
                    IsMatch = True

                if IsMatch:
                    if isinstance(ItemsPayload, list):
                        ResultEntries.extend(ItemsPayload)

                    else:
                        ResultEntries.append(ItemsPayload)

                else:
                    ResultEntries.append(Entry)

            return ResultEntries

        elif (Mode == "appendArr"):
            ResultEntries = list(EntriesList)
            if isinstance(ItemsPayload, list):
                ResultEntries.extend(ItemsPayload)

            else:
                ResultEntries.append(ItemsPayload)

            return ResultEntries

        elif (Mode == "insertArr"):
            ResultEntries = list(EntriesList)
            InsertIndex: int = int(ModEntry.get("index", len(ResultEntries)))
            if isinstance(ItemsPayload, list):
                for ItemOffset, SingleItem in enumerate(ItemsPayload):
                    ResultEntries.insert(InsertIndex + ItemOffset, SingleItem)

            else:
                ResultEntries.insert(InsertIndex, ItemsPayload)

            return ResultEntries

        elif (Mode == "removeArr"):
            TargetNames: Typing.List[str] = list(ModEntry.get("names", []))
            if ReplaceTarget:
                TargetNames.append(ReplaceTarget)

            for Entry in EntriesList:
                ShouldRemove: bool = False
                if isinstance(Entry, dict) and (Entry.get("name") in TargetNames):
                    ShouldRemove = True

                elif isinstance(Entry, str) and (Entry in TargetNames):
                    ShouldRemove = True

                if not ShouldRemove:
                    ResultEntries.append(Entry)

            return ResultEntries

        elif (Mode == "replaceTxt"):
            SearchText: str = str(ModEntry.get("replace", ""))
            ReplacementText: str = str(ModEntry.get("with", ""))
            for Entry in EntriesList:
                if isinstance(Entry, str):
                    ResultEntries.append(Entry.replace(SearchText, ReplacementText))

                else:
                    ResultEntries.append(Entry)

            return ResultEntries

        return EntriesList

    def ResolveCopyDirectives(self, RawEntry: Typing.Dict[str, Typing.Any], LookupDictionary: Typing.Dict[Typing.Tuple[str, str], Typing.Dict[str, Typing.Any]]) -> Typing.Dict[str, Typing.Any]:
        if ("_copy" not in RawEntry) or (not isinstance(RawEntry.get("_copy"), dict)):
            return RawEntry

        CopyInformation: Typing.Dict[str, Typing.Any] = RawEntry["_copy"]
        TargetName: str = str(CopyInformation.get("name", "")).strip().lower()
        TargetSource: str = str(CopyInformation.get("source", "")).strip().lower()
        BaseEntry: Typing.Optional[Typing.Dict[str, Typing.Any]] = LookupDictionary.get((TargetName, TargetSource))
        if not BaseEntry:
            return RawEntry

        ResolvedBase: Typing.Dict[str, Typing.Any] = self.ResolveCopyDirectives(CopyLibrary.deepcopy(BaseEntry), LookupDictionary)
        ModDirectives: Typing.Dict[str, Typing.Any] = CopyInformation.get("_mod", {})
        if isinstance(ModDirectives, dict):
            for PropertyName, ModList in ModDirectives.items():
                if (PropertyName in ResolvedBase) and isinstance(ModList, list):
                    for SingleMod in ModList:
                        if isinstance(SingleMod, dict):
                            ResolvedBase[PropertyName] = self.ApplyModToEntries(ResolvedBase.get(PropertyName, []), SingleMod)

        for AttributeKey, AttributeValue in RawEntry.items():
            if AttributeKey not in ("_copy", "_mod"):
                ResolvedBase[AttributeKey] = AttributeValue

        return ResolvedBase

    def BuildVersionMetadataList(self, VersionsList: Typing.List[Typing.Dict[str, Typing.Any]], PrimarySource: str) -> Typing.List[Typing.Dict[str, Typing.Any]]:
        MetadataList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        for VersionRecord in VersionsList:
            SourceCode: str = str(VersionRecord.get("source") or "PHB")
            MetadataList.append({
                "Source"           : SourceCode,
                "SourceDisplayName": self.GetSourceDisplayName(SourceCode),
                "PublicationYear"  : self.GetSourcePublicationYear(SourceCode),
                "IsPrimary"        : (SourceCode == PrimarySource),
                "IsModern2024"     : self.IsSource2024(SourceCode),
                "IsLegacy"         : not self.IsSource2024(SourceCode),
                "Data"             : VersionRecord
            })

        return MetadataList

    def GetSourcePublicationDate(self, SourceCode: str) -> str:
        NormalizedSource: str = str(SourceCode or "").upper().strip()
        if NormalizedSource.startswith("X"):
            return "2099-01-01"

        if NormalizedSource in self.SourcePublicationDates:
            return self.SourcePublicationDates[NormalizedSource]

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Damage Types from Tables Dataset")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Damage Types from Variant Rules")

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
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Damage Types from Spell File: {SpellFilePath.name}")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Species from Races Dataset")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Backgrounds from Dataset")

        return sorted([Entry[0] for Entry in BackgroundsMap.values()])

    def FindCanonicalBackgroundName(self, BackgroundQuery: str) -> Typing.Optional[str]:
        CleanQuery: str = BackgroundQuery.strip()
        if not CleanQuery:
            return None

        KnownBackgrounds: Typing.List[str] = self.ExtractBackgrounds()
        return FuzzySearch.FuzzySearchService.FindBestMatch(CleanQuery, KnownBackgrounds, Cutoff = 0.5)

    def GetClassCanonicalSourceMap(self) -> Typing.Dict[str, str]:
        if (not hasattr(self, "SourcePublicationDates")) or (not self.SourcePublicationDates):
            self.LoadSourcePublicationDates()

        CanonicalMap: Typing.Dict[str, str] = {
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
                            if ClassName and (not ClassName.startswith("_")):
                                ClassKey: str = ClassName.lower().strip()
                                if ClassKey in CanonicalMap:
                                    ExistingSource: str = CanonicalMap[ClassKey]
                                    if self.IsSourceNewerOrEqual(ClassSource, ExistingSource):
                                        CanonicalMap[ClassKey] = ClassSource

                                else:
                                    CanonicalMap[ClassKey] = ClassSource

                except Exception as ParsingException:
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Class File for Canonical Map: {ClassFilePath.name}")

        return CanonicalMap

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
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Class and Subclass File: {ClassFilePath.name}")

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
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Spells File: {SpellFilePath.name}")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Base Items for Proficiencies")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Standard Items for Proficiencies")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Languages from Dataset")

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
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Conditions from Dataset")

        return sorted(list(ConditionsSet))

    def IsGenericProgressionFeature(self, FeatureName: str) -> bool:
        NormalizedName: str = FeatureName.lower().strip()
        GenericProgressionNames: Typing.Tuple[str, ...] = (
            "ability score improvement",
            "ability score increase",
            "epic boon",
            "epic boon feat",
            "subclass feature"
        )
        if NormalizedName in GenericProgressionNames:
            return True

        if NormalizedName.endswith("subclass"):
            return True

        if NormalizedName.endswith("feature") and (("subclass" in NormalizedName) or ("tradition" in NormalizedName) or ("archetype" in NormalizedName) or ("domain" in NormalizedName) or ("college" in NormalizedName) or ("circle" in NormalizedName) or ("oath" in NormalizedName) or ("origin" in NormalizedName) or ("patron" in NormalizedName) or ("path" in NormalizedName)):
            return True

        if ("improvement" in NormalizedName) or ("improvements" in NormalizedName):
            return True

        return False

    def ExtractSpeciesFeaturesMap(self) -> Typing.Dict[str, Typing.List[str]]:
        SpeciesFeaturesDictionary: Typing.Dict[str, Typing.Tuple[str, Typing.List[str]]] = {
        }
        RacesFilePath: PathLibrary.Path = self.DataDirectoryPath / "races.json"
        if RacesFilePath.exists():
            try:
                with open(RacesFilePath, mode = "r", encoding = "utf-8") as RacesFile:
                    RacesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(RacesFile)
                    for RaceEntry in RacesJSON.get("race", []):
                        RaceName: Typing.Optional[str] = RaceEntry.get("name")
                        RaceSource: str = str(RaceEntry.get("source") or "PHB")
                        if (not RaceName) or RaceName.startswith("_"):
                            continue

                        TraitsList: Typing.List[str] = []
                        for EntryItem in RaceEntry.get("entries", []):
                            if isinstance(EntryItem, dict) and ("name" in EntryItem):
                                TraitCandidateName: str = str(EntryItem.get("name") or "").strip()
                                if (RaceSource != "XPHB") and (TraitCandidateName in ("Age", "Size", "Speed", "Languages")):
                                    continue

                                if TraitCandidateName and (TraitCandidateName not in TraitsList):
                                    TraitsList.append(TraitCandidateName)

                        NormalizedKey: str = RaceName.lower().strip()
                        if NormalizedKey in SpeciesFeaturesDictionary:
                            ExistingSource: str = SpeciesFeaturesDictionary[NormalizedKey][0]
                            if self.IsSourceNewerOrEqual(RaceSource, ExistingSource):
                                SpeciesFeaturesDictionary[NormalizedKey] = (RaceSource, TraitsList)

                        else:
                            SpeciesFeaturesDictionary[NormalizedKey] = (RaceSource, TraitsList)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Species Features Map from Dataset")

        return {Key: Value[1] for Key, Value in SpeciesFeaturesDictionary.items()}

    def ExtractBackgroundFeaturesMap(self) -> Typing.Dict[str, Typing.List[str]]:
        BackgroundFeaturesDictionary: Typing.Dict[str, Typing.Tuple[str, Typing.List[str]]] = {
        }
        BackgroundsFilePath: PathLibrary.Path = self.DataDirectoryPath / "backgrounds.json"
        if BackgroundsFilePath.exists():
            try:
                with open(BackgroundsFilePath, mode = "r", encoding = "utf-8") as BackgroundsFile:
                    BackgroundsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BackgroundsFile)
                    for BackgroundEntry in BackgroundsJSON.get("background", []):
                        BackgroundName: Typing.Optional[str] = BackgroundEntry.get("name")
                        BackgroundSource: str = str(BackgroundEntry.get("source") or "PHB")
                        if (not BackgroundName) or BackgroundName.startswith("_"):
                            continue

                        FeaturesList: Typing.List[str] = []
                        if BackgroundEntry.get("feats"):
                            for FeatDictionary in BackgroundEntry.get("feats", []):
                                for RawFeatKey in FeatDictionary.keys():
                                    CleanFeatName: str = RawFeatKey.split("|")[0].strip()
                                    FormattedFeatName: str = " ".join([Word.capitalize() for Word in CleanFeatName.split()])
                                    if FormattedFeatName and (FormattedFeatName not in FeaturesList):
                                        FeaturesList.append(FormattedFeatName)

                        for EntryItem in BackgroundEntry.get("entries", []):
                            if isinstance(EntryItem, dict) and ("name" in EntryItem):
                                EntryName: str = str(EntryItem.get("name") or "").strip()
                                if EntryName.startswith("Feature:"):
                                    CleanFeatureName: str = EntryName.replace("Feature:", "").strip()
                                    if CleanFeatureName and (CleanFeatureName not in FeaturesList):
                                        FeaturesList.append(CleanFeatureName)

                        NormalizedKey: str = BackgroundName.lower().strip()
                        if NormalizedKey in BackgroundFeaturesDictionary:
                            ExistingSource: str = BackgroundFeaturesDictionary[NormalizedKey][0]
                            if self.IsSourceNewerOrEqual(BackgroundSource, ExistingSource):
                                BackgroundFeaturesDictionary[NormalizedKey] = (BackgroundSource, FeaturesList)

                        else:
                            BackgroundFeaturesDictionary[NormalizedKey] = (BackgroundSource, FeaturesList)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Background Features Map from Dataset")

        return {Key: Value[1] for Key, Value in BackgroundFeaturesDictionary.items()}

    def ExtractClassAndSubclassFeatures(self) -> Typing.Tuple[Typing.Dict[str, Typing.Dict[str, Typing.List[str]]], Typing.Dict[str, Typing.Dict[str, Typing.List[str]]], Typing.Dict[str, Typing.List[str]]]:
        ClassFeaturesMap: Typing.Dict[str, Typing.Dict[str, Typing.List[str]]] = {
        }
        SubclassFeaturesMap: Typing.Dict[str, Typing.Dict[str, Typing.List[str]]] = {
        }
        ClassSubclassesMap: Typing.Dict[str, Typing.List[str]] = {
        }
        ClassSubclassAliasMap: Typing.Dict[str, Typing.Dict[str, str]] = {
        }
        CanonicalClassSourceMap: Typing.Dict[str, str] = self.GetClassCanonicalSourceMap()
        SubclassCanonicalSourceMap: Typing.Dict[str, str] = {
        }
        ClassDirectory: PathLibrary.Path = self.DataDirectoryPath / "class"
        LoadedFilesList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        if ClassDirectory.exists():
            for ClassFilePath in ClassDirectory.glob("class-*.json"):
                if "fluff" in ClassFilePath.name:
                    continue

                try:
                    with open(ClassFilePath, mode = "r", encoding = "utf-8") as ClassFile:
                        ClassJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ClassFile)
                        LoadedFilesList.append(ClassJSON)

                except Exception as ParsingException:
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Class Features File: {ClassFilePath.name}")

        for ClassJSON in LoadedFilesList:
            for SubclassFeature in ClassJSON.get("subclassFeature", []):
                CandidateClassName: Typing.Optional[str] = SubclassFeature.get("className")
                CandidateSubclassShortName: Typing.Optional[str] = SubclassFeature.get("subclassShortName")
                CandidateFeatureSource: str = str(SubclassFeature.get("classSource") or SubclassFeature.get("source") or "PHB")
                if CandidateClassName and CandidateSubclassShortName:
                    CandidateClassKey: str = CandidateClassName.lower().strip()
                    CandidateSubclassKey: str = f"{CandidateClassKey}:{CandidateSubclassShortName.lower().strip()}"
                    TargetClassCanonicalSource: str = CanonicalClassSourceMap.get(CandidateClassKey, "PHB")
                    if CandidateSubclassKey not in SubclassCanonicalSourceMap:
                        SubclassCanonicalSourceMap[CandidateSubclassKey] = CandidateFeatureSource

                    elif CandidateFeatureSource == TargetClassCanonicalSource:
                        SubclassCanonicalSourceMap[CandidateSubclassKey] = CandidateFeatureSource

                    elif (SubclassCanonicalSourceMap[CandidateSubclassKey] != TargetClassCanonicalSource) and self.IsSourceNewerOrEqual(CandidateFeatureSource, SubclassCanonicalSourceMap[CandidateSubclassKey]):
                        SubclassCanonicalSourceMap[CandidateSubclassKey] = CandidateFeatureSource

        for ClassJSON in LoadedFilesList:
            for ClassEntry in ClassJSON.get("class", []):
                ClassName: Typing.Optional[str] = ClassEntry.get("name")
                if ClassName and (not ClassName.startswith("_")):
                    ClassKey: str = ClassName.lower().strip()
                    if ClassKey not in ClassSubclassesMap:
                        ClassSubclassesMap[ClassKey] = []

                    if ClassKey not in ClassSubclassAliasMap:
                        ClassSubclassAliasMap[ClassKey] = {
                        }

            for SubclassEntry in ClassJSON.get("subclass", []):
                SubclassName: Typing.Optional[str] = SubclassEntry.get("name")
                SubclassClassName: Typing.Optional[str] = SubclassEntry.get("className")
                SubclassShortName: Typing.Optional[str] = SubclassEntry.get("shortName")
                if SubclassName and SubclassClassName:
                    ClassKey = SubclassClassName.lower().strip()
                    if ClassKey not in ClassSubclassesMap:
                        ClassSubclassesMap[ClassKey] = []

                    if ClassKey not in ClassSubclassAliasMap:
                        ClassSubclassAliasMap[ClassKey] = {
                        }

                    if SubclassName not in ClassSubclassesMap[ClassKey]:
                        ClassSubclassesMap[ClassKey].append(SubclassName)

                    if SubclassShortName and (SubclassShortName not in ClassSubclassesMap[ClassKey]):
                        ClassSubclassesMap[ClassKey].append(SubclassShortName)

                    if SubclassShortName:
                        ClassSubclassAliasMap[ClassKey][SubclassShortName.lower().strip()] = SubclassName
                        ClassSubclassAliasMap[ClassKey][SubclassName.lower().strip()] = SubclassName

            for ClassFeature in ClassJSON.get("classFeature", []):
                FeatureClassName: Typing.Optional[str] = ClassFeature.get("className")
                FeatureName: Typing.Optional[str] = ClassFeature.get("name")
                FeatureLevel: int = int(ClassFeature.get("level") or 1)
                FeatureClassSource: str = str(ClassFeature.get("classSource") or ClassFeature.get("source") or "PHB")
                if (not FeatureClassName) or (not FeatureName) or FeatureName.startswith("_"):
                    continue

                ClassKey = FeatureClassName.lower().strip()
                CanonicalClassSource: Typing.Optional[str] = CanonicalClassSourceMap.get(ClassKey)
                if CanonicalClassSource and (FeatureClassSource != CanonicalClassSource):
                    continue

                if self.IsGenericProgressionFeature(FeatureName):
                    continue

                LevelKey: str = str(FeatureLevel)
                if ClassKey not in ClassFeaturesMap:
                    ClassFeaturesMap[ClassKey] = {
                    }

                if LevelKey not in ClassFeaturesMap[ClassKey]:
                    ClassFeaturesMap[ClassKey][LevelKey] = []

                if FeatureName not in ClassFeaturesMap[ClassKey][LevelKey]:
                    ClassFeaturesMap[ClassKey][LevelKey].append(FeatureName)

            for SubclassFeature in ClassJSON.get("subclassFeature", []):
                FeatureClassName = SubclassFeature.get("className")
                SubclassShortName = SubclassFeature.get("subclassShortName")
                FeatureName = SubclassFeature.get("name")
                FeatureLevel = int(SubclassFeature.get("level") or 1)
                FeatureClassSource = str(SubclassFeature.get("classSource") or SubclassFeature.get("source") or "PHB")
                if (not FeatureClassName) or (not SubclassShortName) or (not FeatureName) or FeatureName.startswith("_"):
                    continue

                ClassKey = FeatureClassName.lower().strip()
                ShortKey: str = SubclassShortName.lower().strip()
                SubclassKey: str = f"{ClassKey}:{ShortKey}"
                TargetSubclassCanonical: Typing.Optional[str] = SubclassCanonicalSourceMap.get(SubclassKey)
                if TargetSubclassCanonical and (FeatureClassSource != TargetSubclassCanonical):
                    continue

                if (FeatureName.lower().strip() == ShortKey) or self.IsGenericProgressionFeature(FeatureName):
                    continue

                LevelKey = str(FeatureLevel)
                SubclassKeysToUpdate: Typing.List[str] = [SubclassKey]
                MappedFullName: Typing.Optional[str] = ClassSubclassAliasMap.get(ClassKey, {}).get(ShortKey)
                if MappedFullName and (MappedFullName.lower().strip() != ShortKey):
                    SubclassKeysToUpdate.append(f"{ClassKey}:{MappedFullName.lower().strip()}")

                for TargetSubclassKey in SubclassKeysToUpdate:
                    if TargetSubclassKey not in SubclassFeaturesMap:
                        SubclassFeaturesMap[TargetSubclassKey] = {
                        }

                    if LevelKey not in SubclassFeaturesMap[TargetSubclassKey]:
                        SubclassFeaturesMap[TargetSubclassKey][LevelKey] = []

                    if FeatureName not in SubclassFeaturesMap[TargetSubclassKey][LevelKey]:
                        SubclassFeaturesMap[TargetSubclassKey][LevelKey].append(FeatureName)

        for TargetClassKey in ClassSubclassesMap:
            ClassSubclassesMap[TargetClassKey] = sorted(ClassSubclassesMap[TargetClassKey])

        return (ClassFeaturesMap, SubclassFeaturesMap, ClassSubclassesMap)

    def ExtractAllFeats(self) -> Typing.List[str]:
        FeatsSet: Typing.Set[str] = set()
        FeatsFilePath: PathLibrary.Path = self.DataDirectoryPath / "feats.json"
        if FeatsFilePath.exists():
            try:
                with open(FeatsFilePath, mode = "r", encoding = "utf-8") as FeatsFile:
                    FeatsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(FeatsFile)
                    for FeatEntry in FeatsJSON.get("feat", []):
                        FeatName: Typing.Optional[str] = FeatEntry.get("name")
                        if FeatName and not FeatName.startswith("_"):
                            FeatsSet.add(FeatName.strip())

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Feats from Dataset")

        return sorted(list(FeatsSet))

    def BuildRulesDataStore(self) -> Typing.Dict[str, Typing.Any]:
        DamageTypesList: Typing.List[str] = self.ExtractDamageTypes()
        SpeciesList: Typing.List[str] = self.ExtractSpecies()
        BackgroundsList: Typing.List[str] = self.ExtractBackgrounds()
        ClassesList, SubclassesList = self.ExtractClassesAndSubclasses()
        SpellsList: Typing.List[str] = self.ExtractSpells()
        AllItemsList, WeaponsList, ArmorList, ToolsList = self.ExtractAllItemsAndProficiencies()
        LanguagesList: Typing.List[str] = self.ExtractLanguages()
        ConditionsList: Typing.List[str] = self.ExtractConditions()
        SpeciesFeaturesMap: Typing.Dict[str, Typing.List[str]] = self.ExtractSpeciesFeaturesMap()
        BackgroundFeaturesMap: Typing.Dict[str, Typing.List[str]] = self.ExtractBackgroundFeaturesMap()
        ClassFeaturesMap, SubclassFeaturesMap, ClassSubclassesMap = self.ExtractClassAndSubclassFeatures()
        FeatsList: Typing.List[str] = self.ExtractAllFeats()
        MasterFeaturesSet: Typing.Set[str] = set(FeatsList)
        for SpeciesTraitsList in SpeciesFeaturesMap.values():
            MasterFeaturesSet.update(SpeciesTraitsList)

        for BackgroundFeatsList in BackgroundFeaturesMap.values():
            MasterFeaturesSet.update(BackgroundFeatsList)

        for LevelFeaturesMap in ClassFeaturesMap.values():
            for FeatureNamesList in LevelFeaturesMap.values():
                MasterFeaturesSet.update(FeatureNamesList)

        for LevelFeaturesMap in SubclassFeaturesMap.values():
            for FeatureNamesList in LevelFeaturesMap.values():
                MasterFeaturesSet.update(FeatureNamesList)

        MasterFeaturesList: Typing.List[str] = sorted(list(MasterFeaturesSet))

        DataStore: Typing.Dict[str, Typing.Any] = {
            "GameSystem"           : "DND5E",
            "Timestamp"            : TimeLibrary.time(),
            "Species"              : SpeciesList,
            "Backgrounds"          : BackgroundsList,
            "Classes"              : ClassesList,
            "Subclasses"           : SubclassesList,
            "Spells"               : SpellsList,
            "Items"                : AllItemsList,
            "WeaponProficiencies"  : WeaponsList,
            "ArmorProficiencies"   : ArmorList,
            "ToolProficiencies"    : ToolsList,
            "Languages"            : LanguagesList,
            "DamageTypes"          : DamageTypesList,
            "Conditions"           : ConditionsList,
            "Features"             : MasterFeaturesList,
            "Feats"                : FeatsList,
            "SpeciesFeaturesMap"   : SpeciesFeaturesMap,
            "BackgroundFeaturesMap": BackgroundFeaturesMap,
            "ClassFeaturesMap"     : ClassFeaturesMap,
            "SubclassFeaturesMap"  : SubclassFeaturesMap,
            "ClassSubclassesMap"   : ClassSubclassesMap
        }
        return DataStore

    def GetRulesDataStore(self) -> Typing.Dict[str, Typing.Any]:
        self.EnsureDataLoaded()
        if self.RulesDataStore is None:
            self.RulesDataStore = self.BuildRulesDataStore()

        return self.RulesDataStore

    def Is5EToolsFeature(self, FeatureName: str) -> bool:
        CleanName: str = FeatureName.strip().lower()
        Store: Typing.Dict[str, Typing.Any] = self.GetRulesDataStore()
        AllFeaturesList: Typing.List[str] = Store.get("Features", [])
        return any(F.strip().lower() == CleanName for F in AllFeaturesList)

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
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Cantrips: {SpellFilePath.name}")

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
                    "BaseAC"   : ResolvedAC,
                    "ArmorType": ArmorCategory
                }

        self.EquipmentRulesData = {
            "Weights": ItemWeights,
            "Armors" : ArmorData
        }
        return self.EquipmentRulesData

    def BuildEntityVersionResponse(self, CanonicalName: str, VersionsData: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]], DetailData: Typing.Dict[str, Typing.Dict[str, Typing.Any]], SourceKeyedData: Typing.Dict[str, Typing.Dict[str, Typing.Any]], Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        VersionsList: Typing.List[Typing.Dict[str, Typing.Any]] = VersionsData.get(CanonicalName, [])
        if not VersionsList:
            return None

        PrimaryRecord: Typing.Dict[str, Typing.Any] = DetailData.get(CanonicalName, VersionsList[0])
        PrimarySource: str = str(PrimaryRecord.get("source") or "PHB")
        TargetRecord: Typing.Dict[str, Typing.Any] = PrimaryRecord

        if Source:
            CleanSource: str = Source.strip().upper()
            SourceKey: str = f"{RegularExpressions.sub(r'[^a-zA-Z0-9]', '', CanonicalName).lower()}::{CleanSource}"
            if SourceKey in SourceKeyedData:
                TargetRecord = SourceKeyedData[SourceKey]

            else:
                for VersionEntry in VersionsList:
                    if str(VersionEntry.get("source") or "").upper() == CleanSource:
                        TargetRecord = VersionEntry
                        break

        ResultRecord: Typing.Dict[str, Typing.Any] = CopyLibrary.copy(TargetRecord)
        ResultRecord["Versions"] = self.BuildVersionMetadataList(VersionsList, PrimarySource)
        return ResultRecord

    def EnsureFeatsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.FeatsDetailData:
            return

        FeatsFilePath: PathLibrary.Path = self.DataDirectoryPath / "feats.json"
        if not FeatsFilePath.exists():
            return

        try:
            with open(FeatsFilePath, mode = "r", encoding = "utf-8") as FeatsFile:
                FeatsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(FeatsFile)
                for FeatEntry in FeatsJSON.get("feat", []):
                    FeatName: Typing.Optional[str] = FeatEntry.get("name")
                    if FeatName and (not FeatName.startswith("_")):
                        CleanName: str = FeatName.strip()
                        self.FeatsVersionsData.setdefault(CleanName, []).append(FeatEntry)

            for CanonicalName, VersionsList in self.FeatsVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.FeatsDetailData[CanonicalName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
                self.FeatsNormalizedMap[NormalizedKey] = CanonicalName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.FeatsSourceKeyedData[Key] = VersionRecord

        except Exception as ParsingException:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Feats Dataset")

    def FindCanonicalFeatName(self, FeatNameQuery: str) -> Typing.Optional[str]:
        self.EnsureFeatsLoaded()
        CleanQuery: str = FeatNameQuery.strip()
        if CleanQuery in self.FeatsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.FeatsNormalizedMap:
            return self.FeatsNormalizedMap[NormalizedQuery]

        return None

    def GetFeatData(self, FeatName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureFeatsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalFeatName(FeatName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.FeatsVersionsData, self.FeatsDetailData, self.FeatsSourceKeyedData, Source)

    def EnsureOptionsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.OptionsDetailData:
            return

        CreationOptionsPath: PathLibrary.Path = self.DataDirectoryPath / "charcreationoptions.json"
        if CreationOptionsPath.exists():
            try:
                with open(CreationOptionsPath, mode = "r", encoding = "utf-8") as CreationOptionsFile:
                    CreationOptionsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(CreationOptionsFile)
                    for OptionEntry in CreationOptionsJSON.get("charoption", []):
                        OptionName: Typing.Optional[str] = OptionEntry.get("name")
                        if OptionName and (not OptionName.startswith("_")):
                            CleanName: str = OptionName.strip()
                            OptionEntry["OptionCategory"] = "Character Creation Option"
                            self.OptionsVersionsData.setdefault(CleanName, []).append(OptionEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Character Creation Options Dataset")

        OptionalFeaturesPath: PathLibrary.Path = self.DataDirectoryPath / "optionalfeatures.json"
        if OptionalFeaturesPath.exists():
            try:
                with open(OptionalFeaturesPath, mode = "r", encoding = "utf-8") as OptionalFeaturesFile:
                    OptionalFeaturesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(OptionalFeaturesFile)
                    for FeatureEntry in OptionalFeaturesJSON.get("optionalfeature", []):
                        FeatureName: Typing.Optional[str] = FeatureEntry.get("name")
                        if FeatureName and (not FeatureName.startswith("_")):
                            CleanName: str = FeatureName.strip()
                            FeatureEntry["OptionCategory"] = "Optional Feature"
                            self.OptionsVersionsData.setdefault(CleanName, []).append(FeatureEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Optional Features Dataset")

        for CanonicalName, VersionsList in self.OptionsVersionsData.items():
            VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
            self.OptionsDetailData[CanonicalName] = VersionsList[0]

            NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
            self.OptionsNormalizedMap[NormalizedKey] = CanonicalName

            for VersionRecord in VersionsList:
                SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                Key: str = f"{NormalizedKey}::{SourceCode}"
                self.OptionsSourceKeyedData[Key] = VersionRecord

    def FindCanonicalOptionName(self, OptionNameQuery: str) -> Typing.Optional[str]:
        self.EnsureOptionsLoaded()
        CleanQuery: str = OptionNameQuery.strip()
        if CleanQuery in self.OptionsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.OptionsNormalizedMap:
            return self.OptionsNormalizedMap[NormalizedQuery]

        return None

    def GetOptionData(self, OptionName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureOptionsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalOptionName(OptionName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.OptionsVersionsData, self.OptionsDetailData, self.OptionsSourceKeyedData, Source)

    def EnsureRulesLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.RulesDetailData:
            return

        VariantRulesPath: PathLibrary.Path = self.DataDirectoryPath / "variantrules.json"
        if VariantRulesPath.exists():
            try:
                with open(VariantRulesPath, mode = "r", encoding = "utf-8") as VariantRulesFile:
                    VariantRulesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(VariantRulesFile)
                    for RuleEntry in VariantRulesJSON.get("variantrule", []):
                        RuleName: Typing.Optional[str] = RuleEntry.get("name")
                        if RuleName and (not RuleName.startswith("_")):
                            CleanName: str = RuleName.strip()
                            RuleEntry["RuleType"] = "Rule"
                            self.RulesVersionsData.setdefault(CleanName, []).append(RuleEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Variant Rules Dataset")

        TablesPath: PathLibrary.Path = self.DataDirectoryPath / "tables.json"
        if TablesPath.exists():
            try:
                with open(TablesPath, mode = "r", encoding = "utf-8") as TablesFile:
                    TablesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(TablesFile)
                    for TableEntry in TablesJSON.get("table", []):
                        TableName: Typing.Optional[str] = TableEntry.get("name")
                        if TableName and (not TableName.startswith("_")):
                            CleanName: str = TableName.strip()
                            TableEntry["RuleType"] = "Table"
                            self.RulesVersionsData.setdefault(CleanName, []).append(TableEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Tables Dataset")

        for CanonicalName, VersionsList in self.RulesVersionsData.items():
            VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
            self.RulesDetailData[CanonicalName] = VersionsList[0]

            NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
            self.RulesNormalizedMap[NormalizedKey] = CanonicalName

            for VersionRecord in VersionsList:
                SourceCode: str = str(VersionRecord.get("source") or "DMG").upper()
                Key: str = f"{NormalizedKey}::{SourceCode}"
                self.RulesSourceKeyedData[Key] = VersionRecord

    def FindCanonicalRuleName(self, RuleNameQuery: str) -> Typing.Optional[str]:
        self.EnsureRulesLoaded()
        CleanQuery: str = RuleNameQuery.strip()
        if CleanQuery in self.RulesDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.RulesNormalizedMap:
            return self.RulesNormalizedMap[NormalizedQuery]

        return None

    def GetRuleData(self, RuleName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureRulesLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalRuleName(RuleName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.RulesVersionsData, self.RulesDetailData, self.RulesSourceKeyedData, Source)

    def EnsureBackgroundsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.BackgroundsDetailData:
            return

        BackgroundsPath: PathLibrary.Path = self.DataDirectoryPath / "backgrounds.json"
        if not BackgroundsPath.exists():
            return

        try:
            with open(BackgroundsPath, mode = "r", encoding = "utf-8") as BackgroundsFile:
                BackgroundsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BackgroundsFile)
                RawBackgrounds: Typing.List[Typing.Dict[str, Typing.Any]] = BackgroundsJSON.get("background", [])

                LookupMap: Typing.Dict[Typing.Tuple[str, str], Typing.Dict[str, Typing.Any]] = {
                    (str(B.get("name")).strip().lower(), str(B.get("source")).strip().lower()): B
                    for B in RawBackgrounds if B.get("name")
                }

                ResolvedBackgrounds: Typing.List[Typing.Dict[str, Typing.Any]] = [
                    self.ResolveCopyDirectives(B, LookupMap)
                    for B in RawBackgrounds if B.get("name")
                ]

                for BackgroundEntry in ResolvedBackgrounds:
                    BackgroundName: Typing.Optional[str] = BackgroundEntry.get("name")
                    if BackgroundName and (not BackgroundName.startswith("_")):
                        CleanName: str = BackgroundName.strip()
                        self.BackgroundsVersionsData.setdefault(CleanName, []).append(BackgroundEntry)

            for CanonicalName, VersionsList in self.BackgroundsVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.BackgroundsDetailData[CanonicalName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
                self.BackgroundsNormalizedMap[NormalizedKey] = CanonicalName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.BackgroundsSourceKeyedData[Key] = VersionRecord

        except Exception as ParsingException:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Backgrounds Dataset")

    def FindCanonicalBackgroundName(self, BackgroundNameQuery: str) -> Typing.Optional[str]:
        self.EnsureBackgroundsLoaded()
        CleanQuery: str = BackgroundNameQuery.strip()
        if CleanQuery in self.BackgroundsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.BackgroundsNormalizedMap:
            return self.BackgroundsNormalizedMap[NormalizedQuery]

        return None

    def GetBackgroundData(self, BackgroundName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureBackgroundsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalBackgroundName(BackgroundName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.BackgroundsVersionsData, self.BackgroundsDetailData, self.BackgroundsSourceKeyedData, Source)

    def EnsureSpeciesLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.SpeciesDetailData:
            return

        RacesPath: PathLibrary.Path = self.DataDirectoryPath / "races.json"
        if not RacesPath.exists():
            return

        try:
            with open(RacesPath, mode = "r", encoding = "utf-8") as RacesFile:
                RacesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(RacesFile)

            RawRaces: Typing.List[Typing.Dict[str, Typing.Any]] = RacesJSON.get("race", [])
            RawSubraces: Typing.List[Typing.Dict[str, Typing.Any]] = RacesJSON.get("subrace", [])

            RaceLookup: Typing.Dict[Typing.Tuple[str, str], Typing.Dict[str, Typing.Any]] = {
                (str(R.get("name")).strip().lower(), str(R.get("source")).strip().lower()): R
                for R in RawRaces if R.get("name")
            }
            SubraceLookup: Typing.Dict[Typing.Tuple[str, str], Typing.Dict[str, Typing.Any]] = {
                (str(S.get("name")).strip().lower(), str(S.get("source")).strip().lower()): S
                for S in RawSubraces if S.get("name")
            }

            ResolvedRaces: Typing.List[Typing.Dict[str, Typing.Any]] = [
                self.ResolveCopyDirectives(R, RaceLookup)
                for R in RawRaces if R.get("name")
            ]
            ResolvedSubraces: Typing.List[Typing.Dict[str, Typing.Any]] = [
                self.ResolveCopyDirectives(S, SubraceLookup)
                for S in RawSubraces if S.get("name")
            ]

            SubraceMap: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
            }
            for Subrace in ResolvedSubraces:
                ParentRaceName: str = str(Subrace.get("raceName") or "").strip().lower()
                if ParentRaceName:
                    SubraceMap.setdefault(ParentRaceName, []).append(Subrace)

            for RaceEntry in ResolvedRaces:
                RaceName: str = str(RaceEntry.get("name") or "").strip()
                if (not RaceName) or RaceName.startswith("_"):
                    continue

                MatchingSubraces: Typing.List[Typing.Dict[str, Typing.Any]] = []
                for Sub in SubraceMap.get(RaceName.lower(), []):
                    CleanSub: Typing.Dict[str, Typing.Any] = CopyLibrary.copy(Sub)
                    SubName: str = str(CleanSub.get("name") or "").strip()
                    if not SubName.lower().endswith(RaceName.lower()):
                        CleanSub["name"] = f"{SubName} {RaceName}"

                    MatchingSubraces.append(CleanSub)

                RaceEntry["subraces"] = MatchingSubraces
                self.SpeciesVersionsData.setdefault(RaceName, []).append(RaceEntry)

            for CanonicalName, VersionsList in self.SpeciesVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.SpeciesDetailData[CanonicalName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
                self.SpeciesNormalizedMap[NormalizedKey] = CanonicalName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.SpeciesSourceKeyedData[Key] = VersionRecord

                    for Sub in VersionRecord.get("subraces", []):
                        SubName: str = str(Sub.get("name") or "").strip()
                        SubNorm: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", SubName).lower()
                        if SubNorm not in self.SpeciesNormalizedMap:
                            self.SpeciesNormalizedMap[SubNorm] = CanonicalName

        except Exception as ParsingException:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Species Dataset")

    def FindCanonicalSpeciesName(self, SpeciesNameQuery: str) -> Typing.Optional[str]:
        self.EnsureSpeciesLoaded()
        CleanQuery: str = SpeciesNameQuery.strip()
        if CleanQuery in self.SpeciesDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.SpeciesNormalizedMap:
            return self.SpeciesNormalizedMap[NormalizedQuery]

        return None

    def GetSpeciesData(self, SpeciesName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureSpeciesLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalSpeciesName(SpeciesName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.SpeciesVersionsData, self.SpeciesDetailData, self.SpeciesSourceKeyedData, Source)

    def EnsureConditionsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.ConditionsDetailData:
            return

        ConditionsPath: PathLibrary.Path = self.DataDirectoryPath / "conditionsdiseases.json"
        if not ConditionsPath.exists():
            return

        try:
            with open(ConditionsPath, mode = "r", encoding = "utf-8") as ConditionsFile:
                ConditionsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ConditionsFile)
                for CondItem in ConditionsJSON.get("condition", []):
                    NameVal: Typing.Optional[str] = CondItem.get("name")
                    if NameVal and (not NameVal.startswith("_")):
                        CleanName: str = NameVal.strip()
                        CondItem["ConditionKind"] = "Condition"
                        self.ConditionsVersionsData.setdefault(CleanName, []).append(CondItem)

                for DiseaseItem in ConditionsJSON.get("disease", []):
                    NameVal = DiseaseItem.get("name")
                    if NameVal and (not NameVal.startswith("_")):
                        CleanName = NameVal.strip()
                        DiseaseItem["ConditionKind"] = "Disease"
                        self.ConditionsVersionsData.setdefault(CleanName, []).append(DiseaseItem)

                for StatusItem in ConditionsJSON.get("status", []):
                    NameVal = StatusItem.get("name")
                    if NameVal and (not NameVal.startswith("_")):
                        CleanName = NameVal.strip()
                        StatusItem["ConditionKind"] = "Status"
                        self.ConditionsVersionsData.setdefault(CleanName, []).append(StatusItem)

            for CanonicalName, VersionsList in self.ConditionsVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.ConditionsDetailData[CanonicalName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
                self.ConditionsNormalizedMap[NormalizedKey] = CanonicalName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.ConditionsSourceKeyedData[Key] = VersionRecord

        except Exception as ParsingException:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Conditions Dataset")

    def FindCanonicalConditionName(self, ConditionNameQuery: str) -> Typing.Optional[str]:
        self.EnsureConditionsLoaded()
        CleanQuery: str = ConditionNameQuery.strip()
        if CleanQuery in self.ConditionsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.ConditionsNormalizedMap:
            return self.ConditionsNormalizedMap[NormalizedQuery]

        return None

    def GetConditionData(self, ConditionName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureConditionsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalConditionName(ConditionName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.ConditionsVersionsData, self.ConditionsDetailData, self.ConditionsSourceKeyedData, Source)

    def EnsureDeitiesLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.DeitiesDetailData:
            return

        DeitiesPath: PathLibrary.Path = self.DataDirectoryPath / "deities.json"
        if not DeitiesPath.exists():
            return

        try:
            with open(DeitiesPath, mode = "r", encoding = "utf-8") as DeitiesFile:
                DeitiesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(DeitiesFile)
                RawDeities: Typing.List[Typing.Dict[str, Typing.Any]] = DeitiesJSON.get("deity", [])

                LookupMap: Typing.Dict[Typing.Tuple[str, str], Typing.Dict[str, Typing.Any]] = {
                    (str(D.get("name")).strip().lower(), str(D.get("source")).strip().lower()): D
                    for D in RawDeities if D.get("name")
                }

                ResolvedDeities: Typing.List[Typing.Dict[str, Typing.Any]] = [
                    self.ResolveCopyDirectives(D, LookupMap)
                    for D in RawDeities if D.get("name")
                ]

                for DeityEntry in ResolvedDeities:
                    DeityName: Typing.Optional[str] = DeityEntry.get("name")
                    if DeityName and (not DeityName.startswith("_")):
                        CleanName: str = DeityName.strip()
                        self.DeitiesVersionsData.setdefault(CleanName, []).append(DeityEntry)

            for CanonicalName, VersionsList in self.DeitiesVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.DeitiesDetailData[CanonicalName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
                self.DeitiesNormalizedMap[NormalizedKey] = CanonicalName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "DMG").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.DeitiesSourceKeyedData[Key] = VersionRecord

        except Exception as ParsingException:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Deities Dataset")

    def FindCanonicalDeityName(self, DeityNameQuery: str) -> Typing.Optional[str]:
        self.EnsureDeitiesLoaded()
        CleanQuery: str = DeityNameQuery.strip()
        if CleanQuery in self.DeitiesDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.DeitiesNormalizedMap:
            return self.DeitiesNormalizedMap[NormalizedQuery]

        return None

    def GetDeityData(self, DeityName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureDeitiesLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalDeityName(DeityName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.DeitiesVersionsData, self.DeitiesDetailData, self.DeitiesSourceKeyedData, Source)

    def EnsureVehiclesLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.VehiclesDetailData:
            return

        VehiclesPath: PathLibrary.Path = self.DataDirectoryPath / "vehicles.json"
        if not VehiclesPath.exists():
            return

        try:
            with open(VehiclesPath, mode = "r", encoding = "utf-8") as VehiclesFile:
                VehiclesJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(VehiclesFile)
                for VehicleEntry in VehiclesJSON.get("vehicle", []):
                    VehicleName: Typing.Optional[str] = VehicleEntry.get("name")
                    if VehicleName and (not VehicleName.startswith("_")):
                        CleanName: str = VehicleName.strip()
                        VehicleEntry["VehicleKind"] = "Vehicle"
                        self.VehiclesVersionsData.setdefault(CleanName, []).append(VehicleEntry)

                for UpgradeEntry in VehiclesJSON.get("vehicleUpgrade", []):
                    UpgradeName: Typing.Optional[str] = UpgradeEntry.get("name")
                    if UpgradeName and (not UpgradeName.startswith("_")):
                        CleanName = UpgradeName.strip()
                        UpgradeEntry["VehicleKind"] = "Upgrade"
                        self.VehiclesVersionsData.setdefault(CleanName, []).append(UpgradeEntry)

            for CanonicalName, VersionsList in self.VehiclesVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.VehiclesDetailData[CanonicalName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
                self.VehiclesNormalizedMap[NormalizedKey] = CanonicalName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "DMG").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.VehiclesSourceKeyedData[Key] = VersionRecord

        except Exception as ParsingException:
            Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Vehicles Dataset")

    def FindCanonicalVehicleName(self, VehicleNameQuery: str) -> Typing.Optional[str]:
        self.EnsureVehiclesLoaded()
        CleanQuery: str = VehicleNameQuery.strip()
        if CleanQuery in self.VehiclesDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.VehiclesNormalizedMap:
            return self.VehiclesNormalizedMap[NormalizedQuery]

        return None

    def GetVehicleData(self, VehicleName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureVehiclesLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalVehicleName(VehicleName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.VehiclesVersionsData, self.VehiclesDetailData, self.VehiclesSourceKeyedData, Source)

    def EnsureClassesDetailLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.ClassesDetailData:
            return

        ClassDirectory: PathLibrary.Path = self.DataDirectoryPath / "class"
        if not ClassDirectory.exists():
            return

        AllClassEntries: Typing.List[Typing.Dict[str, Typing.Any]] = []
        AllSubclassEntries: Typing.List[Typing.Dict[str, Typing.Any]] = []

        for ClassFilePath in ClassDirectory.glob("class-*.json"):
            if "fluff" in ClassFilePath.name:
                continue

            try:
                with open(ClassFilePath, mode = "r", encoding = "utf-8") as ClassFile:
                    ClassJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ClassFile)
                    for Entry in ClassJSON.get("class", []):
                        if Entry.get("name") and (not Entry.get("name").startswith("_")):
                            AllClassEntries.append(Entry)

                    for SubEntry in ClassJSON.get("subclass", []):
                        if SubEntry.get("name"):
                            AllSubclassEntries.append(SubEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Class Details: {ClassFilePath.name}")

        for ClassEntry in AllClassEntries:
            ClassName: str = str(ClassEntry.get("name") or "").strip()
            ClassSource: str = str(ClassEntry.get("source") or "PHB").strip()
            MatchingSubclasses: Typing.List[str] = [
                str(Sub.get("name") or "")
                for Sub in AllSubclassEntries
                if (str(Sub.get("className") or "").strip().lower() == ClassName.lower()) and ((not Sub.get("classSource")) or (str(Sub.get("classSource") or "").strip().lower() == ClassSource.lower()))
            ]
            ClassEntry["AvailableSubclasses"] = MatchingSubclasses
            self.ClassesVersionsData.setdefault(ClassName, []).append(ClassEntry)

        for CanonicalName, VersionsList in self.ClassesVersionsData.items():
            VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
            self.ClassesDetailData[CanonicalName] = VersionsList[0]

            NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalName).lower()
            self.ClassesDetailNormalizedMap[NormalizedKey] = CanonicalName

            for VersionRecord in VersionsList:
                SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                Key: str = f"{NormalizedKey}::{SourceCode}"
                self.ClassesSourceKeyedData[Key] = VersionRecord

    def FindCanonicalClassDetailName(self, ClassNameQuery: str) -> Typing.Optional[str]:
        self.EnsureClassesDetailLoaded()
        CleanQuery: str = ClassNameQuery.strip()
        if CleanQuery in self.ClassesDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.ClassesDetailNormalizedMap:
            return self.ClassesDetailNormalizedMap[NormalizedQuery]

        return None

    def GetClassDetailData(self, ClassName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureClassesDetailLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalClassDetailName(ClassName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.ClassesVersionsData, self.ClassesDetailData, self.ClassesSourceKeyedData, Source)

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
                            if SpellName and (not SpellName.startswith("_")):
                                CleanName: str = SpellName.strip()
                                self.SpellsVersionsData.setdefault(CleanName, []).append(SpellEntry)

                except Exception as ParsingException:
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Spells File for Statblocks: {SpellFilePath.name}")

            for CanonicalSpellName, VersionsList in self.SpellsVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.SpellsDetailData[CanonicalSpellName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalSpellName).lower()
                self.SpellsNormalizedMap[NormalizedKey] = CanonicalSpellName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.SpellsSourceKeyedData[Key] = VersionRecord

    def FindCanonicalSpellName(self, SpellNameQuery: str) -> Typing.Optional[str]:
        self.EnsureSpellsLoaded()
        CleanQuery: str = SpellNameQuery.strip()
        if CleanQuery in self.SpellsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.SpellsNormalizedMap:
            return self.SpellsNormalizedMap[NormalizedQuery]

        return None

    def GetSpellData(self, SpellName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureSpellsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalSpellName(SpellName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.SpellsVersionsData, self.SpellsDetailData, self.SpellsSourceKeyedData, Source)

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
                            if MonsterName and (not MonsterName.startswith("_")):
                                CleanName: str = MonsterName.strip()
                                self.MonstersVersionsData.setdefault(CleanName, []).append(MonsterEntry)

                except Exception as ParsingException:
                    Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = f"Failed to Parse Bestiary File for Statblocks: {BestiaryFilePath.name}")

            for CanonicalMonsterName, VersionsList in self.MonstersVersionsData.items():
                VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
                self.MonstersDetailData[CanonicalMonsterName] = VersionsList[0]

                NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalMonsterName).lower()
                self.MonstersNormalizedMap[NormalizedKey] = CanonicalMonsterName

                for VersionRecord in VersionsList:
                    SourceCode: str = str(VersionRecord.get("source") or "MM").upper()
                    Key: str = f"{NormalizedKey}::{SourceCode}"
                    self.MonstersSourceKeyedData[Key] = VersionRecord

    def FindCanonicalMonsterName(self, MonsterNameQuery: str) -> Typing.Optional[str]:
        self.EnsureMonstersLoaded()
        CleanQuery: str = MonsterNameQuery.strip()
        if CleanQuery in self.MonstersDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.MonstersNormalizedMap:
            return self.MonstersNormalizedMap[NormalizedQuery]

        return None

    def GetMonsterData(self, MonsterName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureMonstersLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalMonsterName(MonsterName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.MonstersVersionsData, self.MonstersDetailData, self.MonstersSourceKeyedData, Source)

    def EnsureItemsLoaded(self) -> None:
        self.EnsureDataLoaded()
        if self.ItemsDetailData:
            return

        RawItemsList: Typing.List[Typing.Dict[str, Typing.Any]] = []

        BaseItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items-base.json"
        if BaseItemsFilePath.exists():
            try:
                with open(BaseItemsFilePath, mode = "r", encoding = "utf-8") as BaseItemsFile:
                    BaseItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BaseItemsFile)
                    for BaseItemEntry in BaseItemsJSON.get("baseitem", []):
                        if BaseItemEntry.get("name") and (not BaseItemEntry.get("name").startswith("_")):
                            RawItemsList.append(BaseItemEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Base Items for Statblocks")

        ItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items.json"
        if ItemsFilePath.exists():
            try:
                with open(ItemsFilePath, mode = "r", encoding = "utf-8") as ItemsFile:
                    ItemsJSON: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ItemsFile)
                    for ItemEntry in ItemsJSON.get("item", []):
                        if ItemEntry.get("name") and (not ItemEntry.get("name").startswith("_")):
                            RawItemsList.append(ItemEntry)

            except Exception as ParsingException:
                Debug.LogMessage(Level = Debug.LogLevel.Warning, Message = "Failed to Parse Standard Items for Statblocks")

        LookupMap: Typing.Dict[Typing.Tuple[str, str], Typing.Dict[str, Typing.Any]] = {
            (str(I.get("name")).strip().lower(), str(I.get("source")).strip().lower()): I
            for I in RawItemsList if I.get("name")
        }

        ResolvedItems: Typing.List[Typing.Dict[str, Typing.Any]] = [
            self.ResolveCopyDirectives(I, LookupMap)
            for I in RawItemsList if I.get("name")
        ]

        for ItemEntry in ResolvedItems:
            ItemName: Typing.Optional[str] = ItemEntry.get("name")
            if ItemName and (not ItemName.startswith("_")):
                CleanName: str = ItemName.strip()
                self.ItemsVersionsData.setdefault(CleanName, []).append(ItemEntry)

        for CanonicalItemName, VersionsList in self.ItemsVersionsData.items():
            VersionsList.sort(key = lambda Item: self.GetSourcePublicationDate(str(Item.get("source") or "")), reverse = True)
            self.ItemsDetailData[CanonicalItemName] = VersionsList[0]

            NormalizedKey: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CanonicalItemName).lower()
            self.ItemsNormalizedMap[NormalizedKey] = CanonicalItemName

            for VersionRecord in VersionsList:
                SourceCode: str = str(VersionRecord.get("source") or "PHB").upper()
                Key: str = f"{NormalizedKey}::{SourceCode}"
                self.ItemsSourceKeyedData[Key] = VersionRecord

    def FindCanonicalItemName(self, ItemNameQuery: str) -> Typing.Optional[str]:
        self.EnsureItemsLoaded()
        CleanQuery: str = ItemNameQuery.strip()
        if CleanQuery in self.ItemsDetailData:
            return CleanQuery

        NormalizedQuery: str = RegularExpressions.sub(r"[^a-zA-Z0-9]", "", CleanQuery).lower()
        if NormalizedQuery in self.ItemsNormalizedMap:
            return self.ItemsNormalizedMap[NormalizedQuery]

        return None

    def GetItemData(self, ItemName: str, Source: Typing.Optional[str] = None) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        self.EnsureItemsLoaded()
        CanonicalName: Typing.Optional[str] = self.FindCanonicalItemName(ItemName)
        if not CanonicalName:
            return None

        return self.BuildEntityVersionResponse(CanonicalName, self.ItemsVersionsData, self.ItemsDetailData, self.ItemsSourceKeyedData, Source)

    def SearchCompendium(self, QueryText: str, CategoryFilter: Typing.Optional[str] = None, ResultLimit: int = 5) -> Typing.Dict[str, Typing.Any]:
        CleanQuery  : str                  = QueryText.strip().lower()
        CleanFilter : Typing.Optional[str] = (CategoryFilter.strip().lower() if CategoryFilter else None)
        CategoryAliasesMap: Typing.Dict[str, str] = {
            "race"       : "species",
            "races"      : "species",
            "feat"       : "features",
            "feats"      : "features",
            "feature"    : "features",
            "option"     : "options",
            "rule"       : "rules",
            "class"      : "classes",
            "background" : "backgrounds",
            "condition"  : "conditions",
            "deity"      : "deities",
            "god"        : "deities",
            "gods"       : "deities",
            "vehicle"    : "vehicles",
            "spell"      : "spells",
            "item"       : "items",
            "monster"    : "monsters",
            "creature"   : "monsters",
            "creatures"  : "monsters"
        }
        if CleanFilter and (CleanFilter in CategoryAliasesMap):
            CleanFilter = CategoryAliasesMap[CleanFilter]

        ResultsMap: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
            "Features"   : [],
            "Options"    : [],
            "Rules"      : [],
            "Classes"    : [],
            "Backgrounds": [],
            "Species"    : [],
            "Conditions" : [],
            "Deities"    : [],
            "Vehicles"   : [],
            "Spells"     : [],
            "Items"      : [],
            "Monsters"   : []
        }

        CategoryDefinitions: Typing.List[Typing.Tuple[str, Typing.Callable[[], None], Typing.Dict[str, Typing.Dict[str, Typing.Any]], Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]]]] = [
            ("Features",    self.EnsureFeatsLoaded,         self.FeatsDetailData,         self.FeatsVersionsData),
            ("Options",     self.EnsureOptionsLoaded,       self.OptionsDetailData,       self.OptionsVersionsData),
            ("Rules",       self.EnsureRulesLoaded,         self.RulesDetailData,         self.RulesVersionsData),
            ("Classes",     self.EnsureClassesDetailLoaded, self.ClassesDetailData,       self.ClassesVersionsData),
            ("Backgrounds", self.EnsureBackgroundsLoaded,   self.BackgroundsDetailData,   self.BackgroundsVersionsData),
            ("Species",     self.EnsureSpeciesLoaded,       self.SpeciesDetailData,       self.SpeciesVersionsData),
            ("Conditions",  self.EnsureConditionsLoaded,    self.ConditionsDetailData,    self.ConditionsVersionsData),
            ("Deities",     self.EnsureDeitiesLoaded,       self.DeitiesDetailData,       self.DeitiesVersionsData),
            ("Vehicles",    self.EnsureVehiclesLoaded,      self.VehiclesDetailData,      self.VehiclesVersionsData),
            ("Spells",      self.EnsureSpellsLoaded,        self.SpellsDetailData,        self.SpellsVersionsData),
            ("Items",       self.EnsureItemsLoaded,         self.ItemsDetailData,         self.ItemsVersionsData),
            ("Monsters",    self.EnsureMonstersLoaded,      self.MonstersDetailData,      self.MonstersVersionsData)
        ]

        for CategoryName, LoaderFunction, DetailData, VersionsData in CategoryDefinitions:
            if CleanFilter and (CleanFilter != CategoryName.lower()):
                continue

            LoaderFunction()
            CandidateMatches: Typing.List[Typing.Tuple[int, int, str, Typing.Dict[str, Typing.Any]]] = []

            for CanonicalName, PrimaryRecord in DetailData.items():
                LowerName: str = CanonicalName.lower()
                if CleanQuery in LowerName:
                    Score: int = 3
                    if (LowerName == CleanQuery):
                        Score = 0

                    elif LowerName.startswith(CleanQuery):
                        Score = 1

                    elif f" {CleanQuery}" in LowerName:
                        Score = 2

                    CandidateMatches.append((Score, len(CanonicalName), CanonicalName, PrimaryRecord))

            CandidateMatches.sort(key = lambda MatchTuple: (
                MatchTuple[0],
                -1 if self.IsSource2024(str(MatchTuple[3].get("source") or "")) else 0,
                -self.GetSourcePublicationYear(str(MatchTuple[3].get("source") or "")),
                MatchTuple[1]
            ))

            for MatchTuple in CandidateMatches[:ResultLimit]:
                MatchedCanonicalName: str = MatchTuple[2]
                MatchedRecord: Typing.Dict[str, Typing.Any] = MatchTuple[3]
                AllVersionsList: Typing.List[Typing.Dict[str, Typing.Any]] = VersionsData.get(MatchedCanonicalName, [])
                AvailableSourcesList: Typing.List[str] = [str(V.get("source")) for V in AllVersionsList if V.get("source")]

                ResultsMap[CategoryName].append({
                    "name"            : MatchedCanonicalName,
                    "source"          : str(MatchedRecord.get("source") or "PHB"),
                    "AvailableSources": AvailableSourcesList
                })

        return {
            "Query"  : QueryText,
            "Results": ResultsMap
        }

GLOBAL_EXTERNAL_5ETOOLS: External5ETools = External5ETools()
