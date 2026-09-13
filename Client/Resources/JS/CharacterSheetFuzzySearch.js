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
            this.HandleSingleInputInput(Event.currentTarget, "Species");
        });

        $(document).on("blur", "#CharacterSheetSpeciesInput", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Species");
        });

        $(document).on("input", "#CharacterSheetBackgroundInput", (Event) => {
            this.HandleSingleInputInput(Event.currentTarget, "Backgrounds");
        });

        $(document).on("blur", "#CharacterSheetBackgroundInput", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Backgrounds");
        });

        $(document).on("input", ".ClassInputName", (Event) => {
            this.HandleSingleInputInput(Event.currentTarget, "Classes");
        });

        $(document).on("blur", ".ClassInputName", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Classes");
        });

        $(document).on("input", ".ClassInputSubclass", (Event) => {
            this.HandleSingleInputInput(Event.currentTarget, "Subclasses");
        });

        $(document).on("blur", ".ClassInputSubclass", (Event) => {
            this.HandleSingleInputBlur(Event.currentTarget, "Subclasses");
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
                        this.AddTagToContainer(ContainerElement, CategoryName, PartText);
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
                    this.AddTagToContainer(ContainerElement, CategoryName, CleanText);
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
                    this.AddTagToContainer(ContainerElement, CategoryName, CleanText);
                    InputElement.value = "";
                }
                if (this.ActiveTargetElement === InputElement) {
                    this.HidePopover();
                }
            }, 150);
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
            this.AddTagToContainer(ContainerElement, TargetCategory, CanonicalName);
            if (TagInput) {
                TagInput.focus();
            }
        } else if (this.ActiveTargetElement) {
            this.ActiveTargetElement.value = CanonicalName;
            $(this.ActiveTargetElement).trigger("input").trigger("change");
            this.ActiveTargetElement.focus();
        }
        this.IsInteractingWithPopover = false;
        this.HidePopover();
    },

    AddTagToContainer: function (ContainerElement, CategoryName, RawTagText) {
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
            const ExistingText = ExistingTags[Index].getAttribute("data-value");
            if (ExistingText && ExistingText.toLowerCase() === FinalTagText.toLowerCase()) {
                return;
            }
        }

        const TagItem = document.createElement("span");
        TagItem.className = "TagItem";
        TagItem.setAttribute("data-value", FinalTagText);

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

    UpdateHiddenInputFromTags: function (ContainerElement) {
        const HiddenInput = ContainerElement.querySelector(".TagHiddenValueInput");
        if (!HiddenInput) {
            return;
        }
        const TagItems = ContainerElement.querySelectorAll(".TagItem");
        const TagValues = [];
        for (let Index = 0; Index < TagItems.length; Index += 1) {
            const Value = TagItems[Index].getAttribute("data-value");
            if (Value) {
                TagValues.push(Value);
            }
        }
        const SerializedValue = TagValues.join(", ");
        if (HiddenInput.value !== SerializedValue) {
            HiddenInput.value = SerializedValue;
            $(HiddenInput).trigger("change").trigger("input");
        }
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
        const ValueList = RawValue.split(/[,;\n]/);
        for (let Index = 0; Index < ValueList.length; Index += 1) {
            const CleanItem = ValueList[Index].trim();
            if (CleanItem) {
                this.AddTagToContainer(ContainerElement, CategoryName, CleanItem);
            }
        }
    }
};

$(document).ready(() => {
    CharacterSheetFuzzySearch.Initialize();
    CharacterSheetFuzzySearch.InitializeAllTagContainers();
});
