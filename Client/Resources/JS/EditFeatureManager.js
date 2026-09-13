const EditFeatureManager = {
    Initialize: function () {
        window.EditFeatureManager = this;

        $(document).on("input blur", "#EditFeatureNameInput", (Event) => {
            const FeatureName = Event.currentTarget.value.trim();
            this.InspectFeatureName(FeatureName);
        });

        $(document).on("click", "#EditFeatureSaveButton", () => {
            this.SaveFeature();
        });

        $(document).on("click", "#EditFeatureCancelButton", () => {
            if (window.WindowManager) {
                WindowManager.CloseWindow("WindowEditFeature");
            }
        });
    },

    InspectFeatureName: function (FeatureName) {
        if (!FeatureName) {
            $("#EditFeature5EToolsNotice").addClass("HiddenElement");
            this.SetFormEditable(true);
            return;
        }

        const Is5ETools = (typeof RulesDataStoreManager !== "undefined") && RulesDataStoreManager.Is5EToolsFeature(FeatureName);
        if (Is5ETools) {
            $("#EditFeature5EToolsNotice").removeClass("HiddenElement");
            this.SetFormEditable(false);
        } else {
            $("#EditFeature5EToolsNotice").addClass("HiddenElement");
            this.SetFormEditable(true);
        }
    },

    SetFormEditable: function (IsEditable) {
        const FormInputs = $("#EditFeatureForm").find("input, select, textarea").not("#EditFeatureNameInput");
        FormInputs.prop("disabled", !IsEditable);
        $("#EditFeatureSaveButton").prop("disabled", !IsEditable);
    },

    LoadFeature: function (FeatureName, ExplicitData = null) {
        const NameField = document.getElementById("EditFeatureNameInput");
        if (NameField && FeatureName) {
            NameField.value = FeatureName;
        }

        let FeatureData = ExplicitData;
        if (!FeatureData && FeatureName) {
            const FeaturesDataInput = document.getElementById("CharacterSheetFeaturesDataInput");
            if (FeaturesDataInput && FeaturesDataInput.value) {
                try {
                    const ParsedList = JSON.parse(FeaturesDataInput.value);
                    const CleanSearch = FeatureName.toLowerCase().trim();
                    for (let Index = 0; Index < ParsedList.length; Index += 1) {
                        if (ParsedList[Index] && ParsedList[Index].Name && (ParsedList[Index].Name.toLowerCase().trim() === CleanSearch)) {
                            FeatureData = ParsedList[Index];
                            break;
                        }
                    }
                } catch (JsonException) {
                }
            }
        }

        if (FeatureData) {
            const SourceTypeSelect = document.getElementById("EditFeatureSourceTypeSelect");
            if (SourceTypeSelect && FeatureData.SourceType) {
                SourceTypeSelect.value = FeatureData.SourceType;
            }

            const SourceNameInput = document.getElementById("EditFeatureSourceNameInput");
            if (SourceNameInput) {
                SourceNameInput.value = FeatureData.SourceName || "";
            }

            const LevelInput = document.getElementById("EditFeatureLevelInput");
            if (LevelInput) {
                LevelInput.value = FeatureData.LevelRequirement || "";
            }

            const IsEnabledCheckbox = document.getElementById("EditFeatureIsEnabledCheckbox");
            if (IsEnabledCheckbox) {
                IsEnabledCheckbox.checked = FeatureData.IsEnabled !== false;
            }

            const DescriptionInput = document.getElementById("EditFeatureDescriptionInput");
            if (DescriptionInput) {
                DescriptionInput.value = FeatureData.Description || FeatureData.Snippet || "";
            }

            const ModifiersList = FeatureData.Modifiers || [];
            let HasUnarmoredACModifier = false;
            let UnarmoredACAbilityValue = "Constitution";
            let HasFlatACBonusModifier = false;
            let FlatACBonusValue = 1;
            let HasAbilityBonusModifier = false;
            let AbilityBonusNameValue = "Strength";
            let AbilityBonusNumberValue = 1;
            let HasSpeedBonusModifier = false;
            let SpeedBonusValue = 10;

            for (let Index = 0; Index < ModifiersList.length; Index += 1) {
                const ModifierItem = ModifiersList[Index];
                if (!ModifierItem) {
                    continue;
                }
                const SubTypeString = (ModifierItem.ModifierSubType || "").toLowerCase();
                const TypeString = (ModifierItem.ModifierType || "").toLowerCase();
                const StringValueText = (ModifierItem.StringValue || "");

                if (SubTypeString.includes("unarmored") || TypeString.includes("unarmored")) {
                    HasUnarmoredACModifier = true;
                    if (StringValueText) {
                        UnarmoredACAbilityValue = StringValueText.charAt(0).toUpperCase() + StringValueText.slice(1).toLowerCase();
                    }
                } else if ((SubTypeString === "armor-class" || SubTypeString === "ac") && TypeString === "bonus") {
                    HasFlatACBonusModifier = true;
                    FlatACBonusValue = ModifierItem.Value || 1;
                } else if (SubTypeString.endsWith("-score") && TypeString === "bonus") {
                    HasAbilityBonusModifier = true;
                    const RawAbility = SubTypeString.replace("-score", "");
                    AbilityBonusNameValue = RawAbility.charAt(0).toUpperCase() + RawAbility.slice(1).toLowerCase();
                    AbilityBonusNumberValue = ModifierItem.Value || 1;
                } else if (SubTypeString === "speed" && TypeString === "bonus") {
                    HasSpeedBonusModifier = true;
                    SpeedBonusValue = ModifierItem.Value || 10;
                }
            }

            const UnarmoredCheckbox = document.getElementById("EditFeatureIncludeUnarmoredACCheckbox");
            if (UnarmoredCheckbox) {
                UnarmoredCheckbox.checked = HasUnarmoredACModifier;
            }
            const UnarmoredAbilitySelect = document.getElementById("EditFeatureUnarmoredACAbilitySelect");
            if (UnarmoredAbilitySelect) {
                UnarmoredAbilitySelect.value = UnarmoredACAbilityValue;
            }

            const FlatACCheckbox = document.getElementById("EditFeatureFlatACBonusCheckbox");
            if (FlatACCheckbox) {
                FlatACCheckbox.checked = HasFlatACBonusModifier;
            }
            const FlatACInput = document.getElementById("EditFeatureFlatACBonusInput");
            if (FlatACInput) {
                FlatACInput.value = FlatACBonusValue.toString();
            }

            const AbilityBonusCheckbox = document.getElementById("EditFeatureAbilityBonusCheckbox");
            if (AbilityBonusCheckbox) {
                AbilityBonusCheckbox.checked = HasAbilityBonusModifier;
            }
            const AbilityBonusSelect = document.getElementById("EditFeatureAbilityBonusAbilitySelect");
            if (AbilityBonusSelect) {
                AbilityBonusSelect.value = AbilityBonusNameValue;
            }
            const AbilityBonusValueInput = document.getElementById("EditFeatureAbilityBonusValueInput");
            if (AbilityBonusValueInput) {
                AbilityBonusValueInput.value = AbilityBonusNumberValue.toString();
            }

            const SpeedBonusCheckbox = document.getElementById("EditFeatureSpeedBonusCheckbox");
            if (SpeedBonusCheckbox) {
                SpeedBonusCheckbox.checked = HasSpeedBonusModifier;
            }
            const SpeedBonusInput = document.getElementById("EditFeatureSpeedBonusInput");
            if (SpeedBonusInput) {
                SpeedBonusInput.value = SpeedBonusValue.toString();
            }
        }

        this.InspectFeatureName(FeatureName);
    },

    SaveFeature: function () {
        const NameField = document.getElementById("EditFeatureNameInput");
        const FeatureName = NameField ? NameField.value.trim() : "";
        if (!FeatureName) {
            $("#EditFeatureStatusText").text("Feature name cannot be blank.");
            return;
        }

        if ((typeof RulesDataStoreManager !== "undefined") && RulesDataStoreManager.Is5EToolsFeature(FeatureName)) {
            $("#EditFeatureStatusText").text("Cannot modify a feature defined by 5ETools.");
            return;
        }

        const SourceTypeField = document.getElementById("EditFeatureSourceTypeSelect");
        const SourceType = SourceTypeField ? SourceTypeField.value : "Custom";

        const SourceNameField = document.getElementById("EditFeatureSourceNameInput");
        const SourceName = SourceNameField ? SourceNameField.value.trim() : "Custom";

        const LevelField = document.getElementById("EditFeatureLevelInput");
        const LevelRequirement = LevelField && LevelField.value ? parseInt(LevelField.value, 10) : null;

        const IsEnabledCheckbox = document.getElementById("EditFeatureIsEnabledCheckbox");
        const IsEnabled = IsEnabledCheckbox ? IsEnabledCheckbox.checked : true;

        const DescriptionField = document.getElementById("EditFeatureDescriptionInput");
        const DescriptionText = DescriptionField ? DescriptionField.value.trim() : "";

        const ModifiersList = [];

        const UnarmoredCheckbox = document.getElementById("EditFeatureIncludeUnarmoredACCheckbox");
        if (UnarmoredCheckbox && UnarmoredCheckbox.checked) {
            const AbilitySelect = document.getElementById("EditFeatureUnarmoredACAbilitySelect");
            const AbilityName = AbilitySelect ? AbilitySelect.value : "Constitution";
            ModifiersList.push({
                ModifierType   : "Bonus",
                ModifierSubType: "UnarmoredArmorClass",
                StringValue    : AbilityName,
                Value          : null,
                IsActive       : true
            });
        }

        const FlatACCheckbox = document.getElementById("EditFeatureFlatACBonusCheckbox");
        if (FlatACCheckbox && FlatACCheckbox.checked) {
            const ACInput = document.getElementById("EditFeatureFlatACBonusInput");
            const BonusValue = ACInput ? (parseInt(ACInput.value, 10) || 1) : 1;
            ModifiersList.push({
                ModifierType   : "Bonus",
                ModifierSubType: "ArmorClass",
                Value          : BonusValue,
                StringValue    : null,
                IsActive       : true
            });
        }

        const AbilityBonusCheckbox = document.getElementById("EditFeatureAbilityBonusCheckbox");
        if (AbilityBonusCheckbox && AbilityBonusCheckbox.checked) {
            const AbilitySelect = document.getElementById("EditFeatureAbilityBonusAbilitySelect");
            const AbilityName = AbilitySelect ? AbilitySelect.value : "Strength";
            const ValueInput = document.getElementById("EditFeatureAbilityBonusValueInput");
            const BonusValue = ValueInput ? (parseInt(ValueInput.value, 10) || 1) : 1;
            ModifiersList.push({
                ModifierType   : "Bonus",
                ModifierSubType: AbilityName.toLowerCase() + "-score",
                Value          : BonusValue,
                StringValue    : AbilityName,
                IsActive       : true
            });
        }

        const SpeedBonusCheckbox = document.getElementById("EditFeatureSpeedBonusCheckbox");
        if (SpeedBonusCheckbox && SpeedBonusCheckbox.checked) {
            const SpeedInput = document.getElementById("EditFeatureSpeedBonusInput");
            const SpeedValue = SpeedInput ? (parseInt(SpeedInput.value, 10) || 10) : 10;
            ModifiersList.push({
                ModifierType   : "Bonus",
                ModifierSubType: "speed",
                Value          : SpeedValue,
                StringValue    : null,
                IsActive       : true
            });
        }

        const FeaturePayload = {
            ID              : FeatureName.toLowerCase().replace(/\s+/g, "-"),
            Name            : FeatureName,
            SourceType      : SourceType,
            SourceName      : SourceName || "Custom",
            LevelRequirement: LevelRequirement,
            IsEnabled       : IsEnabled,
            IsManual        : true,
            Description     : DescriptionText,
            Snippet         : DescriptionText,
            Modifiers       : ModifiersList
        };

        const FeaturesContainer = document.querySelector('.TagInputContainer[data-category="Features"]');
        const DataHiddenInput = document.getElementById("CharacterSheetFeaturesDataInput");

        if (FeaturesContainer && window.CharacterSheetFuzzySearch) {
            CharacterSheetFuzzySearch.AddTagToContainer(FeaturesContainer, "Features", FeatureName, SourceType, SourceName, LevelRequirement, true);
        }

        if (DataHiddenInput) {
            let ExistingList = [];
            if (DataHiddenInput.value) {
                try {
                    ExistingList = JSON.parse(DataHiddenInput.value);
                } catch (ParseError) {
                    ExistingList = [];
                }
            }

            let FoundExisting = false;
            for (let Index = 0; Index < ExistingList.length; Index += 1) {
                if (ExistingList[Index] && ExistingList[Index].Name && (ExistingList[Index].Name.toLowerCase().trim() === FeatureName.toLowerCase().trim())) {
                    ExistingList[Index] = FeaturePayload;
                    FoundExisting = true;
                    break;
                }
            }

            if (!FoundExisting) {
                ExistingList.push(FeaturePayload);
            }

            DataHiddenInput.value = JSON.stringify(ExistingList);
            $(DataHiddenInput).trigger("change");
        }

        if (window.DesktopApplication) {
            DesktopApplication.RecalculateArmorClass();
            DesktopApplication.EvaluateCharacterSheetDirtyState();
        }

        $("#EditFeatureStatusText").text("Feature saved.");
        setTimeout(() => {
            if (window.WindowManager) {
                WindowManager.CloseWindow("WindowEditFeature");
            }
        }, 300);
    }
};

$(document).ready(() => {
    EditFeatureManager.Initialize();
});
