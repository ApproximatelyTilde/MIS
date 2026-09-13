const CharacterSheetFuzzySearch = {
    ActiveTargetElement: null,
    ActiveCategory: null,
    ActiveTagContainer: null,
    PopoverElement: null,
    PendingBlurTimeoutId: null,
    IsInteractingWithPopover: false,

    Initialize: function () {
        window.CharacterSheetFuzzySearch = this;
        this.EnsurePopoverElement();
        this.BindEventListeners();
    },

    EnsurePopoverElement: function () {
        let ExistingPopover = document.getElementById("FuzzySuggestionPopover");
        const DesktopContainer = document.getElementById("DesktopContainer");
        if (!ExistingPopover) {
            ExistingPopover = document.createElement("div");
            ExistingPopover.id = "FuzzySuggestionPopover";
            ExistingPopover.className = "FuzzySuggestionPopover HiddenElement";
            if (DesktopContainer) {
                DesktopContainer.appendChild(ExistingPopover);
            } else {
                document.body.appendChild(ExistingPopover);
            }
        } else if (DesktopContainer && ExistingPopover.parentElement !== DesktopContainer) {
            DesktopContainer.appendChild(ExistingPopover);
        }
        if (!ExistingPopover.getAttribute("data-listeners-bound")) {
            ExistingPopover.setAttribute("data-listeners-bound", "true");
            ExistingPopover.addEventListener("pointerdown", (Event) => {
                this.IsInteractingWithPopover = true;
                if (this.PendingBlurTimeoutId) {
                    clearTimeout(this.PendingBlurTimeoutId);
                    this.PendingBlurTimeoutId = null;
                }
                Event.stopPropagation();
            });
            ExistingPopover.addEventListener("mousedown", (Event) => {
                this.IsInteractingWithPopover = true;
                if (this.PendingBlurTimeoutId) {
                    clearTimeout(this.PendingBlurTimeoutId);
                    this.PendingBlurTimeoutId = null;
                }
                const SuggestionButton = Event.target.closest(".FuzzySuggestionButton");
                if (SuggestionButton) {
                    Event.preventDefault();
                }
                Event.stopPropagation();
            });
            ExistingPopover.addEventListener("click", (Event) => {
                Event.stopPropagation();
                const SuggestionButton = Event.target.closest(".FuzzySuggestionButton");
                if (SuggestionButton) {
                    Event.preventDefault();
                    if (this.PendingBlurTimeoutId) {
                        clearTimeout(this.PendingBlurTimeoutId);
                        this.PendingBlurTimeoutId = null;
                    }
                    const SelectedCanonicalName = SuggestionButton.getAttribute("data-canonical-name");
                    this.ApplySuggestion(SelectedCanonicalName);
                }
            });
        }
        this.PopoverElement = ExistingPopover;
    },

    BindEventListeners: function () {
        $(document).on("input", "#CharacterSheetSpeciesInput", (Event) => {
            if (!Event.currentTarget.value.trim()) {
                this.SyncSpeciesFeatures("");
            }
            this.HandleSingleInputInput(Event.currentTarget, "Species");
        });

        $(document).on("blur", "#CharacterSheetSpeciesInput", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Species");
        });

        $(document).on("input", "#CharacterSheetBackgroundInput", (Event) => {
            if (!Event.currentTarget.value.trim()) {
                this.SyncBackgroundFeatures("");
            }
            this.HandleSingleInputInput(Event.currentTarget, "Backgrounds");
        });

        $(document).on("blur", "#CharacterSheetBackgroundInput", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Backgrounds");
        });

        $(document).on("input", ".ClassInputName", (Event) => {
            if (!Event.currentTarget.value.trim()) {
                this.SyncClassFeatures();
            }
            this.HandleSingleInputInput(Event.currentTarget, "Classes");
        });

        $(document).on("blur", ".ClassInputName", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Classes");
        });

        $(document).on("input", ".ClassInputSubclass", (Event) => {
            if (!Event.currentTarget.value.trim()) {
                this.SyncClassFeatures();
            }
            this.HandleSubclassInput(Event.currentTarget);
        });

        $(document).on("blur", ".ClassInputSubclass", (Event) => {
            this.HandleSubclassBlur(Event.currentTarget);
        });

        $(document).on("input", "#NewSpellNameInput", (Event) => {
            this.HandleSingleInputInput(Event.currentTarget, "Spells");
        });

        $(document).on("blur", "#NewSpellNameInput", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Spells");
        });

        $(document).on("input", "#NewInventoryItemNameInput", (Event) => {
            this.HandleSingleInputInput(Event.currentTarget, "Items");
        });

        $(document).on("blur", "#NewInventoryItemNameInput", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Items");
        });

        $(document).on("click", ".TagInputContainer", function (Event) {
            if ($(Event.target).closest(".TagRemoveButton").length === 0) {
                $(this).find(".TagTextInput").focus();
            }
        });

        $(document).on("input", ".TagTextInput", (Event) => {
            const InputElement = Event.currentTarget;
            const ContainerElement = InputElement.closest(".TagInputContainer");
            if (!ContainerElement) {
                return;
            }
            const CategoryName = ContainerElement.getAttribute("data-category");
            const CurrentValue = InputElement.value;
            if (CurrentValue.includes(",")) {
                const Parts = CurrentValue.split(",");
                for (let Index = 0; Index < Parts.length; Index += 1) {
                    const PartText = Parts[Index].trim();
                    if (PartText) {
                        this.AddTagToContainer(ContainerElement, CategoryName, PartText, null, "", null, true);
                    }
                }
                InputElement.value = "";
                this.HidePopover();
                return;
            }
            this.HandleTagInputInput(InputElement, ContainerElement, CategoryName);
        });

        $(document).on("keydown", ".TagTextInput", (Event) => {
            const InputElement = Event.currentTarget;
            const ContainerElement = InputElement.closest(".TagInputContainer");
            if (!ContainerElement) {
                return;
            }
            const CategoryName = ContainerElement.getAttribute("data-category");
            if (Event.key === "Enter" || Event.key === ",") {
                Event.preventDefault();
                const CleanText = InputElement.value.replace(/,/g, "").trim();
                if (CleanText) {
                    this.AddTagToContainer(ContainerElement, CategoryName, CleanText, null, "", null, true);
                    InputElement.value = "";
                    this.HidePopover();
                }
            } else if (Event.key === "Backspace" && !InputElement.value) {
                const TagItems = ContainerElement.querySelectorAll(".TagItem");
                if (TagItems.length > 0) {
                    const LastTagItem = TagItems[TagItems.length - 1];
                    this.RemoveTagItem(LastTagItem);
                }
            }
        });

        $(document).on("blur", ".TagTextInput", (Event) => {
            const InputElement = Event.currentTarget;
            const ContainerElement = InputElement.closest(".TagInputContainer");
            if (!ContainerElement) {
                return;
            }
            const CategoryName = ContainerElement.getAttribute("data-category");
            if (this.PendingBlurTimeoutId) {
                clearTimeout(this.PendingBlurTimeoutId);
            }
            this.PendingBlurTimeoutId = setTimeout(() => {
                this.PendingBlurTimeoutId = null;
                if (this.IsInteractingWithPopover) {
                    return;
                }
                const CleanText = InputElement.value.replace(/,/g, "").trim();
                if (CleanText) {
                    this.AddTagToContainer(ContainerElement, CategoryName, CleanText, null, "", null, true);
                    InputElement.value = "";
                }
                if (this.ActiveTargetElement === InputElement) {
                    this.HidePopover();
                }
            }, 150);
        });

        $(document).on("click", ".TagEditButton", (Event) => {
            Event.preventDefault();
            Event.stopPropagation();
            const TagItem = Event.currentTarget.closest(".TagItem");
            const FeatureName = TagItem ? TagItem.getAttribute("data-value") : "";
            if (FeatureName && window.DesktopApplication && DesktopApplication.OpenEditFeatureWindow) {
                DesktopApplication.OpenEditFeatureWindow(FeatureName);
            }
        });

        $(document).on("click", ".FeaturesTagInputContainer .TagItemText", (Event) => {
            Event.preventDefault();
            Event.stopPropagation();
            const TagItem = Event.currentTarget.closest(".TagItem");
            const FeatureName = TagItem ? TagItem.getAttribute("data-value") : "";
            if (FeatureName && window.DesktopApplication && DesktopApplication.OpenEditFeatureWindow) {
                DesktopApplication.OpenEditFeatureWindow(FeatureName);
            }
        });

        $(document).on("click", "#CharacterSheetEditFeatureTriggerButton", (Event) => {
            Event.preventDefault();
            Event.stopPropagation();
            if (window.DesktopApplication && DesktopApplication.OpenEditFeatureWindow) {
                DesktopApplication.OpenEditFeatureWindow("");
            }
        });

        $(document).on("click", ".TagRemoveButton", (Event) => {
            Event.preventDefault();
            Event.stopPropagation();
            const ButtonElement = Event.currentTarget;
            const TagItem = ButtonElement.closest(".TagItem");
            if (TagItem) {
                this.RemoveTagItem(TagItem);
            }
        });

        $(document).on("pointerdown", (Event) => {
            if (this.PopoverElement && !this.PopoverElement.classList.contains("HiddenElement")) {
                if (!$(Event.target).closest("#FuzzySuggestionPopover").length &&
                    !$(Event.target).closest(".TagTextInput").length &&
                    !$(Event.target).is(this.ActiveTargetElement)) {
                    this.HidePopover();
                }
            }
        });

        $(document).on("htmx:afterSwap", (Event) => {
            this.InitializeAllTagContainers(Event.target);
        });
    },

    GetScopedSubclassCandidates: function (SubclassInputElement) {
        if (typeof RulesDataStoreManager === "undefined") {
            return [];
        }
        const ClassContainer = SubclassInputElement.closest(".ClassContainer");
        const ClassNameInput = ClassContainer ? ClassContainer.querySelector(".ClassInputName") : null;
        const ClassName = ClassNameInput ? ClassNameInput.value.trim() : "";
        if (!ClassName) {
            return [];
        }
        const CanonicalClass = RulesDataStoreManager.FindCanonicalMatch("Classes", ClassName) || ClassName;
        return RulesDataStoreManager.GetSubclassesForClass(CanonicalClass);
    },

    HandleSubclassInput: function (InputElement) {
        if (typeof RulesDataStoreManager === "undefined") {
            return;
        }
        const QueryString = InputElement.value.trim();
        if (QueryString.length < 2) {
            this.HidePopover();
            return;
        }
        const ScopedCandidates = this.GetScopedSubclassCandidates(InputElement);
        if (ScopedCandidates.length === 0) {
            this.HidePopover();
            return;
        }
        const Suggestions = RulesDataStoreManager.FindSuggestions(ScopedCandidates, QueryString, 1);
        if (Suggestions.length > 0) {
            const BestSuggestion = Suggestions[0];
            if (BestSuggestion.toLowerCase() !== QueryString.toLowerCase()) {
                this.ShowPopover(InputElement, "Subclasses", null, BestSuggestion);
                return;
            }
        }
        this.HidePopover();
    },

    HandleSubclassBlur: function (InputElement) {
        if (typeof RulesDataStoreManager === "undefined") {
            return;
        }
        const RawValue = InputElement.value.trim();
        const ScopedCandidates = this.GetScopedSubclassCandidates(InputElement);
        if (RawValue && ScopedCandidates.length > 0) {
            const CanonicalMatch = RulesDataStoreManager.FindCanonicalMatch(ScopedCandidates, RawValue);
            if (CanonicalMatch && CanonicalMatch !== RawValue) {
                InputElement.value = CanonicalMatch;
                $(InputElement).trigger("change");
            }
        }
        this.SyncClassFeatures();
        if (this.PendingBlurTimeoutId) {
            clearTimeout(this.PendingBlurTimeoutId);
        }
        this.PendingBlurTimeoutId = setTimeout(() => {
            this.PendingBlurTimeoutId = null;
            if (this.IsInteractingWithPopover) {
                return;
            }
            if (this.ActiveTargetElement === InputElement) {
                this.HidePopover();
            }
        }, 150);
    },

    HandleSingleInputInput: function (InputElement, CategoryName) {
        if (typeof RulesDataStoreManager === "undefined") {
            return;
        }
        const QueryString = InputElement.value.trim();
        if (QueryString.length < 2) {
            this.HidePopover();
            return;
        }
        const Suggestions = RulesDataStoreManager.FindSuggestions(CategoryName, QueryString, 1);
        if (Suggestions.length > 0) {
            const BestSuggestion = Suggestions[0];
            if (BestSuggestion.toLowerCase() !== QueryString.toLowerCase()) {
                this.ShowPopover(InputElement, CategoryName, null, BestSuggestion);
                return;
            }
        }
        this.HidePopover();
    },

    HandleSingleInputBlur: function (InputElement, CategoryName) {
        if (typeof RulesDataStoreManager === "undefined") {
            return;
        }
        const RawValue = InputElement.value.trim();
        if (RawValue) {
            const CanonicalMatch = RulesDataStoreManager.FindCanonicalMatch(CategoryName, RawValue);
            if (CanonicalMatch && CanonicalMatch !== RawValue) {
                InputElement.value = CanonicalMatch;
                $(InputElement).trigger("change");
            }
        }
        if (CategoryName === "Species") {
            this.SyncSpeciesFeatures(InputElement.value);
        } else if (CategoryName === "Backgrounds") {
            this.SyncBackgroundFeatures(InputElement.value);
        } else if (CategoryName === "Classes") {
            this.SyncClassFeatures();
        }
        if (this.PendingBlurTimeoutId) {
            clearTimeout(this.PendingBlurTimeoutId);
        }
        this.PendingBlurTimeoutId = setTimeout(() => {
            this.PendingBlurTimeoutId = null;
            if (this.IsInteractingWithPopover) {
                return;
            }
            if (this.ActiveTargetElement === InputElement) {
                this.HidePopover();
            }
        }, 150);
    },

    HandleTagInputInput: function (InputElement, ContainerElement, CategoryName) {
        if (typeof RulesDataStoreManager === "undefined") {
            return;
        }
        const QueryString = InputElement.value.trim();
        if (QueryString.length < 2) {
            this.HidePopover();
            return;
        }
        const Suggestions = RulesDataStoreManager.FindSuggestions(CategoryName, QueryString, 1);
        if (Suggestions.length > 0) {
            const BestSuggestion = Suggestions[0];
            if (BestSuggestion.toLowerCase() !== QueryString.toLowerCase()) {
                this.ShowPopover(InputElement, CategoryName, ContainerElement, BestSuggestion);
                return;
            }
        }
        this.HidePopover();
    },

    ShowPopover: function (TargetElement, CategoryName, ContainerElement, SuggestionText) {
        this.EnsurePopoverElement();
        this.ActiveTargetElement = TargetElement;
        this.ActiveCategory = CategoryName;
        this.ActiveTagContainer = ContainerElement;

        const SafeSuggestion = SuggestionText.replace(/"/g, "&quot;");
        this.PopoverElement.innerHTML = `Did you mean: <button type="button" class="FuzzySuggestionButton" data-canonical-name="${SafeSuggestion}">${SafeSuggestion}</button>?`;
        this.PopoverElement.classList.remove("HiddenElement");

        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            left: 0,
            top: 0,
            width: 960,
            height: 720
        };
        const ScaleFactorX = DesktopElement ? DesktopElement.offsetWidth / (DesktopRectangle.width || 1) : 1;
        const ScaleFactorY = DesktopElement ? DesktopElement.offsetHeight / (DesktopRectangle.height || 1) : 1;
        const ReferenceElement = ContainerElement || TargetElement;
        const ReferenceRectangle = ReferenceElement.getBoundingClientRect();

        let TargetLeft = (ReferenceRectangle.left - DesktopRectangle.left) * ScaleFactorX;
        let TargetTop = (ReferenceRectangle.bottom - DesktopRectangle.top) * ScaleFactorY + 2;
        const DesktopWidth = DesktopElement ? DesktopElement.offsetWidth : 960;
        const DesktopHeight = DesktopElement ? DesktopElement.offsetHeight : 720;
        TargetLeft = Math.max(0, Math.min(DesktopWidth - 220, TargetLeft));
        TargetTop = Math.max(0, Math.min(DesktopHeight - 40, TargetTop));

        $(this.PopoverElement).css({
            top: `${Math.round(TargetTop)}px`,
            left: `${Math.round(TargetLeft)}px`
        });
    },

    HidePopover: function () {
        if (this.PendingBlurTimeoutId) {
            clearTimeout(this.PendingBlurTimeoutId);
            this.PendingBlurTimeoutId = null;
        }
        if (this.PopoverElement) {
            this.PopoverElement.classList.add("HiddenElement");
        }
        this.ActiveTargetElement = null;
        this.ActiveCategory = null;
        this.ActiveTagContainer = null;
        this.IsInteractingWithPopover = false;
    },

    ApplySuggestion: function (CanonicalName) {
        if (this.PendingBlurTimeoutId) {
            clearTimeout(this.PendingBlurTimeoutId);
            this.PendingBlurTimeoutId = null;
        }
        if (!CanonicalName) {
            this.IsInteractingWithPopover = false;
            return;
        }
        const ContainerElement = this.ActiveTagContainer || (this.ActiveTargetElement ? this.ActiveTargetElement.closest(".TagInputContainer") : null);
        if (ContainerElement) {
            const TargetCategory = this.ActiveCategory || ContainerElement.getAttribute("data-category");
            const TagInput = ContainerElement.querySelector(".TagTextInput");
            if (TagInput) {
                TagInput.value = "";
            }
            this.AddTagToContainer(ContainerElement, TargetCategory, CanonicalName, null, "", null, true);
            if (TagInput) {
                TagInput.focus();
            }
        } else if (this.ActiveTargetElement) {
            this.ActiveTargetElement.value = CanonicalName;
            $(this.ActiveTargetElement).trigger("input").trigger("change");
            this.ActiveTargetElement.focus();
            if (this.ActiveCategory === "Species") {
                this.SyncSpeciesFeatures(CanonicalName);
            } else if (this.ActiveCategory === "Backgrounds") {
                this.SyncBackgroundFeatures(CanonicalName);
            } else if (this.ActiveCategory === "Classes" || this.ActiveCategory === "Subclasses") {
                this.SyncClassFeatures();
            }
        }
        this.IsInteractingWithPopover = false;
        this.HidePopover();
    },

    DetectFeatureSource: function (FeatureName) {
        if (typeof RulesDataStoreManager === "undefined" || !RulesDataStoreManager.DataStore) {
            return "Custom";
        }
        const CleanName = FeatureName.trim().toLowerCase();
        const SpeciesFeaturesMap = RulesDataStoreManager.DataStore["SpeciesFeaturesMap"] || {};
        for (let SpeciesKey in SpeciesFeaturesMap) {
            const TraitsList = SpeciesFeaturesMap[SpeciesKey] || [];
            for (let Index = 0; Index < TraitsList.length; Index += 1) {
                if (TraitsList[Index].toLowerCase() === CleanName) {
                    return "Species";
                }
            }
        }
        const ClassFeaturesMap = RulesDataStoreManager.DataStore["ClassFeaturesMap"] || {};
        for (let ClassKey in ClassFeaturesMap) {
            const LevelMap = ClassFeaturesMap[ClassKey] || {};
            for (let LevelKey in LevelMap) {
                const FeaturesList = LevelMap[LevelKey] || [];
                for (let Index = 0; Index < FeaturesList.length; Index += 1) {
                    if (FeaturesList[Index].toLowerCase() === CleanName) {
                        return "Class";
                    }
                }
            }
        }
        const SubclassFeaturesMap = RulesDataStoreManager.DataStore["SubclassFeaturesMap"] || {};
        for (let SubclassKey in SubclassFeaturesMap) {
            const LevelMap = SubclassFeaturesMap[SubclassKey] || {};
            for (let LevelKey in LevelMap) {
                const FeaturesList = LevelMap[LevelKey] || [];
                for (let Index = 0; Index < FeaturesList.length; Index += 1) {
                    if (FeaturesList[Index].toLowerCase() === CleanName) {
                        return "Class";
                    }
                }
            }
        }
        const FeatsList = RulesDataStoreManager.DataStore["Feats"] || [];
        for (let Index = 0; Index < FeatsList.length; Index += 1) {
            if (FeatsList[Index].toLowerCase() === CleanName) {
                return "Feat";
            }
        }
        const BackgroundFeaturesMap = RulesDataStoreManager.DataStore["BackgroundFeaturesMap"] || {};
        for (let BackgroundKey in BackgroundFeaturesMap) {
            const BackgroundFeats = BackgroundFeaturesMap[BackgroundKey] || [];
            for (let Index = 0; Index < BackgroundFeats.length; Index += 1) {
                if (BackgroundFeats[Index].toLowerCase() === CleanName) {
                    return "Feat";
                }
            }
        }
        return "Custom";
    },

    AddTagToContainer: function (ContainerElement, CategoryName, RawTagText, FeatureSource = null, SourceID = "", SourceLevel = null, IsManual = false) {
        if (!RawTagText) {
            return;
        }
        let FinalTagText = RawTagText.trim();
        if (!FinalTagText) {
            return;
        }
        if (typeof RulesDataStoreManager !== "undefined") {
            const CanonicalMatch = RulesDataStoreManager.FindCanonicalMatch(CategoryName, FinalTagText);
            if (CanonicalMatch) {
                FinalTagText = CanonicalMatch;
            }
        }

        const TagListElement = ContainerElement.querySelector(".TagList");
        if (!TagListElement) {
            return;
        }

        const ExistingTags = TagListElement.querySelectorAll(".TagItem");
        for (let Index = 0; Index < ExistingTags.length; Index += 1) {
            const ExistingTag = ExistingTags[Index];
            const ExistingText = ExistingTag.getAttribute("data-value");
            if (ExistingText && ExistingText.toLowerCase() === FinalTagText.toLowerCase()) {
                if (IsManual) {
                    ExistingTag.setAttribute("data-manually-added", "true");
                }
                if (SourceID && !ExistingTag.getAttribute("data-source-id")) {
                    ExistingTag.setAttribute("data-source-id", SourceID);
                }
                if (SourceLevel !== null && !ExistingTag.getAttribute("data-source-level")) {
                    ExistingTag.setAttribute("data-source-level", SourceLevel.toString());
                }
                return;
            }
        }

        const ResolvedSource = FeatureSource || (CategoryName === "Features" ? this.DetectFeatureSource(FinalTagText) : "Custom");
        const TagItem = document.createElement("span");
        TagItem.className = "TagItem";
        TagItem.setAttribute("data-value", FinalTagText);
        TagItem.setAttribute("data-feature-source", ResolvedSource);
        if (IsManual) {
            TagItem.setAttribute("data-manually-added", "true");
        }
        if (SourceID) {
            TagItem.setAttribute("data-source-id", SourceID);
        }
        if (SourceLevel !== null) {
            TagItem.setAttribute("data-source-level", SourceLevel.toString());
        }

        const TagTextSpan = document.createElement("span");
        TagTextSpan.className = "TagItemText";
        TagTextSpan.textContent = FinalTagText;

        const RemoveButton = document.createElement("button");
        RemoveButton.type = "button";
        RemoveButton.className = "TagRemoveButton";
        RemoveButton.setAttribute("aria-label", "Remove " + FinalTagText);

        const RemoveIcon = document.createElement("span");
        RemoveIcon.className = "TagRemoveIcon";
        RemoveIcon.setAttribute("aria-hidden", "true");
        RemoveButton.appendChild(RemoveIcon);

        TagItem.appendChild(TagTextSpan);

        if (CategoryName === "Features") {
            const EditButton = document.createElement("button");
            EditButton.type = "button";
            EditButton.className = "TagEditButton";
            EditButton.setAttribute("aria-label", "Edit " + FinalTagText);
            EditButton.setAttribute("title", "Edit " + FinalTagText);

            const EditIcon = document.createElement("span");
            EditIcon.className = "TagEditIcon";
            EditIcon.setAttribute("aria-hidden", "true");
            EditButton.appendChild(EditIcon);

            TagItem.appendChild(EditButton);
        }

        TagItem.appendChild(RemoveButton);
        TagListElement.appendChild(TagItem);

        this.UpdateHiddenInputFromTags(ContainerElement);
    },

    RemoveTagItem: function (TagItemElement) {
        const ContainerElement = TagItemElement.closest(".TagInputContainer");
        TagItemElement.remove();
        if (ContainerElement) {
            this.UpdateHiddenInputFromTags(ContainerElement);
        }
    },

    SortFeaturesTagContainer: function (ContainerElement) {
        const TagListElement = ContainerElement.querySelector(".TagList");
        if (!TagListElement) {
            return;
        }
        const TagItems = Array.from(TagListElement.querySelectorAll(".TagItem"));
        if (TagItems.length <= 1) {
            return;
        }
        const SourcePriority = {
            "Species": 1,
            "Class"  : 2,
            "Feat"   : 3,
            "Custom" : 4
        };
        TagItems.sort((FirstItem, SecondItem) => {
            const FirstSource = FirstItem.getAttribute("data-feature-source") || "Custom";
            const SecondSource = SecondItem.getAttribute("data-feature-source") || "Custom";
            const FirstPriority = SourcePriority[FirstSource] || 4;
            const SecondPriority = SourcePriority[SecondSource] || 4;
            if (FirstPriority !== SecondPriority) {
                return FirstPriority - SecondPriority;
            }
            if (FirstSource === "Class") {
                const FirstLevel = parseInt(FirstItem.getAttribute("data-source-level"), 10) || 1;
                const SecondLevel = parseInt(SecondItem.getAttribute("data-source-level"), 10) || 1;
                if (FirstLevel !== SecondLevel) {
                    return FirstLevel - SecondLevel;
                }
            }
            return 0;
        });
        for (let Index = 0; Index < TagItems.length; Index += 1) {
            TagListElement.appendChild(TagItems[Index]);
        }
    },

    UpdateHiddenInputFromTags: function (ContainerElement) {
        const CategoryName = ContainerElement.getAttribute("data-category");
        if (CategoryName === "Features") {
            this.SortFeaturesTagContainer(ContainerElement);
        }
        const HiddenInput = ContainerElement.querySelector(".TagHiddenValueInput");
        const TagItems = ContainerElement.querySelectorAll(".TagItem");
        const TagValues = [];
        for (let Index = 0; Index < TagItems.length; Index += 1) {
            const Value = TagItems[Index].getAttribute("data-value");
            if (Value) {
                TagValues.push(Value);
            }
        }
        const SerializedValue = TagValues.join(", ");
        if (HiddenInput && HiddenInput.value !== SerializedValue) {
            HiddenInput.value = SerializedValue;
            $(HiddenInput).trigger("change").trigger("input");
        }
        if (CategoryName === "Features") {
            const DataHiddenInput = ContainerElement.querySelector(".TagHiddenDataInput");
            if (DataHiddenInput) {
                let ExistingDataMap = {};
                if (DataHiddenInput.value) {
                    try {
                        const ParsedList = JSON.parse(DataHiddenInput.value);
                        for (let Index = 0; Index < ParsedList.length; Index += 1) {
                            if (ParsedList[Index] && ParsedList[Index].Name) {
                                ExistingDataMap[ParsedList[Index].Name.toLowerCase()] = ParsedList[Index];
                            }
                        }
                    } catch (JsonError) {
                    }
                }
                const FeaturesDataList = [];
                for (let Index = 0; Index < TagItems.length; Index += 1) {
                    const CurrentTag = TagItems[Index];
                    const FeatureName = CurrentTag.getAttribute("data-value");
                    const FeatureKey = (FeatureName || "").toLowerCase();
                    const ExistingEntry = ExistingDataMap[FeatureKey] || {};
                    const LevelRequirementAttr = CurrentTag.getAttribute("data-source-level");
                    const FeatureEntry = {
                        ID: ExistingEntry.ID || FeatureKey.replace(/\s+/g, "-"),
                        Name: FeatureName,
                        SourceType: CurrentTag.getAttribute("data-feature-source") || ExistingEntry.SourceType || "Custom",
                        SourceName: CurrentTag.getAttribute("data-source-id") || ExistingEntry.SourceName || "Custom",
                        LevelRequirement: LevelRequirementAttr ? parseInt(LevelRequirementAttr, 10) : (ExistingEntry.LevelRequirement || null),
                        IsEnabled: ExistingEntry.IsEnabled !== undefined ? ExistingEntry.IsEnabled : true,
                        IsManual: CurrentTag.getAttribute("data-manually-added") === "true",
                        Description: ExistingEntry.Description || "",
                        Snippet: ExistingEntry.Snippet || "",
                        Modifiers: ExistingEntry.Modifiers || []
                    };
                    FeaturesDataList.push(FeatureEntry);
                }
                const SerializedData = JSON.stringify(FeaturesDataList);
                if (DataHiddenInput.value !== SerializedData) {
                    DataHiddenInput.value = SerializedData;
                    $(DataHiddenInput).trigger("change");
                }
            }
        }
    },

    SyncSpeciesFeatures: function (SpeciesName) {
        const FeaturesContainer = document.querySelector('.TagInputContainer[data-category="Features"]');
        if (!FeaturesContainer) {
            return;
        }
        const ExistingSpeciesTags = FeaturesContainer.querySelectorAll('.TagItem[data-feature-source="Species"]');
        for (let Index = 0; Index < ExistingSpeciesTags.length; Index += 1) {
            const CurrentTag = ExistingSpeciesTags[Index];
            if (CurrentTag.getAttribute("data-manually-added") === "true") {
                CurrentTag.removeAttribute("data-source-id");
                CurrentTag.setAttribute("data-feature-source", "Custom");
            } else {
                CurrentTag.remove();
            }
        }
        if (SpeciesName && typeof RulesDataStoreManager !== "undefined") {
            const CanonicalSpecies = RulesDataStoreManager.FindCanonicalMatch("Species", SpeciesName) || SpeciesName;
            const Traits = RulesDataStoreManager.GetSpeciesTraits(CanonicalSpecies);
            for (let Index = 0; Index < Traits.length; Index += 1) {
                this.AddTagToContainer(FeaturesContainer, "Features", Traits[Index], "Species", CanonicalSpecies, null, false);
            }
        }
        this.UpdateHiddenInputFromTags(FeaturesContainer);
    },

    SyncBackgroundFeatures: function (BackgroundName) {
        const FeaturesContainer = document.querySelector('.TagInputContainer[data-category="Features"]');
        if (!FeaturesContainer) {
            return;
        }
        const ExistingBackgroundTags = FeaturesContainer.querySelectorAll('.TagItem[data-source-id="Background"]');
        for (let Index = 0; Index < ExistingBackgroundTags.length; Index += 1) {
            const CurrentTag = ExistingBackgroundTags[Index];
            if (CurrentTag.getAttribute("data-manually-added") === "true") {
                CurrentTag.removeAttribute("data-source-id");
                CurrentTag.setAttribute("data-feature-source", "Custom");
            } else {
                CurrentTag.remove();
            }
        }
        if (BackgroundName && typeof RulesDataStoreManager !== "undefined") {
            const CanonicalBackground = RulesDataStoreManager.FindCanonicalMatch("Backgrounds", BackgroundName) || BackgroundName;
            const Features = RulesDataStoreManager.GetBackgroundFeatures(CanonicalBackground);
            for (let Index = 0; Index < Features.length; Index += 1) {
                this.AddTagToContainer(FeaturesContainer, "Features", Features[Index], "Feat", "Background", null, false);
            }
        }
        this.UpdateHiddenInputFromTags(FeaturesContainer);
    },

    SyncClassFeatures: function () {
        const FeaturesContainer = document.querySelector('.TagInputContainer[data-category="Features"]');
        if (!FeaturesContainer) {
            return;
        }
        const ExistingClassTags = FeaturesContainer.querySelectorAll('.TagItem[data-feature-source="Class"]');
        for (let Index = 0; Index < ExistingClassTags.length; Index += 1) {
            const CurrentTag = ExistingClassTags[Index];
            if (CurrentTag.getAttribute("data-manually-added") === "true") {
                CurrentTag.removeAttribute("data-source-id");
                CurrentTag.removeAttribute("data-source-level");
                CurrentTag.setAttribute("data-feature-source", "Custom");
            } else {
                CurrentTag.remove();
            }
        }
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList || typeof RulesDataStoreManager === "undefined") {
            this.UpdateHiddenInputFromTags(FeaturesContainer);
            return;
        }
        const ClassContainers = ContainerList.querySelectorAll(".ClassContainer");
        for (let Index = 0; Index < ClassContainers.length; Index += 1) {
            const Container = ClassContainers[Index];
            const NameInput = Container.querySelector(".ClassInputName");
            const SubclassInput = Container.querySelector(".ClassInputSubclass");
            const LevelInput = Container.querySelector(".ClassInputLevel");
            const ClassName = NameInput ? NameInput.value.trim() : "";
            if (!ClassName) {
                continue;
            }
            const CanonicalClass = RulesDataStoreManager.FindCanonicalMatch("Classes", ClassName) || ClassName;
            const LevelNumber = LevelInput ? parseInt(LevelInput.value, 10) || 1 : 1;
            const SubclassName = SubclassInput ? SubclassInput.value.trim() : "";
            let CanonicalSubclass = "";
            if (SubclassName) {
                const ScopedSubclasses = RulesDataStoreManager.GetSubclassesForClass(CanonicalClass);
                CanonicalSubclass = RulesDataStoreManager.FindCanonicalMatch(ScopedSubclasses, SubclassName) || SubclassName;
            }
            const Features = RulesDataStoreManager.GetClassFeatures(CanonicalClass, LevelNumber, CanonicalSubclass);
            for (let FeatureIndex = 0; FeatureIndex < Features.length; FeatureIndex += 1) {
                this.AddTagToContainer(FeaturesContainer, "Features", Features[FeatureIndex], "Class", CanonicalClass, LevelNumber, false);
            }
        }
        this.UpdateHiddenInputFromTags(FeaturesContainer);
    },

    InitializeAllTagContainers: function (ScopeElement = document) {
        const Containers = ScopeElement.querySelectorAll(".TagInputContainer");
        for (let Index = 0; Index < Containers.length; Index += 1) {
            this.SyncTagsFromHiddenInput(Containers[Index]);
        }
    },

    SyncTagsFromHiddenInput: function (ContainerElement) {
        const HiddenInput = ContainerElement.querySelector(".TagHiddenValueInput");
        const TagListElement = ContainerElement.querySelector(".TagList");
        if (!HiddenInput || !TagListElement) {
            return;
        }
        const RawValue = HiddenInput.value || "";
        TagListElement.innerHTML = "";
        if (!RawValue.trim()) {
            return;
        }
        const CategoryName = ContainerElement.getAttribute("data-category");
        const DataHiddenInput = ContainerElement.querySelector(".TagHiddenDataInput");
        let FeaturesDataMap = {};
        if (CategoryName === "Features" && DataHiddenInput && DataHiddenInput.value) {
            try {
                const ParsedList = JSON.parse(DataHiddenInput.value);
                for (let Index = 0; Index < ParsedList.length; Index += 1) {
                    if (ParsedList[Index] && ParsedList[Index].Name) {
                        FeaturesDataMap[ParsedList[Index].Name.toLowerCase()] = ParsedList[Index];
                    }
                }
            } catch (JsonError) {
            }
        }
        const ValueList = RawValue.split(/[,;\n]/);
        for (let Index = 0; Index < ValueList.length; Index += 1) {
            const CleanItem = ValueList[Index].trim();
            if (CleanItem) {
                const ExistingFeature = FeaturesDataMap[CleanItem.toLowerCase()];
                const ResolvedSource = ExistingFeature ? ExistingFeature.SourceType : (CategoryName === "Features" ? this.DetectFeatureSource(CleanItem) : "Custom");
                const SourceID = ExistingFeature ? ExistingFeature.SourceName : "";
                const SourceLevel = ExistingFeature ? ExistingFeature.LevelRequirement : null;
                const IsManual = ExistingFeature ? Boolean(ExistingFeature.IsManual) : false;
                this.AddTagToContainer(ContainerElement, CategoryName, CleanItem, ResolvedSource, SourceID, SourceLevel, IsManual);
            }
        }
    }
};

$(document).ready(() => {
    CharacterSheetFuzzySearch.Initialize();
    CharacterSheetFuzzySearch.InitializeAllTagContainers();
});
