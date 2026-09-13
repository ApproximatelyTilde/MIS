import html as HyperTextMarkupLanguage
import re as RegularExpressions
import typing as Typing
import Server.Models.DND5thEditionCharacterSchema as CharacterSchema

class CharacterMappingService:
    SKILL_ABILITY_MAP: Typing.Dict[str, CharacterSchema.AbilityType] = {
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

    CLASS_HIT_DIE_MAP: Typing.Dict[str, int] = {
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

    ALIGNMENT_MAP: Typing.Dict[int, str] = {
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

    def MapDNDBeyondCharacter(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        Data: Typing.Dict[str, Typing.Any] = RawJSON.get("data", RawJSON)
        CharacterName: str = (Data.get("name") or "Unnamed Hero").strip()
        PlayerName: Typing.Optional[str] = Data.get("username")
        Gender: Typing.Optional[str] = Data.get("gender")
        Faith: Typing.Optional[str] = Data.get("faith")
        AlignmentID: Typing.Optional[int] = Data.get("alignmentId")
        AlignmentString: Typing.Optional[str] = self.ALIGNMENT_MAP.get(AlignmentID) if AlignmentID else None

        Decorations: Typing.Dict[str, Typing.Any] = Data.get("decorations", {}) or {}
        AvatarURL: Typing.Optional[str] = Decorations.get("avatarUrl")
        BackdropURL: Typing.Optional[str] = Decorations.get("backdropAvatarUrl")

        AppearanceData = CharacterSchema.PhysicalAppearanceData(
            Age = str(Data.get("age")) if (Data.get("age") is not None) else None,
            Height = Data.get("height"),
            Weight = str(Data.get("weight")) if (Data.get("weight") is not None) else None,
            Hair = Data.get("hair"),
            Eyes = Data.get("eyes"),
            Skin = Data.get("skin"),
            AppearanceDescription = self.CleanHTMLString(Data.get("traits", {}).get("appearance")),
            AvatarURL = AvatarURL,
            BackdropAvatarURL = BackdropURL
        )

        RaceDataDict: Typing.Dict[str, Typing.Any] = Data.get("race", {}) or {}
        SpeciesModel = CharacterSchema.SpeciesData(
            RaceName = RaceDataDict.get("baseRaceName") or RaceDataDict.get("fullName", "Human"),
            SubraceName = RaceDataDict.get("fullName") if RaceDataDict.get("isSubRace") else None,
            FullName = RaceDataDict.get("fullName", "Human"),
            Description = self.CleanHTMLString(RaceDataDict.get("description"))
        )

        BackgroundDict: Typing.Dict[str, Typing.Any] = Data.get("background", {}) or {}
        BackgroundDefinition: Typing.Dict[str, Typing.Any] = BackgroundDict.get("definition", {}) or {}
        BackgroundModel = CharacterSchema.BackgroundData(
            Name = BackgroundDefinition.get("name", "Adventurer"),
            Description = self.CleanHTMLString(BackgroundDefinition.get("description")),
            FeatureName = BackgroundDefinition.get("featureName"),
            FeatureDescription = self.CleanHTMLString(BackgroundDefinition.get("featureDescription"))
        )

        ClassesList: Typing.List[CharacterSchema.ClassProgressEntry] = []
        TotalCharacterLevel: int = 0
        for ClassItem in Data.get("classes", []):
            ClassDefinition: Typing.Dict[str, Typing.Any] = ClassItem.get("definition", {}) or {}
            SubclassDefinition: Typing.Dict[str, Typing.Any] = ClassItem.get("subclassDefinition", {}) or {}
            ClassName: str = ClassDefinition.get("name", "Adventurer")
            ClassLevel: int = ClassItem.get("level", 1)
            TotalCharacterLevel += ClassLevel
            HitDieValue: int = ClassDefinition.get("hitDice", self.CLASS_HIT_DIE_MAP.get(ClassName.lower(), 8))
            SpentDice: int = ClassItem.get("hitDiceUsed", 0)
            IsStarting: bool = ClassItem.get("isStartingClass", False)
            ClassesList.append(CharacterSchema.ClassProgressEntry(
                ClassName = ClassName,
                Level = ClassLevel,
                SubclassName = SubclassDefinition.get("name"),
                HitDie = HitDieValue,
                HitDiceTotal = ClassLevel,
                HitDiceUsed = SpentDice,
                IsStartingClass = IsStarting
            ))

        if not ClassesList:
            TotalCharacterLevel = 1
            ClassesList.append(CharacterSchema.ClassProgressEntry())

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

        BaseHP: int = Data.get("baseHitPoints", 10) or 10
        BonusHP: int = Data.get("bonusHitPoints", 0) or 0
        OverrideHP: Typing.Optional[int] = Data.get("overrideHitPoints")
        RemovedHP: int = Data.get("removedHitPoints", 0) or 0
        TempHP: int = Data.get("temporaryHitPoints", 0) or 0
        EffectiveMaxHP: int = OverrideHP if (OverrideHP is not None) else (BaseHP + BonusHP)
        CurrentHP: int = max(0, EffectiveMaxHP - RemovedHP)

        HitPointsModel = CharacterSchema.HitPointsData(
            MaxHitPoints = EffectiveMaxHP,
            CurrentHitPoints = CurrentHP,
            TemporaryHitPoints = TempHP,
            BaseHitPoints = BaseHP,
            BonusHitPoints = BonusHP,
            OverrideHitPoints = OverrideHP,
            RemovedHitPoints = RemovedHP
        )

        DeathSavesDict: Typing.Dict[str, Typing.Any] = Data.get("deathSaves", {}) or {}
        DeathSavesModel = CharacterSchema.DeathSavesData(
            SuccessCount = DeathSavesDict.get("successCount", 0) or 0,
            FailureCount = DeathSavesDict.get("failCount", 0) or 0,
            IsStabilized = DeathSavesDict.get("isStabilized", False) or False
        )

        AllModifiers: Typing.Dict[str, Typing.List[Typing.Dict[str, Typing.Any]]] = Data.get("modifiers", {}) or {}
        SkillProficienciesList: Typing.List[CharacterSchema.SkillProficiencyEntry] = []
        SavingThrowProficienciesList: Typing.List[CharacterSchema.SavingThrowProficiencyEntry] = []
        ArmorProficienciesList: Typing.List[str] = []
        WeaponProficienciesList: Typing.List[str] = []
        ToolProficienciesList: Typing.List[str] = []
        LanguageProficienciesList: Typing.List[str] = []
        DamageResistancesList: Typing.List[str] = []
        DamageImmunitiesList: Typing.List[str] = []
        DamageVulnerabilitiesList: Typing.List[str] = []
        ConditionImmunitiesList: Typing.List[str] = []
        SensesList: Typing.List[CharacterSchema.SenseEntry] = []

        SeenSkills: Typing.Dict[str, str] = {}
        SeenSaves: Typing.Dict[str, bool] = {}

        for GroupModifiers in AllModifiers.values():
            if not GroupModifiers:
                continue

            for ModifierItem in GroupModifiers:
                if not ModifierItem:
                    continue

                ModType: str = (ModifierItem.get("type") or "").lower()
                SubType: str = (ModifierItem.get("subType") or "").lower()
                FriendlyName: str = ModifierItem.get("friendlySubtypeName") or ModifierItem.get("subType") or ""

                if ModType == "proficiency":
                    if SubType in self.SKILL_ABILITY_MAP:
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

                elif ModType == "expertise":
                    if SubType in self.SKILL_ABILITY_MAP:
                        SeenSkills[SubType] = "Expertise"

                elif ModType == "language":
                    if FriendlyName and FriendlyName not in LanguageProficienciesList:
                        LanguageProficienciesList.append(FriendlyName)

                elif ModType == "resistance":
                    if FriendlyName and FriendlyName not in DamageResistancesList:
                        DamageResistancesList.append(FriendlyName)

                elif ModType == "immunity":
                    if FriendlyName and FriendlyName not in DamageImmunitiesList:
                        DamageImmunitiesList.append(FriendlyName)

                elif ModType == "vulnerability":
                    if FriendlyName and FriendlyName not in DamageVulnerabilitiesList:
                        DamageVulnerabilitiesList.append(FriendlyName)

                elif ModType == "sense":
                    SenseRange: int = ModifierItem.get("value", 60) or 60
                    SensesList.append(CharacterSchema.SenseEntry(SenseType = FriendlyName or "Darkvision", RangeFeet = SenseRange))

        for NormalizedSkill, AssociatedAbility in self.SKILL_ABILITY_MAP.items():
            FormattedSkillName: str = " ".join(Word.capitalize() for Word in NormalizedSkill.replace("-", " ").split())
            ProficiencyStatus: str = SeenSkills.get(NormalizedSkill, "None")
            AbilityModifier: int = getattr(AbilityScoresModel, AssociatedAbility.value).Modifier
            ProficiencyBonusToAdd: int = (ComputedProficiencyBonus * 2) if (ProficiencyStatus == "Expertise") else (ComputedProficiencyBonus if (ProficiencyStatus == "Proficient") else 0)
            TotalSkillBonus: int = AbilityModifier + ProficiencyBonusToAdd
            PassiveScore: int = 10 + TotalSkillBonus
            ProficiencyTierValue: CharacterSchema.ProficiencyTierType = CharacterSchema.ProficiencyTierType.Expertise if (ProficiencyStatus == "Expertise") else (CharacterSchema.ProficiencyTierType.Proficient if (ProficiencyStatus == "Proficient") else CharacterSchema.ProficiencyTierType.NoneTier)
            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(
                SkillName = FormattedSkillName,
                AssociatedAbility = AssociatedAbility,
                ProficiencyTier = ProficiencyTierValue,
                BonusModifier = TotalSkillBonus,
                PassiveScore = PassiveScore
            ))

        for AbilityEnum in CharacterSchema.AbilityType:
            IsSaveProficient: bool = SeenSaves.get(AbilityEnum.value.lower(), False)
            AbilityMod: int = getattr(AbilityScoresModel, AbilityEnum.value).Modifier
            SaveBonus: int = AbilityMod + (ComputedProficiencyBonus if IsSaveProficient else 0)
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(
                AbilityName = AbilityEnum,
                IsProficient = IsSaveProficient,
                BonusModifier = SaveBonus
            ))

        CurrenciesDict: Typing.Dict[str, int] = Data.get("currencies", {}) or {}
        CurrenciesModel = CharacterSchema.CurrenciesData(
            CopperPieces = CurrenciesDict.get("cp", 0) or 0,
            SilverPieces = CurrenciesDict.get("sp", 0) or 0,
            ElectrumPieces = CurrenciesDict.get("ep", 0) or 0,
            GoldPieces = CurrenciesDict.get("gp", 0) or 0,
            PlatinumPieces = CurrenciesDict.get("pp", 0) or 0
        )

        InventoryList: Typing.List[CharacterSchema.InventoryItemEntry] = []
        ContainersList: Typing.List[CharacterSchema.ContainerEntry] = []
        SeenContainers: Typing.Dict[str, bool] = {}

        for RawItem in Data.get("inventory", []):
            ItemDefinition: Typing.Dict[str, Typing.Any] = RawItem.get("definition", {}) or {}
            ItemName: str = ItemDefinition.get("name", "Unknown Item")
            ItemQuantity: int = RawItem.get("quantity", 1) or 1
            ItemWeight: float = float(ItemDefinition.get("weight", 0.0) or 0.0)
            ItemCost: float = float(ItemDefinition.get("cost", 0.0) or 0.0)
            IsEquipped: bool = RawItem.get("equipped", False) or False
            IsAttuned: bool = RawItem.get("isAttuned", False) or False
            NeedsAttunement: bool = ItemDefinition.get("canAttune", False) or False
            RarityText: str = ItemDefinition.get("rarity", "Common") or "Common"
            ItemFilterType: str = ItemDefinition.get("filterType", "Gear") or "Gear"
            DescriptionText: str = self.CleanHTMLString(ItemDefinition.get("description")) or ""
            ContainerID: Typing.Optional[str] = str(RawItem.get("containerEntityId")) if RawItem.get("containerEntityId") else None

            if ItemFilterType == "Container" or "backpack" in ItemName.lower() or "pouch" in ItemName.lower():
                ContID: str = str(RawItem.get("id"))
                if ContID not in SeenContainers:
                    SeenContainers[ContID] = True
                    ContainersList.append(CharacterSchema.ContainerEntry(Identifier = ContID, Name = ItemName, IsCarried = True, WeightPounds = ItemWeight))

            InventoryList.append(CharacterSchema.InventoryItemEntry(
                Identifier = str(RawItem.get("id", "")),
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
                Description = DescriptionText
            ))

        SpellsList: Typing.List[CharacterSchema.SpellEntry] = []
        SeenSpellNames: Typing.Dict[str, bool] = {}

        def ProcessSpellItem(RawSpellItem: Typing.Dict[str, Typing.Any], SourceOrigin: str) -> None:
            SpellDefinition: Typing.Dict[str, Typing.Any] = RawSpellItem.get("definition", {}) or {}
            SpellName: str = SpellDefinition.get("name", "Unknown Spell")
            if not SpellName or SpellName in SeenSpellNames:
                return

            SeenSpellNames[SpellName] = True
            SpellLevel: int = SpellDefinition.get("level", 0)
            SchoolName: str = SpellDefinition.get("school", "Evocation")
            ActivationDict: Typing.Dict[str, Typing.Any] = SpellDefinition.get("activation", {}) or {}
            ActivationTime: int = ActivationDict.get("activationTime", 1) or 1
            CastingDescription: str = f"{ActivationTime} Action" if ActivationDict.get("activationType") == 1 else "Special"
            RangeDict: Typing.Dict[str, Typing.Any] = SpellDefinition.get("range", {}) or {}
            RangeOrigin: str = RangeDict.get("origin", "Self") or "Self"
            RangeValue: int = RangeDict.get("rangeValue", 0) or 0
            RangeDescriptionText: str = f"{RangeValue} ft" if RangeValue > 0 else RangeOrigin
            DurationDict: Typing.Dict[str, Typing.Any] = SpellDefinition.get("duration", {}) or {}
            DurationDescriptionText: str = DurationDict.get("durationType", "Instantaneous") or "Instantaneous"
            IsConcentration: bool = SpellDefinition.get("concentration", False) or False
            IsRitual: bool = SpellDefinition.get("ritual", False) or False
            IsPrepared: bool = RawSpellItem.get("prepared", False) or False
            AlwaysPrepared: bool = RawSpellItem.get("alwaysPrepared", False) or False
            DescriptionContent: str = self.CleanHTMLString(SpellDefinition.get("description")) or ""
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
                Description = DescriptionContent
            ))

        SpellsGroupDict: Typing.Dict[str, Typing.Any] = Data.get("spells", {}) or {}
        for GroupOriginName, GroupSpellList in SpellsGroupDict.items():
            if isinstance(GroupSpellList, list):
                for SpellObj in GroupSpellList:
                    ProcessSpellItem(SpellObj, GroupOriginName.capitalize())

        for ClassSpellGroup in Data.get("classSpells", []):
            for ClassSpellItem in ClassSpellGroup.get("spells", []):
                ProcessSpellItem(ClassSpellItem, "Class")

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

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        for FeatItem in Data.get("feats", []):
            FeatDefinition: Typing.Dict[str, Typing.Any] = FeatItem.get("definition", {}) or {}
            FeatName: str = FeatDefinition.get("name", "Unknown Feat")
            FeatDescription: str = self.CleanHTMLString(FeatDefinition.get("description")) or ""
            FeaturesList.append(CharacterSchema.FeatureEntry(
                Identifier = str(FeatItem.get("componentId", "")),
                Name = FeatName,
                SourceType = "Feat",
                SourceName = "Feats",
                Description = FeatDescription
            ))

        for ClassProgress in Data.get("classes", []):
            for ClassFeature in ClassProgress.get("classFeatures", []):
                FeatureDefinition: Typing.Dict[str, Typing.Any] = ClassFeature.get("definition", {}) or {}
                FeatName: str = FeatureDefinition.get("name", "Class Feature")
                FeatDesc: str = self.CleanHTMLString(FeatureDefinition.get("description")) or ""
                ReqLevel: int = FeatureDefinition.get("requiredLevel", 1)
                FeaturesList.append(CharacterSchema.FeatureEntry(
                    Identifier = str(FeatureDefinition.get("id", "")),
                    Name = FeatName,
                    SourceType = "Class",
                    SourceName = ClassProgress.get("definition", {}).get("name", "Class"),
                    LevelRequirement = ReqLevel,
                    Description = FeatDesc
                ))

        AttacksList: Typing.List[CharacterSchema.AttackActionEntry] = []
        ActionsList: Typing.List[CharacterSchema.ActionEntry] = []

        ActionsGroupDict: Typing.Dict[str, Typing.Any] = Data.get("actions", {}) or {}
        for ActionOriginName, ActionItemList in ActionsGroupDict.items():
            if not isinstance(ActionItemList, list):
                continue

            for ActionItem in ActionItemList:
                ActionName: str = ActionItem.get("name", "Action")
                ActionDesc: str = self.CleanHTMLString(ActionItem.get("description")) or ""
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
                        Notes = ActionDesc
                    ))
                else:
                    ActionsList.append(CharacterSchema.ActionEntry(
                        Identifier = str(ActionItem.get("id", "")),
                        Name = ActionName,
                        ActionType = CharacterSchema.ActionActivationType.BonusAction if ActionItem.get("actionType") == 2 else CharacterSchema.ActionActivationType.Action,
                        SourceType = ActionOriginName.capitalize(),
                        Description = ActionDesc
                    ))

        TraitsDict: Typing.Dict[str, Typing.Any] = Data.get("traits", {}) or {}
        PersonalityModel = CharacterSchema.PersonalityData(
            PersonalityTraits = self.CleanHTMLString(TraitsDict.get("personalityTraits")),
            Ideals = self.CleanHTMLString(TraitsDict.get("ideals")),
            Bonds = self.CleanHTMLString(TraitsDict.get("bonds")),
            Flaws = self.CleanHTMLString(TraitsDict.get("flaws"))
        )

        NotesDict: Typing.Dict[str, Typing.Any] = Data.get("notes", {}) or {}
        NotesModel = CharacterSchema.NotesData(
            Backstory = self.CleanHTMLString(NotesDict.get("backstory")),
            Allies = self.CleanHTMLString(NotesDict.get("allies")),
            Enemies = self.CleanHTMLString(NotesDict.get("enemies")),
            Organizations = self.CleanHTMLString(NotesDict.get("organizations")),
            PersonalPossessions = self.CleanHTMLString(NotesDict.get("personalPossessions")),
            OtherHoldings = self.CleanHTMLString(NotesDict.get("otherHoldings")),
            CustomNotes = self.CleanHTMLString(NotesDict.get("otherNotes"))
        )

        CalculatedArmorClass: int = 10 + AbilityScoresModel.Dexterity.Modifier
        ArmorClassModel = CharacterSchema.ArmorClassData(
            TotalArmorClass = CalculatedArmorClass,
            BaseArmorClass = 10,
            DexterityBonus = AbilityScoresModel.Dexterity.Modifier
        )

        PassivePerceptionScore: int = 10 + AbilityScoresModel.Wisdom.Modifier
        PassiveInvestigationScore: int = 10 + AbilityScoresModel.Intelligence.Modifier
        PassiveInsightScore: int = 10 + AbilityScoresModel.Wisdom.Modifier

        for SkillItem in SkillProficienciesList:
            if SkillItem.SkillName == "Perception":
                PassivePerceptionScore = SkillItem.PassiveScore
            elif SkillItem.SkillName == "Investigation":
                PassiveInvestigationScore = SkillItem.PassiveScore
            elif SkillItem.SkillName == "Insight":
                PassiveInsightScore = SkillItem.PassiveScore

        PreferencesDict: Typing.Dict[str, Typing.Any] = Data.get("preferences", {}) or {}
        PreferencesModel = CharacterSchema.CreatorPreferencesData(
            ProgressionType = str(PreferencesDict.get("progressionType", "Milestone")),
            EncumbranceType = str(PreferencesDict.get("encumbranceType", "Standard")),
            IgnoreCoinWeight = PreferencesDict.get("ignoreCoinWeight", True) if (PreferencesDict.get("ignoreCoinWeight") is not None) else True,
            HitPointType = str(PreferencesDict.get("hitPointType", "Manual")),
            ShowUnarmedStrike = PreferencesDict.get("showUnarmedStrike", True) if (PreferencesDict.get("showUnarmedStrike") is not None) else True,
            ShowScaledSpells = PreferencesDict.get("showScaledSpells", True) if (PreferencesDict.get("showScaledSpells") is not None) else True
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
            PassivePerception = PassivePerceptionScore,
            PassiveInvestigation = PassiveInvestigationScore,
            PassiveInsight = PassiveInsightScore,
            InitiativeBonus = AbilityScoresModel.Dexterity.Modifier,
            Species = SpeciesModel,
            Background = BackgroundModel,
            Classes = ClassesList,
            AbilityScores = AbilityScoresModel,
            HitPoints = HitPointsModel,
            DeathSaves = DeathSavesModel,
            ArmorClass = ArmorClassModel,
            Speed = CharacterSchema.SpeedData(WalkingSpeedFeet = 30),
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
            Preferences = PreferencesModel
        )
        return UnifiedSheet

    def MapDicecloudCharacter(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        CharactersList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("characters", [])
        CharacterData: Typing.Dict[str, Typing.Any] = CharactersList[0] if CharactersList else {}

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
            AppearanceDescription = self.CleanHTMLString(CharacterData.get("description")),
            AvatarURL = CharacterData.get("picture")
        )

        SpeciesModel = CharacterSchema.SpeciesData(
            RaceName = RaceName,
            FullName = RaceName,
            Description = None
        )

        BackgroundModel = CharacterSchema.BackgroundData(
            Name = "Soldier" if ("soldier" in (CharacterData.get("backstory") or "").lower()) else "Adventurer",
            Description = self.CleanHTMLString(CharacterData.get("backstory"))
        )

        ClassesList: Typing.List[CharacterSchema.ClassProgressEntry] = []
        TotalCharacterLevel: int = 0
        RawClasses: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("classes", [])
        for ClassIndex, ClassItem in enumerate(RawClasses):
            ClassName: str = ClassItem.get("name", "Fighter")
            ClassLevel: int = ClassItem.get("level", 1)
            TotalCharacterLevel += ClassLevel
            HitDie: int = self.CLASS_HIT_DIE_MAP.get(ClassName.lower(), 8)
            ClassesList.append(CharacterSchema.ClassProgressEntry(
                ClassName = ClassName,
                Level = ClassLevel,
                SubclassName = None,
                HitDie = HitDie,
                HitDiceTotal = ClassLevel,
                HitDiceUsed = 0,
                IsStartingClass = (ClassIndex == 0)
            ))

        if not ClassesList:
            TotalCharacterLevel = 1
            ClassesList.append(CharacterSchema.ClassProgressEntry())

        ComputedProficiencyBonus: int = self.ComputeProficiencyBonusForLevel(TotalCharacterLevel)

        EffectsList: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("effects", [])
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
        for EffectItem in EffectsList:
            StatTarget: str = (EffectItem.get("stat") or "").lower()
            OpType: str = (EffectItem.get("operation") or "").lower()
            if StatTarget in BaseStatValues and OpType == "base":
                EffectVal = EffectItem.get("value")
                if EffectVal is not None:
                    BaseStatValues[StatTarget] = int(EffectVal)
            elif StatTarget == "armor" and OpType == "base":
                CalculatedArmorClassBase = int(EffectItem.get("value") or 10)
                ArmorNameDetected = EffectItem.get("name")

        AbilityScoresModel = CharacterSchema.AbilityScoresData(
            Strength = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["strength"]),
            Dexterity = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["dexterity"]),
            Constitution = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["constitution"]),
            Intelligence = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["intelligence"]),
            Wisdom = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["wisdom"]),
            Charisma = CharacterSchema.AbilityScoreEntry(BaseScore = BaseStatValues["charisma"])
        )

        BaseHPValue: int = 10 + ((TotalCharacterLevel - 1) * 6) + (TotalCharacterLevel * AbilityScoresModel.Constitution.Modifier)
        HitPointsModel = CharacterSchema.HitPointsData(
            MaxHitPoints = BaseHPValue,
            CurrentHitPoints = BaseHPValue,
            TemporaryHitPoints = 0,
            BaseHitPoints = BaseHPValue
        )

        RawDeathSave: Typing.Dict[str, Typing.Any] = CharacterData.get("deathSave", {}) or {}
        DeathSavesModel = CharacterSchema.DeathSavesData(
            SuccessCount = RawDeathSave.get("pass", 0) or 0,
            FailureCount = RawDeathSave.get("fail", 0) or 0,
            IsStabilized = RawDeathSave.get("stable", False) or False
        )

        SkillProficienciesList: Typing.List[CharacterSchema.SkillProficiencyEntry] = []
        SavingThrowProficienciesList: Typing.List[CharacterSchema.SavingThrowProficiencyEntry] = []
        ArmorProficienciesList: Typing.List[str] = []
        WeaponProficienciesList: Typing.List[str] = []
        ToolProficienciesList: Typing.List[str] = []
        LanguageProficienciesList: Typing.List[str] = []

        RawProficiencies: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("proficiencies", [])
        SeenSkills: Typing.Dict[str, int] = {}
        SeenSaves: Typing.Dict[str, bool] = {}

        for ProfItem in RawProficiencies:
            ProfType: str = (ProfItem.get("type") or "").lower()
            ProfName: str = ProfItem.get("name", "")
            ProfValue: int = int(ProfItem.get("value", 1) or 1)

            if ProfType == "skill":
                SeenSkills[ProfName.lower()] = ProfValue
            elif ProfType == "save":
                SaveKey: str = ProfName.lower().replace("save", "")
                SeenSaves[SaveKey] = True
            elif ProfType == "armor":
                if ProfName not in ArmorProficienciesList:
                    ArmorProficienciesList.append(ProfName)
            elif ProfType == "weapon":
                if ProfName not in WeaponProficienciesList:
                    WeaponProficienciesList.append(ProfName)
            elif ProfType == "tool":
                if ProfName not in ToolProficienciesList:
                    ToolProficienciesList.append(ProfName)
            elif ProfType == "language":
                if ProfName not in LanguageProficienciesList:
                    LanguageProficienciesList.append(ProfName)

        for NormalizedSkill, AssociatedAbility in self.SKILL_ABILITY_MAP.items():
            FormattedSkillName: str = " ".join(Word.capitalize() for Word in NormalizedSkill.replace("-", " ").split())
            ProfLevelValue: int = SeenSkills.get(NormalizedSkill.lower(), 0)
            ProfTier: CharacterSchema.ProficiencyTierType = CharacterSchema.ProficiencyTierType.Expertise if (ProfLevelValue == 2) else (CharacterSchema.ProficiencyTierType.Proficient if (ProfLevelValue == 1) else CharacterSchema.ProficiencyTierType.NoneTier)
            AbilityMod: int = getattr(AbilityScoresModel, AssociatedAbility.value).Modifier
            ProfBonusToAdd: int = (ComputedProficiencyBonus * 2) if (ProfTier == CharacterSchema.ProficiencyTierType.Expertise) else (ComputedProficiencyBonus if (ProfTier == CharacterSchema.ProficiencyTierType.Proficient) else 0)
            SkillBonus: int = AbilityMod + ProfBonusToAdd
            PassiveScore: int = 10 + SkillBonus
            SkillProficienciesList.append(CharacterSchema.SkillProficiencyEntry(
                SkillName = FormattedSkillName,
                AssociatedAbility = AssociatedAbility,
                ProficiencyTier = ProfTier,
                BonusModifier = SkillBonus,
                PassiveScore = PassiveScore
            ))

        for AbilityEnum in CharacterSchema.AbilityType:
            IsSaveProf: bool = SeenSaves.get(AbilityEnum.value.lower(), False)
            AbilityMod = getattr(AbilityScoresModel, AbilityEnum.value).Modifier
            SaveBonus = AbilityMod + (ComputedProficiencyBonus if IsSaveProf else 0)
            SavingThrowProficienciesList.append(CharacterSchema.SavingThrowProficiencyEntry(
                AbilityName = AbilityEnum,
                IsProficient = IsSaveProf,
                BonusModifier = SaveBonus
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
            ParentDict: Typing.Dict[str, Typing.Any] = ItemItem.get("parent", {}) or {}
            ContainerID: Typing.Optional[str] = ParentDict.get("id") if (ParentDict.get("collection") == "Containers") else None

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
                    Description = self.CleanHTMLString(ItemItem.get("description")) or ""
                ))

        CurrenciesModel = CharacterSchema.CurrenciesData(
            CopperPieces = CopperPiecesCount,
            SilverPieces = SilverPiecesCount,
            GoldPieces = GoldPiecesCount
        )

        AttacksList: Typing.List[CharacterSchema.AttackActionEntry] = []
        RawAttacks: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("attacks", [])
        for AttackItem in RawAttacks:
            AtkName: str = AttackItem.get("name", "Attack")
            DamageFormula: str = AttackItem.get("damage", "")
            DamageType: str = AttackItem.get("damageType", "slashing")
            DetailsText: str = AttackItem.get("details", "")
            PropertiesList: Typing.List[str] = [Prop.strip() for Prop in DetailsText.split(";") if Prop.strip()]
            AtkBonus: int = AbilityScoresModel.Strength.Modifier + ComputedProficiencyBonus
            AttacksList.append(CharacterSchema.AttackActionEntry(
                Identifier = str(AttackItem.get("_id", "")),
                Name = AtkName,
                AttackBonus = AtkBonus,
                DamageExpression = DamageFormula,
                DamageType = DamageType,
                RangeDescription = "5 ft",
                Properties = PropertiesList,
                IsEquipped = AttackItem.get("enabled", True),
                AttackSource = AttackItem.get("source", "Weapon") or "Weapon",
                Notes = DetailsText
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
            ComponentsDict: Typing.Dict[str, Typing.Any] = SpellItem.get("components", {}) or {}
            IsConc: bool = ComponentsDict.get("concentration", False) or False
            IsRitual: bool = SpellItem.get("ritual", False) or False
            PreparedVal: str = SpellItem.get("prepared", "prepared")
            DescClean: str = self.CleanHTMLString(SpellItem.get("description")) or ""

            RawMaterialValue = ComponentsDict.get("material", False)
            HasMaterialComponent: bool = bool(RawMaterialValue)
            MaterialDesc: Typing.Optional[str] = RawMaterialValue if isinstance(RawMaterialValue, str) else None

            SpellsList.append(CharacterSchema.SpellEntry(
                Identifier = str(SpellItem.get("_id", "")),
                Name = SpellName,
                Level = SpellLevel,
                School = SchoolName,
                CastingTime = CastingTimeStr,
                RangeDescription = RangeStr,
                DurationDescription = DurationStr,
                Components = CharacterSchema.SpellComponentData(Verbal = bool(ComponentsDict.get("verbal", False)), Somatic = bool(ComponentsDict.get("somatic", False)), Material = HasMaterialComponent, MaterialDescription = MaterialDesc),
                IsConcentration = IsConc,
                IsRitual = IsRitual,
                IsPrepared = (PreparedVal == "prepared"),
                SourceType = "Warlock",
                Description = DescClean
            ))

        SpellcastingModel = CharacterSchema.SpellcastingData(
            SpellSlots = [CharacterSchema.SpellSlotEntry(Level = 1, TotalSlots = 0)],
            PactMagic = CharacterSchema.PactMagicSlotData(SlotLevel = 2, TotalSlots = 2, UsedSlots = 0),
            Spells = SpellsList
        )

        FeaturesList: Typing.List[CharacterSchema.FeatureEntry] = []
        RawFeatures: Typing.List[Typing.Dict[str, Typing.Any]] = RawJSON.get("features", [])
        for FeatItem in RawFeatures:
            FeatName: str = FeatItem.get("name", "Feature")
            ResetTypeStr: str = FeatItem.get("reset", "longRest")
            ResetEnum: CharacterSchema.ResetScheduleType = CharacterSchema.ResetScheduleType.ShortRest if (ResetTypeStr == "shortRest") else (CharacterSchema.ResetScheduleType.LongRest if (ResetTypeStr == "longRest") else CharacterSchema.ResetScheduleType.Manual)
            FeaturesList.append(CharacterSchema.FeatureEntry(
                Identifier = str(FeatItem.get("_id", "")),
                Name = FeatName,
                SourceType = "Class",
                SourceName = "Fighter / Warlock",
                Description = self.CleanHTMLString(FeatItem.get("description")) or "",
                IsEnabled = FeatItem.get("enabled", True),
                LimitedUse = CharacterSchema.LimitedUseData(MaxUses = 1, UsedUses = FeatItem.get("used", 0) or 0, ResetType = ResetEnum)
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

        TotalAC: int = CalculatedArmorClassBase
        ArmorClassModel = CharacterSchema.ArmorClassData(
            TotalArmorClass = TotalAC,
            BaseArmorClass = CalculatedArmorClassBase,
            ArmorName = ArmorNameDetected
        )

        PassivePerceptionScore = 10 + AbilityScoresModel.Wisdom.Modifier
        PassiveInvestigationScore = 10 + AbilityScoresModel.Intelligence.Modifier
        PassiveInsightScore = 10 + AbilityScoresModel.Wisdom.Modifier

        for SkillItem in SkillProficienciesList:
            if SkillItem.SkillName == "Perception":
                PassivePerceptionScore = SkillItem.PassiveScore
            elif SkillItem.SkillName == "Investigation":
                PassiveInvestigationScore = SkillItem.PassiveScore
            elif SkillItem.SkillName == "Insight":
                PassiveInsightScore = SkillItem.PassiveScore

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
            PassivePerception = PassivePerceptionScore,
            PassiveInvestigation = PassiveInvestigationScore,
            PassiveInsight = PassiveInsightScore,
            InitiativeBonus = AbilityScoresModel.Dexterity.Modifier,
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
            Attacks = AttacksList,
            Containers = ContainersList,
            Inventory = InventoryList,
            Currencies = CurrenciesModel,
            Spellcasting = SpellcastingModel,
            Features = FeaturesList,
            Personality = PersonalityModel,
            PhysicalAppearance = AppearanceData,
            Notes = NotesModel
        )
        return UnifiedSheet

    def IngestUniversalCharacterData(self, RawJSON: Typing.Dict[str, Typing.Any]) -> CharacterSchema.DND5thEditionCharacterSheet:
        if "data" in RawJSON and isinstance(RawJSON["data"], dict) and "classes" in RawJSON["data"]:
            return self.MapDNDBeyondCharacter(RawJSON)

        if "characters" in RawJSON and isinstance(RawJSON["characters"], list):
            return self.MapDicecloudCharacter(RawJSON)

        if "AbilityScores" in RawJSON and "Classes" in RawJSON:
            return CharacterSchema.DND5thEditionCharacterSheet.model_validate(RawJSON)

        raise ValueError("Unsupported or invalid character data structure provided for universal ingestion.")

    def ExportToDatabasePayload(self, Sheet: CharacterSchema.DND5thEditionCharacterSheet, RawImportData: Typing.Optional[Typing.Dict[str, Typing.Any]] = None) -> Typing.Dict[str, Typing.Any]:
        PrimaryClass: str = Sheet.Classes[0].ClassName if Sheet.Classes else "Adventurer"
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
        return Payload

GLOBAL_CHARACTER_MAPPER: CharacterMappingService = CharacterMappingService()
