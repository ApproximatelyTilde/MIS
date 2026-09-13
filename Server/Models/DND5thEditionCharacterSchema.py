import enum     as Enumeration
import pydantic as Pydantic
import typing   as Typing

class AbilityType(str, Enumeration.Enum):
    Strength     = "Strength"
    Dexterity    = "Dexterity"
    Constitution = "Constitution"
    Intelligence = "Intelligence"
    Wisdom       = "Wisdom"
    Charisma     = "Charisma"

class ProficiencyTierType(str, Enumeration.Enum):
    NoneTier       = "None"
    Proficient     = "Proficient"
    Expertise      = "Expertise"
    HalfProficient = "HalfProficient"

class ResetScheduleType(str, Enumeration.Enum):
    ShortRest = "ShortRest"
    LongRest  = "LongRest"
    Dawn      = "Dawn"
    Manual    = "Manual"
    Other     = "Other"

class ActionActivationType(str, Enumeration.Enum):
    Action      = "Action"
    BonusAction = "BonusAction"
    Reaction    = "Reaction"
    FreeAction  = "FreeAction"
    Special     = "Special"

class ModifierEntry(Pydantic.BaseModel):
    ModifierType   : str
    ModifierSubType: str
    Value          : Typing.Optional[int] = None
    StringValue    : Typing.Optional[str] = None
    IsActive       : bool = True

class AbilityScoreEntry(Pydantic.BaseModel):
    BaseScore    : int = 10
    BonusScore   : int = 0
    OverrideScore: Typing.Optional[int] = None
    TotalScore   : int = 10
    Modifier     : int = 0

    @Pydantic.model_validator(mode = "after")
    def ComputeCalculatedValues(self) -> "AbilityScoreEntry":
        EffectiveScore: int = self.OverrideScore if (self.OverrideScore is not None) else (self.BaseScore + self.BonusScore)
        self.TotalScore = EffectiveScore
        self.Modifier   = (EffectiveScore - 10) // 2
        return self

class AbilityScoresData(Pydantic.BaseModel):
    Strength    : AbilityScoreEntry = Pydantic.Field(default_factory = lambda: AbilityScoreEntry(BaseScore = 10))
    Dexterity   : AbilityScoreEntry = Pydantic.Field(default_factory = lambda: AbilityScoreEntry(BaseScore = 10))
    Constitution: AbilityScoreEntry = Pydantic.Field(default_factory = lambda: AbilityScoreEntry(BaseScore = 10))
    Intelligence: AbilityScoreEntry = Pydantic.Field(default_factory = lambda: AbilityScoreEntry(BaseScore = 10))
    Wisdom      : AbilityScoreEntry = Pydantic.Field(default_factory = lambda: AbilityScoreEntry(BaseScore = 10))
    Charisma    : AbilityScoreEntry = Pydantic.Field(default_factory = lambda: AbilityScoreEntry(BaseScore = 10))
    IsDirty     : bool = False

LEVEL_EXPERIENCE_REQUIREMENTS: Typing.Dict[int, int] = {
    1: 0,
    2: 300,
    3: 900,
    4: 2700,
    5: 6500,
    6: 14000,
    7: 23000,
    8: 34000,
    9: 48000,
    10: 64000,
    11: 85000,
    12: 100000,
    13: 120000,
    14: 140000,
    15: 165000,
    16: 195000,
    17: 225000,
    18: 265000,
    19: 305000,
    20: 355000
}

class ClassProgressEntry(Pydantic.BaseModel):
    ClassName          : str
    Level              : int
    SubclassName       : Typing.Optional[str] = None
    HitDie             : int
    HitDiceTotal       : int = 0
    HitDiceUsed        : int = 0
    IsStartingClass    : bool = False
    SpellcastingAbility: Typing.Optional[AbilityType] = None
    ExperiencePoints   : int = 0
    Modifiers          : Typing.List[ModifierEntry] = Pydantic.Field(default_factory = list)
    IsDirty            : bool = False

    @Pydantic.model_validator(mode = "after")
    def ComputeHitDiceTotal(self) -> "ClassProgressEntry":
        if self.HitDiceTotal <= 0:
            self.HitDiceTotal = self.Level
        return self

class HitPointsData(Pydantic.BaseModel):
    MaxHitPoints      : int = 0
    CurrentHitPoints  : int = 0
    TemporaryHitPoints: int = 0
    BaseHitPoints     : int = 0
    BonusHitPoints    : int = 0
    OverrideHitPoints : Typing.Optional[int] = None
    RemovedHitPoints  : int = 0
    IsDirty           : bool = False

    @Pydantic.model_validator(mode = "after")
    def ComputeHitPoints(self) -> "HitPointsData":
        EffectiveMax: int = self.OverrideHitPoints if (self.OverrideHitPoints is not None) else (self.BaseHitPoints + self.BonusHitPoints)
        if self.MaxHitPoints <= 0:
            self.MaxHitPoints = EffectiveMax
        if self.CurrentHitPoints <= 0 and self.MaxHitPoints > 0:
            self.CurrentHitPoints = max(0, self.MaxHitPoints - self.RemovedHitPoints)
        return self

class DeathSavesData(Pydantic.BaseModel):
    SuccessCount: int = 0
    FailureCount: int = 0

class ArmorClassData(Pydantic.BaseModel):
    TotalArmorClass   : int = 10
    BaseArmorClass    : int = 10
    DexterityBonus    : int = 0
    ArmorName         : Typing.Optional[str] = None
    HasShield         : bool = False
    ShieldBonus       : int = 0
    MagicBonus        : int = 0
    OverrideArmorClass: Typing.Optional[int] = None
    Notes             : Typing.Optional[str] = None

class SpeedData(Pydantic.BaseModel):
    WalkingSpeedFeet          : int = 30
    FlyingSpeedFeet           : int = 0
    SwimmingSpeedFeet         : int = 0
    ClimbingSpeedFeet         : int = 0
    BurrowingSpeedFeet        : int = 0
    OverrideWalkingSpeedFeet  : Typing.Optional[int] = None
    OverrideFlyingSpeedFeet   : Typing.Optional[int] = None
    OverrideSwimmingSpeedFeet : Typing.Optional[int] = None
    OverrideClimbingSpeedFeet : Typing.Optional[int] = None
    OverrideBurrowingSpeedFeet: Typing.Optional[int] = None
    SpecialSpeedNotes         : Typing.Optional[str] = None

class SenseEntry(Pydantic.BaseModel):
    SenseType: str
    RangeFeet: int

class SkillProficiencyEntry(Pydantic.BaseModel):
    SkillName           : str
    AssociatedAbility   : AbilityType
    ProficiencyTier     : ProficiencyTierType = ProficiencyTierType.NoneTier
    BonusModifier       : int = 0
    PassiveScore        : int = 10
    OverrideScore       : Typing.Optional[int] = None
    OverridePassiveScore: Typing.Optional[int] = None

class SavingThrowProficiencyEntry(Pydantic.BaseModel):
    AbilityName  : AbilityType
    IsProficient : bool = False
    BonusModifier: int = 0
    OverrideScore: Typing.Optional[int] = None

class AttackActionEntry(Pydantic.BaseModel):
    Identifier      : str
    Name            : str
    AttackBonus     : int = 0
    DamageExpression: str = ""
    DamageType      : str = ""
    RangeDescription: str
    Properties      : Typing.List[str] = Pydantic.Field(default_factory = list)
    IsEquipped      : bool = True
    AttackSource    : str
    Notes           : Typing.Optional[str] = None
    IsDirty         : bool = False

class LimitedUseData(Pydantic.BaseModel):
    MaxUses  : int
    UsedUses : int = 0
    ResetType: ResetScheduleType = ResetScheduleType.LongRest

class ActionEntry(Pydantic.BaseModel):
    Identifier: str
    Name      : str
    ActionType: ActionActivationType
    SourceType: str
    LimitedUse: Typing.Optional[LimitedUseData] = None
    IsDirty   : bool = False

class ContainerEntry(Pydantic.BaseModel):
    Identifier    : str
    Name          : str
    IsCarried     : bool = True
    WeightPounds  : float = 0.0
    CapacityPounds: Typing.Optional[float] = None

class InventoryItemEntry(Pydantic.BaseModel):
    Identifier         : str
    Name               : str
    Quantity           : int = 1
    WeightPounds       : float = 0.0
    TotalWeightPounds  : float = 0.0
    CostInGoldPieces   : float = 0.0
    IsEquipped         : bool = False
    RequiresAttunement : bool = False
    IsAttuned          : bool = False
    Rarity             : Typing.Optional[str] = None
    ItemType           : Typing.Optional[str] = None
    ContainerIdentifier: Typing.Optional[str] = None
    Properties         : Typing.List[str] = Pydantic.Field(default_factory = list)
    Modifiers          : Typing.List[ModifierEntry] = Pydantic.Field(default_factory = list)
    IsDirty            : bool = False

    @Pydantic.model_validator(mode = "after")
    def CalculateTotalWeight(self) -> "InventoryItemEntry":
        self.TotalWeightPounds = round(self.Quantity * self.WeightPounds, 2)
        return self

class CurrenciesData(Pydantic.BaseModel):
    CopperPieces  : int = 0
    SilverPieces  : int = 0
    ElectrumPieces: int = 0
    GoldPieces    : int = 0
    PlatinumPieces: int = 0
    TotalGoldValue: float = 0.0

    @Pydantic.model_validator(mode = "after")
    def ComputeTotalGoldValue(self) -> "CurrenciesData":
        self.TotalGoldValue = round((self.CopperPieces * 0.01) + (self.SilverPieces * 0.1) + (self.ElectrumPieces * 0.5) + self.GoldPieces + (self.PlatinumPieces * 10.0), 2)
        return self

class SpellComponentData(Pydantic.BaseModel):
    Verbal             : bool = False
    Somatic            : bool = False
    Material           : bool = False
    MaterialDescription: Typing.Optional[str] = None

class SpellEntry(Pydantic.BaseModel):
    Identifier         : str
    Name               : str
    Level              : int
    School             : str
    CastingTime        : str
    RangeDescription   : str
    DurationDescription: str
    Components         : SpellComponentData = Pydantic.Field(default_factory = SpellComponentData)
    IsConcentration    : bool = False
    IsRitual           : bool = False
    IsPrepared         : bool = False
    AlwaysPrepared     : bool = False
    SourceType         : str
    SourceName         : Typing.Optional[str] = None
    SaveAbility        : Typing.Optional[AbilityType] = None
    IsDirty            : bool = False

class SpellSlotEntry(Pydantic.BaseModel):
    Level         : int
    TotalSlots    : int
    UsedSlots     : int = 0
    AvailableSlots: int = 0

    @Pydantic.model_validator(mode = "after")
    def ComputeAvailableSlots(self) -> "SpellSlotEntry":
        self.AvailableSlots = max(0, self.TotalSlots - self.UsedSlots)
        return self

class PactMagicSlotData(Pydantic.BaseModel):
    SlotLevel     : int
    TotalSlots    : int
    UsedSlots     : int = 0
    AvailableSlots: int = 0

    @Pydantic.model_validator(mode = "after")
    def ComputeAvailableSlots(self) -> "PactMagicSlotData":
        self.AvailableSlots = max(0, self.TotalSlots - self.UsedSlots)
        return self

class SpellcastingEntry(Pydantic.BaseModel):
    SpellcastingClass       : str
    SpellcastingAbility     : AbilityType
    SpellSaveDC             : int
    SpellAttackBonus        : int
    OverrideSpellSaveDC     : Typing.Optional[int] = None
    OverrideSpellAttackBonus: Typing.Optional[int] = None
    IsDirty                 : bool = False

class SpellcastingData(Pydantic.BaseModel):
    SpellcastingEntries: Typing.List[SpellcastingEntry] = Pydantic.Field(default_factory = list)
    SpellSlots         : Typing.List[SpellSlotEntry] = Pydantic.Field(default_factory = list)
    PactMagic          : Typing.Optional[PactMagicSlotData] = None
    Spells             : Typing.List[SpellEntry] = Pydantic.Field(default_factory = list)

class FeatureEntry(Pydantic.BaseModel):
    Identifier      : str
    Name            : str
    SourceType      : str
    SourceName      : str
    LevelRequirement: Typing.Optional[int] = None
    IsEnabled       : bool = True
    SelectedChoices : Typing.List[str] = Pydantic.Field(default_factory = list)
    Modifiers       : Typing.List[ModifierEntry] = Pydantic.Field(default_factory = list)
    LimitedUse      : Typing.Optional[LimitedUseData] = None
    IsDirty         : bool = False

class PersonalityData(Pydantic.BaseModel):
    PersonalityTraits: Typing.Optional[str] = None
    Ideals           : Typing.Optional[str] = None
    Bonds            : Typing.Optional[str] = None
    Flaws            : Typing.Optional[str] = None

class PhysicalAppearanceData(Pydantic.BaseModel):
    Age                   : Typing.Optional[str] = None
    Height                : Typing.Optional[str] = None
    Weight                : Typing.Optional[str] = None
    Hair                  : Typing.Optional[str] = None
    Eyes                  : Typing.Optional[str] = None
    Skin                  : Typing.Optional[str] = None
    AppearanceDescription : Typing.Optional[str] = None
    PortraitFileIdentifier: Typing.Optional[str] = None

class NotesData(Pydantic.BaseModel):
    Backstory          : Typing.Optional[str] = None
    Allies             : Typing.Optional[str] = None
    Enemies            : Typing.Optional[str] = None
    Organizations      : Typing.Optional[str] = None
    PersonalPossessions: Typing.Optional[str] = None
    OtherHoldings      : Typing.Optional[str] = None
    CustomNotes        : Typing.Optional[str] = None

class BackgroundData(Pydantic.BaseModel):
    Name       : str
    FeatureName: Typing.Optional[str] = None
    Modifiers  : Typing.List[ModifierEntry] = Pydantic.Field(default_factory = list)

class SpeciesData(Pydantic.BaseModel):
    RaceName   : str
    SubraceName: Typing.Optional[str] = None
    FullName   : str
    Modifiers  : Typing.List[ModifierEntry] = Pydantic.Field(default_factory = list)

class DND5thEditionCharacterSheet(Pydantic.BaseModel):
    SchemaVersion               : str = "1.0.0"
    GameSystem                  : str = "DND5thEdition"
    OriginalSource              : str = "MIS"
    Name                        : str
    PlayerName                  : Typing.Optional[str] = None
    Gender                      : Typing.Optional[str] = None
    Alignment                   : Typing.Optional[str] = None
    Faith                       : Typing.Optional[str] = None
    Lifestyle                   : Typing.Optional[str] = None
    TotalLevel                  : int = 1
    ExperiencePoints            : int = 0
    Inspiration                 : bool = False
    ProficiencyBonus            : int = 0
    OverrideProficiencyBonus    : Typing.Optional[int] = None
    PassivePerception           : int = 0
    OverridePassivePerception   : Typing.Optional[int] = None
    PassiveInvestigation        : int = 0
    OverridePassiveInvestigation: Typing.Optional[int] = None
    PassiveInsight              : int = 0
    OverridePassiveInsight      : Typing.Optional[int] = None
    InitiativeBonus             : int = 0
    OverrideInitiativeBonus     : Typing.Optional[int] = None
    IsDirty                     : bool = False
    Species                     : SpeciesData
    Background                  : BackgroundData
    Classes                     : Typing.List[ClassProgressEntry] = Pydantic.Field(default_factory = list)
    AbilityScores               : AbilityScoresData = Pydantic.Field(default_factory = AbilityScoresData)
    HitPoints                   : HitPointsData = Pydantic.Field(default_factory = HitPointsData)
    DeathSaves                  : DeathSavesData = Pydantic.Field(default_factory = DeathSavesData)
    ArmorClass                  : ArmorClassData = Pydantic.Field(default_factory = ArmorClassData)
    Speed                       : SpeedData = Pydantic.Field(default_factory = SpeedData)
    Senses                      : Typing.List[SenseEntry] = Pydantic.Field(default_factory = list)
    SavingThrowProficiencies    : Typing.List[SavingThrowProficiencyEntry] = Pydantic.Field(default_factory = list)
    SkillProficiencies          : Typing.List[SkillProficiencyEntry] = Pydantic.Field(default_factory = list)
    ArmorProficiencies          : Typing.List[str] = Pydantic.Field(default_factory = list)
    WeaponProficiencies         : Typing.List[str] = Pydantic.Field(default_factory = list)
    ToolProficiencies           : Typing.List[str] = Pydantic.Field(default_factory = list)
    LanguageProficiencies       : Typing.List[str] = Pydantic.Field(default_factory = list)
    DamageResistances           : Typing.List[str] = Pydantic.Field(default_factory = list)
    DamageImmunities            : Typing.List[str] = Pydantic.Field(default_factory = list)
    DamageVulnerabilities       : Typing.List[str] = Pydantic.Field(default_factory = list)
    ConditionImmunities         : Typing.List[str] = Pydantic.Field(default_factory = list)
    Attacks                     : Typing.List[AttackActionEntry] = Pydantic.Field(default_factory = list)
    Actions                     : Typing.List[ActionEntry] = Pydantic.Field(default_factory = list)
    Containers                  : Typing.List[ContainerEntry] = Pydantic.Field(default_factory = list)
    Inventory                   : Typing.List[InventoryItemEntry] = Pydantic.Field(default_factory = list)
    Currencies                  : CurrenciesData = Pydantic.Field(default_factory = CurrenciesData)
    Spellcasting                : SpellcastingData = Pydantic.Field(default_factory = SpellcastingData)
    Features                    : Typing.List[FeatureEntry] = Pydantic.Field(default_factory = list)
    Personality                 : PersonalityData = Pydantic.Field(default_factory = PersonalityData)
    PhysicalAppearance          : PhysicalAppearanceData = Pydantic.Field(default_factory = PhysicalAppearanceData)
    Notes                       : NotesData = Pydantic.Field(default_factory = NotesData)
    Modifiers                   : Typing.List[ModifierEntry] = Pydantic.Field(default_factory = list)

    @Pydantic.model_validator(mode = "after")
    def ComputeSheetCalculatedValues(self) -> "DND5thEditionCharacterSheet":
        if self.Classes:
            CalculatedLevel: int = sum(ClassItem.Level for ClassItem in self.Classes)
            if CalculatedLevel > 0:
                self.TotalLevel = CalculatedLevel

            TotalClassExperience: int = sum(ClassItem.ExperiencePoints for ClassItem in self.Classes)
            if TotalClassExperience == 0 and self.ExperiencePoints > 0:
                InitialClassEntry: ClassProgressEntry = next((ClassItem for ClassItem in self.Classes if ClassItem.IsStartingClass), self.Classes[0])
                InitialClassEntry.ExperiencePoints = self.ExperiencePoints

            for ClassItem in self.Classes:
                MinimumExperience: int = LEVEL_EXPERIENCE_REQUIREMENTS.get(ClassItem.Level, 0)
                if ClassItem.ExperiencePoints < MinimumExperience:
                    ClassItem.ExperiencePoints = MinimumExperience

            self.ExperiencePoints = sum(ClassItem.ExperiencePoints for ClassItem in self.Classes)

        if self.OverrideProficiencyBonus is not None:
            self.ProficiencyBonus = self.OverrideProficiencyBonus
        else:
            BoundedLevel: int = max(1, min(20, self.TotalLevel))
            self.ProficiencyBonus = 2 + ((BoundedLevel - 1) // 4)

        ActiveModifiers: Typing.List[ModifierEntry] = []
        for SheetModifier in self.Modifiers:
            if SheetModifier.IsActive:
                ActiveModifiers.append(SheetModifier)

        for SpeciesModifier in self.Species.Modifiers:
            if SpeciesModifier.IsActive:
                ActiveModifiers.append(SpeciesModifier)

        for BackgroundModifier in self.Background.Modifiers:
            if BackgroundModifier.IsActive:
                ActiveModifiers.append(BackgroundModifier)

        for ClassItem in self.Classes:
            for ClassModifier in ClassItem.Modifiers:
                if ClassModifier.IsActive:
                    ActiveModifiers.append(ClassModifier)

        for FeatureItem in self.Features:
            if FeatureItem.IsEnabled:
                for FeatureModifier in FeatureItem.Modifiers:
                    if FeatureModifier.IsActive:
                        ActiveModifiers.append(FeatureModifier)

        EquippedArmorModifier: Typing.Optional[ModifierEntry] = None
        EquippedShieldModifier: Typing.Optional[ModifierEntry] = None
        EquippedArmorName    : Typing.Optional[str]           = None
        for InventoryItem in self.Inventory:
            if InventoryItem.IsEquipped:
                for ItemModifier in InventoryItem.Modifiers:
                    if ItemModifier.IsActive:
                        ActiveModifiers.append(ItemModifier)
                        if ItemModifier.ModifierSubType.lower() in ["basearmorclass", "armor-class"] and ItemModifier.ModifierType.lower() == "set":
                            EquippedArmorModifier = ItemModifier
                            EquippedArmorName     = InventoryItem.Name
                        elif ItemModifier.ModifierSubType.lower() in ["shieldarmorclass", "shield"] and ItemModifier.ModifierType.lower() == "bonus":
                            EquippedShieldModifier = ItemModifier

        AbilityMap: Typing.Dict[str, AbilityScoreEntry] = {
            "strength": self.AbilityScores.Strength,
            "dexterity": self.AbilityScores.Dexterity,
            "constitution": self.AbilityScores.Constitution,
            "intelligence": self.AbilityScores.Intelligence,
            "wisdom": self.AbilityScores.Wisdom,
            "charisma": self.AbilityScores.Charisma
        }

        for AbilityKey, AbilityEntry in AbilityMap.items():
            if AbilityEntry.OverrideScore is not None:
                AbilityEntry.TotalScore = AbilityEntry.OverrideScore
                AbilityEntry.Modifier   = (AbilityEntry.TotalScore - 10) // 2
                continue

            BonusModifierSum: int = 0
            SetScoreValue: Typing.Optional[int] = None
            for ActiveMod in ActiveModifiers:
                SubtypeKey: str = ActiveMod.ModifierSubType.lower()
                TypeKey   : str = ActiveMod.ModifierType.lower()
                if SubtypeKey == f"{AbilityKey}-score" or SubtypeKey == AbilityKey:
                    if TypeKey == "bonus" and ActiveMod.Value is not None:
                        BonusModifierSum += ActiveMod.Value
                    elif TypeKey == "set" and ActiveMod.Value is not None:
                        if (SetScoreValue is None) or (ActiveMod.Value > SetScoreValue):
                            SetScoreValue = ActiveMod.Value

            CalculatedScore: int = AbilityEntry.BaseScore + AbilityEntry.BonusScore + BonusModifierSum
            if SetScoreValue is not None and SetScoreValue > CalculatedScore:
                CalculatedScore = SetScoreValue

            AbilityEntry.TotalScore = CalculatedScore
            AbilityEntry.Modifier   = (CalculatedScore - 10) // 2

        if self.ArmorClass.OverrideArmorClass is not None:
            self.ArmorClass.TotalArmorClass = self.ArmorClass.OverrideArmorClass
        else:
            BaseArmorValue    : int = 10
            DexterityAllowance: int = self.AbilityScores.Dexterity.Modifier
            ShieldBonusValue  : int = 0

            if EquippedArmorModifier is not None and EquippedArmorModifier.Value is not None:
                BaseArmorValue = EquippedArmorModifier.Value
                ArmorTypeString: str = (EquippedArmorModifier.StringValue or "").lower()
                if "medium" in ArmorTypeString:
                    DexterityAllowance = min(2, max(0, self.AbilityScores.Dexterity.Modifier))
                elif "heavy" in ArmorTypeString:
                    DexterityAllowance = 0
            else:
                UnarmoredSetModifier: Typing.Optional[ModifierEntry] = next((Mod for Mod in ActiveModifiers if Mod.ModifierSubType.lower() in ["unarmored-armor-class", "unarmored"] and Mod.ModifierType.lower() == "set" and Mod.Value is not None), None)
                if UnarmoredSetModifier is not None and UnarmoredSetModifier.Value is not None:
                    BaseArmorValue = UnarmoredSetModifier.Value

            if EquippedShieldModifier is not None and EquippedShieldModifier.Value is not None:
                ShieldBonusValue = EquippedShieldModifier.Value
                self.ArmorClass.HasShield = True
            else:
                self.ArmorClass.HasShield = False

            BonusArmorClassSum: int = 0
            for ActiveMod in ActiveModifiers:
                SubtypeKey: str = ActiveMod.ModifierSubType.lower()
                TypeKey   : str = ActiveMod.ModifierType.lower()
                if (SubtypeKey in ["armor-class", "ac"] or TypeKey in ["armor-class", "ac"]) and TypeKey == "bonus" and ActiveMod.Value is not None:
                    BonusArmorClassSum += ActiveMod.Value

            self.ArmorClass.ArmorName       = EquippedArmorName
            self.ArmorClass.BaseArmorClass  = BaseArmorValue
            self.ArmorClass.DexterityBonus  = DexterityAllowance
            self.ArmorClass.ShieldBonus     = ShieldBonusValue
            self.ArmorClass.TotalArmorClass = BaseArmorValue + DexterityAllowance + ShieldBonusValue + BonusArmorClassSum + self.ArmorClass.MagicBonus

        if self.OverrideInitiativeBonus is not None:
            self.InitiativeBonus = self.OverrideInitiativeBonus
        else:
            InitiativeBonusSum: int = 0
            for ActiveMod in ActiveModifiers:
                if "initiative" in ActiveMod.ModifierSubType.lower() and ActiveMod.ModifierType.lower() == "bonus" and ActiveMod.Value is not None:
                    InitiativeBonusSum += ActiveMod.Value
            self.InitiativeBonus = self.AbilityScores.Dexterity.Modifier + InitiativeBonusSum

        for SaveEntry in self.SavingThrowProficiencies:
            if SaveEntry.OverrideScore is not None:
                SaveEntry.BonusModifier = SaveEntry.OverrideScore
                continue

            SaveAbilityName    : str                                = SaveEntry.AbilityName.value.lower()
            TargetAbilityEntry : Typing.Optional[AbilityScoreEntry] = AbilityMap.get(SaveAbilityName)
            AbilitySaveModifier: int                                = TargetAbilityEntry.Modifier if TargetAbilityEntry else 0
            ProficiencyAdd     : int                                = self.ProficiencyBonus if SaveEntry.IsProficient else 0
            SaveBonusSum       : int                                = 0
            for ActiveMod in ActiveModifiers:
                SubtypeKey: str = ActiveMod.ModifierSubType.lower()
                if (SubtypeKey == f"{SaveAbilityName}-saving-throws" or SubtypeKey == "saving-throws") and ActiveMod.ModifierType.lower() == "bonus" and ActiveMod.Value is not None:
                    SaveBonusSum += ActiveMod.Value
            SaveEntry.BonusModifier = AbilitySaveModifier + ProficiencyAdd + SaveBonusSum

        PerceptionSkillScore   : Typing.Optional[int] = None
        InvestigationSkillScore: Typing.Optional[int] = None
        InsightSkillScore      : Typing.Optional[int] = None

        for SkillEntry in self.SkillProficiencies:
            SkillKey            : str   = SkillEntry.SkillName.lower().replace(" ", "-")
            TargetAbilityEntry          = AbilityMap.get(SkillEntry.AssociatedAbility.value.lower())
            AbilitySkillModifier: int   = TargetAbilityEntry.Modifier if TargetAbilityEntry else 0

            if SkillEntry.OverrideScore is not None:
                SkillEntry.BonusModifier = SkillEntry.OverrideScore
            else:
                TierMultiplier: float = 0.0
                if SkillEntry.ProficiencyTier == ProficiencyTierType.Expertise:
                    TierMultiplier = 2.0
                elif SkillEntry.ProficiencyTier == ProficiencyTierType.Proficient:
                    TierMultiplier = 1.0
                elif SkillEntry.ProficiencyTier == ProficiencyTierType.HalfProficient:
                    TierMultiplier = 0.5

                ProficiencyValue: int = int(self.ProficiencyBonus * TierMultiplier)
                SkillBonusSum   : int = 0
                for ActiveMod in ActiveModifiers:
                    SubtypeKey = ActiveMod.ModifierSubType.lower()
                    if SubtypeKey == SkillKey and ActiveMod.ModifierType.lower() == "bonus" and ActiveMod.Value is not None:
                        SkillBonusSum += ActiveMod.Value
                SkillEntry.BonusModifier = AbilitySkillModifier + ProficiencyValue + SkillBonusSum

            if SkillEntry.OverridePassiveScore is not None:
                SkillEntry.PassiveScore = SkillEntry.OverridePassiveScore
            else:
                SkillEntry.PassiveScore = 10 + SkillEntry.BonusModifier

            if SkillKey == "perception":
                PerceptionSkillScore = SkillEntry.PassiveScore
            elif SkillKey == "investigation":
                InvestigationSkillScore = SkillEntry.PassiveScore
            elif SkillKey == "insight":
                InsightSkillScore = SkillEntry.PassiveScore

        if self.OverridePassivePerception is not None:
            self.PassivePerception = self.OverridePassivePerception
        elif PerceptionSkillScore is not None:
            self.PassivePerception = PerceptionSkillScore
        else:
            self.PassivePerception = 10 + self.AbilityScores.Wisdom.Modifier

        if self.OverridePassiveInvestigation is not None:
            self.PassiveInvestigation = self.OverridePassiveInvestigation
        elif InvestigationSkillScore is not None:
            self.PassiveInvestigation = InvestigationSkillScore
        else:
            self.PassiveInvestigation = 10 + self.AbilityScores.Intelligence.Modifier

        if self.OverridePassiveInsight is not None:
            self.PassiveInsight = self.OverridePassiveInsight
        elif InsightSkillScore is not None:
            self.PassiveInsight = InsightSkillScore
        else:
            self.PassiveInsight = 10 + self.AbilityScores.Wisdom.Modifier

        if self.Speed.OverrideWalkingSpeedFeet is not None:
            self.Speed.WalkingSpeedFeet = self.Speed.OverrideWalkingSpeedFeet
        else:
            WalkingSpeedBonus: int = 0
            for ActiveMod in ActiveModifiers:
                SubtypeKey = ActiveMod.ModifierSubType.lower()
                if (SubtypeKey in ["speed", "innate-speed-walking"]) and ActiveMod.ModifierType.lower() == "bonus" and ActiveMod.Value is not None:
                    WalkingSpeedBonus += ActiveMod.Value
            if WalkingSpeedBonus > 0:
                self.Speed.WalkingSpeedFeet = max(0, self.Speed.WalkingSpeedFeet + WalkingSpeedBonus)

        if self.Speed.OverrideFlyingSpeedFeet is not None:
            self.Speed.FlyingSpeedFeet = self.Speed.OverrideFlyingSpeedFeet
        if self.Speed.OverrideSwimmingSpeedFeet is not None:
            self.Speed.SwimmingSpeedFeet = self.Speed.OverrideSwimmingSpeedFeet
        if self.Speed.OverrideClimbingSpeedFeet is not None:
            self.Speed.ClimbingSpeedFeet = self.Speed.OverrideClimbingSpeedFeet
        if self.Speed.OverrideBurrowingSpeedFeet is not None:
            self.Speed.BurrowingSpeedFeet = self.Speed.OverrideBurrowingSpeedFeet

        for SpellcastingItem in self.Spellcasting.SpellcastingEntries:
            CasterAbilityEntry   : Typing.Optional[AbilityScoreEntry] = AbilityMap.get(SpellcastingItem.SpellcastingAbility.value.lower())
            CasterAbilityModifier: int                                = CasterAbilityEntry.Modifier if CasterAbilityEntry else 0
            if SpellcastingItem.OverrideSpellSaveDC is not None:
                SpellcastingItem.SpellSaveDC = SpellcastingItem.OverrideSpellSaveDC
            else:
                SpellcastingItem.SpellSaveDC = 8 + self.ProficiencyBonus + CasterAbilityModifier

            if SpellcastingItem.OverrideSpellAttackBonus is not None:
                SpellcastingItem.SpellAttackBonus = SpellcastingItem.OverrideSpellAttackBonus
            else:
                SpellcastingItem.SpellAttackBonus = self.ProficiencyBonus + CasterAbilityModifier

        return self
