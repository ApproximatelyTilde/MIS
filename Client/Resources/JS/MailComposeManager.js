const MailComposeManager = {
    EligibleRecipientsCache: null,
    IsFetchingRecipients: false,
    ActiveTagContainer: null,
    ActiveInputElement: null,
    PopoverElement: null,
    PendingBlurTimeoutId: null,
    PreviewUpdateTimeoutId: null,
    ComposeResizeObserver: null,

    Initialize: function () {
        window.MailComposeManager = this;
        this.EnsurePopoverElement();
        this.BindEventListeners();
        this.FetchEligibleRecipients();
        this.AttachComposeWindowObserver();
    },

    EnsurePopoverElement: function () {
        let ExistingPopover = document.getElementById("MailRecipientSuggestionPopover");
        const DesktopContainer = document.getElementById("DesktopContainer");
        if (!ExistingPopover) {
            ExistingPopover = document.createElement("div");
            ExistingPopover.id = "MailRecipientSuggestionPopover";
            ExistingPopover.className = "FuzzySuggestionPopover HiddenElement";
            if (DesktopContainer) {
                DesktopContainer.appendChild(ExistingPopover);
            } else {
                document.body.appendChild(ExistingPopover);
            }
        } else if (DesktopContainer && ExistingPopover.parentElement !== DesktopContainer) {
            DesktopContainer.appendChild(ExistingPopover);
        }
        this.PopoverElement = ExistingPopover;
    },

    FetchEligibleRecipients: function () {
        if (this.EligibleRecipientsCache !== null || this.IsFetchingRecipients) {
            return;
        }
        this.IsFetchingRecipients = true;
        $.ajax({
            url: "/API/Mail/Recipients",
            type: "GET",
            dataType: "json",
            success: (Data) => {
                this.EligibleRecipientsCache = Array.isArray(Data) ? Data : [];
                this.IsFetchingRecipients = false;
            },
            error: () => {
                this.EligibleRecipientsCache = [];
                this.IsFetchingRecipients = false;
            }
        });
    },

    BindEventListeners: function () {
        $(document).on("focus", "#MailRecipientTextInput", (Event) => {
            this.FetchEligibleRecipients();
            const InputElement = Event.currentTarget;
            const ContainerElement = InputElement.closest(".TagInputContainer");
            this.HandleRecipientInput(InputElement, ContainerElement);
        });

        $(document).on("input", "#MailRecipientTextInput", (Event) => {
            const InputElement = Event.currentTarget;
            const ContainerElement = InputElement.closest(".TagInputContainer");
            this.HandleRecipientInput(InputElement, ContainerElement);
        });

        $(document).on("keydown", "#MailRecipientTextInput", (Event) => {
            const InputElement = Event.currentTarget;
            const ContainerElement = InputElement.closest(".TagInputContainer");
            if (Event.key === "Enter" || Event.key === ",") {
                Event.preventDefault();
                const PopoverButton = this.PopoverElement ? this.PopoverElement.querySelector(".MailFuzzySuggestionButton") : null;
                if (PopoverButton && !this.PopoverElement.classList.contains("HiddenElement")) {
                    const TagValue = PopoverButton.getAttribute("data-tag");
                    this.AddRecipientTag(ContainerElement, TagValue);
                    this.HidePopover();
                    return;
                }
                const RawValue = InputElement.value.trim();
                if (RawValue.length > 0) {
                    const FormattedTag = RawValue.startsWith("@") ? RawValue : ("@" + RawValue);
                    this.AddRecipientTag(ContainerElement, FormattedTag);
                    this.HidePopover();
                }
            } else if (Event.key === "Backspace" && InputElement.value.length === 0) {
                const TagItems = ContainerElement.querySelectorAll(".TagItem");
                if (TagItems.length > 0) {
                    const LastTag = TagItems[TagItems.length - 1];
                    this.RemoveRecipientTag(LastTag);
                }
            } else if (Event.key === "Escape") {
                this.HidePopover();
            }
        });

        $(document).on("click", ".MailTagInputContainer", function (Event) {
            if ($(Event.target).closest(".TagRemoveButton").length === 0) {
                $(this).find(".TagTextInput").focus();
            }
        });

        $(document).on("click", "#MailRecipientTagContainer .TagRemoveButton", (Event) => {
            Event.stopPropagation();
            const TagItem = Event.currentTarget.closest(".TagItem");
            if (TagItem) {
                this.RemoveRecipientTag(TagItem);
            }
        });

        $(document).on("click", ".MailFuzzySuggestionButton", (Event) => {
            Event.preventDefault();
            Event.stopPropagation();
            const ButtonElement = Event.currentTarget;
            const FormattedTag = ButtonElement.getAttribute("data-tag");
            const ContainerElement = this.ActiveTagContainer || document.getElementById("MailRecipientTagContainer");
            if (ContainerElement && FormattedTag) {
                this.AddRecipientTag(ContainerElement, FormattedTag);
            }
            this.HidePopover();
            const TextInput = ContainerElement ? ContainerElement.querySelector(".TagTextInput") : null;
            if (TextInput) {
                TextInput.focus();
            }
        });

        $(document).on("blur", "#MailRecipientTextInput", () => {
            this.PendingBlurTimeoutId = setTimeout(() => {
                this.HidePopover();
            }, 150);
        });

        $(document).on("htmx:afterSwap", (Event) => {
            if ($(Event.target).closest("#WindowMailCompose").length > 0 || $(Event.target).is("#WindowMailCompose")) {
                this.AttachComposeWindowObserver();
            }
        });

        $(document).on("input", "#MailComposeBody", () => {
            this.SchedulePreviewUpdate();
        });

        $(document).on("focus", "#MailComposeBody", () => {
            this.AttachComposeWindowObserver();
            this.UpdateMarkdownPreview();
        });

        $(document).on("click", "#MailToggleRawButton", function () {
            const RenderedContainer = $("#MailMessageRenderedText");
            const RawContainer = $("#MailMessageRawText");
            if (RawContainer.hasClass("HiddenElement")) {
                RawContainer.removeClass("HiddenElement");
                RenderedContainer.addClass("HiddenElement");
                $(this).addClass("ActiveRawButton").addClass("ButtonActive");
            } else {
                RawContainer.addClass("HiddenElement");
                RenderedContainer.removeClass("HiddenElement");
                $(this).removeClass("ActiveRawButton").removeClass("ButtonActive");
            }
        });

        $(document).on("click", "#MailComposeCancelButton, #MailComposeSuccessCloseButton", () => {
            if (typeof WindowManager !== "undefined") {
                WindowManager.CloseWindow("WindowMailCompose");
            }
        });
    },

    SchedulePreviewUpdate: function () {
        if (this.PreviewUpdateTimeoutId) {
            clearTimeout(this.PreviewUpdateTimeoutId);
        }
        this.PreviewUpdateTimeoutId = setTimeout(() => {
            this.UpdateMarkdownPreview();
        }, 150);
    },

    UpdateMarkdownPreview: function () {
        const BodyElement = document.getElementById("MailComposeBody");
        const PreviewPane = document.getElementById("MailPreviewPane");
        if (!BodyElement || !PreviewPane) {
            return;
        }
        const ContentText = BodyElement.value;
        $.ajax({
            url: "/API/Mail/Preview/Partial",
            type: "POST",
            data: { Body: ContentText },
            success: (RenderedHtml) => {
                $("#MailPreviewPane").html(RenderedHtml);
            }
        });
    },

    AttachComposeWindowObserver: function () {
        const WindowElement = document.getElementById("WindowMailCompose");
        if (!WindowElement) {
            return;
        }
        if (this.ComposeResizeObserver) {
            this.ComposeResizeObserver.disconnect();
        }
        const UpdatePaneVisibility = (CurrentWidth) => {
            const PreviewPane = document.getElementById("MailPreviewPane");
            if (PreviewPane) {
                if (CurrentWidth < 600) {
                    PreviewPane.classList.add("HiddenElement");
                } else {
                    PreviewPane.classList.remove("HiddenElement");
                }
            }
        };
        UpdatePaneVisibility(WindowElement.offsetWidth);
        this.ComposeResizeObserver = new ResizeObserver((Entries) => {
            for (let Entry of Entries) {
                const CurrentWidth = Entry.contentRect ? Entry.contentRect.width : WindowElement.offsetWidth;
                UpdatePaneVisibility(CurrentWidth);
            }
        });
        this.ComposeResizeObserver.observe(WindowElement);
    },

    HandleRecipientInput: function (InputElement, ContainerElement) {
        if (!this.EligibleRecipientsCache) {
            this.FetchEligibleRecipients();
            return;
        }
        const RawQuery = InputElement.value.trim();
        const CleanQuery = RawQuery.startsWith("@") ? RawQuery.slice(1).trim() : RawQuery;
        if (CleanQuery.length < 1) {
            this.HidePopover();
            return;
        }
        const TopCandidate = this.FindBestRecipientCandidate(CleanQuery);
        if (TopCandidate) {
            this.ShowPopover(InputElement, ContainerElement, TopCandidate);
        } else {
            this.HidePopover();
        }
    },

    CalculateLevenshteinDistance: function (FirstString, SecondString) {
        const FirstLength = FirstString.length;
        const SecondLength = SecondString.length;
        const DistanceMatrix = [];
        for (let RowIndex = 0; RowIndex <= FirstLength; RowIndex += 1) {
            DistanceMatrix[RowIndex] = [RowIndex];
        }
        for (let ColumnIndex = 0; ColumnIndex <= SecondLength; ColumnIndex += 1) {
            DistanceMatrix[0][ColumnIndex] = ColumnIndex;
        }
        for (let RowIndex = 1; RowIndex <= FirstLength; RowIndex += 1) {
            for (let ColumnIndex = 1; ColumnIndex <= SecondLength; ColumnIndex += 1) {
                const SubstitutionCost = FirstString[RowIndex - 1] === SecondString[ColumnIndex - 1] ? 0 : 1;
                DistanceMatrix[RowIndex][ColumnIndex] = Math.min(
                    DistanceMatrix[RowIndex - 1][ColumnIndex] + 1,
                    DistanceMatrix[RowIndex][ColumnIndex - 1] + 1,
                    DistanceMatrix[RowIndex - 1][ColumnIndex - 1] + SubstitutionCost
                );
            }
        }
        return DistanceMatrix[FirstLength][SecondLength];
    },

    CalculateSimilarityScore: function (QueryString, CandidateString) {
        const NormalizedQuery = QueryString.toLowerCase().trim();
        const NormalizedCandidate = CandidateString.toLowerCase().trim();
        if (NormalizedQuery === NormalizedCandidate) {
            return 1.0;
        }
        if (NormalizedCandidate.startsWith(NormalizedQuery)) {
            return 0.95;
        }
        if (NormalizedCandidate.includes(" " + NormalizedQuery)) {
            return 0.9;
        }
        if (NormalizedCandidate.includes(NormalizedQuery)) {
            return 0.85;
        }
        const MaximumLength = Math.max(NormalizedQuery.length, NormalizedCandidate.length);
        if (MaximumLength === 0) {
            return 1.0;
        }
        const EditDistance = this.CalculateLevenshteinDistance(NormalizedQuery, NormalizedCandidate);
        return 1.0 - (EditDistance / MaximumLength);
    },

    FindBestRecipientCandidate: function (QueryString) {
        if (!this.EligibleRecipientsCache || this.EligibleRecipientsCache.length === 0) {
            return null;
        }
        const CleanQuery = QueryString.toLowerCase().trim();
        let BestCandidate = null;
        let HighestScore = 0.45;

        for (let Index = 0; Index < this.EligibleRecipientsCache.length; Index += 1) {
            const Candidate = this.EligibleRecipientsCache[Index];
            const UsernameScore = this.CalculateSimilarityScore(CleanQuery, Candidate.Username);
            const DisplayNameScore = this.CalculateSimilarityScore(CleanQuery, Candidate.DisplayName);
            const MatchScore = Math.max(UsernameScore, DisplayNameScore);

            if (MatchScore > HighestScore) {
                HighestScore = MatchScore;
                BestCandidate = Candidate;
            }
        }
        return BestCandidate;
    },

    ShowPopover: function (InputElement, ContainerElement, Candidate) {
        this.EnsurePopoverElement();
        this.ActiveInputElement = InputElement;
        this.ActiveTagContainer = ContainerElement;

        const EscapedDisplayName = Candidate.DisplayName.replace(/"/g, "&quot;");
        const EscapedTag = Candidate.FormattedTag.replace(/"/g, "&quot;");
        const EscapedUsername = Candidate.Username.replace(/"/g, "&quot;");

        this.PopoverElement.innerHTML = `Did you mean: <button type="button" class="FuzzySuggestionButton MailFuzzySuggestionButton" data-username="${EscapedUsername}" data-tag="${EscapedTag}">${EscapedDisplayName}</button>?`;
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
        const ReferenceElement = ContainerElement || InputElement;
        const ReferenceRectangle = ReferenceElement.getBoundingClientRect();

        let TargetLeft = (ReferenceRectangle.left - DesktopRectangle.left) * ScaleFactorX;
        let TargetTop = (ReferenceRectangle.bottom - DesktopRectangle.top) * ScaleFactorY + 2;
        const DesktopWidth = DesktopElement ? DesktopElement.offsetWidth : 960;
        const DesktopHeight = DesktopElement ? DesktopElement.offsetHeight : 720;
        TargetLeft = Math.max(0, Math.min(DesktopWidth - 260, TargetLeft));
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
        this.ActiveInputElement = null;
        this.ActiveTagContainer = null;
    },

    AddRecipientTag: function (ContainerElement, FormattedTag) {
        if (!FormattedTag) {
            return;
        }
        const CleanTag = FormattedTag.trim();
        if (!CleanTag) {
            return;
        }
        const TagListElement = ContainerElement.querySelector(".TagList");
        if (!TagListElement) {
            return;
        }
        const ExistingTags = TagListElement.querySelectorAll(".TagItem");
        for (let Index = 0; Index < ExistingTags.length; Index += 1) {
            const ExistingValue = ExistingTags[Index].getAttribute("data-value");
            if (ExistingValue && ExistingValue.toLowerCase() === CleanTag.toLowerCase()) {
                return;
            }
        }

        const TagItem = document.createElement("span");
        TagItem.className = "TagItem";
        TagItem.setAttribute("data-value", CleanTag);

        const TagTextSpan = document.createElement("span");
        TagTextSpan.className = "TagItemText";
        TagTextSpan.textContent = CleanTag;

        const RemoveButton = document.createElement("button");
        RemoveButton.type = "button";
        RemoveButton.className = "TagRemoveButton";
        RemoveButton.setAttribute("aria-label", "Remove " + CleanTag);

        const RemoveIcon = document.createElement("span");
        RemoveIcon.className = "TagRemoveIcon";
        RemoveIcon.setAttribute("aria-hidden", "true");

        RemoveButton.appendChild(RemoveIcon);
        TagItem.appendChild(TagTextSpan);
        TagItem.appendChild(RemoveButton);
        TagListElement.appendChild(TagItem);

        this.UpdateHiddenInputFromTags(ContainerElement);

        const TagTextInput = ContainerElement.querySelector(".TagTextInput");
        if (TagTextInput) {
            TagTextInput.value = "";
        }
    },

    RemoveRecipientTag: function (TagItemElement) {
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
        HiddenInput.value = SerializedValue;
        $(HiddenInput).trigger("change").trigger("input");
    }
};

$(document).ready(() => {
    MailComposeManager.Initialize();
});
