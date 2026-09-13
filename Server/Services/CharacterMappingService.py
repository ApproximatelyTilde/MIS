import html                                         as HyperTextMarkupLanguage
import re                                           as RegularExpressions
import typing                                       as Typing
import Server.Models.DND5thEditionCharacterSchema   as CharacterSchema
import Server.Services.External5ETools             as External5ETools
import Server.Services.DebugService                 as DebugService
import Server.Services.FuzzySearchService           as FuzzySearchService

class CharacterMappingService:
    def __init__(self) -> None:
        self.FiveETools: External5ETools.External5ETools = External5ETools.External5ETools()

    SkillAbilityMapping: Typing.Dict[str, CharacterSchema.AbilityType] = {
        "acrobatics": CharacterSchema.AbilityType.Dexterity,
        "animal-handling": CharacterSchema.AbilityType.Wisdom,
        "animalhandling": CharacterSchema.AbilityType.Wisdom,
        "arcana": CharacterSchema.AbilityType.Intelligence,
        "athletics": CharacterSchema.AbilityType.Strength,
        "deception": CharacterSchema.AbilityType.Charisma,
        "history": CharacterSchema.AbilityType.Intelligence,
        "insight": CharacterSchema.AbilityType.Wisdom,
        "intimidation": CharacterSchema.AbilityType.Charisma,
        "investigation": CharacterSchema.AbilityType.Intelligence,
        "medicine": CharacterSchema.AbilityType.Wisdom,
        "nature": CharacterSchema.AbilityType.Intelligence,
        "perception": CharacterSchema.AbilityType.Wisdom,
        "performance": CharacterSchema.AbilityType.Charisma,
        "persuasion": CharacterSchema.AbilityType.Charisma,
        "religion": CharacterSchema.AbilityType.Intelligence,
        "sleight-of-hand": CharacterSchema.AbilityType.Dexterity,
        "sleightofhand": CharacterSchema.AbilityType.Dexterity,
        "stealth": CharacterSchema.AbilityType.Dexterity,
        "survival": CharacterSchema.AbilityType.Wisdom
    }

    ClassHitDieMapping: Typing.Dict[str, int] = {
        "barbarian": 12,
        "fighter": 10,
        "paladin": 10,
        "ranger": 10,
        "bard": 8,
        "cleric": 8,
        "druid": 8,
        "monk": 8,
        "rogue": 8,
        "warlock": 8,
        "sorcerer": 6,
        "wizard": 6,
        "artificer": 8
    }

    AlignmentMapping: Typing.Dict[int, str] = {
        1: "Lawful Good",
        2: "Neutral Good",
        3: "Chaotic Good",
        4: "Lawful Neutral",
        5: "Neutral",
        6: "Chaotic Neutral",
        7: "Lawful Evil",
        8: "Neutral Evil",
        9: "Chaotic Evil"
    }

    DamageMultiplierStatMapping: Typing.Dict[str, str] = {
        "acidmultiplier": "Acid",
        "bludgeoningmultiplier": "Bludgeoning",
        "coldmultiplier": "Cold",
        "firemultiplier": "Fire",
        "forcemultiplier": "Force",
        "lightningmultiplier": "Lightning",
        "necroticmultiplier": "Necrotic",
        "piercingmultiplier": "Piercing",
        "poisonmultiplier": "Poison",
        "psychicmultiplier": "Psychic",
        "radiantmultiplier": "Radiant",
        "slashingmultiplier": "Slashing",
        "thundermultiplier": "Thunder"
    }

    @staticmethod
    def MapStringToAbilityType(AbilityString: Typing.Optional[str]) -> Typing.Optional[CharacterSchema.AbilityType]:
        if not AbilityString:
            return None

        CleanedString: str = AbilityString.strip().lower()
        if "str" in CleanedString:
            return CharacterSchema.AbilityType.Strength
        if "dex" in CleanedString:
            return CharacterSchema.AbilityType.Dexterity
        if "con" in CleanedString:
            return CharacterSchema.AbilityType.Constitution
        if "int" in CleanedString:
            return CharacterSchema.AbilityType.Intelligence
        if "wis" in CleanedString:
            return CharacterSchema.AbilityType.Wisdom
        if "cha" in CleanedString:
            return CharacterSchema.AbilityType.Charisma

        return None

    @staticmethod
    def ExtractNumericStat(RawValue: Typing.Any, Default: int = 0) -> int:
        if RawValue is None:
            return Default
        if isinstance(RawValue, (int, float)):
            return int(RawValue)
        if isinstance(RawValue, dict):
            ValueCandidate = RawValue.get("adjustment", RawValue.get("value", Default))
            if ValueCandidate is not None and isinstance(ValueCandidate, (int, float)):
                return int(ValueCandidate)
            return Default
        if isinstance(RawValue, str) and RawValue.strip().lstrip("-").isdigit():
            return int(RawValue.strip())
        return Default

    def EvaluateDicecloudFormula(self, Expression: Typing.Any, Context: Typing.Dict[str, int]) -> int:
        if Expression is None:
            return 1

        ExpressionString: str = str(Expression).strip()
        if not ExpressionString:
            return 1

        if ExpressionString.isdigit():
            return max(1, int(ExpressionString))

        for ContextKey, ContextValue in Context.items():
            Pattern: str = rf"\b{ContextKey}\b"
            ExpressionString = RegularExpressions.sub(Pattern, str(ContextValue), ExpressionString, flags = RegularExpressions.IGNORECASE)

        Index: int = ExpressionString.rfind("if(")
        while Index != -1:
            Depth: int = 1
            Position: int = Index + 3
            CommaIndices: Typing.List[int] = []
            while Position < len(ExpressionString) and Depth > 0:
                Character: str = ExpressionString[Position]
                if Character == "(":
                    Depth += 1
                elif Character == ")":
                    Depth -= 1
                elif Character == "," and Depth == 1:
                    CommaIndices.append(Position)
                Position += 1

            if len(CommaIndices) == 2 and Depth == 0:
                ConditionExpression: str = ExpressionString[Index + 3:CommaIndices[0]].strip()
                ThenExpression: str = ExpressionString[CommaIndices[0] + 1:CommaIndices[1]].strip()
                ElseExpression: str = ExpressionString[CommaIndices[1] + 1:Position - 1].strip()
                Replacement: str = f"(({ThenExpression}) if ({ConditionExpression}) else ({ElseExpression}))"
                ExpressionString = ExpressionString[:Index] + Replacement + ExpressionString[Position:]

            Index = ExpressionString.rfind("if(")

        try:
            EvaluatedResult = eval(ExpressionString, {
                "__builtins__": {}
            })
            return max(1, int(EvaluatedResult))
        except Exception:
            return 1

    def CleanHTMLString(self, RawText: Typing.Optional[str]) -> Typing.Optional[str]:
        if not RawText:
            return None

        CleanedText: str = RegularExpressions.sub(r"<[^>]+>", "", RawText)
        UnescapedText: str = HyperTextMarkupLanguage.unescape(CleanedText)
        FinalString: str = UnescapedText.strip()
        return FinalString if FinalString else None

    def ComputeProficiencyBonusForLevel(self, TotalLevel: int) -> int:
        BoundedLevel: int = max(1, min(20, TotalLevel))
        return 2 + ((BoundedLevel - 1) // 4)

    @staticmethod
    def ConvertRawModifier(RawModifierItem: Typing.Dict[str, Typing.Any]) -> CharacterSchema.ModifierEntry:
        RawValue = RawModifierItem.get("value")
        FixedValue = RawModifierItem.get("fixedValue")
        ParsedValue: Typing.Optional[int] = None
        if isinstance(RawValue, int):
            ParsedValue = RawValue
        elif isinstance(FixedValue, int):
            ParsedValue = FixedValue

        ModifierTypeValue: str = str(RawModifierItem.get("type") or RawModifierItem.get("friendlyTypeName") or "")
        ModifierSubtypeValue: str = str(RawModifierItem.get("subType") or RawModifierItem.get("friendlySubtypeName") or "")
        StringValueText: Typing.Optional[str] = RawModifierItem.get("friendlySubtypeName") or RawModifierItem.get("subType")

        return CharacterSchema.ModifierEntry(
            ModifierType = ModifierTypeValue,
            ModifierSubType = ModifierSubtypeValue,
            Value = ParsedValue,
            StringValue = str(StringValueText) if StringValueText else None,
            IsActive = True
        )

    def MapDNDBeyondCharacter(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        Data: Typing.Dict[str, Typing.Any] = RawJSON.get("data", RawJSON)
        CharacterName: str = str(Data["name"]).strip()
        PlayerName: Typing.Optional[str] = Data.get("username")
        Gender: Typing.Optional[str] = Data.get("gender")
        Faith: Typing.Optional[str] = Data.get("faith")
        AlignmentID: Typing.Optional[int] = Data.get("alignmentId")
        AlignmentString: Typing.Optional[str] = self.AlignmentMapping.get(AlignmentID) if AlignmentID else None

        AppearanceData = CharacterSchema.PhysicalAppearanceData(
            Age = str(Data.get("age")) if (Data.get("age") is not None) else None,
            Height = Data.get("height"),
            Weight = str(Data.get("weight")) if (Data.get("weight") is not None) else None,
            Hair = Data.get("hair"),
            Eyes = Data.get("eyes"),
            Skin = Data.get("skin"),
            AppearanceDescription = self.CleanHTMLString(Data.get("traits", {}).get("appearance"))
        )

        AllModifiers: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = Data.get("modifiers", {}) or {}

        RaceModifiers: Typing.List[CharacterSchema.ModifierEntry] = [
            self.ConvertRawModifier(ModItem) for ModItem in AllModifiers.get("race", []) if ModItem
        ]
        RaceDataDictionary: Typing.Dict[str, Typing.Any] = Data.get("race", {}) or {}
        SpeciesModel = CharacterSchema.SpeciesData(
            RaceName = str(RaceDataDictionary.get("baseRaceName") or RaceDataDictionary["fullName"]),
            SubraceName = RaceDataDictionary.get("fullName") if RaceDataDictionary.get("isSubRace") else None,
            FullName = str(RaceDataDictionary["fullName"]),
            Modifiers = RaceModifiers
        )

        BackgroundModifiers: Typing.List[CharacterSchema.ModifierEntry] = [
            self.ConvertRawModifier(ModItem) for ModItem in AllModifiers.get("background", []) if ModItem
        ]
        BackgroundDictionary: Typing.Dict[str, Typing.Any] = Data.get("background", {}) or {}
        BackgroundDefinition: Typing.Dict[str, Typing.Any] = BackgroundDictionary.get("definition", {}) or {}
        BackgroundModel = CharacterSchema.BackgroundData(
            Name = str(BackgroundDefinition["name"]),
            FeatureName = BackgroundDefinition.get("featureName"),
            Modifiers = BackgroundModifiers
        )

        ClassesList: Typing.List[CharacterSchema.ClassProgressEntry] = []
        TotalCharacterLevel: int = 0
        HasAnyClassDirty: bool = False
        for ClassItem in Data.get("classes", []):
            ClassDefinition: Typing.Dict[str, Typing.Any] = ClassItem.get("definition", {}) or {}
            SubclassDefinition: Typing.Dict[str, Typing.Any] = ClassItem.get("subclassDefinition", {}) or {}
            RawClassName: str = str(ClassDefinition["name"])
            CanonicalClassName: Typing.Optional[str] = self.FiveETools.FindCanonicalClassName(RawClassName)
            IsClassDirty: bool = False
            if CanonicalClassName:
                ClassName: str = CanonicalClassName
            else:
                ClassName = RawClassName
                IsClassDirty = True
                HasAnyClassDirty = True

            ClassLevel: int = int(ClassItem["level"])
            TotalCharacterLevel += ClassLevel
            
            ExpectedHitDie: Typing.Optional[int] = self.FiveETools.GetClassHitDie(ClassName)
            ProvidedHitDie: int = int(ClassDefinition["hitDice"])
            HitDieValue: int = ExpectedHitDie if ExpectedHitDie is not None else ProvidedHitDie
            if ExpectedHitDie is None or ExpectedHitDie != ProvidedHitDie:
                IsClassDirty = True
                HasAnyClassDirty = True

            SpentDice: int = int(ClassItem.get("hitDiceUsed", 0) or 0)
            IsStarting: bool = bool(ClassItem.get("isStartingClass", False))
            
            SubclassName: Typing.Optional[str] = SubclassDefinition.get("name")
            SpellcastingAbilityStr: Typing.Optional[str] = self.FiveETools.GetClassSpellcastingAbility(ClassName, SubclassName)
            SpellcastingAbilityEnum: Typing.Optional[CharacterSchema.AbilityType] = self.MapStringToAbilityType(SpellcastingAbilityStr)
            
            ClassesList.append(CharacterSchema.ClassProgressEntry(
                ClassName = ClassName,
                Level = ClassLevel,
                SubclassName = SubclassName,
                HitDie = HitDieValue,
                HitDiceTotal = ClassLevel,
                HitDiceUsed = SpentDice,
                IsStartingClass = IsStarting,
                SpellcastingAbility = SpellcastingAbilityEnum,
                IsDirty = IsClassDirty
            ))

        ComputedProficiencyBonus: int = self.ComputeProficiencyBonusForLevel(TotalCharacterLevel)

        StatsList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("stats", []) or []
        BonusStatsList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("bonusStats", []) or []
        OverrideStatsList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("overrideStats", []) or []

        def ExtractAbility(Index: int) -> CharacterSchema.AbilityScoreEntry:
            BaseValue: int = StatsList[Index].get("value", 10) if (len(StatsList) > Index and StatsList[Index].get("value") is not None) else 10
            BonusValue: int = BonusStatsList[Index].get("value", 0) if (len(BonusStatsList) > Index and BonusStatsList[Index].get("value") is not None) else 0
            OverrideValue: Typing.Optional[int] = OverrideStatsList[Index].get("value") if (len(OverrideStatsList) > Index and OverrideStatsList[Index].get("value") is not None) else None
            return CharacterSchema.AbilityScoreEntry(BaseScore = BaseValue, BonusScore = BonusValue, OverrideScore = OverrideValue)

        AbilityScoresModel = CharacterSchema.AbilityScoresData(
            Strength = ExtractAbility(0),
            Dexterity = ExtractAbility(1),
            Constitution = ExtractAbility(2),
            Intelligence = ExtractAbility(3),
            Wisdom = ExtractAbility(4),
            Charisma = ExtractAbility(5)
        )

        BaseHitPoints: int = Data.get("baseHitPoints", 10) or 10
        BonusHitPoints: int = Data.get("bonusHitPoints", 0) or 0
        OverrideHitPoints: Typing.Optional[int] = Data.get("overrideHitPoints")
        RemovedHitPoints: int = Data.get("removedHitPoints", 0) or 0
        TemporaryHitPoints: int = Data.get("temporaryHitPoints", 0) or 0
        EffectiveMaxHitPoints: int = OverrideHitPoints if (OverrideHitPoints is not None) else (BaseHitPoints + BonusHitPoints)
        CurrentHitPoints: int = max(0, EffectiveMaxHitPoints - RemovedHitPoints)

        HitPointsModel = CharacterSchema.HitPointsData(
            MaxHitPoints = EffectiveMaxHitPoints,
            CurrentHitPoints = CurrentHitPoints,
            TemporaryHitPoints = TemporaryHitPoints,
            BaseHitPoints = BaseHitPoints,
            BonusHitPoints = BonusHitPoints,
            OverrideHitPoints = OverrideHitPoints,
            RemovedHitPoints = RemovedHitPoints
        )

        DeathSavesDictionary: Typing.Dict[str, Typing.Any] = Data.get("deathSaves", {}) or {}
        DeathSavesModel = CharacterSchema.DeathSavesData(
            SuccessCount = DeathSavesDictionary.get("successCount", 0) or 0,
            FailureCount = DeathSavesDictionary.get("failCount", 0) or 0
        )

        OptionNameMapping: Typing.Dict[int, str] = {
        }
        for GroupOptionList in (Data.get("options", {}) or {}).values():
            if isinstance(GroupOptionList, list):
                for OptionItem in GroupOptionList:
                    OptionDefinition: Typing.Dict[str, Typing.Any] = OptionItem.get("definition", {}) or {}
                    OptionID: Typing.Optional[int] = OptionDefinition.get("id")
                    OptionName: Typing.Optional[str] = OptionDefinition.get("name")
                    if OptionID is not None and OptionName:
                        OptionNameMapping[OptionID] = OptionName

        ChoiceNameMapping: Typing.Dict[str, Typing.List[str]] = {
        }
        for GroupChoiceList in (Data.get("choices", {}) or {}).values():
            if isinstance(GroupChoiceList, list):
                for ChoiceItem in GroupChoiceList:
                    ComponentIDString: str = str(ChoiceItem.get("componentId") or "")
                    OptionValueID = ChoiceItem.get("optionValue")
                    SelectedNameCandidate: Typing.Optional[str] = None
                    if OptionValueID is not None and OptionValueID in OptionNameMapping:
                        SelectedNameCandidate = OptionNameMapping[OptionValueID]
                    elif ChoiceItem.get("label"):
                        LabelText: str = str(ChoiceItem.get("label"))
                        if not LabelText.lower().startswith("choose"):
                            SelectedNameCandidate = LabelText

                    if ComponentIDString and SelectedNameCandidate:
                        if ComponentIDString not in ChoiceNameMapping:
                            ChoiceNameMapping[ComponentIDString] = []
                        if SelectedNameCandidate not in ChoiceNameMapping[ComponentIDString]:
                            ChoiceNameMapping[ComponentIDString].append(SelectedNameCandidate)

        ComponentModifierMapping: Typing.Dict[str, Typing.List[CharacterSchema.ModifierEntry]] = {
        }
        TopLevelModifiersList: Typing.List[CharacterSchema.ModifierEntry] = []

        for ModifierCategoryName in ["class", "feat"]:
            for RawModifier in AllModifiers.get(ModifierCategoryName, []):
                if not RawModifier:
                    continue
                ConvertedModifier: CharacterSchema.ModifierEntry = self.ConvertRawModifier(RawModifier)
                ComponentIdentifier: Typing.Optional[str] = str(RawModifier.get("componentId")) if RawModifier.get("componentId") else None
                if ComponentIdentifier:
                    if ComponentIdentifier not in ComponentModifierMapping:
                        ComponentModifierMapping[ComponentIdentifier] = []
                    ComponentModifierMapping[ComponentIdentifier].append(ConvertedModifier)
                else:
                    TopLevelModifiersList.append(ConvertedModifier)

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        for FeatItem in Data.get("feats", []):
            FeatDefinition: Typing.Dict[str, Typing.Any] = FeatItem.get("definition", {}) or {}
            FeatName: str = str(FeatDefinition["name"])
            ComponentIdentifierKey: str = str(FeatItem.get("componentId", ""))
            AssignedChoices: Typing.List[str] = ChoiceNameMapping.get(ComponentIdentifierKey, [])
            AssignedModifiers: Typing.List[CharacterSchema.ModifierEntry] = ComponentModifierMapping.get(ComponentIdentifierKey, [])
            FeaturesList.append(CharacterSchema.FeatureEntry(
                Identifier = ComponentIdentifierKey,
                Name = FeatName,
                SourceType = "Feat",
                SourceName = "Feats",
                SelectedChoices = AssignedChoices,
                Modifiers = AssignedModifiers
            ))

        for ClassProgress in Data.get("classes", []):
            ClassProgressionName: str = str(ClassProgress.get("definition", {}).get("name") or "")
            for ClassFeature in ClassProgress.get("classFeatures", []):
                FeatureDefinition: Typing.Dict[str, Typing.Any] = ClassFeature.get("definition", {}) or {}
                FeatureIdentifierKey: str = str(FeatureDefinition.get("id", ""))
                FeatureName: str = str(FeatureDefinition["name"])
                RequiredLevel: int = FeatureDefinition.get("requiredLevel", 1)
                AssignedChoices = ChoiceNameMapping.get(FeatureIdentifierKey, [])
                AssignedModifiers = ComponentModifierMapping.get(FeatureIdentifierKey, [])
                FeaturesList.append(CharacterSchema.FeatureEntry(
                    Identifier = FeatureIdentifierKey,
                    Name = FeatureName,
                    SourceType = "Class",
                    SourceName = ClassProgressionName,
                    LevelRequirement = RequiredLevel,
                    SelectedChoices = AssignedChoices,
                    Modifiers = AssignedModifiers
                ))

        ItemModifierMapping: Typing.Dict[str, Typing.List[CharacterSchema.ModifierEntry]] = {
        }
        for RawItemModifier in AllModifiers.get("item", []):
            if not RawItemModifier:
                continue
            ConvertedItemModifier: CharacterSchema.ModifierEntry = self.ConvertRawModifier(RawItemModifier)
            ItemComponentID: Typing.Optional[str] = str(RawItemModifier.get("componentId")) if RawItemModifier.get("componentId") else None
            if ItemComponentID:
                if ItemComponentID not in ItemModifierMapping:
                    ItemModifierMapping[ItemComponentID] = []
                ItemModifierMapping[ItemComponentID].append(ConvertedItemModifier)

        InventoryList: Typing.List[CharacterSchema.InventoryItemEntry] = []
        ContainersList: Typing.List[CharacterSchema.ContainerEntry] = []
        SeenContainers: Typing.Dict[str, bool] = {
        }

        for RawItem in Data.get("inventory", []):
            ItemDefinition: Typing.Dict[str, Typing.Any] = RawItem.get("definition", {}) or {}
            ItemName: str = str(ItemDefinition["name"])
            ItemQuantity: int = RawItem.get("quantity", 1) or 1
            ItemWeight: float = float(ItemDefinition.get("weight", 0.0) or 0.0)
            ItemCost: float = float(ItemDefinition.get("cost", 0.0) or 0.0)
            IsEquipped: bool = RawItem.get("equipped", False) or False
            IsAttuned: bool = RawItem.get("isAttuned", False) or False
            NeedsAttunement: bool = ItemDefinition.get("canAttune", False) or False
            RarityText: Typing.Optional[str] = ItemDefinition.get("rarity")
            ItemFilterType: Typing.Optional[str] = ItemDefinition.get("filterType")
            ContainerID: Typing.Optional[str] = str(RawItem.get("containerEntityId")) if RawItem.get("containerEntityId") else None
            RawItemIDString: str = str(RawItem.get("id", ""))
            DefinitionIDString: str = str(ItemDefinition.get("id", ""))

            ItemModifiersList: Typing.List[CharacterSchema.ModifierEntry] = []
            for GrantedModifier in ItemDefinition.get("grantedModifiers", []):
                if GrantedModifier:
                    ItemModifiersList.append(self.ConvertRawModifier(GrantedModifier))

            if RawItemIDString in ItemModifierMap:
                ItemModifiersList.extend(ItemModifierMap[RawItemIDString])
            elif DefinitionIDString in ItemModifierMap:
                ItemModifiersList.extend(ItemModifierMap[DefinitionIDString])

            ArmorClassValue: int = int(ItemDefinition.get("armorClass", 0) or 0)
            ArmorTypeIDValue: int = int(ItemDefinition.get("armorTypeId", 1) or 1)
            if ItemFilterType == "Armor":
                if ArmorTypeIDValue == 4:
                    ItemModifiersList.append(CharacterSchema.ModifierEntry(
                        ModifierType = "Bonus",
                        ModifierSubType = "ShieldArmorClass",
                        Value = ArmorClassValue if ArmorClassValue > 0 else 2,
                        StringValue = "Shield",
                        IsActive = True
                    ))
                elif ArmorClassValue > 0:
                    ArmorTypeNameString: str = "Light" if ArmorTypeIDValue == 1 else ("Medium" if ArmorTypeIDValue == 2 else "Heavy")
                    ItemModifiersList.append(CharacterSchema.ModifierEntry(
                        ModifierType = "Set",
                        ModifierSubType = "BaseArmorClass",
                        Value = ArmorClassValue,
                        StringValue = ArmorTypeNameString,
                        IsActive = True
                    ))

            if ItemFilterType == "Container" or "backpack" in ItemName.lower() or "pouch" in ItemName.lower():
                ContainerIdentifierKey: str = str(RawItem.get("id"))
                if ContainerIdentifierKey not in SeenContainers:
                    SeenContainers[ContainerIdentifierKey] = True
                    ContainersList.append(CharacterSchema.ContainerEntry(Identifier = ContainerIdentifierKey, Name = ItemName, IsCarried = True, WeightPounds = ItemWeight))

            InventoryList.append(CharacterSchema.InventoryItemEntry(
                Identifier = RawItemIDString,
                Name = ItemName,
                Quantity = ItemQuantity,
                WeightPounds = ItemWeight,
                CostInGoldPieces = ItemCost,
                IsEquipped = IsEquipped,
                RequiresAttunement = NeedsAttunement,
                IsAttuned = IsAttuned,
                Rarity = RarityText,
                ItemType = ItemFilterType,
                ContainerIdentifier = ContainerID,
                Properties = [],
                Modifiers = ItemModifiersList
            ))

        SpellsList: Typing.List[CharacterSchema.SpellEntry] = []
        SeenSpellNames: Typing.Dict[str, bool] = {
        }

        def ProcessSpellItem(RawSpellItem: Typing.Dict[str, Typing.Any], SourceOrigin: str, SourceOriginName: Typing.Optional[str] = None) -> None:
            SpellDefinition: Typing.Dict[str, Typing.Any] = RawSpellItem.get("definition", {}) or {}
            SpellName: str = str(SpellDefinition["name"])
            if not SpellName or SpellName in SeenSpellNames:
                return

            SeenSpellNames[SpellName] = True
            SpellLevel: int = SpellDefinition.get("level", 0)
            SchoolName: str = str(SpellDefinition["school"])
            ActivationDictionary: Typing.Dict[str, Typing.Any] = SpellDefinition.get("activation", {}) or {}
            ActivationTime: int = ActivationDictionary.get("activationTime", 1) or 1
            CastingDescription: str = f"{ActivationTime} Action" if ActivationDictionary.get("activationType") == 1 else "Special"
            RangeDictionary: Typing.Dict[str, Typing.Any] = SpellDefinition.get("range", {}) or {}
            RangeOrigin: str = RangeDictionary.get("origin", "Self") or "Self"
            RangeValue: int = RangeDictionary.get("rangeValue", 0) or 0
            RangeDescriptionText: str = f"{RangeValue} ft" if RangeValue > 0 else RangeOrigin
            DurationDictionary: Typing.Dict[str, Typing.Any] = SpellDefinition.get("duration", {}) or {}
            DurationDescriptionText: str = DurationDictionary.get("durationType", "Instantaneous") or "Instantaneous"
            IsConcentration: bool = SpellDefinition.get("concentration", False) or False
            IsRitual: bool = SpellDefinition.get("ritual", False) or False
            IsPrepared: bool = RawSpellItem.get("prepared", False) or False
            AlwaysPrepared: bool = RawSpellItem.get("alwaysPrepared", False) or False
            ComponentsString: str = str(SpellDefinition.get("components", ""))
            HasVerbal: bool = "1" in ComponentsString
            HasSomatic: bool = "2" in ComponentsString
            HasMaterial: bool = "3" in ComponentsString
            MaterialText: Typing.Optional[str] = SpellDefinition.get("componentsDescription")

            SpellsList.append(CharacterSchema.SpellEntry(
                Identifier = str(RawSpellItem.get("id", "")),
                Name = SpellName,
                Level = SpellLevel,
                School = SchoolName,
                CastingTime = CastingDescription,
                RangeDescription = RangeDescriptionText,
                DurationDescription = DurationDescriptionText,
                Components = CharacterSchema.SpellComponentData(Verbal = HasVerbal, Somatic = HasSomatic, Material = HasMaterial, MaterialDescription = MaterialText),
                IsConcentration = IsConcentration,
                IsRitual = IsRitual,
                IsPrepared = IsPrepared or AlwaysPrepared,
                AlwaysPrepared = AlwaysPrepared,
                SourceType = SourceOrigin,
                SourceName = SourceOriginName
            ))

        SpellsGroupDictionary: Typing.Dict[str, Typing.Any] = Data.get("spells", {}) or {}
        for GroupOriginName, GroupSpellList in SpellsGroupDictionary.items():
            if isinstance(GroupSpellList, list):
                for SpellObject in GroupSpellList:
                    ProcessSpellItem(SpellObject, GroupOriginName.capitalize(), GroupOriginName.capitalize())

        for ClassSpellGroup in Data.get("classSpells", []):
            MatchedClassName: str = "Class"
            for SpellGroupClass in Data.get("classes", []):
                if SpellGroupClass.get("id") == ClassSpellGroup.get("characterClassId"):
                    MatchedClassName = SpellGroupClass.get("definition", {}).get("name", "Class")
            for ClassSpellItem in ClassSpellGroup.get("spells", []):
                ProcessSpellItem(ClassSpellItem, "Class", MatchedClassName)

        SpellSlotsList: Typing.List[CharacterSchema.SpellSlotEntry] = []
        for SlotItem in Data.get("spellSlots", []):
            SlotLevel: int = SlotItem.get("level", 1)
            SlotUsed: int = SlotItem.get("used", 0) or 0
            SlotTotal: int = SlotItem.get("available", 0) or 0
            SpellSlotsList.append(CharacterSchema.SpellSlotEntry(Level = SlotLevel, TotalSlots = SlotTotal, UsedSlots = SlotUsed))

        PactMagicSlotModel: Typing.Optional[CharacterSchema.PactMagicSlotData] = None
        PactMagicRawList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("pactMagic", []) or []
        if PactMagicRawList:
            FirstPactSlot: Typing.Dict[str, Typing.Any] = PactMagicRawList[0]
            PactMagicSlotModel = CharacterSchema.PactMagicSlotData(
                SlotLevel = FirstPactSlot.get("level", 1),
                TotalSlots = FirstPactSlot.get("available", 0) or 0,
                UsedSlots = FirstPactSlot.get("used", 0) or 0
            )

        SpellcastingModel = CharacterSchema.SpellcastingData(
            SpellSlots = SpellSlotsList,
            PactMagic = PactMagicSlotModel,
            Spells = SpellsList
        )

        SeenSkills: Typing.Dict[str, str] = {
        }
        SeenSaves: Typing.Dict[str, bool] = {
        }
        ArmorProficienciesList: Typing.List[str] = []
        WeaponProficienciesList: Typing.List[str] = []
        ToolProficienciesList: Typing.List[str] = []
        LanguageProficienciesList: Typing.List[str] = []
        DamageResistancesList: Typing.List[str] = []
        DamageImmunitiesList: Typing.List[str] = []
        DamageVulnerabilitiesList: Typing.List[str] = []
        ConditionImmunitiesList: Typing.List[str] = []
        SensesList: Typing.List[CharacterSchema.SenseEntry] = []

        for GroupModifiers in AllModifiers.values():
            if not GroupModifiers:
                continue

            for ModifierItem in GroupModifiers:
                if not ModifierItem:
                    continue

                ModifierType: str = (ModifierItem.get("type") or "").lower()
                SubType: str = (ModifierItem.get("subType") or "").lower()
                FriendlyName: str = ModifierItem.get("friendlySubtypeName") or ModifierItem.get("subType") or ""

                if ModifierType == "proficiency":
                    if SubType in self.SkillAbilityMapping:
                        SeenSkills[SubType] = "Proficient"
                    elif "saving-throw" in SubType or "saving_throw" in SubType:
                        SaveAbilityKey: str = SubType.replace("-saving-throws", "").replace("-saving_throws", "").replace("-saving-throw", "").strip()
                        SeenSaves[SaveAbilityKey] = True
                    elif "armor" in SubType or "shield" in SubType:
                        if FriendlyName and FriendlyName not in ArmorProficienciesList:
                            ArmorProficienciesList.append(FriendlyName)
                    elif "weapon" in SubType or "sword" in SubType or "bow" in SubType or "crossbow" in SubType:
                        if FriendlyName and FriendlyName not in WeaponProficienciesList:
                            WeaponProficienciesList.append(FriendlyName)
                    elif "tool" in SubType or "supplies" in SubType or "kit" in SubType or "instrument" in SubType:
                        if FriendlyName and FriendlyName not in ToolProficienciesList:
                            ToolProficienciesList.append(FriendlyName)

                elif ModifierType == "expertise":
                    if SubType in self.SkillAbilityMapping:
                        SeenSkills[SubType] = "Expertise"

                elif ModifierType == "language":
                    if FriendlyName and FriendlyName not in LanguageProficienciesList:
                        LanguageProficienciesList.append(FriendlyName)

                elif ModifierType == "resistance":
                    if FriendlyName and FriendlyName not in DamageResistancesList:
                        DamageResistancesList.append(FriendlyName)

                elif ModifierType == "immunity":
                    if FriendlyName and FriendlyName not in DamageImmunitiesList:
                        DamageImmunitiesList.append(FriendlyName)

                elif ModifierType == "vulnerability":
                    if FriendlyName and FriendlyName not in DamageVulnerabilitiesList:
                        DamageVulnerabilitiesList.append(FriendlyName)

                elif ModifierType == "sense":
                    SenseRange: int = ModifierItem.get("value", 60) or 60
                    SensesList.append(CharacterSchema.SenseEntry(SenseType = FriendlyName or "Darkvision", RangeFeet = SenseRange))

        SkillProficienciesList: Typing.List[CharacterSchema.SkillProficiencyEntry] = []
        for NormalizedSkill, AssociatedAbility in self.SkillAbilityMapping.items():
            FormattedSkillName: str = " ".join(Word.capitalize() for Word in NormalizedSkill.replace("-", " ").split())
            ProficiencyStatus: str = SeenSkills.get(NormalizedSkill, "None")
            ProficiencyTierValue: CharacterSchema.ProficiencyTierType = CharacterSchema.ProficiencyTierType.Expertise if (ProficiencyStatus == "Expertise") else (CharacterSchema.ProficiencyTierType.Proficient if (ProficiencyStatus == "Proficient") else CharacterSchema.ProficiencyTierType.NoneTier)
            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(
                SkillName = FormattedSkillName,
                AssociatedAbility = AssociatedAbility,
                ProficiencyTier = ProficiencyTierValue
            ))

        SavingThrowProficienciesList: Typing.List[CharacterSchema.SavingThrowProficiencyEntry] = []
        for AbilityEnum in CharacterSchema.AbilityType:
            IsSaveProficient: bool = SeenSaves.get(AbilityEnum.value.lower(), False)
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(
                AbilityName = AbilityEnum,
                IsProficient = IsSaveProficient
            ))

        CurrenciesDictionary: Typing.Dict[str, int] = Data.get("currencies", {}) or {}
        CurrenciesModel = CharacterSchema.CurrenciesData(
            CopperPieces = CurrenciesDictionary.get("cp", 0) or 0,
            SilverPieces = CurrenciesDictionary.get("sp", 0) or 0,
            ElectrumPieces = CurrenciesDictionary.get("ep", 0) or 0,
            GoldPieces = CurrenciesDictionary.get("gp", 0) or 0,
            PlatinumPieces = CurrenciesDictionary.get("pp", 0) or 0
        )

        OverrideWalkingSpeedValue: Typing.Optional[int] = None
        OverrideInitiativeScoreValue: Typing.Optional[int] = None
        OverrideArmorClassScoreValue: Typing.Optional[int] = None

        for CharacterValueItem in Data.get("characterValues", []):
            ValueTypeIDCandidate: Typing.Optional[int] = CharacterValueItem.get("typeId")
            NumericValueCandidate: Typing.Optional[int] = CharacterValueItem.get("value")
            if NumericValueCandidate is None:
                continue
            if ValueTypeIDCandidate == 1:
                OverrideWalkingSpeedValue = NumericValueCandidate
            elif ValueTypeIDCandidate == 2:
                OverrideInitiativeScoreValue = NumericValueCandidate
            elif ValueTypeIDCandidate == 3:
                OverrideArmorClassScoreValue = NumericValueCandidate

        AttacksList: Typing.List[CharacterSchema.AttackActionEntry] = []
        ActionsList: Typing.List[CharacterSchema.ActionEntry] = []

        ActionsGroupDictionary: Typing.Dict[str, Typing.Any] = Data.get("actions", {}) or {}
        for ActionOriginName, ActionItemList in ActionsGroupDictionary.items():
            if not isinstance(ActionItemList, list):
                continue

            for ActionItem in ActionItemList:
                ActionName: str = str(ActionItem["name"])
                ActionNotes: Typing.Optional[str] = self.CleanHTMLString(ActionItem.get("description"))
                DisplayAsAttack: bool = bool(ActionItem.get("displayAsAttack", False))

                if DisplayAsAttack:
                    AttacksList.append(CharacterSchema.AttackActionEntry(
                        Identifier = str(ActionItem.get("id", "")),
                        Name = ActionName,
                        AttackBonus = ComputedProficiencyBonus + AbilityScoresModel.Dexterity.Modifier,
                        DamageExpression = "",
                        DamageType = "",
                        RangeDescription = "5 ft",
                        AttackSource = ActionOriginName.capitalize(),
                        Notes = ActionNotes
                    ))
                else:
                    ActionsList.append(CharacterSchema.ActionEntry(
                        Identifier = str(ActionItem.get("id", "")),
                        Name = ActionName,
                        ActionType = CharacterSchema.ActionActivationType.BonusAction if ActionItem.get("actionType") == 2 else CharacterSchema.ActionActivationType.Action,
                        SourceType = ActionOriginName.capitalize()
                    ))

        TraitsDictionary: Typing.Dict[str, Typing.Any] = Data.get("traits", {}) or {}
        PersonalityModel = CharacterSchema.PersonalityData(
            PersonalityTraits = self.CleanHTMLString(TraitsDictionary.get("personalityTraits")),
            Ideals = self.CleanHTMLString(TraitsDictionary.get("ideals")),
            Bonds = self.CleanHTMLString(TraitsDictionary.get("bonds")),
            Flaws = self.CleanHTMLString(TraitsDictionary.get("flaws"))
        )

        NotesDictionary: Typing.Dict[str, Typing.Any] = Data.get("notes", {}) or {}
        NotesModel = CharacterSchema.NotesData(
            Backstory = self.CleanHTMLString(NotesDictionary.get("backstory")),
            Allies = self.CleanHTMLString(NotesDictionary.get("allies")),
            Enemies = self.CleanHTMLString(NotesDictionary.get("enemies")),
            Organizations = self.CleanHTMLString(NotesDictionary.get("organizations")),
            PersonalPossessions = self.CleanHTMLString(NotesDictionary.get("personalPossessions")),
            OtherHoldings = self.CleanHTMLString(NotesDictionary.get("otherHoldings")),
            CustomNotes = self.CleanHTMLString(NotesDictionary.get("otherNotes"))
        )

        UnifiedSheet = CharacterSchema.DND5thEditionCharacterSheet(
            SchemaVersion = "1.0.0",
            GameSystem = "DND5thEdition",
            OriginalSource = "DNDBeyond",
            Name = CharacterName,
            PlayerName = PlayerName,
            Gender = Gender,
            Alignment = AlignmentString,
            Faith = Faith,
            Lifestyle = Data.get("lifestyle"),
            TotalLevel = TotalCharacterLevel,
            ExperiencePoints = Data.get("currentXp", 0) or 0,
            Inspiration = Data.get("inspiration", False) or False,
            ProficiencyBonus = ComputedProficiencyBonus,
            OverrideInitiativeBonus = OverrideInitiativeScoreValue,
            IsDirty = HasAnyClassDirty,
            Species = SpeciesModel,
            Background = BackgroundModel,
            Classes = ClassesList,
            AbilityScores = AbilityScoresModel,
            HitPoints = HitPointsModel,
            DeathSaves = DeathSavesModel,
            ArmorClass = CharacterSchema.ArmorClassData(OverrideArmorClass = OverrideArmorClassScoreValue),
            Speed = CharacterSchema.SpeedData(WalkingSpeedFeet = 30, OverrideWalkingSpeedFeet = OverrideWalkingSpeedValue),
            Senses = SensesList,
            SavingThrowProficiencies = SavingThrowProficienciesList,
            SkillProficiencies = SkillProficienciesList,
            ArmorProficiencies = ArmorProficienciesList,
            WeaponProficiencies = WeaponProficienciesList,
            ToolProficiencies = ToolProficienciesList,
            LanguageProficiencies = LanguageProficienciesList,
            DamageResistances = DamageResistancesList,
            DamageImmunities = DamageImmunitiesList,
            DamageVulnerabilities = DamageVulnerabilitiesList,
            ConditionImmunities = ConditionImmunitiesList,
            Attacks = AttacksList,
            Actions = ActionsList,
            Containers = ContainersList,
            Inventory = InventoryList,
            Currencies = CurrenciesModel,
            Spellcasting = SpellcastingModel,
            Features = FeaturesList,
            Personality = PersonalityModel,
            PhysicalAppearance = AppearanceData,
            Notes = NotesModel,
            Modifiers = TopLevelModifiersList
        )
        PrimaryClassName: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "None"
        DebugService.LogDebugMessage(f"Mapped DNDBeyond Character: '{UnifiedSheet.Name}' (Lvl={UnifiedSheet.TotalLevel}, Class='{PrimaryClassName}', Race='{UnifiedSheet.Species.FullName}')")
        return UnifiedSheet

    def MapDicecloudCharacter(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        CharactersList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("characters", [])
        if CharactersList:
            CharacterData: Typing.Dict[str, Typing.Any] = CharactersList[0]
        else:
            CharacterData = {
            }

        CharacterName: str = (CharacterData.get("name") or "Unnamed Hero").strip()
        Gender: Typing.Optional[str] = CharacterData.get("gender")
        RaceName: str = CharacterData.get("race", "Human") or "Human"
        Alignment: Typing.Optional[str] = CharacterData.get("alignment")

        RawWeight = CharacterData.get("weight")
        WeightString: Typing.Optional[str] = None
        if isinstance(RawWeight, (int, float, str)):
            WeightString = str(RawWeight)
        elif isinstance(RawWeight, dict) and "value" in RawWeight and RawWeight["value"]:
            WeightString = str(RawWeight["value"])

        AppearanceData = CharacterSchema.PhysicalAppearanceData(
            Age = str(CharacterData.get("age")) if (isinstance(CharacterData.get("age"), (int, float, str))) else None,
            Height = str(CharacterData.get("height")) if CharacterData.get("height") else None,
            Weight = WeightString,
            Hair = CharacterData.get("hair"),
            Eyes = CharacterData.get("eyes"),
            Skin = CharacterData.get("skin"),
            AppearanceDescription = self.CleanHTMLString(CharacterData.get("description"))
        )

        SpeciesModel = CharacterSchema.SpeciesData(
            RaceName = RaceName,
            FullName = RaceName
        )

        BackgroundModel = CharacterSchema.BackgroundData(
            Name = "Soldier" if ("soldier" in (CharacterData.get("backstory") or "").lower()) else "Adventurer"
        )

        ClassesList: Typing.List[CharacterSchema.ClassProgressEntry] = []
        TotalCharacterLevel: int = 0
        HasAnyClassDirty: bool = False
        RawClasses: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("classes", [])

        for ClassIndex, ClassItem in enumerate(RawClasses):
            RawClassName: str = ClassItem.get("name", "Fighter")
            CanonicalClassName: Typing.Optional[str] = self.FiveETools.FindCanonicalClassName(RawClassName)
            IsClassDirty: bool = False
            if CanonicalClassName:
                ClassName: str = CanonicalClassName
            else:
                ClassName = RawClassName
                IsClassDirty = True
                HasAnyClassDirty = True

            ClassLevel: int = int(ClassItem.get("level", 1) or 1)
            TotalCharacterLevel += ClassLevel
            HitDie: Typing.Optional[int] = self.FiveETools.GetClassHitDie(ClassName)
            if HitDie is None:
                HitDie = int(ClassItem.get("hitDie", 8) or 8)
                IsClassDirty = True
                HasAnyClassDirty = True

            SubclassName: Typing.Optional[str] = ClassItem.get("subclass")
            SpellcastingAbilityStr: Typing.Optional[str] = self.FiveETools.GetClassSpellcastingAbility(ClassName, SubclassName)
            SpellcastingAbilityEnum: Typing.Optional[CharacterSchema.AbilityType] = self.MapStringToAbilityType(SpellcastingAbilityStr)

            ClassesList.append(CharacterSchema.ClassProgressEntry(
                ClassName = ClassName,
                Level = ClassLevel,
                SubclassName = SubclassName,
                HitDie = HitDie,
                HitDiceTotal = ClassLevel,
                HitDiceUsed = 0,
                IsStartingClass = (ClassIndex == 0),
                SpellcastingAbility = SpellcastingAbilityEnum,
                IsDirty = IsClassDirty
            ))

        if not ClassesList:
            TotalCharacterLevel = 1
            ClassesList.append(CharacterSchema.ClassProgressEntry(
                ClassName = "Fighter",
                Level = 1,
                HitDie = 10,
                HitDiceTotal = 1,
                HitDiceUsed = 0,
                IsStartingClass = True,
                IsDirty = True
            ))
            HasAnyClassDirty = True

        ComputedProficiencyBonus: int = self.ComputeProficiencyBonusForLevel(TotalCharacterLevel)

        EffectsList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("effects", [])
        TopLevelModifiersList: Typing.List[CharacterSchema.ModifierEntry] = []
        BaseStatValues: Typing.Dict[str, int] = {
            "strength": 10,
            "dexterity": 10,
            "constitution": 10,
            "intelligence": 10,
            "wisdom": 10,
            "charisma": 10
        }
        CalculatedArmorClassBase: int = 10
        ArmorNameDetected: Typing.Optional[str] = None
        MultiplierOverrides: Typing.Dict[str, float] = {
        }

        for EffectItem in EffectsList:
            StatTarget: str = (EffectItem.get("stat") or "").lower()
            OperationType: str = (EffectItem.get("operation") or "").lower()
            EffectValue = EffectItem.get("value")
            if StatTarget in BaseStatValues and OperationType == "base":
                if EffectValue is not None:
                    BaseStatValues[StatTarget] = int(EffectValue)
            elif StatTarget == "armor" and OperationType == "base":
                CalculatedArmorClassBase = int(EffectValue or 10)
                ArmorNameDetected = EffectItem.get("name")
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(
                    ModifierType = "Set",
                    ModifierSubType = "BaseArmorClass",
                    Value = CalculatedArmorClassBase,
                    StringValue = ArmorNameDetected or "Armor",
                    IsActive = True
                ))
            elif StatTarget in self.DamageMultiplierStatMapping:
                if EffectValue is not None:
                    MultiplierOverrides[StatTarget] = float(EffectValue)

        AbilityScoresModel = CharacterSchema.AbilityScoresData(
            Strength = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["strength"]),
            Dexterity = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["dexterity"]),
            Constitution = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["constitution"]),
            Intelligence = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["intelligence"]),
            Wisdom = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["wisdom"]),
            Charisma = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["charisma"]),
            IsDirty = False
        )

        ClassLevelsForHitPoints: Typing.List[Typing.Tuple[str, int, bool]] = [
            (ClassItem.ClassName, ClassItem.Level, ClassItem.IsStartingClass) for ClassItem in ClassesList
        ]
        CalculatedHitPoints, HitPointsDirty = self.FiveETools.CalculateHitPoints(ClassLevelsForHitPoints, AbilityScoresModel.Constitution.Modifier)
        if CalculatedHitPoints <= 0:
            CalculatedHitPoints = self.ExtractNumericStat(CharacterData.get("maxHitPoints"), Default = 10)
            HitPointsDirty = True

        DamageTaken: int = self.ExtractNumericStat(CharacterData.get("damage"), Default = 0)
        CurrentHitPoints: int = max(0, CalculatedHitPoints - DamageTaken)
        TemporaryHitPoints: int = self.ExtractNumericStat(CharacterData.get("tempHP"), Default = 0)

        HitPointsModel = CharacterSchema.HitPointsData(
            MaxHitPoints = CalculatedHitPoints,
            CurrentHitPoints = CurrentHitPoints,
            TemporaryHitPoints = TemporaryHitPoints,
            BaseHitPoints = CalculatedHitPoints,
            IsDirty = HitPointsDirty or HasAnyClassDirty
        )

        RawDeathSave: Typing.Dict[str, Typing.Any] = CharacterData.get("deathSave", {}) or {}
        DeathSavesModel = CharacterSchema.DeathSavesData(
            SuccessCount = RawDeathSave.get("pass", 0) or 0,
            FailureCount = RawDeathSave.get("fail", 0) or 0
        )

        DamageResistancesList: Typing.List[str] = []
        DamageImmunitiesList: Typing.List[str] = []
        DamageVulnerabilitiesList: Typing.List[str] = []

        for StatKey, DamageTypeName in self.DamageMultiplierStatMapping.items():
            MultiplierValue: float = 1.0
            if StatKey in MultiplierOverrides:
                MultiplierValue = MultiplierOverrides[StatKey]
            elif StatKey in CharacterData:
                RawMultiplier = CharacterData.get(StatKey)
                if isinstance(RawMultiplier, dict):
                    MultiplierValue = float(RawMultiplier.get("adjustment", 1.0) or 1.0)
                elif isinstance(RawMultiplier, (int, float)):
                    MultiplierValue = float(RawMultiplier)

            if MultiplierValue == 0.0:
                DamageImmunitiesList.append(DamageTypeName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Immunity", ModifierSubType = DamageTypeName.lower(), StringValue = DamageTypeName, IsActive = True))
            elif MultiplierValue == 0.5:
                DamageResistancesList.append(DamageTypeName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Resistance", ModifierSubType = DamageTypeName.lower(), StringValue = DamageTypeName, IsActive = True))
            elif MultiplierValue == 2.0:
                DamageVulnerabilitiesList.append(DamageTypeName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Vulnerability", ModifierSubType = DamageTypeName.lower(), StringValue = DamageTypeName, IsActive = True))

        SkillProficienciesList: Typing.List[CharacterSchema.SkillProficiencyEntry] = []
        SavingThrowProficienciesList: Typing.List[CharacterSchema.SavingThrowProficiencyEntry] = []
        ArmorProficienciesList: Typing.List[str] = []
        WeaponProficienciesList: Typing.List[str] = []
        ToolProficienciesList: Typing.List[str] = []
        LanguageProficienciesList: Typing.List[str] = []

        RawProficiencies: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("proficiencies", [])
        SeenSkills: Typing.Dict[str, int] = {
        }
        SeenSaves: Typing.Dict[str, bool] = {
        }

        for ProficiencyItem in RawProficiencies:
            ProficiencyType: str = (ProficiencyItem.get("type") or "").lower()
            ProficiencyName: str = ProficiencyItem.get("name", "")
            ProficiencyValue: int = int(ProficiencyItem.get("value", 1) or 1)

            if ProficiencyType == "skill":
                SeenSkills[ProficiencyName.lower()] = ProficiencyValue
                ModifierType = "Expertise" if ProficiencyValue == 2 else "Proficiency"
                FormattedSkillName = " ".join(Word.capitalize() for Word in ProficiencyName.lower().replace("-", " ").split())
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(
                    ModifierType = ModifierType,
                    ModifierSubType = ProficiencyName.lower().replace(" ", "-"),
                    StringValue = FormattedSkillName,
                    IsActive = True
                ))
            elif ProficiencyType == "save":
                SaveKey: str = ProficiencyName.lower().replace("save", "").strip()
                SeenSaves[SaveKey] = True
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(
                    ModifierType = "Proficiency",
                    ModifierSubType = f"{SaveKey}-saving-throws",
                    StringValue = ProficiencyName,
                    IsActive = True
                ))
            elif ProficiencyType == "armor":
                if ProficiencyName not in ArmorProficienciesList:
                    ArmorProficienciesList.append(ProficiencyName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Proficiency", ModifierSubType = "armors", StringValue = ProficiencyName, IsActive = True))
            elif ProficiencyType == "weapon":
                if ProficiencyName not in WeaponProficienciesList:
                    WeaponProficienciesList.append(ProficiencyName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Proficiency", ModifierSubType = "weapons", StringValue = ProficiencyName, IsActive = True))
            elif ProficiencyType == "tool":
                if ProficiencyName not in ToolProficienciesList:
                    ToolProficienciesList.append(ProficiencyName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Proficiency", ModifierSubType = "tools", StringValue = ProficiencyName, IsActive = True))
            elif ProficiencyType == "language":
                if ProficiencyName not in LanguageProficienciesList:
                    LanguageProficienciesList.append(ProficiencyName)
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Language", ModifierSubType = "language", StringValue = ProficiencyName, IsActive = True))

        for NormalizedSkill, AssociatedAbility in self.SkillAbilityMapping.items():
            FormattedSkillName: str = " ".join(Word.capitalize() for Word in NormalizedSkill.replace("-", " ").split())
            ProficiencyLevelValue: int = SeenSkills.get(NormalizedSkill.lower(), 0)
            ProficiencyTier: CharacterSchema.ProficiencyTierType = CharacterSchema.ProficiencyTierType.Expertise if (ProficiencyLevelValue == 2) else (CharacterSchema.ProficiencyTierType.Proficient if (ProficiencyLevelValue == 1) else CharacterSchema.ProficiencyTierType.NoneTier)
            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(
                SkillName = FormattedSkillName,
                AssociatedAbility = AssociatedAbility,
                ProficiencyTier = ProficiencyTier
            ))

        for AbilityEnum in CharacterSchema.AbilityType:
            IsSaveProf: bool = SeenSaves.get(AbilityEnum.value.lower(), False)
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(
                AbilityName = AbilityEnum,
                IsProficient = IsSaveProf
            ))

        ContainersList: Typing.List[CharacterSchema.ContainerEntry] = []
        RawContainers: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("containers", [])
        for ContItem in RawContainers:
            ContainersList.append(CharacterSchema.ContainerEntry(
                Identifier = str(ContItem.get("_id", "")),
                Name = ContItem.get("name", "Backpack"),
                IsCarried = ContItem.get("isCarried", True),
                WeightPounds = float(ContItem.get("weight", 0.0) or 0.0)
            ))

        InventoryList: Typing.List[CharacterSchema.InventoryItemEntry] = []
        GoldPiecesCount: int = 0
        SilverPiecesCount: int = 0
        CopperPiecesCount: int = 0

        RawItems: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("items", [])
        for ItemItem in RawItems:
            ItemName: str = ItemItem.get("name", "Unknown Item")
            ItemQuantity: int = int(ItemItem.get("quantity", 1) or 1)
            ItemWeight: float = float(ItemItem.get("weight", 0.0) or 0.0)
            ItemCost: float = float(ItemItem.get("value", 0.0) or 0.0)
            IsEquipped: bool = ItemItem.get("enabled", False) or False
            NeedsAttunement: bool = ItemItem.get("requiresAttunement", False) or False
            ParentDictionary: Typing.Dict[str, Typing.Any] = ItemItem.get("parent", {}) or {}
            ContainerID: Typing.Optional[str] = ParentDictionary.get("id") if (ParentDictionary.get("collection") == "Containers") else None

            if "gold piece" in ItemName.lower():
                GoldPiecesCount += ItemQuantity
            elif "silver piece" in ItemName.lower():
                SilverPiecesCount += ItemQuantity
            elif "copper piece" in ItemName.lower():
                CopperPiecesCount += ItemQuantity
            else:
                InventoryList.append(CharacterSchema.InventoryItemEntry(
                    Identifier = str(ItemItem.get("_id", "")),
                    Name = ItemName,
                    Quantity = ItemQuantity,
                    WeightPounds = ItemWeight,
                    CostInGoldPieces = ItemCost,
                    IsEquipped = IsEquipped,
                    RequiresAttunement = NeedsAttunement,
                    ContainerIdentifier = ContainerID,
                    IsDirty = False
                ))

        CurrenciesModel = CharacterSchema.CurrenciesData(
            CopperPieces = CopperPiecesCount,
            SilverPieces = SilverPiecesCount,
            GoldPieces = GoldPiecesCount
        )

        AttacksList: Typing.List[CharacterSchema.AttackActionEntry] = []
        RawAttacks: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("attacks", [])
        for AttackItem in RawAttacks:
            AttackName: str = AttackItem.get("name", "Attack")
            DetailsText: str = AttackItem.get("details", "")
            PropertiesList: Typing.List[str] = [PropertyItem.strip() for PropertyItem in DetailsText.split(";") if PropertyItem.strip()]
            IsRanged: Typing.Optional[bool] = self.FiveETools.IsWeaponRanged(AttackName)
            IsAttackDirty: bool = False

            if IsRanged is True:
                AttackModifier: int = AbilityScoresModel.Dexterity.Modifier
                RangeDescription: str = "80/320 ft"
            elif IsRanged is False:
                if self.FiveETools.IsWeaponFinesse(AttackName) and AbilityScoresModel.Dexterity.Modifier > AbilityScoresModel.Strength.Modifier:
                    AttackModifier = AbilityScoresModel.Dexterity.Modifier
                else:
                    AttackModifier = AbilityScoresModel.Strength.Modifier
                RangeDescription = "5 ft"
            else:
                IsAttackDirty = True
                if "ranged" in DetailsText.lower() or "bow" in AttackName.lower():
                    AttackModifier = AbilityScoresModel.Dexterity.Modifier
                    RangeDescription = "80/320 ft"
                else:
                    AttackModifier = AbilityScoresModel.Strength.Modifier
                    RangeDescription = "5 ft"

            AttackBonus: int = AttackModifier + ComputedProficiencyBonus
            DamageExpression: str = AttackItem.get("damage", "")
            WeaponData: Typing.Optional[Typing.Dict[str, Typing.Any]] = self.FiveETools.GetWeaponData(AttackName)
            if WeaponData and WeaponData.get("DamageExpression"):
                DamageDice: str = WeaponData["DamageExpression"]
                DamageExpression = f"{DamageDice} + {AttackModifier}"
            elif DamageExpression:
                DamageExpression = RegularExpressions.sub(r"\{strengthMod\}|\{dexterityMod\}", str(AttackModifier), DamageExpression, flags = RegularExpressions.IGNORECASE)

            DamageType: str = AttackItem.get("damageType") or (WeaponData.get("DamageType") if WeaponData else "slashing") or "slashing"

            AttacksList.append(CharacterSchema.AttackActionEntry(
                Identifier = str(AttackItem.get("_id", "")),
                Name = AttackName,
                AttackBonus = AttackBonus,
                DamageExpression = DamageExpression,
                DamageType = DamageType,
                RangeDescription = RangeDescription,
                Properties = PropertiesList,
                IsEquipped = AttackItem.get("enabled", True),
                AttackSource = AttackItem.get("source", "Weapon") or "Weapon",
                Notes = DetailsText,
                IsDirty = IsAttackDirty
            ))

        SpellsList: Typing.List[CharacterSchema.SpellEntry] = []
        RawSpells: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("spells", [])
        for SpellItem in RawSpells:
            SpellName: str = SpellItem.get("name", "Spell")
            SpellLevel: int = int(SpellItem.get("level", 0) or 0)
            SchoolName: str = SpellItem.get("school", "Evocation")
            CastingTimeStr: str = SpellItem.get("castingTime", "Action")
            RangeStr: str = SpellItem.get("range", "Self")
            DurationStr: str = SpellItem.get("duration", "Instantaneous")
            ComponentsDictionary: Typing.Dict[str, Typing.Any] = SpellItem.get("components", {}) or {}
            IsConcentration: bool = ComponentsDictionary.get("concentration", False) or False
            IsRitual: bool = SpellItem.get("ritual", False) or False
            PreparedValue: str = SpellItem.get("prepared", "prepared")

            RawMaterialValue = ComponentsDictionary.get("material", False)
            HasMaterialComponent: bool = bool(RawMaterialValue)
            MaterialDescription: Typing.Optional[str] = RawMaterialValue if isinstance(RawMaterialValue, str) else None

            SpellsList.append(CharacterSchema.SpellEntry(
                Identifier = str(SpellItem.get("_id", "")),
                Name = SpellName,
                Level = SpellLevel,
                School = SchoolName,
                CastingTime = CastingTimeStr,
                RangeDescription = RangeStr,
                DurationDescription = DurationStr,
                Components = CharacterSchema.SpellComponentData(
                    Verbal = bool(ComponentsDictionary.get("verbal", False)),
                    Somatic = bool(ComponentsDictionary.get("somatic", False)),
                    Material = HasMaterialComponent,
                    MaterialDescription = MaterialDescription
                ),
                IsConcentration = IsConcentration,
                IsRitual = IsRitual,
                IsPrepared = (PreparedValue == "prepared"),
                SourceType = "Class",
                SourceName = "Spellbook",
                IsDirty = False
            ))

        ClassProgressionList: Typing.List[Typing.Tuple[str, int, Typing.Optional[str]]] = [
            (ClassItem.ClassName, ClassItem.Level, ClassItem.SubclassName) for ClassItem in ClassesList
        ]
        CalculatedSpellSlots: Typing.List[Typing.Tuple[int, int]] = self.FiveETools.CalculateMulticlassSpellSlots(ClassProgressionList)
        SpellSlotsList: Typing.List[CharacterSchema.SpellSlotEntry] = [
            CharacterSchema.SpellSlotEntry(Level = SlotLevel, TotalSlots = SlotCount, UsedSlots = 0)
            for SlotLevel, SlotCount in CalculatedSpellSlots
        ]

        WarlockLevel: int = sum(
            ClassItem.Level for ClassItem in ClassesList
            if (self.FiveETools.FindCanonicalClassName(ClassItem.ClassName) or ClassItem.ClassName).lower() == "warlock"
        )
        PactMagicData: Typing.Optional[CharacterSchema.PactMagicSlotData] = None
        if WarlockLevel > 0:
            PactSlotInformation: Typing.Optional[Typing.Tuple[int, int]] = self.FiveETools.CalculatePactMagicSlots(WarlockLevel)
            if PactSlotInformation:
                PactMagicData = CharacterSchema.PactMagicSlotData(
                    SlotLevel = PactSlotInformation[0],
                    TotalSlots = PactSlotInformation[1],
                    UsedSlots = 0
                )

        SpellcastingEntriesList: Typing.List[CharacterSchema.SpellcastingEntry] = []
        RawSpellLists: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("spellLists", [])

        for ClassItem in ClassesList:
            CanonicalName: str = self.FiveETools.FindCanonicalClassName(ClassItem.ClassName) or ClassItem.ClassName
            CasterProgression: Typing.Optional[str] = self.FiveETools.GetClassCasterProgression(CanonicalName, ClassItem.SubclassName)
            if not CasterProgression:
                continue

            SpellcastingAbilityEnum = ClassItem.SpellcastingAbility
            IsEntryDirty: bool = False
            if not SpellcastingAbilityEnum:
                for SpellListItem in RawSpellLists:
                    ListName: str = SpellListItem.get("name", "")
                    if CanonicalName.lower() in ListName.lower():
                        AbilityString = SpellListItem.get("ability")
                        SpellcastingAbilityEnum = self.MapStringToAbilityType(AbilityString)
                        break

            if not SpellcastingAbilityEnum:
                SpellcastingAbilityEnum = CharacterSchema.AbilityType.Charisma
                IsEntryDirty = True

            AbilityModifier: int = getattr(AbilityScoresModel, SpellcastingAbilityEnum.value).Modifier
            SaveDC: int = 8 + ComputedProficiencyBonus + AbilityModifier
            AttackBonus: int = ComputedProficiencyBonus + AbilityModifier

            SpellcastingEntriesList.append(CharacterSchema.SpellcastingEntry(
                SpellcastingClass = CanonicalName,
                SpellcastingAbility = SpellcastingAbilityEnum,
                SpellSaveDC = SaveDC,
                SpellAttackBonus = AttackBonus,
                IsDirty = IsEntryDirty
            ))

        SpellcastingModel = CharacterSchema.SpellcastingData(
            SpellcastingEntries = SpellcastingEntriesList,
            SpellSlots = SpellSlotsList,
            PactMagic = PactMagicData,
            Spells = SpellsList
        )

        FormulaContext: Typing.Dict[str, int] = {
            "level": TotalCharacterLevel,
            "totallevel": TotalCharacterLevel,
            "characterlevel": TotalCharacterLevel,
            "proficiencybonus": ComputedProficiencyBonus,
            "strengthmod": AbilityScoresModel.Strength.Modifier,
            "dexteritymod": AbilityScoresModel.Dexterity.Modifier,
            "constitutionmod": AbilityScoresModel.Constitution.Modifier,
            "intelligencemod": AbilityScoresModel.Intelligence.Modifier,
            "wisdommod": AbilityScoresModel.Wisdom.Modifier,
            "charismamod": AbilityScoresModel.Charisma.Modifier
        }
        for ClassItem in ClassesList:
            CleanClassName: str = ClassItem.ClassName.replace(" ", "")
            FormulaContext[f"{CleanClassName}Level"] = ClassItem.Level
            FormulaContext[f"{CleanClassName.lower()}level"] = ClassItem.Level

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        RawFeatures: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("features", [])
        for FeatItem in RawFeatures:
            RawFeatName: str = FeatItem.get("name", "Feature")
            CleanFeatName: str = RegularExpressions.sub(r"^[0-9]+[│|]\s*", "", RawFeatName).strip()
            ResetTypeStr: str = (FeatItem.get("reset") or "longRest").lower()
            ResetEnum: CharacterSchema.ResetScheduleType = CharacterSchema.ResetScheduleType.ShortRest if ("short" in ResetTypeStr) else (CharacterSchema.ResetScheduleType.LongRest if ("long" in ResetTypeStr) else CharacterSchema.ResetScheduleType.Manual)

            SourceType: str = "Class"
            SourceName: str = "Class Feature"
            LowerFeatName: str = CleanFeatName.lower()
            if "feat" in LowerFeatName:
                SourceType = "Feat"
                SourceName = CleanFeatName
            elif "human" in LowerFeatName or "race" in LowerFeatName:
                SourceType = "Species"
                SourceName = RaceName
            else:
                for ClassItem in ClassesList:
                    if ClassItem.ClassName.lower() in LowerFeatName:
                        SourceType = "Class"
                        SourceName = ClassItem.ClassName
                        break

            LimitedUseDataModel: Typing.Optional[CharacterSchema.LimitedUseData] = None
            RawUses = FeatItem.get("uses")
            if RawUses is not None:
                CalculatedMaxUses: int = self.EvaluateDicecloudFormula(RawUses, FormulaContext)
                LimitedUseDataModel = CharacterSchema.LimitedUseData(
                    MaxUses = CalculatedMaxUses,
                    UsedUses = int(FeatItem.get("used", 0) or 0),
                    ResetType = ResetEnum
                )

            FeaturesList.append(CharacterSchema.FeatureEntry(
                Identifier = str(FeatItem.get("_id", "")),
                Name = CleanFeatName,
                SourceType = SourceType,
                SourceName = SourceName,
                IsEnabled = FeatItem.get("enabled", True),
                LimitedUse = LimitedUseDataModel,
                IsDirty = False
            ))

        PersonalityModel = CharacterSchema.PersonalityData(
            PersonalityTraits = self.CleanHTMLString(CharacterData.get("personality")),
            Ideals = self.CleanHTMLString(CharacterData.get("ideals")),
            Bonds = self.CleanHTMLString(CharacterData.get("bonds")),
            Flaws = self.CleanHTMLString(CharacterData.get("flaws"))
        )

        NotesModel = CharacterSchema.NotesData(
            Backstory = self.CleanHTMLString(CharacterData.get("backstory"))
        )

        ArmorClassModel = CharacterSchema.ArmorClassData(
            OverrideArmorClass = CalculatedArmorClassBase if CalculatedArmorClassBase > 10 else None,
            BaseArmorClass = CalculatedArmorClassBase,
            ArmorName = ArmorNameDetected
        )

        IsSheetDirty: bool = (
            HasAnyClassDirty
            or HitPointsModel.IsDirty
            or any(ClassItem.IsDirty for ClassItem in ClassesList)
            or any(AttackItem.IsDirty for AttackItem in AttacksList)
            or any(SpellcastItem.IsDirty for SpellcastItem in SpellcastingModel.SpellcastingEntries)
        )

        UnifiedSheet = CharacterSchema.DND5thEditionCharacterSheet(
            SchemaVersion = "1.0.0",
            GameSystem = "DND5thEdition",
            OriginalSource = "Dicecloud",
            Name = CharacterName,
            Gender = Gender,
            Alignment = Alignment,
            TotalLevel = TotalCharacterLevel,
            ExperiencePoints = 0,
            ProficiencyBonus = ComputedProficiencyBonus,
            IsDirty = IsSheetDirty,
            Species = SpeciesModel,
            Background = BackgroundModel,
            Classes = ClassesList,
            AbilityScores = AbilityScoresModel,
            HitPoints = HitPointsModel,
            DeathSaves = DeathSavesModel,
            ArmorClass = ArmorClassModel,
            Speed = CharacterSchema.SpeedData(WalkingSpeedFeet = 30),
            SavingThrowProficiencies = SavingThrowProficienciesList,
            SkillProficiencies = SkillProficienciesList,
            ArmorProficiencies = ArmorProficienciesList,
            WeaponProficiencies = WeaponProficienciesList,
            ToolProficiencies = ToolProficienciesList,
            LanguageProficiencies = LanguageProficienciesList,
            DamageResistances = DamageResistancesList,
            DamageImmunities = DamageImmunitiesList,
            DamageVulnerabilities = DamageVulnerabilitiesList,
            Attacks = AttacksList,
            Containers = ContainersList,
            Inventory = InventoryList,
            Currencies = CurrenciesModel,
            Spellcasting = SpellcastingModel,
            Features = FeaturesList,
            Personality = PersonalityModel,
            PhysicalAppearance = AppearanceData,
            Notes = NotesModel,
            Modifiers = TopLevelModifiersList
        )
        PrimaryClassName: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "None"
        DebugService.LogDebugMessage(f"Mapped Dicecloud Character: '{UnifiedSheet.Name}' (Lvl={UnifiedSheet.TotalLevel}, Class='{PrimaryClassName}', Race='{UnifiedSheet.Species.FullName}')")
        return UnifiedSheet

    def IngestUniversalCharacterData(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        if "data" in RawJSON and isinstance(RawJSON["data"], dict) and "classes" in RawJSON["data"]:
            return self.MapDNDBeyondCharacter(RawJSON)

        if "characters" in RawJSON and isinstance(RawJSON["characters"], list):
            return self.MapDicecloudCharacter(RawJSON)

        if "AbilityScores" in RawJSON and "Classes" in RawJSON:
            DebugService.LogDebugMessage(f"Ingested Universal Sheet: Name='{RawJSON.get('Name', 'Unknown')}', System='{RawJSON.get('GameSystem', 'DND5thEdition')}'")
            return CharacterSchema.DND5thEditionCharacterSheet.model_validate(RawJSON)

        DebugService.LogDebugMessage(f"Universal Character Ingestion Failed: Unsupported Keys={list(RawJSON.keys())}")
        raise ValueError("Unsupported or invalid character data structure provided for universal ingestion.")

    def ExportToDatabasePayload(self, Sheet: CharacterSchema.DND5thEditionCharacterSheet, RawImportData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None) -> Typing.Dict[str, Typing.Any]:
        PrimaryClass: str = Sheet.Classes[0].ClassName if Sheet.Classes else ""
        SummaryDictionary: Typing.Dict[str, Typing.Any] = {
            "System": "DND5thEdition",
            "Class": PrimaryClass,
            "Level": Sheet.TotalLevel,
            "Species": Sheet.Species.FullName,
            "Background": Sheet.Background.Name,
            "HitPoints": Sheet.HitPoints.MaxHitPoints,
            "ArmorClass": Sheet.ArmorClass.TotalArmorClass
        }
        DetailDictionary: Typing.Dict[str, Typing.Any] = Sheet.model_dump()
        Payload: Typing.Dict[str, Typing.Any] = {
            "Name": Sheet.Name,
            "GameSystem": "DND5thEdition",
            "SummaryData": SummaryDictionary,
            "DetailData": DetailDictionary,
            "RawImportData": RawImportData
        }
        DebugService.LogDebugMessage(f"Exported Database Payload: '{Sheet.Name}' ({Sheet.GameSystem}, Lvl={Sheet.TotalLevel}, HP={Sheet.HitPoints.MaxHitPoints}, AC={Sheet.ArmorClass.TotalArmorClass})")
        return Payload

GLOBAL_CHARACTER_MAPPER: CharacterMappingService = CharacterMappingService()
