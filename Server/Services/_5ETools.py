import json                                as JavaScriptObjectNotation
import pathlib                             as PathLibrary
import typing                              as Typing
import Server.Services.FuzzySearchService  as FuzzySearchService

class _5ETools:
    MULTICLASS_SPELL_SLOT_TABLE: Typing.Dict[int, Typing.List[int]] = {
        1: [2, 0, 0, 0, 0, 0, 0, 0, 0],
        2: [3, 0, 0, 0, 0, 0, 0, 0, 0],
        3: [4, 2, 0, 0, 0, 0, 0, 0, 0],
        4: [4, 3, 0, 0, 0, 0, 0, 0, 0],
        5: [4, 3, 2, 0, 0, 0, 0, 0, 0],
        6: [4, 3, 3, 0, 0, 0, 0, 0, 0],
        7: [4, 3, 3, 1, 0, 0, 0, 0, 0],
        8: [4, 3, 3, 2, 0, 0, 0, 0, 0],
        9: [4, 3, 3, 3, 1, 0, 0, 0, 0],
        10: [4, 3, 3, 3, 2, 0, 0, 0, 0],
        11: [4, 3, 3, 3, 2, 1, 0, 0, 0],
        12: [4, 3, 3, 3, 2, 1, 0, 0, 0],
        13: [4, 3, 3, 3, 2, 1, 1, 0, 0],
        14: [4, 3, 3, 3, 2, 1, 1, 0, 0],
        15: [4, 3, 3, 3, 2, 1, 1, 1, 0],
        16: [4, 3, 3, 3, 2, 1, 1, 1, 0],
        17: [4, 3, 3, 3, 2, 1, 1, 1, 1],
        18: [4, 3, 3, 3, 3, 1, 1, 1, 1],
        19: [4, 3, 3, 3, 3, 2, 1, 1, 1],
        20: [4, 3, 3, 3, 3, 2, 2, 1, 1]
    }

    WARLOCK_PACT_MAGIC_TABLE: Typing.Dict[int, Typing.Tuple[int, int]] = {
        1: (1, 1),
        2: (1, 2),
        3: (2, 2),
        4: (2, 2),
        5: (3, 2),
        6: (3, 2),
        7: (4, 2),
        8: (4, 2),
        9: (5, 2),
        10: (5, 2),
        11: (5, 3),
        12: (5, 3),
        13: (5, 3),
        14: (5, 3),
        15: (5, 3),
        16: (5, 3),
        17: (5, 4),
        18: (5, 4),
        19: (5, 4),
        20: (5, 4)
    }

    def __init__(self, DataDirectoryPath: Typing.Optional[PathLibrary.Path] = None) -> None:
        if DataDirectoryPath is None:
            self.DataDirectoryPath: PathLibrary.Path = PathLibrary.Path(__file__).resolve().parent / "External" / "5eTools" / "data"
        else:
            self.DataDirectoryPath = DataDirectoryPath

        self.ClassesData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {}
        self.SubclassesData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {}
        self.WeaponsData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {}
        self.ItemsData: Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {}
        self.IsInitialized: bool = False
        self.InitializeData()

    def InitializeData(self) -> None:
        if self.IsInitialized:
            return

        ClassDirectory: PathLibrary.Path = self.DataDirectoryPath / "class"
        if ClassDirectory.exists():
            for ClassFilePath in ClassDirectory.glob("class-*.json"):
                if "fluff" in ClassFilePath.name:
                    continue

                try:
                    with open(ClassFilePath, mode = "r", encoding = "utf-8") as ClassFile:
                        ClassJson: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ClassFile)
                        for ClassEntry in ClassJson.get("class", []):
                            ClassName: Typing.Optional[str] = ClassEntry.get("name")
                            if ClassName and ClassName not in self.ClassesData:
                                self.ClassesData[ClassName] = {
                                    "HitDie": ClassEntry.get("hd", {}).get("faces"),
                                    "CasterProgression": ClassEntry.get("casterProgression"),
                                    "SpellcastingAbility": ClassEntry.get("spellcastingAbility"),
                                    "Raw": ClassEntry
                                }

                        for SubclassEntry in ClassJson.get("subclass", []):
                            SubclassName: Typing.Optional[str] = SubclassEntry.get("name")
                            SubclassClassName: Typing.Optional[str] = SubclassEntry.get("className")
                            if SubclassName and SubclassClassName:
                                SubclassKey: str = f"{SubclassClassName}:{SubclassName}"
                                if SubclassKey not in self.SubclassesData:
                                    self.SubclassesData[SubclassKey] = {
                                        "CasterProgression": SubclassEntry.get("casterProgression"),
                                        "SpellcastingAbility": SubclassEntry.get("spellcastingAbility"),
                                        "Raw": SubclassEntry
                                    }
                except Exception:
                    pass

        BaseItemsFilePath: PathLibrary.Path = self.DataDirectoryPath / "items-base.json"
        if BaseItemsFilePath.exists():
            try:
                with open(BaseItemsFilePath, mode = "r", encoding = "utf-8") as BaseItemsFile:
                    BaseItemsJson: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(BaseItemsFile)
                    for BaseItemEntry in BaseItemsJson.get("baseitem", []):
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
                    ItemsJson: Typing.Dict[str, Typing.Any] = JavaScriptObjectNotation.load(ItemsFile)
                    for ItemEntry in ItemsJson.get("item", []):
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

        self.IsInitialized = True

    def FindCanonicalClassName(self, ClassNameQuery: str) -> Typing.Optional[str]:
        KnownClassNames: Typing.List[str] = list(self.ClassesData.keys())
        CanonicalName: Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(ClassNameQuery, KnownClassNames, Cutoff = 0.5)
        return CanonicalName

    def GetClassData(self, ClassName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        CanonicalName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if CanonicalName:
            return self.ClassesData.get(CanonicalName)

        return None

    def GetClassHitDie(self, ClassName: str) -> Typing.Optional[int]:
        ClassInfo: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.GetClassData(ClassName)
        if ClassInfo:
            HitDieValue: Typing.Optional[int] = ClassInfo.get("HitDie")
            if HitDieValue is not None:
                return int(HitDieValue)

        return None

    def GetClassSpellcastingAbility(self, ClassName: str, SubclassName: Typing.Optional[str] = None) -> Typing.Optional[str]:
        CanonicalClassName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if not CanonicalClassName:
            return None

        if SubclassName:
            SubclassKey: str = f"{CanonicalClassName}:{SubclassName}"
            for KnownKey, SubclassInfo in self.SubclassesData.items():
                if KnownKey.lower() == SubclassKey.lower() or SubclassKey.lower() in KnownKey.lower():
                    SubclassAbility: Typing.Optional[str] = SubclassInfo.get("SpellcastingAbility")
                    if SubclassAbility:
                        return SubclassAbility

        ClassInfo: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.ClassesData.get(CanonicalClassName)
        if ClassInfo:
            ClassAbility: Typing.Optional[str] = ClassInfo.get("SpellcastingAbility")
            if ClassAbility:
                return ClassAbility

        return None

    def GetClassCasterProgression(self, ClassName: str, SubclassName: Typing.Optional[str] = None) -> Typing.Optional[str]:
        CanonicalClassName: Typing.Optional[str] = self.FindCanonicalClassName(ClassName)
        if not CanonicalClassName:
            return None

        if SubclassName:
            SubclassKey: str = f"{CanonicalClassName}:{SubclassName}"
            for KnownKey, SubclassInfo in self.SubclassesData.items():
                if KnownKey.lower() == SubclassKey.lower() or SubclassKey.lower() in KnownKey.lower():
                    SubclassProgression: Typing.Optional[str] = SubclassInfo.get("CasterProgression")
                    if SubclassProgression:
                        return SubclassProgression

        ClassInfo: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.ClassesData.get(CanonicalClassName)
        if ClassInfo:
            ClassProgression: Typing.Optional[str] = ClassInfo.get("CasterProgression")
            if ClassProgression:
                return ClassProgression

        return None

    def CalculateHitPoints(self, ClassLevels: Typing.List[Typing.Tuple[str, int, bool]], ConstitutionModifier: int) -> Typing.Tuple[int, bool]:
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
        TotalEffectiveCasterLevel: int = 0
        HasSpellcaster: bool = False

        for ClassName, Level, SubclassName in ClassProgressionList:
            CasterProgression: Typing.Optional[str] = self.GetClassCasterProgression(ClassName, SubclassName)
            if not CasterProgression:
                continue

            if CasterProgression == "full":
                TotalEffectiveCasterLevel += Level
                HasSpellcaster = True
            elif CasterProgression == "1/2":
                TotalEffectiveCasterLevel += Level // 2
                HasSpellcaster = True
            elif CasterProgression == "artificer":
                if len(ClassProgressionList) == 1:
                    TotalEffectiveCasterLevel += (Level + 1) // 2
                else:
                    TotalEffectiveCasterLevel += Level // 2
                HasSpellcaster = True
            elif CasterProgression == "1/3":
                TotalEffectiveCasterLevel += Level // 3
                HasSpellcaster = True

        if not HasSpellcaster or TotalEffectiveCasterLevel <= 0:
            return []

        ClampedLevel: int = min(20, max(1, TotalEffectiveCasterLevel))
        SlotCounts: Typing.List[int] = self.MULTICLASS_SPELL_SLOT_TABLE.get(ClampedLevel, [0] * 9)
        SpellSlotEntries: Typing.List[Typing.Tuple[int, int]] = []

        for SlotIndex, Count in enumerate(SlotCounts):
            SlotLevel: int = SlotIndex + 1
            if Count > 0:
                SpellSlotEntries.append((SlotLevel, Count))

        return SpellSlotEntries

    def CalculatePactMagicSlots(self, WarlockLevel: int) -> Typing.Optional[Typing.Tuple[int, int]]:
        if WarlockLevel <= 0:
            return None

        ClampedLevel: int = min(20, max(1, WarlockLevel))
        PactData: Typing.Optional[Typing.Tuple[int, int]] = self.WARLOCK_PACT_MAGIC_TABLE.get(ClampedLevel)
        return PactData

    def FindCanonicalWeaponName(self, WeaponNameQuery: str) -> Typing.Optional[str]:
        KnownWeaponNames: Typing.List[str] = list(self.WeaponsData.keys())
        CanonicalName: Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(WeaponNameQuery, KnownWeaponNames, Cutoff = 0.5)
        return CanonicalName

    def GetWeaponData(self, WeaponName: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
        CanonicalName: Typing.Optional[str] = self.FindCanonicalWeaponName(WeaponName)
        if CanonicalName:
            return self.WeaponsData.get(CanonicalName)

        ItemMatch: Typing.Optional[str] = FuzzySearchService.FuzzySearchService.FindBestMatch(WeaponName, list(self.ItemsData.keys()), Cutoff = 0.5)
        if ItemMatch:
            ItemEntry: Typing.Dict[str, Typing.Any] = self.ItemsData[ItemMatch]
            BaseItemRef: Typing.Optional[str] = ItemEntry.get("BaseItem")
            if BaseItemRef:
                BaseItemClean: str = BaseItemRef.split("|")[0]
                BaseCanonical: Typing.Optional[str] = self.FindCanonicalWeaponName(BaseItemClean)
                if BaseCanonical:
                    return self.WeaponsData.get(BaseCanonical)

            return ItemEntry

        return None

    def IsWeaponRanged(self, WeaponName: str) -> Typing.Optional[bool]:
        WeaponInfo: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.GetWeaponData(WeaponName)
        if WeaponInfo:
            ItemType: str = WeaponInfo.get("Type", "")
            if ItemType.startswith("R"):
                return True
            if ItemType.startswith("M"):
                return False

        return None

    def IsWeaponFinesse(self, WeaponName: str) -> bool:
        WeaponInfo: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.GetWeaponData(WeaponName)
        if WeaponInfo:
            Properties: Typing.List[str] = WeaponInfo.get("Properties", [])
            for PropertyItem in Properties:
                if PropertyItem == "F" or PropertyItem.startswith("F|"):
                    return True

        return False
