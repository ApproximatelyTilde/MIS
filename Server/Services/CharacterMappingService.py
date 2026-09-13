import html                                       as HyperTextMarkupLanguage
import re                                         as RegularExpressions
import typing                                     as Typing
import Server.Models.Character                    as CharacterModel
import Server.Models.DND5thEditionCharacterSchema as CharacterSchema
import Server.Services.External5ETools            as External5ETools
import Server.Services.DebugService               as DebugService
import Server.Services.FuzzySearchService         as FuzzySearchService

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
            EvaluatedResult = eval(ExpressionString, {"__builtins__": {}})
            return max(1, int(EvaluatedResult))

        except Exception:
            return 1

    def CleanHTMLString(self, RawText: Typing.Optional[str]) -> Typing.Optional[str]:
        if not RawText:
            return None

        NormalizedText: str = RegularExpressions.sub(r"<br\s*/?>|</p>", "\n", RawText, flags = RegularExpressions.IGNORECASE)
        CleanedText: str = RegularExpressions.sub(r"<[^>]+>", "", NormalizedText)
        UnescapedText: str = HyperTextMarkupLanguage.unescape(CleanedText)
        FinalString: str = UnescapedText.strip()
        return FinalString if FinalString else None

    def ComputeProficiencyBonusForLevel(self, TotalLevel: int) -> int:
        BoundedLevel: int = max(1, min(20, TotalLevel))
        return 2 + ((BoundedLevel - 1) // 4)

    @staticmethod
    def ParseCommaSeparatedList(RawInput: Typing.Any) -> Typing.List[str]:
        if not RawInput:
            return []

        if isinstance(RawInput, list):
            return [str(Item).strip() for Item in RawInput if str(Item).strip()]

        return [Item.strip() for Item in RegularExpressions.split(r"[,;\n]", str(RawInput)) if Item.strip()]

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

        return CharacterSchema.ModifierEntry(ModifierType = ModifierTypeValue, ModifierSubType = ModifierSubtypeValue, Value = ParsedValue, StringValue = str(StringValueText) if StringValueText else None, IsActive = True)

    def MapDNDBeyondCharacter(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        Data: Typing.Dict[str, Typing.Any] = RawJSON.get("data", RawJSON)
        CharacterName: str = str(Data["name"]).strip()
        PlayerName: Typing.Optional[str] = Data.get("username")
        Gender: Typing.Optional[str] = Data.get("gender")
        Faith: Typing.Optional[str] = Data.get("faith")
        AlignmentID: Typing.Optional[int] = Data.get("alignmentId")
        AlignmentString: Typing.Optional[str] = self.AlignmentMapping.get(AlignmentID) if AlignmentID else None

        DecorationsDictionary: Typing.Dict[str, Typing.Any] = Data.get("decorations", {}) or {}
        AvatarURL: Typing.Optional[str] = DecorationsDictionary.get("avatarUrl")
        AppearanceData = CharacterSchema.PhysicalAppearanceData(Age = str(Data.get("age")) if (Data.get("age") is not None) else None, Height = Data.get("height"), Weight = str(Data.get("weight")) if (Data.get("weight") is not None) else None, Hair = Data.get("hair"), Eyes = Data.get("eyes"), Skin = Data.get("skin"), AppearanceDescription = self.CleanHTMLString(Data.get("traits", {}).get("appearance")), PortraitURL = AvatarURL)

        AllModifiers: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = Data.get("modifiers", {}) or {}

        RaceModifiers: Typing.List[CharacterSchema.ModifierEntry] = [self.ConvertRawModifier(ModifierItem) for ModifierItem in AllModifiers.get("race", []) if ModifierItem]
        RaceDataDictionary: Typing.Dict[str, Typing.Any] = Data.get("race", {}) or {}
        SpeciesModel = CharacterSchema.SpeciesData(RaceName = str(RaceDataDictionary.get("baseRaceName") or RaceDataDictionary["fullName"]), SubraceName = RaceDataDictionary.get("fullName") if RaceDataDictionary.get("isSubRace") else None, FullName = str(RaceDataDictionary["fullName"]), Modifiers = RaceModifiers)

        BackgroundModifiers: Typing.List[CharacterSchema.ModifierEntry] = [self.ConvertRawModifier(ModifierItem) for ModifierItem in AllModifiers.get("background", []) if ModifierItem]
        BackgroundDictionary: Typing.Dict[str, Typing.Any] = Data.get("background", {}) or {}
        BackgroundDefinition: Typing.Dict[str, Typing.Any] = BackgroundDictionary.get("definition", {}) or {}
        BackgroundFeatureDescription: Typing.Optional[str] = self.CleanHTMLString(BackgroundDefinition.get("featureDescription")) or self.CleanHTMLString(BackgroundDefinition.get("description")) or self.CleanHTMLString(BackgroundDefinition.get("shortDescription"))
        BackgroundModel = CharacterSchema.BackgroundData(Name = str(BackgroundDefinition["name"]), FeatureName = BackgroundDefinition.get("featureName"), FeatureDescription = BackgroundFeatureDescription, Modifiers = BackgroundModifiers)

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
            
            ClassesList.append(CharacterSchema.ClassProgressEntry(ClassName = ClassName, Level = ClassLevel, SubclassName = SubclassName, HitDie = HitDieValue, HitDiceTotal = ClassLevel, HitDiceUsed = SpentDice, IsStartingClass = IsStarting, SpellcastingAbility = SpellcastingAbilityEnum, IsDirty = IsClassDirty))

        ComputedProficiencyBonus: int = self.ComputeProficiencyBonusForLevel(TotalCharacterLevel)

        StatsList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("stats", []) or []
        BonusStatsList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("bonusStats", []) or []
        OverrideStatsList: Typing.List[Typing.Dict[str, Typing.Any]] = Data.get("overrideStats", []) or []

        def ExtractAbility(Index: int) -> CharacterSchema.AbilityScoreEntry:
            BaseValue: int = StatsList[Index].get("value", 10) if (len(StatsList) > Index and StatsList[Index].get("value") is not None) else 10
            BonusValue: int = BonusStatsList[Index].get("value", 0) if (len(BonusStatsList) > Index and BonusStatsList[Index].get("value") is not None) else 0
            OverrideValue: Typing.Optional[int] = OverrideStatsList[Index].get("value") if (len(OverrideStatsList) > Index and OverrideStatsList[Index].get("value") is not None) else None
            return CharacterSchema.AbilityScoreEntry(BaseScore = BaseValue, BonusScore = BonusValue, OverrideScore = OverrideValue)

        AbilityScoresModel = CharacterSchema.AbilityScoresData(Strength = ExtractAbility(0), Dexterity = ExtractAbility(1), Constitution = ExtractAbility(2), Intelligence = ExtractAbility(3), Wisdom = ExtractAbility(4), Charisma = ExtractAbility(5))

        BaseHitPoints: int = Data.get("baseHitPoints", 10) or 10
        BonusHitPoints: int = Data.get("bonusHitPoints", 0) or 0
        OverrideHitPoints: Typing.Optional[int] = Data.get("overrideHitPoints")
        RemovedHitPoints: int = Data.get("removedHitPoints", 0) or 0
        TemporaryHitPoints: int = Data.get("temporaryHitPoints", 0) or 0
        EffectiveMaxHitPoints: int = OverrideHitPoints if (OverrideHitPoints is not None) else (BaseHitPoints + BonusHitPoints)
        CurrentHitPoints: int = max(0, EffectiveMaxHitPoints - RemovedHitPoints)

        HitPointsModel = CharacterSchema.HitPointsData(MaxHitPoints = EffectiveMaxHitPoints, CurrentHitPoints = CurrentHitPoints, TemporaryHitPoints = TemporaryHitPoints, BaseHitPoints = BaseHitPoints, BonusHitPoints = BonusHitPoints, OverrideHitPoints = OverrideHitPoints, RemovedHitPoints = RemovedHitPoints)

        DeathSavesDictionary: Typing.Dict[str, Typing.Any] = Data.get("deathSaves", {}) or {}
        DeathSavesModel = CharacterSchema.DeathSavesData(SuccessCount = DeathSavesDictionary.get("successCount", 0) or 0, FailureCount = DeathSavesDictionary.get("failCount", 0) or 0)

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
                    CandidateName: Typing.Optional[str] = None
                    if OptionValueID is not None and OptionValueID in OptionNameMapping:
                        CandidateName = OptionNameMapping[OptionValueID]

                    elif ChoiceItem.get("label"):
                        LabelText: str = str(ChoiceItem.get("label"))
                        if not LabelText.lower().startswith("choose"):
                            CandidateName = LabelText

                    if ComponentIDString and CandidateName:
                        if ComponentIDString not in ChoiceNameMapping:
                            ChoiceNameMapping[ComponentIDString] = []

                        if CandidateName not in ChoiceNameMapping[ComponentIDString]:
                            ChoiceNameMapping[ComponentIDString].append(CandidateName)

        ComponentModifierMapping: Typing.Dict[str, Typing.List[CharacterSchema.ModifierEntry]] = {
        }
        TopLevelModifiersList: Typing.List[CharacterSchema.ModifierEntry] = []

        for ModifierCategoryName in ["class", "feat"]:
            for RawModifier in AllModifiers.get(ModifierCategoryName, []):
                if not RawModifier:
                    continue

                ConvertedModifier: CharacterSchema.ModifierEntry = self.ConvertRawModifier(RawModifier)
                ComponentID: Typing.Optional[str] = str(RawModifier.get("componentId")) if RawModifier.get("componentId") else None
                if ComponentID:
                    if ComponentID not in ComponentModifierMapping:
                        ComponentModifierMapping[ComponentID] = []

                    ComponentModifierMapping[ComponentID].append(ConvertedModifier)

                else:
                    TopLevelModifiersList.append(ConvertedModifier)

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        if BackgroundDefinition.get("featureName"):
            FeaturesList.append(CharacterSchema.FeatureEntry(ID = f"background-{BackgroundDefinition.get("id", "feature")}", Name = str(BackgroundDefinition["featureName"]), SourceType = "Background", SourceName = str(BackgroundDefinition.get("name") or "Background"), Description = BackgroundFeatureDescription, IsEnabled = True))

        for TraitItem in Data.get("race", {}).get("racialTraits", []):
            TraitDefinition: Typing.Dict[str, Typing.Any] = TraitItem.get("definition", {}) or {}
            TraitName: str = str(TraitDefinition.get("name") or "")
            if not TraitName:
                continue

            FeaturesList.append(CharacterSchema.FeatureEntry(ID = str(TraitDefinition.get("id", TraitName.lower().replace(" ", "-"))), Name = TraitName, SourceType = "Species", SourceName = SpeciesModel.FullName, Description = self.CleanHTMLString(TraitDefinition.get("description") or TraitDefinition.get("snippet")), Snippet = self.CleanHTMLString(TraitDefinition.get("snippet")), IsEnabled = True))

        for FeatureItem in Data.get("feats", []):
            FeatureDefinition: Typing.Dict[str, Typing.Any] = FeatureItem.get("definition", {}) or {}
            FeatureName: str = str(FeatureDefinition["name"])
            ComponentIDKey: str = str(FeatureItem.get("componentId", ""))
            AssignedChoices: Typing.List[str] = ChoiceNameMapping.get(ComponentIDKey, [])
            AssignedModifiers: Typing.List[CharacterSchema.ModifierEntry] = ComponentModifierMapping.get(ComponentIDKey, [])
            FeaturesList.append(CharacterSchema.FeatureEntry(ID = ComponentIDKey, Name = FeatureName, SourceType = "Feat", SourceName = "Feats", SelectedChoices = AssignedChoices, Modifiers = AssignedModifiers, Description = self.CleanHTMLString(FeatureDefinition.get("description") or FeatureDefinition.get("snippet")), Snippet = self.CleanHTMLString(FeatureDefinition.get("snippet"))))

        for ClassProgress in Data.get("classes", []):
            ClassProgressionName: str = str(ClassProgress.get("definition", {}).get("name") or "")
            for ClassFeature in ClassProgress.get("classFeatures", []):
                FeatureDefinition: Typing.Dict[str, Typing.Any] = ClassFeature.get("definition", {}) or {}
                FeatureIDKey: str = str(FeatureDefinition.get("id", ""))
                FeatureName: str = str(FeatureDefinition["name"])
                RequiredLevel: int = FeatureDefinition.get("requiredLevel", 1)
                AssignedChoices = ChoiceNameMapping.get(FeatureIDKey, [])
                AssignedModifiers = ComponentModifierMapping.get(FeatureIDKey, [])
                FeaturesList.append(CharacterSchema.FeatureEntry(ID = FeatureIDKey, Name = FeatureName, SourceType = "Class", SourceName = ClassProgressionName, LevelRequirement = RequiredLevel, SelectedChoices = AssignedChoices, Modifiers = AssignedModifiers, Description = self.CleanHTMLString(FeatureDefinition.get("description") or FeatureDefinition.get("snippet")), Snippet = self.CleanHTMLString(FeatureDefinition.get("snippet"))))

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

        ContainersList: Typing.List[CharacterSchema.ContainerEntry] = []
        ContainersList.append(CharacterSchema.ContainerEntry(ID = "equipment", Name = "Equipment", IsCarried = True, WeightPounds = 0.0))
        ContainersList.append(CharacterSchema.ContainerEntry(ID = "carried", Name = "Carried", IsCarried = True, WeightPounds = 0.0))
        SeenContainers: Typing.Dict[str, bool] = {
            "equipment": True,
            "carried": True
        }

        for RawItem in Data.get("inventory", []):
            ItemDefinition: Typing.Dict[str, Typing.Any] = RawItem.get("definition", {}) or {}
            ItemName: str = str(ItemDefinition.get("name", "Item"))
            ItemWeight: float = float(ItemDefinition.get("weight", 0.0) or 0.0)
            ItemCost: float = float(ItemDefinition.get("cost", 0.0) or 0.0)
            ItemFilterType: Typing.Optional[str] = ItemDefinition.get("filterType")
            if ItemFilterType == "Container" or ItemDefinition.get("isContainer") or "backpack" in ItemName.lower() or "quiver" in ItemName.lower() or "pouch" in ItemName.lower():
                ContainerIDKey: str = str(RawItem.get("id"))
                if ContainerIDKey not in SeenContainers:
                    SeenContainers[ContainerIDKey] = True
                    CapacityVal: Typing.Optional[float] = float(ItemDefinition.get("capacityWeight", 0.0) or 0.0) if ItemDefinition.get("capacityWeight") else None
                    ContainersList.append(CharacterSchema.ContainerEntry(ID = ContainerIDKey, Name = ItemName, IsCarried = True, WeightPounds = ItemWeight, CostInGoldPieces = ItemCost, CapacityPounds = CapacityVal, Description = self.CleanHTMLString(ItemDefinition.get("description"))))

        InventoryList: Typing.List[CharacterSchema.InventoryItemEntry] = []
        for RawItem in Data.get("inventory", []):
            ItemDefinition = RawItem.get("definition", {}) or {}
            ItemName = str(ItemDefinition.get("name", "Item"))
            ItemQuantity: int = int(RawItem.get("quantity", 1) or 1)
            ItemWeight = float(ItemDefinition.get("weight", 0.0) or 0.0)
            ItemCost = float(ItemDefinition.get("cost", 0.0) or 0.0)
            IsEquipped: bool = bool(RawItem.get("equipped", False))
            IsAttuned: bool = bool(RawItem.get("isAttuned", False))
            NeedsAttunement: bool = bool(ItemDefinition.get("canAttune", False))
            RarityText: Typing.Optional[str] = ItemDefinition.get("rarity")
            ItemFilterType = ItemDefinition.get("filterType")
            RawContainerID: Typing.Optional[str] = str(RawItem.get("containerEntityId")) if RawItem.get("containerEntityId") else None
            RawItemIDString: str = str(RawItem.get("id", ""))
            DefinitionIDString: str = str(ItemDefinition.get("id", ""))

            ResolvedContainerID: str = "carried"
            if RawContainerID and RawContainerID in SeenContainers and RawContainerID not in ["equipment", "carried"]:
                ResolvedContainerID = RawContainerID

            elif IsEquipped:
                ResolvedContainerID = "equipment"

            ItemModifiersList: Typing.List[CharacterSchema.ModifierEntry] = []
            for GrantedModifier in ItemDefinition.get("grantedModifiers", []):
                if GrantedModifier:
                    ItemModifiersList.append(self.ConvertRawModifier(GrantedModifier))

            if RawItemIDString in ItemModifierMapping:
                ItemModifiersList.extend(ItemModifierMapping[RawItemIDString])

            elif DefinitionIDString in ItemModifierMapping:
                ItemModifiersList.extend(ItemModifierMapping[DefinitionIDString])

            ArmorClassValue: int = int(ItemDefinition.get("armorClass", 0) or 0)
            ArmorTypeIDValue: int = int(ItemDefinition.get("armorTypeId", 1) or 1)
            if ItemFilterType == "Armor":
                if ArmorTypeIDValue == 4:
                    ItemModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Bonus", ModifierSubType = "ShieldArmorClass", Value = ArmorClassValue if ArmorClassValue > 0 else 2, StringValue = "Shield", IsActive = True))

                elif ArmorClassValue > 0:
                    ArmorTypeNameString: str = "Light" if ArmorTypeIDValue == 1 else ("Medium" if ArmorTypeIDValue == 2 else "Heavy")
                    ItemModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Set", ModifierSubType = "BaseArmorClass", Value = ArmorClassValue, StringValue = ArmorTypeNameString, IsActive = True))

            InventoryList.append(CharacterSchema.InventoryItemEntry(ID = RawItemIDString, Name = ItemName, Quantity = ItemQuantity, WeightPounds = ItemWeight, CostInGoldPieces = ItemCost, IsEquipped = IsEquipped, RequiresAttunement = NeedsAttunement, IsAttuned = IsAttuned, Rarity = RarityText, ItemType = ItemFilterType, ContainerID = ResolvedContainerID, Description = self.CleanHTMLString(ItemDefinition.get("description") or ItemDefinition.get("snippet")), Properties = [], Modifiers = ItemModifiersList))

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
            SpellDescriptionText: Typing.Optional[str] = self.CleanHTMLString(SpellDefinition.get("description"))

            SpellsList.append(CharacterSchema.SpellEntry(ID = str(RawSpellItem.get("id", "")), Name = SpellName, Level = SpellLevel, School = SchoolName, CastingTime = CastingDescription, RangeDescription = RangeDescriptionText, DurationDescription = DurationDescriptionText, Components = CharacterSchema.SpellComponentData(Verbal = HasVerbal, Somatic = HasSomatic, Material = HasMaterial, MaterialDescription = MaterialText), IsConcentration = IsConcentration, IsRitual = IsRitual, IsPrepared = IsPrepared or AlwaysPrepared, AlwaysPrepared = AlwaysPrepared, SourceType = SourceOrigin, SourceName = SourceOriginName, Description = SpellDescriptionText))

        SpellsGroupDictionary: Typing.Dict[str, Typing.Any] = Data.get("spells", {}) or {}
        for GroupOriginName, GroupSpellList in SpellsGroupDictionary.items():
            if isinstance(GroupSpellList, list):
                for SpellObject in GroupSpellList:
                    ProcessSpellItem(SpellObject, GroupOriginName.capitalize(), GroupOriginName.capitalize())

        SpellListEntriesList: Typing.List[CharacterSchema.SpellListEntry] = []
        SeenSpellListNames: Typing.Dict[str, bool] = {
        }
        for ClassSpellGroup in Data.get("classSpells", []):
            MatchedClassName: str = "Class"
            for SpellGroupClass in Data.get("classes", []):
                if SpellGroupClass.get("id") == ClassSpellGroup.get("characterClassId"):
                    MatchedClassName = SpellGroupClass.get("definition", {}).get("name", "Class")

            ListName: str = f"{MatchedClassName} Spells"
            if ListName not in SeenSpellListNames:
                SeenSpellListNames[ListName] = True
                SpellListEntriesList.append(CharacterSchema.SpellListEntry(ID = ListName.lower().replace(" ", "-"), Name = ListName))

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
            PactMagicSlotModel = CharacterSchema.PactMagicSlotData(SlotLevel = FirstPactSlot.get("level", 1), TotalSlots = FirstPactSlot.get("available", 0) or 0, UsedSlots = FirstPactSlot.get("used", 0) or 0)

        SpellcastingModel = CharacterSchema.SpellcastingData(SpellSlots = SpellSlotsList, SpellLists = SpellListEntriesList, PactMagic = PactMagicSlotModel, Spells = SpellsList)

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
            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(SkillName = FormattedSkillName, AssociatedAbility = AssociatedAbility, ProficiencyTier = ProficiencyTierValue))

        SavingThrowProficienciesList: Typing.List[CharacterSchema.SavingThrowProficiencyEntry] = []
        for AbilityEnum in CharacterSchema.AbilityType:
            IsSaveProficient: bool = SeenSaves.get(AbilityEnum.value.lower(), False)
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(AbilityName = AbilityEnum, IsProficient = IsSaveProficient))

        CurrenciesDictionary: Typing.Dict[str, int] = Data.get("currencies", {}) or {}
        CurrenciesModel = CharacterSchema.CurrenciesData(CopperPieces = CurrenciesDictionary.get("cp", 0) or 0, SilverPieces = CurrenciesDictionary.get("sp", 0) or 0, ElectrumPieces = CurrenciesDictionary.get("ep", 0) or 0, GoldPieces = CurrenciesDictionary.get("gp", 0) or 0, PlatinumPieces = CurrenciesDictionary.get("pp", 0) or 0)

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
                    AttacksList.append(CharacterSchema.AttackActionEntry(ID = str(ActionItem.get("id", "")), Name = ActionName, AttackBonus = ComputedProficiencyBonus + AbilityScoresModel.Dexterity.Modifier, DamageExpression = "", DamageType = "", RangeDescription = "5 ft", AttackSource = ActionOriginName.capitalize(), Notes = ActionNotes))

                else:
                    ActionsList.append(CharacterSchema.ActionEntry(ID = str(ActionItem.get("id", "")), Name = ActionName, ActionType = CharacterSchema.ActionActivationType.BonusAction if ActionItem.get("actionType") == 2 else CharacterSchema.ActionActivationType.Action, SourceType = ActionOriginName.capitalize()))

        TraitsDictionary: Typing.Dict[str, Typing.Any] = Data.get("traits", {}) or {}
        PersonalityModel = CharacterSchema.PersonalityData(PersonalityTraits = self.CleanHTMLString(TraitsDictionary.get("personalityTraits")), Ideals = self.CleanHTMLString(TraitsDictionary.get("ideals")), Bonds = self.CleanHTMLString(TraitsDictionary.get("bonds")), Flaws = self.CleanHTMLString(TraitsDictionary.get("flaws")))

        NotesDictionary: Typing.Dict[str, Typing.Any] = Data.get("notes", {}) or {}
        NotesModel = CharacterSchema.NotesData(Backstory = self.CleanHTMLString(NotesDictionary.get("backstory")), Allies = self.CleanHTMLString(NotesDictionary.get("allies")), Enemies = self.CleanHTMLString(NotesDictionary.get("enemies")), Organizations = self.CleanHTMLString(NotesDictionary.get("organizations")), PersonalPossessions = self.CleanHTMLString(NotesDictionary.get("personalPossessions")), OtherHoldings = self.CleanHTMLString(NotesDictionary.get("otherHoldings")), CustomNotes = self.CleanHTMLString(NotesDictionary.get("otherNotes")))

        UnifiedSheet = CharacterSchema.DND5thEditionCharacterSheet(SchemaVersion = "1.0.0", GameSystem = "DND5thEdition", OriginalSource = "DNDBeyond", Name = CharacterName, PlayerName = PlayerName, Gender = Gender, Alignment = AlignmentString, Faith = Faith, Lifestyle = Data.get("lifestyle"), TotalLevel = TotalCharacterLevel, ExperiencePoints = Data.get("currentXp", 0) or 0, Inspiration = Data.get("inspiration", False) or False, ProficiencyBonus = ComputedProficiencyBonus, OverrideInitiativeBonus = OverrideInitiativeScoreValue, IsDirty = HasAnyClassDirty, Species = SpeciesModel, Background = BackgroundModel, Classes = ClassesList, AbilityScores = AbilityScoresModel, HitPoints = HitPointsModel, DeathSaves = DeathSavesModel, ArmorClass = CharacterSchema.ArmorClassData(OverrideArmorClass = OverrideArmorClassScoreValue), Speed = CharacterSchema.SpeedData(WalkingSpeedFeet = 30, OverrideWalkingSpeedFeet = OverrideWalkingSpeedValue), Senses = SensesList, SavingThrowProficiencies = SavingThrowProficienciesList, SkillProficiencies = SkillProficienciesList, ArmorProficiencies = ArmorProficienciesList, WeaponProficiencies = WeaponProficienciesList, ToolProficiencies = ToolProficienciesList, LanguageProficiencies = LanguageProficienciesList, DamageResistances = DamageResistancesList, DamageImmunities = DamageImmunitiesList, DamageVulnerabilities = DamageVulnerabilitiesList, ConditionImmunities = ConditionImmunitiesList, Attacks = AttacksList, Actions = ActionsList, Containers = ContainersList, Inventory = InventoryList, AttunementTotalSlots = 3, AttunementUsedSlots = sum(1 for InventoryItem in InventoryList if InventoryItem.IsAttuned), CarryingCapacityMultiplier = 1.0, CarryingCapacityPounds = round(AbilityScoresModel.Strength.BaseScore * 15.0, 2), Currencies = CurrenciesModel, Spellcasting = SpellcastingModel, Features = FeaturesList, Personality = PersonalityModel, PhysicalAppearance = AppearanceData, Notes = NotesModel, Modifiers = TopLevelModifiersList)
        PrimaryClassName: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "None"
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Mapped Character Sheet: \"{UnifiedSheet.Name}\" ({PrimaryClassName}, Level {UnifiedSheet.TotalLevel})")
        return UnifiedSheet

    def MapDicecloudCharacter(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        CharactersList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("characters", [])
        if CharactersList:
            CharacterData: Typing.Dict[str, Typing.Any] = CharactersList[0]

        else:
            CharacterData = {
            }

        RawCharacterName: str = str(CharacterData.get("name") or "").strip()
        if not RawCharacterName:
            raise ValueError("Dicecloud character sheet does not contain a character name.")

        CharacterName: str = RawCharacterName
        Gender: Typing.Optional[str] = CharacterData.get("gender")
        RaceName: str = str(CharacterData.get("race") or "").strip()
        Alignment: Typing.Optional[str] = CharacterData.get("alignment")

        RawWeight = CharacterData.get("weight")
        WeightString: Typing.Optional[str] = None
        if isinstance(RawWeight, (int, float, str)):
            WeightString = str(RawWeight)

        elif isinstance(RawWeight, dict) and "value" in RawWeight and RawWeight["value"]:
            WeightString = str(RawWeight["value"])

        AppearanceData = CharacterSchema.PhysicalAppearanceData(Age = str(CharacterData.get("age")) if (isinstance(CharacterData.get("age"), (int, float, str))) else None, Height = str(CharacterData.get("height")) if CharacterData.get("height") else None, Weight = WeightString, Hair = CharacterData.get("hair"), Eyes = CharacterData.get("eyes"), Skin = CharacterData.get("skin"), AppearanceDescription = self.CleanHTMLString(CharacterData.get("description")), PortraitURL = CharacterData.get("picture"))

        SpeciesModel = CharacterSchema.SpeciesData(RaceName = RaceName, FullName = RaceName)

        BackgroundModel = CharacterSchema.BackgroundData(Name = "Soldier" if ("soldier" in (CharacterData.get("backstory") or "").lower()) else "Adventurer")

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

            ClassesList.append(CharacterSchema.ClassProgressEntry(ClassName = ClassName, Level = ClassLevel, SubclassName = SubclassName, HitDie = HitDie, HitDiceTotal = ClassLevel, HitDiceUsed = 0, IsStartingClass = (ClassIndex == 0), SpellcastingAbility = SpellcastingAbilityEnum, IsDirty = IsClassDirty))

        if not ClassesList:
            raise ValueError("Dicecloud character sheet must specify at least one valid class.")

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
        CarryCapacityMultiplierValue: float = 1.0
        WalkingSpeedBaseValue: int = 30

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
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Set", ModifierSubType = "BaseArmorClass", Value = CalculatedArmorClassBase, StringValue = ArmorNameDetected or "Armor", IsActive = True))

            elif StatTarget in self.DamageMultiplierStatMapping:
                if EffectValue is not None:
                    MultiplierOverrides[StatTarget] = float(EffectValue)

            elif StatTarget in ["carrymultiplier", "carry-multiplier", "carryingcapacitymultiplier"]:
                if EffectValue is not None:
                    CarryCapacityMultiplierValue = float(EffectValue)

            elif StatTarget == "speed" and OperationType == "base":
                if EffectValue is not None:
                    WalkingSpeedBaseValue = int(EffectValue)

        AbilityScoresModel = CharacterSchema.AbilityScoresData(Strength = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["strength"]), Dexterity = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["dexterity"]), Constitution = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["constitution"]), Intelligence = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["intelligence"]), Wisdom = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["wisdom"]), Charisma = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["charisma"]), IsDirty = False)

        ClassLevelsForHitPoints: Typing.List[Typing.Tuple[str, int, bool]] = [(ClassItem.ClassName, ClassItem.Level, ClassItem.IsStartingClass) for ClassItem in ClassesList]
        CalculatedHitPoints, HitPointsDirty = self.FiveETools.CalculateHitPoints(ClassLevelsForHitPoints, AbilityScoresModel.Constitution.Modifier)
        if CalculatedHitPoints <= 0:
            CalculatedHitPoints = self.ExtractNumericStat(CharacterData.get("maxHitPoints"), Default = 10)
            HitPointsDirty = True

        DamageTaken: int = self.ExtractNumericStat(CharacterData.get("damage"), Default = 0)
        CurrentHitPoints: int = max(0, CalculatedHitPoints - DamageTaken)
        TemporaryHitPoints: int = self.ExtractNumericStat(CharacterData.get("tempHP"), Default = 0)

        HitPointsModel = CharacterSchema.HitPointsData(MaxHitPoints = CalculatedHitPoints, CurrentHitPoints = CurrentHitPoints, TemporaryHitPoints = TemporaryHitPoints, BaseHitPoints = CalculatedHitPoints, IsDirty = HitPointsDirty or HasAnyClassDirty)

        RawDeathSave: Typing.Dict[str, Typing.Any] = CharacterData.get("deathSave", {}) or {}
        DeathSavesModel = CharacterSchema.DeathSavesData(SuccessCount = RawDeathSave.get("pass", 0) or 0, FailureCount = RawDeathSave.get("fail", 0) or 0)

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
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = ModifierType, ModifierSubType = ProficiencyName.lower().replace(" ", "-"), StringValue = FormattedSkillName, IsActive = True))

            elif ProficiencyType == "save":
                SaveKey: str = ProficiencyName.lower().replace("save", "").strip()
                SeenSaves[SaveKey] = True
                TopLevelModifiersList.append(CharacterSchema.ModifierEntry(ModifierType = "Proficiency", ModifierSubType = f"{SaveKey}-saving-throws", StringValue = ProficiencyName, IsActive = True))

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
            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(SkillName = FormattedSkillName, AssociatedAbility = AssociatedAbility, ProficiencyTier = ProficiencyTier))

        for AbilityEnum in CharacterSchema.AbilityType:
            IsSaveProf: bool = SeenSaves.get(AbilityEnum.value.lower(), False)
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(AbilityName = AbilityEnum, IsProficient = IsSaveProf))

        ContainersList: Typing.List[CharacterSchema.ContainerEntry] = [CharacterSchema.ContainerEntry(ID = "equipment", Name = "Equipment", IsCarried = True, WeightPounds = 0.0), CharacterSchema.ContainerEntry(ID = "carried", Name = "Carried", IsCarried = True, WeightPounds = 0.0)]
        SeenContainerIDs: Typing.Dict[str, bool] = {
            "equipment": True,
            "carried": True
        }
        RawContainers: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("containers", [])
        for ContainerItem in RawContainers:
            ContainerID: str = str(ContainerItem.get("_id", ""))
            SeenContainerIDs[ContainerID] = True
            ContainerDescriptionText: Typing.Optional[str] = self.CleanHTMLString(ContainerItem.get("description"))
            ParsedCapacityPounds: Typing.Optional[float] = None
            if ContainerDescriptionText:
                CapacityMatch = RegularExpressions.search(r"holds up to\s+([0-9]+(?:\.[0-9]+)?)\s+pounds", ContainerDescriptionText, flags = RegularExpressions.IGNORECASE)
                if CapacityMatch:
                    ParsedCapacityPounds = float(CapacityMatch.group(1))

            ContainersList.append(CharacterSchema.ContainerEntry(ID = ContainerID, Name = ContainerItem.get("name", "Backpack"), IsCarried = ContainerItem.get("isCarried", True), WeightPounds = float(ContainerItem.get("weight", 0.0) or 0.0), CapacityPounds = ParsedCapacityPounds, CostInGoldPieces = float(ContainerItem.get("value", 0.0) or 0.0), Description = ContainerDescriptionText, Color = ContainerItem.get("color")))

        InventoryList: Typing.List[CharacterSchema.InventoryItemEntry] = []
        GoldPiecesCount: int = 0
        SilverPiecesCount: int = 0
        ElectrumPiecesCount: int = 0
        CopperPiecesCount: int = 0
        PlatinumPiecesCount: int = 0

        RawItems: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("items", [])
        for ItemItem in RawItems:
            ItemName: str = ItemItem.get("name", "Unknown Item")
            ItemQuantity: int = int(ItemItem.get("quantity", 1) or 1)
            ItemWeight: float = float(ItemItem.get("weight", 0.0) or 0.0)
            ItemCost: float = float(ItemItem.get("value", 0.0) or 0.0)
            IsEquipped: bool = ItemItem.get("enabled", False) or False
            NeedsAttunement: bool = ItemItem.get("requiresAttunement", False) or False
            IsItemAttuned: bool = bool(ItemItem.get("attuned", False) or (NeedsAttunement and IsEquipped))
            ParentDictionary: Typing.Dict[str, Typing.Any] = ItemItem.get("parent", {}) or {}
            ParentCollection: str = ParentDictionary.get("collection", "")
            ParentID: Typing.Optional[str] = ParentDictionary.get("id")

            if ParentCollection == "Containers" and ParentID and ParentID in SeenContainerIDs:
                ContainerID = ParentID

            else:
                ContainerID = "equipment" if IsEquipped else "carried"

            LowerItemName: str = ItemName.lower()
            if "gold piece" in LowerItemName:
                GoldPiecesCount += ItemQuantity

            elif "silver piece" in LowerItemName:
                SilverPiecesCount += ItemQuantity

            elif "copper piece" in LowerItemName:
                CopperPiecesCount += ItemQuantity

            elif "electrum piece" in LowerItemName:
                ElectrumPiecesCount += ItemQuantity

            elif "platinum piece" in LowerItemName:
                PlatinumPiecesCount += ItemQuantity

            else:
                InventoryList.append(CharacterSchema.InventoryItemEntry(ID = str(ItemItem.get("_id", "")), Name = ItemName, Quantity = ItemQuantity, WeightPounds = ItemWeight, CostInGoldPieces = ItemCost, IsEquipped = IsEquipped, RequiresAttunement = NeedsAttunement, IsAttuned = IsItemAttuned, ContainerID = ContainerID, Description = self.CleanHTMLString(ItemItem.get("description")), Color = ItemItem.get("color"), PluralName = ItemItem.get("plural"), IsDirty = False))

        CurrenciesModel = CharacterSchema.CurrenciesData(CopperPieces = CopperPiecesCount, SilverPieces = SilverPiecesCount, ElectrumPieces = ElectrumPiecesCount, GoldPieces = GoldPiecesCount, PlatinumPieces = PlatinumPiecesCount)

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

            AttacksList.append(CharacterSchema.AttackActionEntry(ID = str(AttackItem.get("_id", "")), Name = AttackName, AttackBonus = AttackBonus, DamageExpression = DamageExpression, DamageType = DamageType, RangeDescription = RangeDescription, Properties = PropertiesList, IsEquipped = AttackItem.get("enabled", True), AttackSource = AttackItem.get("source", "Weapon") or "Weapon", Notes = DetailsText, Color = AttackItem.get("color"), IsDirty = IsAttackDirty))

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

        SpellListEntriesList: Typing.List[CharacterSchema.SpellListEntry] = []
        SpellListIDToName: Typing.Dict[str, str] = {
        }
        RawSpellLists: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("spellLists", [])
        for SpellListItem in RawSpellLists:
            RawListName: str = SpellListItem.get("name", "Spell List")
            CleanListName: str = RegularExpressions.sub(r"^[0-9]+[│|]\s*", "", RawListName).strip()
            ListID: str = str(SpellListItem.get("_id", ""))
            SpellListIDToName[ListID] = CleanListName
            ListAbilityStr = SpellListItem.get("ability")
            ListAbilityEnum: Typing.Optional[CharacterSchema.AbilityType] = self.MapStringToAbilityType(ListAbilityStr) if ListAbilityStr else None

            RawSaveDC = SpellListItem.get("saveDC")
            CalculatedSaveDC: Typing.Optional[int] = None
            if RawSaveDC is not None:
                CalculatedSaveDC = self.EvaluateDicecloudFormula(RawSaveDC, FormulaContext)

            RawAttackBonus = SpellListItem.get("attackBonus")
            CalculatedAttackBonus: Typing.Optional[int] = None
            if RawAttackBonus is not None:
                CalculatedAttackBonus = self.EvaluateDicecloudFormula(RawAttackBonus, FormulaContext)

            RawMaxPrepared = SpellListItem.get("maxPrepared")
            CalculatedMaxPrepared: Typing.Optional[int] = None
            if RawMaxPrepared is not None:
                CalculatedMaxPrepared = self.EvaluateDicecloudFormula(RawMaxPrepared, FormulaContext)

            SpellListEntriesList.append(CharacterSchema.SpellListEntry(ID = ListID, Name = CleanListName, SpellcastingAbility = ListAbilityEnum, SpellSaveDC = CalculatedSaveDC, SpellAttackBonus = CalculatedAttackBonus, MaxPrepared = CalculatedMaxPrepared, Color = SpellListItem.get("color"), IsDirty = False))

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

            ParentDictionary = SpellItem.get("parent", {}) or {}
            SpellParentID: Typing.Optional[str] = ParentDictionary.get("id")
            SpellSourceName: str = SpellListIDToName.get(SpellParentID, "Spellbook") if SpellParentID else "Spellbook"

            SpellsList.append(CharacterSchema.SpellEntry(ID = str(SpellItem.get("_id", "")), Name = SpellName, Level = SpellLevel, School = SchoolName, CastingTime = CastingTimeStr, RangeDescription = RangeStr, DurationDescription = DurationStr, Components = CharacterSchema.SpellComponentData(Verbal = bool(ComponentsDictionary.get("verbal", False)), Somatic = bool(ComponentsDictionary.get("somatic", False)), Material = HasMaterialComponent, MaterialDescription = MaterialDescription), IsConcentration = IsConcentration, IsRitual = IsRitual, IsPrepared = (PreparedValue == "prepared"), SourceType = "Class", SourceName = SpellSourceName, Description = self.CleanHTMLString(SpellItem.get("description")), Color = SpellItem.get("color"), IsDirty = False))

        ClassProgressionList: Typing.List[Typing.Tuple[str, int, Typing.Optional[str]]] = [(ClassItem.ClassName, ClassItem.Level, ClassItem.SubclassName) for ClassItem in ClassesList]
        CalculatedSpellSlots: Typing.List[Typing.Tuple[int, int]] = self.FiveETools.CalculateMulticlassSpellSlots(ClassProgressionList)
        SpellSlotsList: Typing.List[CharacterSchema.SpellSlotEntry] = [CharacterSchema.SpellSlotEntry(Level = SlotLevel, TotalSlots = SlotCount, UsedSlots = 0) for SlotLevel, SlotCount in CalculatedSpellSlots]

        WarlockLevel: int = sum(ClassItem.Level for ClassItem in ClassesList if (self.FiveETools.FindCanonicalClassName(ClassItem.ClassName) or ClassItem.ClassName).lower() == "warlock")
        PactMagicData: Typing.Optional[CharacterSchema.PactMagicSlotData] = None
        if WarlockLevel > 0:
            PactSlotInformation: Typing.Optional[Typing.Tuple[int, int]] = self.FiveETools.CalculatePactMagicSlots(WarlockLevel)
            if PactSlotInformation:
                PactMagicData = CharacterSchema.PactMagicSlotData(SlotLevel = PactSlotInformation[0], TotalSlots = PactSlotInformation[1], UsedSlots = 0)

        SpellcastingEntriesList: Typing.List[CharacterSchema.SpellcastingEntry] = []

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

            SpellcastingEntriesList.append(CharacterSchema.SpellcastingEntry(SpellcastingClass = CanonicalName, SpellcastingAbility = SpellcastingAbilityEnum, SpellSaveDC = SaveDC, SpellAttackBonus = AttackBonus, IsDirty = IsEntryDirty))

        SpellcastingModel = CharacterSchema.SpellcastingData(SpellcastingEntries = SpellcastingEntriesList, SpellLists = SpellListEntriesList, SpellSlots = SpellSlotsList, PactMagic = PactMagicData, Spells = SpellsList)

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        RawFeatures: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("features", [])
        for FeatureItem in RawFeatures:
            RawFeatureName: str = FeatureItem.get("name", "Feature")
            CleanFeatureName: str = RegularExpressions.sub(r"^[0-9]+[│|]\s*", "", RawFeatureName).strip()
            ResetTypeStr: str = (FeatureItem.get("reset") or "longRest").lower()
            ResetEnum: CharacterSchema.ResetScheduleType = CharacterSchema.ResetScheduleType.ShortRest if ("short" in ResetTypeStr) else (CharacterSchema.ResetScheduleType.LongRest if ("long" in ResetTypeStr) else CharacterSchema.ResetScheduleType.Manual)

            SourceType: str = "Class"
            SourceName: str = "Class Feature"
            LowerFeatureName: str = CleanFeatureName.lower()
            if "feat" in LowerFeatureName:
                SourceType = "Feat"
                SourceName = CleanFeatureName

            elif "human" in LowerFeatureName or "race" in LowerFeatureName:
                SourceType = "Species"
                SourceName = RaceName

            else:
                for ClassItem in ClassesList:
                    if ClassItem.ClassName.lower() in LowerFeatureName:
                        SourceType = "Class"
                        SourceName = ClassItem.ClassName
                        break

            LimitedUseDataModel: Typing.Optional[CharacterSchema.LimitedUseData] = None
            RawUses = FeatureItem.get("uses")
            if RawUses is not None:
                CalculatedMaxUses: int = self.EvaluateDicecloudFormula(RawUses, FormulaContext)
                LimitedUseDataModel = CharacterSchema.LimitedUseData(MaxUses = CalculatedMaxUses, UsedUses = int(FeatureItem.get("used", 0) or 0), ResetType = ResetEnum)

            FeaturesList.append(CharacterSchema.FeatureEntry(ID = str(FeatureItem.get("_id", "")), Name = CleanFeatureName, SourceType = SourceType, SourceName = SourceName, IsEnabled = FeatureItem.get("enabled", True), LimitedUse = LimitedUseDataModel, Description = self.CleanHTMLString(FeatureItem.get("description")), Color = FeatureItem.get("color"), IsDirty = False))

        PersonalityModel = CharacterSchema.PersonalityData(PersonalityTraits = self.CleanHTMLString(CharacterData.get("personality")), Ideals = self.CleanHTMLString(CharacterData.get("ideals")), Bonds = self.CleanHTMLString(CharacterData.get("bonds")), Flaws = self.CleanHTMLString(CharacterData.get("flaws")))

        DicecloudDescription: Typing.Optional[str] = CharacterData.get("description") or CharacterData.get("backstory")
        NotesModel = CharacterSchema.NotesData(Backstory = self.CleanHTMLString(DicecloudDescription))

        ArmorClassModel = CharacterSchema.ArmorClassData(OverrideArmorClass = CalculatedArmorClassBase if CalculatedArmorClassBase > 10 else None, BaseArmorClass = CalculatedArmorClassBase, ArmorName = ArmorNameDetected)

        IsSheetDirty: bool = (HasAnyClassDirty or HitPointsModel.IsDirty or any(ClassItem.IsDirty for ClassItem in ClassesList) or any(AttackItem.IsDirty for AttackItem in AttacksList) or any(SpellcastItem.IsDirty for SpellcastItem in SpellcastingModel.SpellcastingEntries))

        UnifiedSheet = CharacterSchema.DND5thEditionCharacterSheet(SchemaVersion = "1.0.0", GameSystem = "DND5thEdition", OriginalSource = "Dicecloud", Name = CharacterName, Gender = Gender, Alignment = Alignment, TotalLevel = TotalCharacterLevel, ExperiencePoints = 0, ProficiencyBonus = ComputedProficiencyBonus, IsDirty = IsSheetDirty, Species = SpeciesModel, Background = BackgroundModel, Classes = ClassesList, AbilityScores = AbilityScoresModel, HitPoints = HitPointsModel, DeathSaves = DeathSavesModel, ArmorClass = ArmorClassModel, Speed = CharacterSchema.SpeedData(WalkingSpeedFeet = WalkingSpeedBaseValue), SavingThrowProficiencies = SavingThrowProficienciesList, SkillProficiencies = SkillProficienciesList, ArmorProficiencies = ArmorProficienciesList, WeaponProficiencies = WeaponProficienciesList, ToolProficiencies = ToolProficienciesList, LanguageProficiencies = LanguageProficienciesList, DamageResistances = DamageResistancesList, DamageImmunities = DamageImmunitiesList, DamageVulnerabilities = DamageVulnerabilitiesList, Attacks = AttacksList, Containers = ContainersList, Inventory = InventoryList, AttunementTotalSlots = 3, AttunementUsedSlots = sum(1 for InventoryItem in InventoryList if InventoryItem.IsAttuned), CarryingCapacityMultiplier = CarryCapacityMultiplierValue, CarryingCapacityPounds = round(AbilityScoresModel.Strength.BaseScore * 15.0 * CarryCapacityMultiplierValue, 2), Currencies = CurrenciesModel, Spellcasting = SpellcastingModel, Features = FeaturesList, Personality = PersonalityModel, PhysicalAppearance = AppearanceData, Notes = NotesModel, Modifiers = TopLevelModifiersList)
        PrimaryClassName: str = UnifiedSheet.Classes[0].ClassName if UnifiedSheet.Classes else "None"
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Mapped Character Sheet: \"{UnifiedSheet.Name}\" ({PrimaryClassName}, Level {UnifiedSheet.TotalLevel})")
        return UnifiedSheet

    def MapManualFormData(self, FormData: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        ClassPattern: RegularExpressions.Pattern = RegularExpressions.compile(r"^Classes\[(\d+)\]\.(\w+)$")
        SpellListPattern: RegularExpressions.Pattern = RegularExpressions.compile(r"^SpellLists\[(\d+)\]\.(\w+)$")
        SpellSlotPattern: RegularExpressions.Pattern = RegularExpressions.compile(r"^SpellSlots\[(\d+)\]\.(\w+)$")
        ContainerPattern: RegularExpressions.Pattern = RegularExpressions.compile(r"^Containers\[(\d+)\]\.(\w+)$")
        InventoryPattern: RegularExpressions.Pattern = RegularExpressions.compile(r"^Inventory\[(\d+)\]\.(\w+)$")

        ClassEntriesDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
        }
        SpellListsDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
        }
        SpellSlotsDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
        }
        ContainerEntriesDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
        }
        InventoryEntriesDictionary: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = {
        }

        for FieldKey, FieldValue in FormData.items():
            ClassMatch = ClassPattern.match(FieldKey)
            if ClassMatch:
                ClassIndex: int = int(ClassMatch.group(1))
                ClassProperty: str = ClassMatch.group(2)
                if ClassIndex not in ClassEntriesDictionary:
                    ClassEntriesDictionary[ClassIndex] = {
                    }

                ClassEntriesDictionary[ClassIndex][ClassProperty] = FieldValue
                continue

            SpellListMatch = SpellListPattern.match(FieldKey)
            if SpellListMatch:
                ListIndex: int = int(SpellListMatch.group(1))
                ListProperty: str = SpellListMatch.group(2)
                if ListIndex not in SpellListsDictionary:
                    SpellListsDictionary[ListIndex] = {
                    }

                SpellListsDictionary[ListIndex][ListProperty] = FieldValue
                continue

            SpellSlotMatch = SpellSlotPattern.match(FieldKey)
            if SpellSlotMatch:
                SlotIndex: int = int(SpellSlotMatch.group(1))
                SlotProperty: str = SpellSlotMatch.group(2)
                if SlotIndex not in SpellSlotsDictionary:
                    SpellSlotsDictionary[SlotIndex] = {
                    }

                SpellSlotsDictionary[SlotIndex][SlotProperty] = FieldValue
                continue

            ContainerMatch = ContainerPattern.match(FieldKey)
            if ContainerMatch:
                ContainerIndex: int = int(ContainerMatch.group(1))
                ContainerProperty: str = ContainerMatch.group(2)
                if ContainerIndex not in ContainerEntriesDictionary:
                    ContainerEntriesDictionary[ContainerIndex] = {
                    }

                ContainerEntriesDictionary[ContainerIndex][ContainerProperty] = FieldValue
                continue

            InventoryMatch = InventoryPattern.match(FieldKey)
            if InventoryMatch:
                InventoryIndex: int = int(InventoryMatch.group(1))
                InventoryProperty: str = InventoryMatch.group(2)
                if InventoryIndex not in InventoryEntriesDictionary:
                    InventoryEntriesDictionary[InventoryIndex] = {
                    }

                InventoryEntriesDictionary[InventoryIndex][InventoryProperty] = FieldValue
                continue

        RawCharacterName: str = str(FormData.get("Name") or "").strip()
        if not RawCharacterName:
            raise ValueError("Character name is required and cannot be empty.")

        CharacterName: str = RawCharacterName
        PlayerName: Typing.Optional[str] = FormData.get("PlayerName")
        Gender: Typing.Optional[str] = FormData.get("Gender")
        Alignment: Typing.Optional[str] = FormData.get("Alignment")
        Faith: Typing.Optional[str] = FormData.get("Faith")
        Lifestyle: Typing.Optional[str] = FormData.get("Lifestyle")
        InspirationRaw = FormData.get("Inspiration", False)
        Inspiration: bool = str(InspirationRaw).lower() in ["true", "1", "yes", "on"]

        SpeciesName: str = str(FormData.get("Species") or "").strip()
        SubraceName: Typing.Optional[str] = FormData.get("Subrace")
        FullSpeciesName: str = f"{SubraceName} {SpeciesName}".strip() if (SubraceName and SpeciesName) else SpeciesName
        SpeciesModel = CharacterSchema.SpeciesData(RaceName = SpeciesName, SubraceName = SubraceName, FullName = FullSpeciesName)

        BackgroundName: str = str(FormData.get("Background") or "").strip()
        BackgroundModel = CharacterSchema.BackgroundData(Name = BackgroundName)

        ClassesList: Typing.List[CharacterSchema.ClassProgressEntry] = []
        if ClassEntriesDictionary:
            SortedClassIndices = sorted(ClassEntriesDictionary.keys())
            HasInitialAssigned: bool = False
            for CIndex in SortedClassIndices:
                ClassData = ClassEntriesDictionary[CIndex]
                ClassNameStr: str = str(ClassData.get("ClassName") or "").strip()
                if not ClassNameStr:
                    raise ValueError("Character class is required.")

                CanonicalName: str = self.FiveETools.FindCanonicalClassName(ClassNameStr) or ClassNameStr
                SubclassNameStr: Typing.Optional[str] = str(ClassData.get("Subclass") or "").strip() or None
                RawLevel = ClassData.get("Level")
                if (RawLevel is None) or (not str(RawLevel).strip()):
                    raise ValueError("Character level must be a valid positive integer.")

                LevelNum: int = int(RawLevel)
                if LevelNum < 1:
                    raise ValueError("Character level must be a valid positive integer.")

                ExpNum: int = int(ClassData.get("Experience", 0) or 0)
                IsInitialRaw = ClassData.get("IsInitialClass", False)
                IsInitial: bool = str(IsInitialRaw).lower() in ["true", "1", "on"]
                if IsInitial and not HasInitialAssigned:
                    HasInitialAssigned = True

                elif IsInitial and HasInitialAssigned:
                    IsInitial = False

                HitDieVal: int = self.FiveETools.GetClassHitDie(CanonicalName) or int(ClassData.get("HitDie", 8) or 8)
                SpellcastAbilityStr: Typing.Optional[str] = self.FiveETools.GetClassSpellcastingAbility(CanonicalName, SubclassNameStr)
                SpellcastAbilityEnum: Typing.Optional[CharacterSchema.AbilityType] = self.MapStringToAbilityType(SpellcastAbilityStr)

                ClassesList.append(CharacterSchema.ClassProgressEntry(ClassName = CanonicalName, Level = LevelNum, SubclassName = SubclassNameStr, HitDie = HitDieVal, HitDiceTotal = LevelNum, HitDiceUsed = 0, IsStartingClass = IsInitial, SpellcastingAbility = SpellcastAbilityEnum, ExperiencePoints = ExpNum, IsDirty = False))

            if ClassesList and not any(C.IsStartingClass for C in ClassesList):
                ClassesList[0].IsStartingClass = True

        else:
            FlatClassName: str = str(FormData.get("ClassOrCareer") or "").strip()
            if not FlatClassName:
                raise ValueError("Character class is required.")

            CanonicalName = self.FiveETools.FindCanonicalClassName(FlatClassName) or FlatClassName
            FlatSubclass: Typing.Optional[str] = FormData.get("Subclass")
            RawLevel = FormData.get("LevelOrTerms")
            if (RawLevel is None) or (not str(RawLevel).strip()):
                raise ValueError("Character level must be a valid positive integer.")

            FlatLevel: int = int(RawLevel)
            if FlatLevel < 1:
                raise ValueError("Character level must be a valid positive integer.")

            FlatExp: int = int(FormData.get("ExperiencePoints", 0) or 0)
            FlatHitDie: int = self.FiveETools.GetClassHitDie(CanonicalName) or 8
            FlatSpellcastAbilityStr: Typing.Optional[str] = self.FiveETools.GetClassSpellcastingAbility(CanonicalName, FlatSubclass)
            ClassesList.append(CharacterSchema.ClassProgressEntry(ClassName = CanonicalName, Level = FlatLevel, SubclassName = FlatSubclass, HitDie = FlatHitDie, HitDiceTotal = FlatLevel, HitDiceUsed = 0, IsStartingClass = True, SpellcastingAbility = self.MapStringToAbilityType(FlatSpellcastAbilityStr), ExperiencePoints = FlatExp, IsDirty = False))

        if not ClassesList:
            raise ValueError("Character must specify at least one valid class.")

        TotalCharacterLevel: int = sum(C.Level for C in ClassesList)
        ComputedProficiencyBonus: int = self.ComputeProficiencyBonusForLevel(TotalCharacterLevel)

        RawStrength = FormData.get("Strength") or FormData.get("AbilityScores.Strength")
        RawDexterity = FormData.get("Dexterity") or FormData.get("AbilityScores.Dexterity")
        RawConstitution = FormData.get("Constitution") or FormData.get("AbilityScores.Constitution")
        RawIntelligence = FormData.get("Intelligence") or FormData.get("AbilityScores.Intelligence")
        RawWisdom = FormData.get("Wisdom") or FormData.get("AbilityScores.Wisdom")
        RawCharisma = FormData.get("Charisma") or FormData.get("AbilityScores.Charisma")
        if (RawStrength is None) or (RawDexterity is None) or (RawConstitution is None) or (RawIntelligence is None) or (RawWisdom is None) or (RawCharisma is None):
            raise ValueError("All six ability scores must be provided as valid integers.")

        StrengthScore: int = int(RawStrength)
        DexterityScore: int = int(RawDexterity)
        ConstitutionScore: int = int(RawConstitution)
        IntelligenceScore: int = int(RawIntelligence)
        WisdomScore: int = int(RawWisdom)
        CharismaScore: int = int(RawCharisma)

        AbilityScoresModel = CharacterSchema.AbilityScoresData(Strength = CharacterSchema.AbilityScoreEntry(BaseScore = StrengthScore), Dexterity = CharacterSchema.AbilityScoreEntry(BaseScore = DexterityScore), Constitution = CharacterSchema.AbilityScoreEntry(BaseScore = ConstitutionScore), Intelligence = CharacterSchema.AbilityScoreEntry(BaseScore = IntelligenceScore), Wisdom = CharacterSchema.AbilityScoreEntry(BaseScore = WisdomScore), Charisma = CharacterSchema.AbilityScoreEntry(BaseScore = CharismaScore), IsDirty = False)

        RawHitPoints = FormData.get("HitPoints") or FormData.get("MaxHitPoints")
        if RawHitPoints is not None:
            CalculatedMaxHP = int(RawHitPoints)

        else:
            ClassTuples = [(C.ClassName, C.Level, C.IsStartingClass) for C in ClassesList]
            CalculatedMaxHP, HitDiceBreakdown = self.FiveETools.CalculateHitPoints(ClassTuples, AbilityScoresModel.Constitution.Modifier)
            if CalculatedMaxHP <= 0:
                CalculatedMaxHP = 10

        CurrentHP: int = int(FormData.get("CurrentHitPoints", CalculatedMaxHP) or CalculatedMaxHP)
        TempHP: int = int(FormData.get("TemporaryHitPoints", 0) or 0)
        HitPointsModel = CharacterSchema.HitPointsData(MaxHitPoints = CalculatedMaxHP, CurrentHitPoints = CurrentHP, TemporaryHitPoints = TempHP, BaseHitPoints = CalculatedMaxHP, IsDirty = False)

        DeathSavesModel = CharacterSchema.DeathSavesData(SuccessCount = int(FormData.get("DeathSaves.SuccessCount", 0) or 0), FailureCount = int(FormData.get("DeathSaves.FailureCount", 0) or 0))

        RawArmorClass = int(FormData.get("ArmorClass", 10) or 10)
        ArmorClassModel = CharacterSchema.ArmorClassData(BaseArmorClass = RawArmorClass, TotalArmorClass = RawArmorClass)

        WalkingSpeedValue: int = int(FormData.get("Speed", 30) or 30)
        SpeedModel = CharacterSchema.SpeedData(WalkingSpeedFeet = WalkingSpeedValue)

        SkillProficienciesList: Typing.List[CharacterSchema.SkillProficiencyEntry] = []
        for NormalizedSkill, AssociatedAbility in self.SkillAbilityMapping.items():
            FormattedSkillName: str = " ".join(Word.capitalize() for Word in NormalizedSkill.replace("-", " ").split())
            CompactSkillName: str = FormattedSkillName.replace(" ", "")
            FormValue = (FormData.get(f"SkillProficiency{CompactSkillName}") or FormData.get(f"SkillProficiency.{CompactSkillName}") or FormData.get(f"SkillProficiency{NormalizedSkill}") or FormData.get(f"SkillProficiency.{NormalizedSkill}") or FormData.get(FormattedSkillName) or 0)
            TierValue: CharacterSchema.ProficiencyTierType = CharacterSchema.ProficiencyTierType.NoneTier
            if str(FormValue) in ["2", "Expertise"]:
                TierValue = CharacterSchema.ProficiencyTierType.Expertise

            elif str(FormValue) in ["1", "Proficient", "true", "True", "on"]:
                TierValue = CharacterSchema.ProficiencyTierType.Proficient

            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(SkillName = FormattedSkillName, AssociatedAbility = AssociatedAbility, ProficiencyTier = TierValue))

        SavingThrowProficienciesList: Typing.List[CharacterSchema.SavingThrowProficiencyEntry] = []
        for AbilityEnum in CharacterSchema.AbilityType:
            FormSaveValue = (FormData.get(f"SavingThrowProficiency{AbilityEnum.value}") or FormData.get(f"SavingThrowProficiency.{AbilityEnum.value}") or FormData.get(f"SavingThrow{AbilityEnum.value}") or False)
            IsSaveProf: bool = str(FormSaveValue).lower() in ["true", "1", "yes", "on"]
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(AbilityName = AbilityEnum, IsProficient = IsSaveProf))

        ArmorProficienciesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("ArmorProficiencies"))
        WeaponProficienciesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("WeaponProficiencies"))
        ToolProficienciesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("ToolProficiencies"))
        LanguageProficienciesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("Languages") or FormData.get("LanguageProficiencies"))
        DamageResistancesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("DamageResistances"))
        DamageImmunitiesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("DamageImmunities"))
        DamageVulnerabilitiesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("DamageVulnerabilities"))
        ConditionImmunitiesList: Typing.List[str] = self.ParseCommaSeparatedList(FormData.get("ConditionImmunities"))

        ContainersList: Typing.List[CharacterSchema.ContainerEntry] = [CharacterSchema.ContainerEntry(ID = "equipment", Name = "Equipment", IsCarried = True, WeightPounds = 0.0), CharacterSchema.ContainerEntry(ID = "carried", Name = "Carried", IsCarried = True, WeightPounds = 0.0)]
        SeenContainerIDs: Typing.Dict[str, bool] = {
            "equipment": True,
            "carried": True
        }
        for ContainerIndex in sorted(ContainerEntriesDictionary.keys()):
            ContainerData = ContainerEntriesDictionary[ContainerIndex]
            ContainerName: str = str(ContainerData.get("Name") or "Container").strip()
            ContainerID: str = str(ContainerData.get("ID") or ContainerName.lower().replace(" ", "-")).strip()
            if ContainerID not in SeenContainerIDs:
                SeenContainerIDs[ContainerID] = True
                ContainersList.append(CharacterSchema.ContainerEntry(ID = ContainerID, Name = ContainerName, IsCarried = True, WeightPounds = float(ContainerData.get("WeightPounds", 0.0) or 0.0), CostInGoldPieces = float(ContainerData.get("CostInGoldPieces", 0.0) or 0.0), CapacityPounds = float(ContainerData.get("CapacityPounds", 0.0) or 0.0) if ContainerData.get("CapacityPounds") else None, Description = self.CleanHTMLString(ContainerData.get("Description")), Color = ContainerData.get("Color")))

        InventoryList: Typing.List[CharacterSchema.InventoryItemEntry] = []
        for InventoryIndex in sorted(InventoryEntriesDictionary.keys()):
            ItemData = InventoryEntriesDictionary[InventoryIndex]
            ItemName: str = str(ItemData.get("Name") or "").strip()
            if not ItemName:
                continue

            ItemWeight: float = float(ItemData.get("WeightPounds", 0.0) or 0.0)
            ItemQuantity: int = int(ItemData.get("Quantity", 1) or 1)
            ItemType: str = str(ItemData.get("ItemType") or "Gear").strip()
            ContainerID: str = str(ItemData.get("ContainerID") or "carried").strip()
            IsEquipped: bool = str(ItemData.get("IsEquipped", "false")).lower() in ["true", "1", "yes", "on"]
            IsAttuned: bool = str(ItemData.get("IsAttuned", "false")).lower() in ["true", "1", "yes", "on"]
            ItemCost: float = float(ItemData.get("CostInGoldPieces", 0.0) or 0.0)
            InventoryList.append(CharacterSchema.InventoryItemEntry(ID = str(ItemData.get("ID") or f"item-{InventoryIndex}"), Name = ItemName, Quantity = ItemQuantity, WeightPounds = ItemWeight, CostInGoldPieces = ItemCost, IsEquipped = IsEquipped, RequiresAttunement = IsAttuned or str(ItemData.get("RequiresAttunement", "false")).lower() in ["true", "1", "yes", "on"], IsAttuned = IsAttuned, ItemType = ItemType, ContainerID = ContainerID, Description = self.CleanHTMLString(ItemData.get("Description")), Color = ItemData.get("Color"), PluralName = ItemData.get("PluralName"), IsDirty = False))

        SpellListsList: Typing.List[CharacterSchema.SpellListEntry] = []
        SpellsList: Typing.List[CharacterSchema.SpellEntry] = []
        SpellcastingEntriesList: Typing.List[CharacterSchema.SpellcastingEntry] = []

        if SpellListsDictionary:
            for ListIndex in sorted(SpellListsDictionary.keys()):
                ListData = SpellListsDictionary[ListIndex]
                ListNameStr: str = str(ListData.get("Name") or "Spell List").strip()
                ListAbilityCandidate: Typing.Optional[str] = str(ListData.get("Ability") or "").strip() or None
                ListAbilityEnum: Typing.Optional[CharacterSchema.AbilityType] = self.MapStringToAbilityType(ListAbilityCandidate) if ListAbilityCandidate else None
                ListIDStr: str = str(ListData.get("ID") or f"spell-list-{ListIndex}")

                SaveDCVal: Typing.Optional[int] = None
                AttackBonusVal: Typing.Optional[int] = None
                if ListAbilityEnum:
                    AbilityMod: int = getattr(AbilityScoresModel, ListAbilityEnum.value).Modifier
                    SaveDCVal = 8 + ComputedProficiencyBonus + AbilityMod
                    AttackBonusVal = ComputedProficiencyBonus + AbilityMod
                    SpellcastingEntriesList.append(CharacterSchema.SpellcastingEntry(SpellcastingClass = ListNameStr, SpellcastingAbility = ListAbilityEnum, SpellSaveDC = SaveDCVal, SpellAttackBonus = AttackBonusVal, IsDirty = False))

                SpellListsList.append(CharacterSchema.SpellListEntry(ID = ListIDStr, Name = ListNameStr, SpellcastingAbility = ListAbilityEnum, SpellSaveDC = SaveDCVal, SpellAttackBonus = AttackBonusVal, MaxPrepared = int(ListData.get("MaxPrepared", 0) or 0) if ListData.get("MaxPrepared") else None, Color = ListData.get("Color"), IsDirty = False))

                RawSpellsStr: str = str(ListData.get("Spells") or "").strip()
                if RawSpellsStr:
                    for RawSpellCandidate in RegularExpressions.split(r"[,\n]", RawSpellsStr):
                        CleanSpellCandidate: str = RawSpellCandidate.strip()
                        if CleanSpellCandidate:
                            IsCantrip: bool = "cantrip" in ListNameStr.lower()
                            SpellsList.append(CharacterSchema.SpellEntry(ID = CleanSpellCandidate.lower().replace(" ", "-"), Name = CleanSpellCandidate, Level = 0 if IsCantrip else 1, School = "Universal", CastingTime = "1 Action", RangeDescription = "Self", DurationDescription = "Instantaneous", IsPrepared = True, SourceType = "SpellList", SourceName = ListNameStr, IsDirty = False))

        SpellSlotsList: Typing.List[CharacterSchema.SpellSlotEntry] = []
        if SpellSlotsDictionary:
            for SlotIndex in sorted(SpellSlotsDictionary.keys()):
                SlotData = SpellSlotsDictionary[SlotIndex]
                SlotLevelNum: int = int(SlotData.get("Level", SlotIndex) or SlotIndex)
                SlotTotalNum: int = int(SlotData.get("Total", 0) or 0)
                SlotUsedNum: int = int(SlotData.get("Used", 0) or 0)
                if SlotTotalNum > 0:
                    SpellSlotsList.append(CharacterSchema.SpellSlotEntry(Level = SlotLevelNum, TotalSlots = SlotTotalNum, UsedSlots = SlotUsedNum))

        else:
            ProgressionTuples = [(C.ClassName, C.Level, C.SubclassName) for C in ClassesList]
            ComputedSlots = self.FiveETools.CalculateMulticlassSpellSlots(ProgressionTuples)
            for SlotLevelNumber, SlotCountNumber in ComputedSlots:
                SpellSlotsList.append(CharacterSchema.SpellSlotEntry(Level = SlotLevelNumber, TotalSlots = SlotCountNumber, UsedSlots = 0))

        WarlockLevelTotal: int = sum(C.Level for C in ClassesList if (self.FiveETools.FindCanonicalClassName(C.ClassName) or C.ClassName).lower() == "warlock")
        PactMagicDataModel: Typing.Optional[CharacterSchema.PactMagicSlotData] = None
        if WarlockLevelTotal > 0:
            PactSlotInfo = self.FiveETools.CalculatePactMagicSlots(WarlockLevelTotal)
            if PactSlotInfo:
                RawPactUsed = FormData.get("PactMagic.UsedSlots")
                PactUsedNum: int = min(PactSlotInfo[1], max(0, int(RawPactUsed or 0))) if RawPactUsed is not None else 0
                PactMagicDataModel = CharacterSchema.PactMagicSlotData(SlotLevel = PactSlotInfo[0], TotalSlots = PactSlotInfo[1], UsedSlots = PactUsedNum)

        SpellcastingModel = CharacterSchema.SpellcastingData(SpellcastingEntries = SpellcastingEntriesList, SpellLists = SpellListsList, SpellSlots = SpellSlotsList, PactMagic = PactMagicDataModel, Spells = SpellsList)

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        RawFeaturesStr = FormData.get("Features")
        if RawFeaturesStr:
            for RawFeatCandidate in RegularExpressions.split(r"[,\n]", str(RawFeaturesStr)):
                CleanFeatCandidate: str = RawFeatCandidate.strip()
                if CleanFeatCandidate:
                    FeaturesList.append(CharacterSchema.FeatureEntry(ID = CleanFeatCandidate.lower().replace(" ", "-"), Name = CleanFeatCandidate, SourceType = "Class", SourceName = ClassesList[0].ClassName if ClassesList else "Adventurer", IsDirty = False))

        CurrenciesModel = CharacterSchema.CurrenciesData(CopperPieces = int(FormData.get("CopperPieces", 0) or 0), SilverPieces = int(FormData.get("SilverPieces", 0) or 0), ElectrumPieces = int(FormData.get("ElectrumPieces", 0) or 0), GoldPieces = int(FormData.get("GoldPieces", 0) or 0), PlatinumPieces = int(FormData.get("PlatinumPieces", 0) or 0))

        AppearanceData = CharacterSchema.PhysicalAppearanceData(Age = str(FormData.get("Age")) if FormData.get("Age") else None, Height = str(FormData.get("Height")) if FormData.get("Height") else None, Weight = str(FormData.get("Weight")) if FormData.get("Weight") else None, Hair = FormData.get("Hair"), Eyes = FormData.get("Eyes"), Skin = FormData.get("Skin"), AppearanceDescription = self.CleanHTMLString(FormData.get("AppearanceDescription") or FormData.get("Appearance")), PortraitFileID = FormData.get("PortraitFileID"), PortraitURL = FormData.get("PortraitURL"))

        PersonalityModel = CharacterSchema.PersonalityData(PersonalityTraits = self.CleanHTMLString(FormData.get("PersonalityTraits")), Ideals = self.CleanHTMLString(FormData.get("Ideals")), Bonds = self.CleanHTMLString(FormData.get("Bonds")), Flaws = self.CleanHTMLString(FormData.get("Flaws")))

        NotesModel = CharacterSchema.NotesData(Backstory = self.CleanHTMLString(FormData.get("Backstory")))

        AttunementTotal = int(FormData.get("AttunementTotalSlots", 3) or 3)
        CarryMultiplier = float(FormData.get("CarryingCapacityMultiplier", 1.0) or 1.0)

        UnifiedSheet = CharacterSchema.DND5thEditionCharacterSheet(SchemaVersion = "1.0.0", GameSystem = "DND5thEdition", OriginalSource = "MIS", Name = CharacterName, PlayerName = PlayerName, Gender = Gender, Alignment = Alignment, Faith = Faith, Lifestyle = Lifestyle, TotalLevel = TotalCharacterLevel, ExperiencePoints = sum(int(ClassData.get("Experience", 0) or 0) for ClassData in ClassEntriesDictionary.values()) if ClassEntriesDictionary else int(FormData.get("ExperiencePoints", 0) or 0), Inspiration = Inspiration, ProficiencyBonus = ComputedProficiencyBonus, IsDirty = False, Species = SpeciesModel, Background = BackgroundModel, Classes = ClassesList, AbilityScores = AbilityScoresModel, HitPoints = HitPointsModel, DeathSaves = DeathSavesModel, ArmorClass = ArmorClassModel, Speed = SpeedModel, SavingThrowProficiencies = SavingThrowProficienciesList, SkillProficiencies = SkillProficienciesList, ArmorProficiencies = ArmorProficienciesList, WeaponProficiencies = WeaponProficienciesList, ToolProficiencies = ToolProficienciesList, LanguageProficiencies = LanguageProficienciesList, DamageResistances = DamageResistancesList, DamageImmunities = DamageImmunitiesList, DamageVulnerabilities = DamageVulnerabilitiesList, ConditionImmunities = ConditionImmunitiesList, Containers = ContainersList, Inventory = InventoryList, AttunementTotalSlots = AttunementTotal, AttunementUsedSlots = sum(1 for Inv in InventoryList if Inv.IsAttuned), CarryingCapacityMultiplier = CarryMultiplier, Currencies = CurrenciesModel, Spellcasting = SpellcastingModel, Features = FeaturesList, Personality = PersonalityModel, PhysicalAppearance = AppearanceData, Notes = NotesModel)
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Mapped Manual Form Character: \"{UnifiedSheet.Name}\" (Level {UnifiedSheet.TotalLevel})")
        return UnifiedSheet

    def IngestUniversalCharacterData(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        if "data" in RawJSON and isinstance(RawJSON["data"], dict) and "classes" in RawJSON["data"]:
            return self.MapDNDBeyondCharacter(RawJSON)

        if "characters" in RawJSON and isinstance(RawJSON["characters"], list):
            return self.MapDicecloudCharacter(RawJSON)

        if "ClassOrCareer" in RawJSON or ("Name" in RawJSON and ("Strength" in RawJSON or "AbilityScores.Strength" in RawJSON)):
            return self.MapManualFormData(RawJSON)

        if "AbilityScores" in RawJSON and "Classes" in RawJSON:
            DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Ingested Universal Sheet: Name=\"{RawJSON.get("Name", "Unknown")}\", System=\"{RawJSON.get("GameSystem", "DND5thEdition")}\"")
            return CharacterSchema.DND5thEditionCharacterSheet.model_validate(RawJSON)

        DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Universal Ingestion Failed: Keys={list(RawJSON.keys())[:5]}")
        raise ValueError("Unsupported or invalid character data structure provided for universal ingestion.")

    def ExportToDatabasePayload(self, Sheet: CharacterSchema.DND5thEditionCharacterSheet, RawImportData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None) -> Typing.Dict[str, Typing.Any]:
        PrimaryClass: str = Sheet.Classes[0].ClassName if Sheet.Classes else ""
        PortraitURL: Typing.Optional[str] = getattr(getattr(Sheet, "PhysicalAppearance", None), "PortraitURL", None)
        SummaryDictionary: Typing.Dict[str, Typing.Any] = {
            "System"     : "DND5thEdition",
            "Class"      : PrimaryClass,
            "Level"      : Sheet.TotalLevel,
            "Species"    : Sheet.Species.FullName,
            "Background" : Sheet.Background.Name,
            "HitPoints"  : Sheet.HitPoints.MaxHitPoints,
            "ArmorClass" : Sheet.ArmorClass.TotalArmorClass,
            "PortraitURL": PortraitURL
        }
        DetailDictionary: Typing.Dict[str, Typing.Any] = Sheet.model_dump()
        IsDicecloud: bool = bool(Sheet.OriginalSource == "Dicecloud")
        IsProtected: bool = True if IsDicecloud else False
        ImportSource: Typing.Optional[str] = "DicecloudV1" if IsDicecloud else (Sheet.OriginalSource or None)
        Payload: Typing.Dict[str, Typing.Any] = {
            "Name"         : Sheet.Name,
            "GameSystem"   : "DND5thEdition",
            "IsProtected"  : IsProtected,
            "IsOverridden" : False,
            "ImportSource" : ImportSource,
            "SummaryData"  : SummaryDictionary,
            "DetailData"   : DetailDictionary,
            "RawImportData": RawImportData
        }
        DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Exported Payload: \"{Sheet.Name}\" ({Sheet.GameSystem}, Level {Sheet.TotalLevel}, HP={Sheet.HitPoints.MaxHitPoints})")

        return Payload

    def BuildCharacterSheetContext(self, TargetCharacter: Typing.Optional[CharacterModel.Character] = None, DetailDataOverride: Typing.Optional[Typing.Dict[str, Typing.Any]] = None, IsAllowed: bool = True, IsProtected: Typing.Optional[bool] = None, IsOverridden: Typing.Optional[bool] = None, ActiveTab: str = "CharacterSheetOverviewTab") -> Typing.Dict[str, Typing.Any]:
        DetailData: Typing.Dict[str, Typing.Any] = DetailDataOverride if (DetailDataOverride is not None) else ((TargetCharacter.DetailData or ({})) if (TargetCharacter is not None) else ({}))
        SummaryData: Typing.Dict[str, Typing.Any] = (TargetCharacter.SummaryData or ({})) if (TargetCharacter is not None) else ({})
        CharacterID: str = TargetCharacter.ID if (TargetCharacter is not None) else ""
        CharacterName: str = TargetCharacter.Name if (TargetCharacter is not None) else str(DetailData.get("Name") or "")
        GameSystem: str = TargetCharacter.GameSystem.value if (TargetCharacter is not None) else str(DetailData.get("GameSystem") or "DND5thEdition")
        EffectiveProtected: bool = IsProtected if (IsProtected is not None) else (TargetCharacter.IsProtected if (TargetCharacter is not None) else False)
        EffectiveOverridden: bool = IsOverridden if (IsOverridden is not None) else (TargetCharacter.IsOverridden if (TargetCharacter is not None) else False)

        PhysicalAppearanceDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("PhysicalAppearance") or ({})
        PortraitFileID: Typing.Optional[str] = SummaryData.get("PortraitFileID") or DetailData.get("PortraitFileID") or PhysicalAppearanceDictionary.get("PortraitFileID")
        PortraitURL: Typing.Optional[str] = SummaryData.get("PortraitURL") or DetailData.get("PortraitURL") or PhysicalAppearanceDictionary.get("PortraitURL")

        ProficiencyBonus: int = int(DetailData.get("ProficiencyBonus") or 2)
        SpeciesDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("Species") or ({})
        SpeciesName: str = str(SpeciesDictionary.get("FullName") or SpeciesDictionary.get("RaceName") or "")
        InitiativeBonus: int = int(DetailData.get("InitiativeBonus") or 0)
        BackgroundDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("Background") or ({})
        BackgroundName: str = str(BackgroundDictionary.get("Name") or "")
        ExperiencePoints: int = int(DetailData.get("ExperiencePoints") or 0)
        Alignment: str = str(DetailData.get("Alignment") or "")
        PassivePerception: int = int(DetailData.get("PassivePerception") or 10)
        PassiveInvestigation: int = int(DetailData.get("PassiveInvestigation") or 10)

        HPDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("HitPoints") or ({})
        HitPoints: int = int(HPDictionary.get("MaxHitPoints") or DetailData.get("HitPoints") or 10)
        ACDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("ArmorClass") or ({})
        ArmorClass: int = int(ACDictionary.get("TotalArmorClass") or ACDictionary.get("BaseArmorClass") or DetailData.get("ArmorClass") or 10)
        SpeedDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("Speed") or ({})
        Speed: int = int(SpeedDictionary.get("WalkingSpeedFeet") or DetailData.get("Speed") or 30)

        AbilitiesDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("AbilityScores") or ({})
        AbilityScores: Typing.Dict[str, int] = {
        }
        AbilityModifiers: Typing.Dict[str, int] = {
        }
        for AbilityName in ["Strength", "Dexterity", "Constitution", "Intelligence", "Wisdom", "Charisma"]:
            ScoreEntry = AbilitiesDictionary.get(AbilityName) or AbilitiesDictionary.get(AbilityName.lower()) or 10
            ScoreValue: int = int(ScoreEntry.get("BaseScore") or ScoreEntry.get("TotalScore") or 10) if isinstance(ScoreEntry, dict) else int(ScoreEntry)
            AbilityScores[AbilityName] = ScoreValue
            AbilityModifiers[AbilityName] = (ScoreValue - 10) // 2

        SkillProficiencyStates: Typing.Dict[str, int] = {
            "Athletics"     : 0,
            "Acrobatics"    : 0,
            "SleightOfHand" : 0,
            "Stealth"       : 0,
            "Arcana"        : 0,
            "History"       : 0,
            "Investigation" : 0,
            "Nature"        : 0,
            "Religion"      : 0,
            "AnimalHandling": 0,
            "Insight"       : 0,
            "Medicine"      : 0,
            "Perception"    : 0,
            "Survival"      : 0,
            "Deception"     : 0,
            "Intimidation"  : 0,
            "Performance"   : 0,
            "Persuasion"    : 0
        }
        RawSkillProficiencies: Typing.List[Typing.Dict[str, Typing.Any]] = DetailData.get("SkillProficiencies") or []
        for SkillItem in RawSkillProficiencies:
            RawSkillName: str = str(SkillItem.get("SkillName") or "")
            NormalizedSkillName: str = RawSkillName.replace(" ", "").replace("-", "")
            RawTier = SkillItem.get("ProficiencyTier")
            TierState: int = 2 if (str(RawTier) in ["2", "Expertise"]) else (1 if (str(RawTier) in ["1", "Proficient", "HalfProficient", "True", "true"]) else 0)
            SkillProficiencyStates[NormalizedSkillName] = TierState
            SkillProficiencyStates[RawSkillName] = TierState

        WeaponProficienciesString: str = ", ".join(DetailData.get("WeaponProficiencies") or [])
        DamageResistancesString: str = ", ".join(DetailData.get("DamageResistances") or [])
        ArmorProficienciesString: str = ", ".join(DetailData.get("ArmorProficiencies") or [])
        DamageImmunitiesString: str = ", ".join(DetailData.get("DamageImmunities") or [])
        ToolProficienciesString: str = ", ".join(DetailData.get("ToolProficiencies") or [])
        DamageVulnerabilitiesString: str = ", ".join(DetailData.get("DamageVulnerabilities") or [])
        LanguagesString: str = ", ".join(DetailData.get("LanguageProficiencies") or DetailData.get("Languages") or [])
        ConditionImmunitiesString: str = ", ".join(DetailData.get("ConditionImmunities") or [])

        RawClasses: Typing.List[Typing.Dict[str, Typing.Any]] = DetailData.get("Classes") or []
        ClassesList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        if RawClasses:
            for ClassIndex, ClassItem in enumerate(RawClasses):
                ClassDict: Typing.Dict[str, Typing.Any] = {
                    "Index"          : ClassIndex,
                    "ClassName"      : str(ClassItem.get("ClassName") or ""),
                    "Subclass"       : str(ClassItem.get("SubclassName") or ""),
                    "Level"          : int(ClassItem.get("Level") or 1),
                    "Experience"     : int(ClassItem.get("ExperiencePoints") or 0),
                    "IsInitialClass" : bool(ClassItem.get("IsStartingClass") or (ClassIndex == 0))
                }
                ClassesList.append(ClassDict)

        else:
            DefaultClassDict: Typing.Dict[str, Typing.Any] = {
                "Index"          : 0,
                "ClassName"      : "",
                "Subclass"       : "",
                "Level"          : 1,
                "Experience"     : 0,
                "IsInitialClass" : True
            }
            ClassesList.append(DefaultClassDict)

        RawFeatures: Typing.List[Typing.Dict[str, Typing.Any]] = DetailData.get("Features") or []
        FeaturesString: str = ", ".join([str(FeatureItem.get("Name") or "").strip() for FeatureItem in RawFeatures if FeatureItem.get("Name")])

        SpellcastingDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("Spellcasting") or ({})
        RawSpellSlots: Typing.List[Typing.Dict[str, Typing.Any]] = SpellcastingDictionary.get("SpellSlots") or []
        SpellSlotDataMap: Typing.Dict[int, Typing.Dict[str, Typing.Any]] = ({SlotLevel: {"Level": SlotLevel, "Total": 0, "Used": 0, "IsVisible": False} for SlotLevel in range(1, 10)})
        for SlotEntry in RawSpellSlots:
            SlotLevelNumber: int = int(SlotEntry.get("Level") or 0)
            if (1 <= SlotLevelNumber <= 9):
                SlotTotalNumber: int = int(SlotEntry.get("TotalSlots") or 0)
                SlotUsedNumber: int = int(SlotEntry.get("UsedSlots") or 0)
                SpellSlotDataMap[SlotLevelNumber] = {
                    "Level"    : SlotLevelNumber,
                    "Total"    : SlotTotalNumber,
                    "Used"     : SlotUsedNumber,
                    "IsVisible": (SlotTotalNumber > 0)
                }

        RawPactMagicDictionary: Typing.Dict[str, Typing.Any] = SpellcastingDictionary.get("PactMagic") or ({})
        PactMagicTotalSlots: int = int(RawPactMagicDictionary.get("TotalSlots") or 0)
        PactMagicSlotLevel: int = int(RawPactMagicDictionary.get("SlotLevel") or 0)
        PactMagicUsedSlots: int = int(RawPactMagicDictionary.get("UsedSlots") or 0)
        HasPactMagic: bool = (PactMagicTotalSlots > 0)
        PactMagicData: Typing.Dict[str, Typing.Any] = {
            "SlotLevel" : PactMagicSlotLevel,
            "TotalSlots": PactMagicTotalSlots,
            "UsedSlots" : PactMagicUsedSlots
        }
        HasRegularSpellSlots: bool = any((SlotInfo["Total"] > 0) for SlotInfo in SpellSlotDataMap.values())
        HasAnySpellSlots: bool = (HasRegularSpellSlots or HasPactMagic)

        RawSpellLists: Typing.List[Typing.Dict[str, Typing.Any]] = SpellcastingDictionary.get("SpellLists") or []
        RawSpells: Typing.List[Typing.Dict[str, Typing.Any]] = SpellcastingDictionary.get("Spells") or []
        SpellsByListName: Typing.Dict[str, Typing.List[str]] = {
        }
        for SpellEntry in RawSpells:
            SpellNameString: str = str(SpellEntry.get("Name") or "").strip()
            if not SpellNameString:
                continue

            SpellLevelInt: int = int(SpellEntry.get("Level") or 0)
            SourceNameString: str = str(SpellEntry.get("SourceName") or ("Cantrips" if (SpellLevelInt == 0) else "Spellbook")).strip()
            if (SourceNameString not in SpellsByListName):
                SpellsByListName[SourceNameString] = []

            SpellsByListName[SourceNameString].append(SpellNameString)

        SpellListsRenderData: Typing.List[Typing.Dict[str, Typing.Any]] = []
        if RawSpellLists:
            for ListIndex, ListObject in enumerate(RawSpellLists):
                ListNameString: str = str(ListObject.get("Name") or "Spell List").strip()
                AbilityEnumOrStr = ListObject.get("SpellcastingAbility")
                ListAbilityString: str = AbilityEnumOrStr.get("value") if isinstance(AbilityEnumOrStr, dict) else str(AbilityEnumOrStr or "None")
                SpellsInList: Typing.List[str] = SpellsByListName.get(ListNameString) or []
                CanDeleteList: bool = (ListNameString.lower() not in ["cantrips", "prepared spells"])
                AbilityModifierValue: int = AbilityModifiers.get(ListAbilityString, 0) if (ListAbilityString != "None") else 0
                SaveDCValue: int = 8 + ProficiencyBonus + AbilityModifierValue
                AttackBonusValue: int = ProficiencyBonus + AbilityModifierValue
                SpellListDict: Typing.Dict[str, Typing.Any] = {
                    "Index"        : ListIndex,
                    "Name"         : ListNameString,
                    "Ability"      : ListAbilityString,
                    "CanDelete"    : CanDeleteList,
                    "IsCustomList" : (ListNameString.lower() not in ["cantrips", "prepared spells", "spellbook"]),
                    "Spells"       : SpellsInList,
                    "SpellsJoined" : ", ".join(SpellsInList),
                    "ModifierText" : (f"+{AbilityModifierValue}" if (AbilityModifierValue >= 0) else str(AbilityModifierValue)) if (ListAbilityString != "None") else "—",
                    "AttackText"   : (f"+{AttackBonusValue}" if (AttackBonusValue >= 0) else str(AttackBonusValue)) if (ListAbilityString != "None") else "—",
                    "SaveDCText"   : str(SaveDCValue) if (ListAbilityString != "None") else "—"
                }
                SpellListsRenderData.append(SpellListDict)

        else:
            DefaultListNames: Typing.List[Typing.Tuple[str, bool]] = [("Cantrips", False), ("Prepared Spells", False), ("Spellbook", True)]
            for ListIndex, (ListNameString, CanDeleteList) in enumerate(DefaultListNames):
                SpellsInList = SpellsByListName.get(ListNameString) or []
                SpellListDict: Typing.Dict[str, Typing.Any] = {
                    "Index"        : ListIndex,
                    "Name"         : ListNameString,
                    "Ability"      : "None",
                    "CanDelete"    : CanDeleteList,
                    "IsCustomList" : False,
                    "Spells"       : SpellsInList,
                    "SpellsJoined" : ", ".join(SpellsInList),
                    "ModifierText" : "—",
                    "AttackText"   : "—",
                    "SaveDCText"   : "—"
                }
                SpellListsRenderData.append(SpellListDict)

        RawContainers: Typing.List[Typing.Dict[str, Typing.Any]] = DetailData.get("Containers") or []
        RawInventory: Typing.List[Typing.Dict[str, Typing.Any]] = DetailData.get("Inventory") or []
        ItemsByContainer: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = {
        }
        GlobalItemIndexCounter: int = 0
        for InventoryItemObject in RawInventory:
            ContainerKey: str = str(InventoryItemObject.get("ContainerID") or "carried").lower().strip()
            if (ContainerKey not in ItemsByContainer):
                ItemsByContainer[ContainerKey] = []

            InventoryItemDict: Typing.Dict[str, Typing.Any] = {
                "GlobalIndex" : GlobalItemIndexCounter,
                "Name"        : str(InventoryItemObject.get("Name") or "Item"),
                "WeightPounds": float(InventoryItemObject.get("WeightPounds") or 0.0),
                "Quantity"    : int(InventoryItemObject.get("Quantity") or 1),
                "ContainerID" : ContainerKey,
                "IsEquipped"  : bool(InventoryItemObject.get("IsEquipped") or (ContainerKey == "equipment"))
            }
            ItemsByContainer[ContainerKey].append(InventoryItemDict)
            GlobalItemIndexCounter += 1

        ContainersRenderData: Typing.List[Typing.Dict[str, Typing.Any]] = []
        OrderedContainersList: Typing.List[Typing.Dict[str, Typing.Any]] = []
        EquipmentContainer: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
        CarriedContainer: Typing.Optional[Typing.Dict[str, Typing.Any]] = None
        OtherContainers: Typing.List[Typing.Dict[str, Typing.Any]] = []

        if RawContainers:
            for Container in RawContainers:
                ContainerIDCandidate: str = str(Container.get("ID") or Container.get("Name") or "").lower().strip()
                if (ContainerIDCandidate == "equipment"):
                    EquipmentContainer = Container

                elif (ContainerIDCandidate == "carried"):
                    CarriedContainer = Container

                else:
                    OtherContainers.append(Container)

        if (EquipmentContainer is None):
            EquipmentContainer = {
                "Name": "Equipment",
                "ID"  : "equipment"
            }

        if (CarriedContainer is None):
            CarriedContainer = {
                "Name": "Carried",
                "ID"  : "carried"
            }

        OrderedContainersList = [EquipmentContainer, CarriedContainer] + OtherContainers

        for ContainerIndex, ContainerObject in enumerate(OrderedContainersList):
            ContainerNameString: str = str(ContainerObject.get("Name") or "Container").strip()
            ContainerIDString: str = str(ContainerObject.get("ID") or ContainerNameString.lower().replace(" ", "-")).lower().strip()
            CanDeleteContainer: bool = (ContainerIDString not in ["equipment", "carried"])
            ItemsInContainer: Typing.List[Typing.Dict[str, Typing.Any]] = ItemsByContainer.get(ContainerIDString) or []
            ContainerWeightTotal: float = sum((ItemEntry["WeightPounds"] * ItemEntry["Quantity"]) for ItemEntry in ItemsInContainer)
            ContainerDict: Typing.Dict[str, Typing.Any] = {
                "Index"            : ContainerIndex,
                "Name"             : ContainerNameString,
                "ID"               : ContainerIDString,
                "CanDelete"        : CanDeleteContainer,
                "IsCustomContainer": CanDeleteContainer,
                "TotalWeight"      : round(ContainerWeightTotal, 2),
                "ItemCount"        : len(ItemsInContainer),
                "Items"            : ItemsInContainer
            }
            ContainersRenderData.append(ContainerDict)

        AttunementTotalSlots: int = int(DetailData.get("AttunementTotalSlots") or 3)
        AttunementUsedSlots: int = int(DetailData.get("AttunementUsedSlots") or sum(1 for InventoryItem in RawInventory if InventoryItem.get("IsAttuned")))
        CarryingCapacityPounds: float = float(DetailData.get("CarryingCapacityPounds") or (AbilityScores["Strength"] * 15.0))
        TotalCarriedWeightPounds: float = float(DetailData.get("TotalCarriedWeightPounds") or sum(ContainerEntry["TotalWeight"] for ContainerEntry in ContainersRenderData))
        CarryingCapacityPercentage: float = min(100.0, round((TotalCarriedWeightPounds / max(1.0, CarryingCapacityPounds)) * 100.0, 1))

        PersonalityDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("Personality") or ({})
        PersonalityTraits: str = str(PersonalityDictionary.get("PersonalityTraits") or "")
        Ideals: str = str(PersonalityDictionary.get("Ideals") or "")
        Bonds: str = str(PersonalityDictionary.get("Bonds") or "")
        Flaws: str = str(PersonalityDictionary.get("Flaws") or "")

        NotesDictionary: Typing.Dict[str, Typing.Any] = DetailData.get("Notes") or ({})
        Backstory: str = str(NotesDictionary.get("Backstory") or "")

        Age: str = str(PhysicalAppearanceDictionary.get("Age") or "")
        Height: str = str(PhysicalAppearanceDictionary.get("Height") or "")
        Weight: str = str(PhysicalAppearanceDictionary.get("Weight") or "")
        Faith: str = str(DetailData.get("Faith") or "")
        Lifestyle: str = str(DetailData.get("Lifestyle") or "")

        TemplateContext: Typing.Dict[str, Typing.Any] = {
            "IsAllowed"                 : IsAllowed,
            "Character"                 : TargetCharacter,
            "CharacterID"               : CharacterID,
            "CharacterName"             : CharacterName,
            "GameSystem"                : GameSystem,
            "IsProtected"               : EffectiveProtected,
            "IsOverridden"              : EffectiveOverridden,
            "ActiveTab"                 : ActiveTab,
            "PortraitFileID"            : PortraitFileID,
            "PortraitURL"               : PortraitURL,
            "ProficiencyBonus"           : ProficiencyBonus,
            "SpeciesName"                : SpeciesName,
            "InitiativeBonus"            : InitiativeBonus,
            "BackgroundName"             : BackgroundName,
            "ExperiencePoints"           : ExperiencePoints,
            "Alignment"                  : Alignment,
            "PassivePerception"          : PassivePerception,
            "PassiveInvestigation"       : PassiveInvestigation,
            "HitPoints"                  : HitPoints,
            "ArmorClass"                 : ArmorClass,
            "Speed"                      : Speed,
            "AbilityScores"              : AbilityScores,
            "AbilityModifiers"           : AbilityModifiers,
            "SkillProficiencyStates"     : SkillProficiencyStates,
            "WeaponProficienciesString"  : WeaponProficienciesString,
            "DamageResistancesString"    : DamageResistancesString,
            "ArmorProficienciesString"   : ArmorProficienciesString,
            "DamageImmunitiesString"     : DamageImmunitiesString,
            "ToolProficienciesString"    : ToolProficienciesString,
            "DamageVulnerabilitiesString": DamageVulnerabilitiesString,
            "LanguagesString"            : LanguagesString,
            "ConditionImmunitiesString"  : ConditionImmunitiesString,
            "ClassesList"                : ClassesList,
            "FeaturesString"             : FeaturesString,
            "SpellSlotDataMap"           : SpellSlotDataMap,
            "HasRegularSpellSlots"       : HasRegularSpellSlots,
            "HasPactMagic"               : HasPactMagic,
            "HasAnySpellSlots"           : HasAnySpellSlots,
            "PactMagicData"              : PactMagicData,
            "SpellListsRenderData"       : SpellListsRenderData,
            "ContainersRenderData"       : ContainersRenderData,
            "AttunementTotalSlots"       : AttunementTotalSlots,
            "AttunementUsedSlots"        : AttunementUsedSlots,
            "CarryingCapacityPounds"     : CarryingCapacityPounds,
            "TotalCarriedWeightPounds"   : TotalCarriedWeightPounds,
            "CarryingCapacityPercentage" : CarryingCapacityPercentage,
            "PersonalityTraits"          : PersonalityTraits,
            "Ideals"                     : Ideals,
            "Bonds"                      : Bonds,
            "Flaws"                      : Flaws,
            "Backstory"                  : Backstory,
            "Age"                        : Age,
            "Height"                     : Height,
            "Weight"                     : Weight,
            "Faith"                      : Faith,
            "Lifestyle"                  : Lifestyle
        }
        return TemplateContext

GLOBAL_CHARACTER_MAPPER: CharacterMappingService = CharacterMappingService()
