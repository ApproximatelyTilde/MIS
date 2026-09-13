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

class AbilityScoreEntry(Pydantic.BaseModel):
    BaseScore    : int = 10
    BonusScore   : int = 0
    OverrideScore: Typing.Optional[int] = None
    TotalScore   : int = 0
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

class ClassProgressEntry(Pydantic.BaseModel):
    ClassName          : str
    Level              : int
    SubclassName       : Typing.Optional[str] = None
    HitDie             : int
    HitDiceTotal       : int  = 0
    HitDiceUsed        : int  = 0
    IsStartingClass    : bool = False
    SpellcastingAbility: Typing.Optional[AbilityType] = None

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
    IsStabilized: bool = False

class ArmorClassData(Pydantic.BaseModel):
    TotalArmorClass: int = 10
    BaseArmorClass : int = 10
    DexterityBonus : int = 0
    ArmorName      : Typing.Optional[str] = None
    HasShield      : bool = False
    ShieldBonus    : int  = 0
    MagicBonus     : int  = 0
    Notes          : Typing.Optional[str] = None

class SpeedData(Pydantic.BaseModel):
    WalkingSpeedFeet  : int = 30
    FlyingSpeedFeet   : int = 0
    SwimmingSpeedFeet : int = 0
    ClimbingSpeedFeet : int = 0
    BurrowingSpeedFeet: int = 0
    SpecialSpeedNotes : Typing.Optional[str] = None

class SenseEntry(Pydantic.BaseModel):
    SenseType: str
    RangeFeet: int

class SkillProficiencyEntry(Pydantic.BaseModel):
    SkillName        : str
    AssociatedAbility: AbilityType
    ProficiencyTier  : ProficiencyTierType = ProficiencyTierType.NoneTier
    BonusModifier    : int = 0
    PassiveScore     : int

class SavingThrowProficiencyEntry(Pydantic.BaseModel):
    AbilityName  : AbilityType
    IsProficient : bool = False
    BonusModifier: int = 0

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

class LimitedUseData(Pydantic.BaseModel):
    MaxUses  : int
    UsedUses : int = 0
    ResetType: ResetScheduleType = ResetScheduleType.LongRest

class ActionEntry(Pydantic.BaseModel):
    Identifier : str
    Name       : str
    ActionType : ActionActivationType
    SourceType : str
    Description: str
    LimitedUse : Typing.Optional[LimitedUseData] = None

class ContainerEntry(Pydantic.BaseModel):
    Identifier    : str
    Name          : str
    IsCarried     : bool  = True
    WeightPounds  : float = 0.0
    CapacityPounds: Typing.Optional[float] = None

class InventoryItemEntry(Pydantic.BaseModel):
    Identifier         : str
    Name               : str
    Quantity           : int   = 1
    WeightPounds       : float = 0.0
    TotalWeightPounds  : float = 0.0
    CostInGoldPieces   : float = 0.0
    IsEquipped         : bool  = False
    RequiresAttunement : bool  = False
    IsAttuned          : bool  = False
    Rarity             : Typing.Optional[str] = None
    ItemType           : Typing.Optional[str] = None
    ContainerIdentifier: Typing.Optional[str] = None
    Description        : str = ""
    Properties         : Typing.List[str] = Pydantic.Field(default_factory = list)

    @Pydantic.model_validator(mode = "after")
    def CalculateTotalWeight(self) -> "InventoryItemEntry":
        self.TotalWeightPounds = round(self.Quantity * self.WeightPounds, 2)
        return self

class CurrenciesData(Pydantic.BaseModel):
    CopperPieces  : int   = 0
    SilverPieces  : int   = 0
    ElectrumPieces: int   = 0
    GoldPieces    : int   = 0
    PlatinumPieces: int   = 0
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
    Identifier                : str
    Name                      : str
    Level                     : int
    School                    : str
    CastingTime               : str
    RangeDescription          : str
    DurationDescription       : str
    Components                : SpellComponentData = Pydantic.Field(default_factory = SpellComponentData)
    IsConcentration           : bool = False
    IsRitual                  : bool = False
    IsPrepared                : bool = False
    AlwaysPrepared            : bool = False
    SourceType                : str
    Description               : str
    HigherLevelDescription    : Typing.Optional[str]         = None
    DamageOrHealingDescription: Typing.Optional[str]         = None
    SaveAbility               : Typing.Optional[AbilityType] = None

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
    SpellcastingClass  : str
    SpellcastingAbility: AbilityType
    SpellSaveDC        : int
    SpellAttackBonus   : int

class SpellcastingData(Pydantic.BaseModel):
    SpellcastingEntries: Typing.List[SpellcastingEntry]     = Pydantic.Field(default_factory = list)
    SpellSlots         : Typing.List[SpellSlotEntry]        = Pydantic.Field(default_factory = list)
    PactMagic          : Typing.Optional[PactMagicSlotData] = None
    Spells             : Typing.List[SpellEntry]            = Pydantic.Field(default_factory = list)

class FeatureEntry(Pydantic.BaseModel):
    Identifier      : str
    Name            : str
    SourceType      : str
    SourceName      : str
    LevelRequirement: Typing.Optional[int] = None
    Description     : str
    IsEnabled       : bool = True
    LimitedUse      : Typing.Optional[LimitedUseData] = None

class PersonalityData(Pydantic.BaseModel):
    PersonalityTraits: Typing.Optional[str] = None
    Ideals           : Typing.Optional[str] = None
    Bonds            : Typing.Optional[str] = None
    Flaws            : Typing.Optional[str] = None

class PhysicalAppearanceData(Pydantic.BaseModel):
    Age                  : Typing.Optional[str] = None
    Height               : Typing.Optional[str] = None
    Weight               : Typing.Optional[str] = None
    Hair                 : Typing.Optional[str] = None
    Eyes                 : Typing.Optional[str] = None
    Skin                 : Typing.Optional[str] = None
    AppearanceDescription: Typing.Optional[str] = None
    AvatarURL            : Typing.Optional[str] = None
    BackdropAvatarURL    : Typing.Optional[str] = None

class NotesData(Pydantic.BaseModel):
    Backstory          : Typing.Optional[str] = None
    Allies             : Typing.Optional[str] = None
    Enemies            : Typing.Optional[str] = None
    Organizations      : Typing.Optional[str] = None
    PersonalPossessions: Typing.Optional[str] = None
    OtherHoldings      : Typing.Optional[str] = None
    CustomNotes        : Typing.Optional[str] = None

class BackgroundData(Pydantic.BaseModel):
    Name              : str
    Description       : Typing.Optional[str] = None
    FeatureName       : Typing.Optional[str] = None
    FeatureDescription: Typing.Optional[str] = None

class SpeciesData(Pydantic.BaseModel):
    RaceName   : str
    SubraceName: Typing.Optional[str] = None
    FullName   : str
    Description: Typing.Optional[str] = None

class CreatorPreferencesData(Pydantic.BaseModel):
    ProgressionType  : Typing.Optional[str] = None
    EncumbranceType  : Typing.Optional[str] = None
    IgnoreCoinWeight : bool = True
    HitPointType     : Typing.Optional[str] = None
    ShowUnarmedStrike: bool = True
    ShowScaledSpells : bool = True

class DND5thEditionCharacterSheet(Pydantic.BaseModel):
    SchemaVersion           : str = "1.0.0"
    GameSystem              : str = "DND5thEdition"
    OriginalSource          : str = "MIS"
    Name                    : str
    PlayerName              : Typing.Optional[str] = None
    Gender                  : Typing.Optional[str] = None
    Alignment               : Typing.Optional[str] = None
    Faith                   : Typing.Optional[str] = None
    Lifestyle               : Typing.Optional[str] = None
    TotalLevel              : int  = 1
    ExperiencePoints        : int  = 0
    Inspiration             : bool = False
    ProficiencyBonus        : int  = 0
    PassivePerception       : int  = 0
    PassiveInvestigation    : int  = 0
    PassiveInsight          : int  = 0
    InitiativeBonus         : int  = 0
    Species                 : SpeciesData
    Background              : BackgroundData
    Classes                 : Typing.List[ClassProgressEntry]          = Pydantic.Field(default_factory = list)
    AbilityScores           : AbilityScoresData                        = Pydantic.Field(default_factory = AbilityScoresData)
    HitPoints               : HitPointsData                            = Pydantic.Field(default_factory = HitPointsData)
    DeathSaves              : DeathSavesData                           = Pydantic.Field(default_factory = DeathSavesData)
    ArmorClass              : ArmorClassData                           = Pydantic.Field(default_factory = ArmorClassData)
    Speed                   : SpeedData                                = Pydantic.Field(default_factory = SpeedData)
    Senses                  : Typing.List[SenseEntry]                  = Pydantic.Field(default_factory = list)
    SavingThrowProficiencies: Typing.List[SavingThrowProficiencyEntry] = Pydantic.Field(default_factory = list)
    SkillProficiencies      : Typing.List[SkillProficiencyEntry]       = Pydantic.Field(default_factory = list)
    ArmorProficiencies      : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    WeaponProficiencies     : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    ToolProficiencies       : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    LanguageProficiencies   : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    DamageResistances       : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    DamageImmunities        : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    DamageVulnerabilities   : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    ConditionImmunities     : Typing.List[str]                         = Pydantic.Field(default_factory = list)
    Attacks                 : Typing.List[AttackActionEntry]           = Pydantic.Field(default_factory = list)
    Actions                 : Typing.List[ActionEntry]                 = Pydantic.Field(default_factory = list)
    Containers              : Typing.List[ContainerEntry]              = Pydantic.Field(default_factory = list)
    Inventory               : Typing.List[InventoryItemEntry]          = Pydantic.Field(default_factory = list)
    Currencies              : CurrenciesData                           = Pydantic.Field(default_factory = CurrenciesData)
    Spellcasting            : SpellcastingData                         = Pydantic.Field(default_factory = SpellcastingData)
    Features                : Typing.List[FeatureEntry]                = Pydantic.Field(default_factory = list)
    Personality             : PersonalityData                          = Pydantic.Field(default_factory = PersonalityData)
    PhysicalAppearance      : PhysicalAppearanceData                   = Pydantic.Field(default_factory = PhysicalAppearanceData)
    Notes                   : NotesData                                = Pydantic.Field(default_factory = NotesData)
    Preferences             : CreatorPreferencesData                   = Pydantic.Field(default_factory = CreatorPreferencesData)

    @Pydantic.model_validator(mode = "after")
    def ComputeSheetCalculatedValues(self) -> "DND5thEditionCharacterSheet":
        if self.Classes:
            CalculatedLevel: int = sum(ClassItem.Level for ClassItem in self.Classes)
            if CalculatedLevel > 0:
                self.TotalLevel = CalculatedLevel

        if self.ProficiencyBonus <= 0:
            BoundedLevel: int = max(1, min(20, self.TotalLevel))
            self.ProficiencyBonus = 2 + ((BoundedLevel - 1) // 4)

        if self.PassivePerception <= 0:
            self.PassivePerception = 10 + self.AbilityScores.Wisdom.Modifier

        if self.PassiveInvestigation <= 0:
            self.PassiveInvestigation = 10 + self.AbilityScores.Intelligence.Modifier

        if self.PassiveInsight <= 0:
            self.PassiveInsight = 10 + self.AbilityScores.Wisdom.Modifier

        if self.InitiativeBonus == 0:
            self.InitiativeBonus = self.AbilityScores.Dexterity.Modifier

        return self
