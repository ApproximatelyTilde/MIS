const DesktopApplication = {
    ContextMenuTargetWindow: null,
    PendingSystemAction: null,
    LastDesktopClickTimestamp: 0,
    PointerDownInsideScreen: false,
    PointerDownPositionX: 0,
    PointerDownPositionY: 0,
    ClassRulesDataCache: null,

    Initialize: function () {
        SystemDebugger.LogDebugMessage("Desktop Application Initialized");
        window.DesktopApplication = this;
        this.BindStaticEventListeners();
        this.BindDelegatedEventListeners();
        WorkstationTiltManager.Initialize();
    },

    BindStaticEventListeners: function () {
        const RecordPointerDown = (Event) => {
            let TargetElement = Event.target;
            if (!document.body.contains(TargetElement)) {
                TargetElement = document.elementFromPoint(Event.clientX, Event.clientY);
            }
            this.PointerDownInsideScreen = Boolean($(TargetElement).closest("#DesktopScreenContainer").length > 0);
            this.PointerDownPositionX = Event.clientX;
            this.PointerDownPositionY = Event.clientY;
        };

        document.addEventListener("pointerdown", RecordPointerDown, true);
        document.addEventListener("mousedown", RecordPointerDown, true);

        $(document).on("contextmenu", (Event) => {
            Event.preventDefault();
        });

        $(document).on("click", (Event) => {
            this.HandleViewportInteraction(Event);
            if (!$(Event.target).closest("#DesktopContextMenu").length) {
                this.CloseContextMenu();
            }
            if (!$(Event.target).closest(".LauncherItemParent").length) {
                this.CloseLaunchpadSubmenus();
            }
        });

        $(document).on("keydown", (Event) => {
            if (Event.key === "Escape") {
                if (!$("#SystemConfirmationModalContainer").hasClass("HiddenElement")) {
                    this.CloseSystemConfirmation();
                    return;
                }
                const ActiveLauncherSubmenu = $(".LauncherSubmenu:not(.HiddenElement)");
                if (ActiveLauncherSubmenu.length) {
                    this.CloseLaunchpadSubmenus();
                    return;
                }
                this.CloseContextMenu();
            }
        });

        $(document).on("click", "#DesktopContainer", (Event) => {
            if (typeof SystemBootManager !== "undefined" && !SystemBootManager.IsDesktopUnlocked) {
                return;
            }
            if (WindowManager.IsPlacementActive || WindowManager.JustFinishedPlacement) {
                return;
            }
            if (Event.target.id === "DesktopContainer") {
                const CurrentTimestamp = Date.now();
                const ElapsedMilliseconds = CurrentTimestamp - this.LastDesktopClickTimestamp;
                if (ElapsedMilliseconds <= 500) {
                    this.OpenApplicationLauncherWindow(Event.clientX, Event.clientY);
                    this.LastDesktopClickTimestamp = 0;
                } else {
                    this.LastDesktopClickTimestamp = CurrentTimestamp;
                }
            }
        });

        $(document).on("dblclick", "#DesktopContainer", (Event) => {
            if (typeof SystemBootManager !== "undefined" && !SystemBootManager.IsDesktopUnlocked) {
                return;
            }
            if (WindowManager.IsPlacementActive || WindowManager.JustFinishedPlacement) {
                return;
            }
            if (Event.target.id === "DesktopContainer") {
                this.OpenApplicationLauncherWindow(Event.clientX, Event.clientY);
                this.LastDesktopClickTimestamp = 0;
            }
        });


        $(document).on("contextmenu", "#DesktopContainer", (Event) => {
            if (WindowManager.IsPlacementActive) {
                Event.preventDefault();
                return;
            }
            if (Event.target.id === "DesktopContainer") {
                Event.preventDefault();
                this.OpenContextMenu(Event.clientX, Event.clientY, null);
            }
        });

        $(document).on("contextmenu", ".DesktopWindow", (Event) => {
            if (WindowManager.IsPlacementActive) {
                Event.preventDefault();
                return;
            }
            Event.preventDefault();
            Event.stopPropagation();
            const WindowIdentifier = $(Event.currentTarget).attr("id");
            this.OpenContextMenu(Event.clientX, Event.clientY, WindowIdentifier);
        });

        $(document).on("contextmenu", ".DesktopIconBox", (Event) => {
            if (WindowManager.IsPlacementActive) {
                Event.preventDefault();
                return;
            }
            Event.preventDefault();
            Event.stopPropagation();
            const WindowIdentifier = $(Event.currentTarget).attr("data-window-identifier");
            this.OpenContextMenu(Event.clientX, Event.clientY, WindowIdentifier);
        });
    },

    BindDelegatedEventListeners: function () {
        $(document).on("click", "#ContextMenuButtonToggleIconManager", () => {
            this.ToggleIconManager();
        });

        $(document).on("click", "#ContextMenuButtonIconifyWindow", () => {
            this.IconifyContextTargetWindow();
        });

        $(document).on("click", "#ContextMenuButtonRaiseWindow", () => {
            this.RaiseContextTargetWindow();
        });

        $(document).on("click", "#ContextMenuButtonLowerWindow", () => {
            this.LowerContextTargetWindow();
        });

        $(document).on("click", "#ContextMenuButtonDeleteWindow", () => {
            this.DeleteContextTargetWindow();
        });

        $(document).on("click", "#SystemConfirmationButtonCancel", () => {
            this.CloseSystemConfirmation();
        });

        $(document).on("click", "#SystemConfirmationButtonJoin", () => {
            this.HandleJoinServerClick();
        });

        $(document).on("click", "#SystemConfirmationButtonConfirm", () => {
            this.ConfirmPendingSystemAction();
        });

        $(document).on("click", "#LauncherButtonAccountCentre", function () {
            DesktopApplication.OpenAccountCentreWindow();
        });

        $(document).on("click", "#LauncherButtonDiceRoller", function () {
            DesktopApplication.CloseLaunchpadToolsSubmenu();
            DesktopApplication.OpenDiceRollerWindow();
        });

        $(document).on("click", "#LauncherButtonNPCGenerator", function () {
            DesktopApplication.CloseLaunchpadToolsSubmenu();
            if (!DesktopApplication.HasGameMasterRole()) {
                DesktopApplication.ShowPermissionDeniedAlert("You do not have the Game Master role required to use the NPC Generator.");
                return;
            }
            DesktopApplication.OpenNPCGeneratorWindow();
        });

        $(document).on("click", "#LauncherButtonCharacterGenerator", function () {
            DesktopApplication.CloseLaunchpadToolsSubmenu();
            DesktopApplication.OpenCharacterGeneratorWindow();
        });

        $(document).on("click", "#LauncherButtonCalendar", function () {
            DesktopApplication.OpenCalendarWindow();
        });

        $(document).on("click", "#LauncherButtonStorage", function () {
            DesktopApplication.OpenStorageWindow();
        });

        $(document).on("click", "#LauncherButtonDeleteWindow", function () {
            WindowManager.DeleteTargetWindow();
        });

        $(document).on("click", ".AccountTabButton", function () {
            const TargetTab = $(this).attr("data-target-tab");
            DesktopApplication.SwitchAccountTab(TargetTab, this);
        });

        $(document).on("click", ".CalendarTabButton", function () {
            const TargetTab = $(this).attr("data-target-tab");
            DesktopApplication.SwitchCalendarTab(TargetTab, this);
        });

        $(document).on("click", ".CharacterGeneratorTabButton", function () {
            const TargetTab = $(this).attr("data-target-tab");
            DesktopApplication.SwitchCharacterGeneratorTab(TargetTab, this);
        });

        $(document).on("click", ".EditCharacterButton", function () {
            const CharacterIdentifier = $(this).attr("data-character-identifier");
            DesktopApplication.EditCharacter(CharacterIdentifier);
        });

        $(document).on("click", ".OpenCharacterGeneratorButton", function () {
            DesktopApplication.OpenCharacterSheetWindow("DND5thEdition");
        });

        $(document).on("click", ".CharacterSheetTabButton", function () {
            const TargetTab = $(this).attr("data-target-tab");
            DesktopApplication.SwitchCharacterSheetTab(TargetTab, this);
        });

        $(document).on("click", "#CharacterPortraitUploadTriggerButton, #CharacterPortraitBoxTrigger", function () {
            DesktopApplication.OpenPortraitAssetPickerWindow();
        });

        $(document).on("click", "#PortraitPickerUploadButton", function () {
            if (!DesktopApplication.IsUserInGuild()) {
                DesktopApplication.ShowGuildMembershipWarning();
                return;
            }
            const PickerFileInput = document.getElementById("PortraitPickerFileInput");
            if (PickerFileInput) {
                PickerFileInput.click();
            }
        });

        $(document).on("input change", "#CharacterSheetCreationForm", function () {
            DesktopApplication.EvaluateCharacterSheetDirtyState();
        });

        $(document).on("input change", "textarea", function () {
            DesktopApplication.AutoResizeTextarea(this);
        });

        document.body.addEventListener("characterSaved", function (Event) {
            DesktopApplication.HandleCharacterSavedEvent(Event);
        });

        document.body.addEventListener("portraitSelected", function () {
            DesktopApplication.HandlePortraitSelectedEvent();
        });

        document.body.addEventListener("htmx:afterSwap", function (Event) {
            if ($(Event.target).closest("#WindowCharacterSheet").length > 0) {
                DesktopApplication.InitializeCharacterSheetBaseline();
                DesktopApplication.InitializeAbilitiesTab(Event.target);
                DesktopApplication.EvaluateCharacterSheetDirtyState();
                DesktopApplication.InitializeAutoResizeTextareas(Event.target);
            }
        });

        $(document).on("click", ".AddClassButton", function () {
            DesktopApplication.AddClassContainer();
        });

        $(document).on("click", ".ClassStarButton", function () {
            const ContainerElement = $(this).closest(".ClassContainer")[0];
            if (ContainerElement) {
                DesktopApplication.SetInitialClass(ContainerElement);
            }
        });

        $(document).on("click", ".ClassDeleteButton", function () {
            const ContainerElement = $(this).closest(".ClassContainer")[0];
            if (ContainerElement) {
                DesktopApplication.DeleteClassContainer(ContainerElement);
            }
        });

        $(document).on("input change", ".ClassInputLevel, .ClassInputExperience", function () {
            DesktopApplication.HandleClassFieldChange(this);
        });

        $(document).on("input change", ".ClassInputName, .ClassInputSubclass", function () {
            DesktopApplication.UpdateSpellSlotsFromClasses();
            DesktopApplication.UpdateSpellcastingAbilityFromInitialClass();
        });

        $(document).on("click", ".CreateSpellListButton", function () {
            DesktopApplication.OpenCreateSpellListModal();
        });

        $(document).on("click", "#ModalSpellListCancelButton", function () {
            DesktopApplication.CloseCreateSpellListModal();
        });

        $(document).on("click", "#ModalSpellListConfirmButton", function () {
            DesktopApplication.ConfirmCreateSpellListModal();
        });

        $(document).on("keydown", "#ModalSpellListNameInput", function (Event) {
            if (Event.key === "Enter") {
                Event.preventDefault();
                DesktopApplication.ConfirmCreateSpellListModal();
            } else if (Event.key === "Escape") {
                Event.preventDefault();
                DesktopApplication.CloseCreateSpellListModal();
            }
        });

        $(document).on("click", ".DeleteSpellListButton", function (Event) {
            const ListContainer = $(this).closest(".SpellListContainer")[0];
            if (ListContainer) {
                DesktopApplication.DeleteSpellList(ListContainer, Event.shiftKey);
            }
        });

        $(document).on("click", ".AddSpellButton", function () {
            const NameInput = document.getElementById("NewSpellNameInput");
            const TargetSelect = document.getElementById("NewSpellTargetListSelect");
            if (NameInput && NameInput.value.trim()) {
                const SpellName = NameInput.value.trim();
                const TargetList = TargetSelect ? TargetSelect.value : "Spellbook";
                DesktopApplication.AddSpellToList(SpellName, TargetList);
                NameInput.value = "";
            }
        });

        $(document).on("click", ".RemoveSpellButton", function () {
            const SpellEntry = $(this).closest(".SpellListSpellEntry")[0];
            if (SpellEntry) {
                DesktopApplication.RemoveSpellFromList(SpellEntry);
            }
        });

        $(document).on("change", ".SpellListAbilitySelect", function () {
            const ListContainer = $(this).closest(".SpellListContainer")[0];
            if (ListContainer) {
                ListContainer.setAttribute("data-custom-list", "true");
                DesktopApplication.RecalculateSpellListStats(ListContainer);
            }
        });

        $(document).on("click", "#CharacterSheetOverrideButton, #CharacterSheetProtectButton", function () {
            $(this).toggleClass("ButtonActive");
        });

        $(document).on("input change", ".CharacterSheetAbilityInput, #CharacterSheetProficiencyBonusInput", function () {
            DesktopApplication.RecalculateAllSpellListStats();
        });

        $(document).on("click", ".SpellSlotIcon", function () {
            DesktopApplication.ToggleSpellSlot(this);
        });

        $(document).on("click", ".SkillProficiencyIcon", function () {
            const SkillName = $(this).attr("data-skill-name");
            let CurrentState = parseInt($(this).attr("data-proficiency-state") || "0", 10);
            CurrentState = (CurrentState + 1) % 3;
            $(this).attr("data-proficiency-state", CurrentState.toString());

            const HiddenInput = document.querySelector('input[name="SkillProficiency' + SkillName + '"]');
            if (HiddenInput) {
                HiddenInput.value = CurrentState.toString();
            }
        });

        $(document).on("change", "#CharacterGeneratorSystemSelect", function () {
            DesktopApplication.UpdateCharacterGeneratorControls();
        });

        $(document).on("click", "#CharacterGeneratorRandomNameButton", function () {
            DesktopApplication.RandomizeCharacterName();
        });

        $(document).on("change", "#DiceSystemSelect", function () {
            DesktopApplication.UpdateDiceControls();
        });

        $(document).on("change", "#StorageFileInput", function () {
            DesktopApplication.SubmitStorageUpload();
        });

        $(document).on("click", "#StorageUploadTriggerButton", function () {
            if (!DesktopApplication.IsUserInGuild()) {
                DesktopApplication.ShowGuildMembershipWarning();
                return;
            }
            $("#StorageFileInput").trigger("click");
        });

        $(document).on("mouseenter", "#LauncherParentCharacters", () => {
            this.OpenLaunchpadCharactersSubmenu();
        });

        $(document).on("mouseleave", "#LauncherParentCharacters", () => {
            this.CloseLaunchpadCharactersSubmenu();
        });

        $(document).on("click", "#LauncherButtonToggleCharacters", (Event) => {
            Event.stopPropagation();
            this.ToggleLaunchpadCharacters();
        });

        $(document).on("mouseenter", "#LauncherParentCharactersNew", () => {
            this.OpenLaunchpadCharactersNewSubmenu();
        });

        $(document).on("mouseleave", "#LauncherParentCharactersNew", () => {
            this.CloseLaunchpadCharactersNewSubmenu();
        });

        $(document).on("click", "#LauncherButtonToggleCharactersNew", (Event) => {
            Event.stopPropagation();
            this.ToggleLaunchpadCharactersNew();
        });

        $(document).on("click", "#LauncherButtonNewCharacterDND5thEdition", () => {
            this.CloseLaunchpadSubmenus();
            this.OpenCharacterSheetWindow("DND5thEdition");
        });

        $(document).on("click", "#LauncherButtonNewCharacterTraveller2ndEdition", () => {
            this.CloseLaunchpadSubmenus();
            this.OpenCharacterSheetWindow("Traveller2ndEdition");
        });

        $(document).on("mouseenter", "#LauncherParentTools", () => {
            this.OpenLaunchpadToolsSubmenu();
        });

        $(document).on("mouseleave", "#LauncherParentTools", () => {
            this.CloseLaunchpadToolsSubmenu();
        });

        $(document).on("click", "#LauncherButtonToggleTools", (Event) => {
            Event.stopPropagation();
            this.ToggleLaunchpadTools();
        });

        $(document).on("mouseenter", "#LauncherParentSystem", () => {
            this.OpenLaunchpadSystemSubmenu();
        });

        $(document).on("mouseleave", "#LauncherParentSystem", () => {
            this.CloseLaunchpadSystemSubmenu();
        });

        $(document).on("click", "#LauncherButtonToggleSystem", (Event) => {
            Event.stopPropagation();
            this.ToggleLaunchpadSystem();
        });

        $(document).on("click", "#LauncherButtonRestartSystem", () => {
            this.CloseLaunchpadSubmenus();
            this.ShowSystemConfirmation("Restart");
        });

        $(document).on("click", "#LauncherButtonExitSystem", () => {
            this.CloseLaunchpadSubmenus();
            this.ShowSystemConfirmation("Exit");
        });

        if (window.htmx && htmx.onLoad) {
            htmx.onLoad(() => {
                this.AdjustCharacterCardNames();
            });
        }

        document.addEventListener("htmx:after:swap", () => {
            this.AdjustCharacterCardNames();
        });

        document.addEventListener("htmx:after:settle", () => {
            this.AdjustCharacterCardNames();
        });

        document.addEventListener("htmx:afterSwap", () => {
            this.AdjustCharacterCardNames();
        });

        document.addEventListener("htmx:load", () => {
            this.AdjustCharacterCardNames();
        });

        const CharacterObserver = new MutationObserver((Mutations) => {
            let HasNewCards = false;
            for (const Mutation of Mutations) {
                if (Mutation.type === "childList") {
                    for (const Node of Mutation.addedNodes) {
                        if (Node.nodeType === 1 && (Node.classList?.contains("EntityCard") || Node.querySelector?.(".EntityCard"))) {
                            HasNewCards = true;
                            break;
                        }
                    }
                }
                if (HasNewCards) {
                    break;
                }
            }
            if (HasNewCards) {
                this.AdjustCharacterCardNames();
            }
        });

        const DesktopRoot = document.getElementById("DesktopContainer") || document.body;
        if (DesktopRoot) {
            CharacterObserver.observe(DesktopRoot, {
                childList: true,
                subtree: true
            });
        }

        $(window).on("resize", () => {
            this.AdjustCharacterCardNames();
        });

        if (document.fonts && document.fonts.ready) {
            document.fonts.ready.then(() => {
                this.AdjustCharacterCardNames();
            });
        }
    },

    OpenContextMenu: function (ClickX, ClickY, TargetWindowIdentifier) {
        if (!$("#SystemConfirmationModalContainer").hasClass("HiddenElement")) {
            return;
        }
        this.CloseLaunchpadSubmenus();
        this.ContextMenuTargetWindow = TargetWindowIdentifier || WindowManager.LastActiveClientWindow;
        const TargetWindowElement = TargetWindowIdentifier ? $(`#${TargetWindowIdentifier}`) : null;
        if (TargetWindowElement && TargetWindowElement.hasClass("MinimizedWindow")) {
            $("#ContextMenuTitleIconifyWindow").text("De-iconify Window");
        } else {
            $("#ContextMenuTitleIconifyWindow").text("Iconify Window");
        }
        const LauncherElement = $("#WindowApplicationLauncher");
        const IsLauncherOpen = LauncherElement.length > 0 && LauncherElement.is(":visible");
        if (IsLauncherOpen) {
            $("#ContextMenuTitleToggleIconManager").text("Hide Launchpad");
        } else {
            $("#ContextMenuTitleToggleIconManager").text("Show Launchpad");
        }
        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            left: 0,
            top: 0,
            width: 800,
            height: 600
        };
        const ScaleFactorX = DesktopElement ? DesktopElement.offsetWidth / (DesktopRectangle.width || 1) : 1;
        const ScaleFactorY = DesktopElement ? DesktopElement.offsetHeight / (DesktopRectangle.height || 1) : 1;
        let TargetLeft = (ClickX - DesktopRectangle.left) * ScaleFactorX;
        let TargetTop = (ClickY - DesktopRectangle.top) * ScaleFactorY;
        const DesktopWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
        const DesktopHeight = DesktopElement ? DesktopElement.offsetHeight : 600;
        TargetLeft = Math.max(0, Math.min(DesktopWidth - 200, TargetLeft));
        TargetTop = Math.max(0, Math.min(DesktopHeight - 220, TargetTop));
        TargetLeft = Math.round(TargetLeft / 4) * 4;
        TargetTop = Math.round(TargetTop / 4) * 4;
        const MenuElement = $("#DesktopContextMenu");
        MenuElement.css({
            "left": `${TargetLeft}px`,
            "top": `${TargetTop}px`
        });
        MenuElement.removeClass("HiddenElement");
        SystemDebugger.LogDebugMessage("Context Menu Opened: Target='" + (this.ContextMenuTargetWindow || "Desktop") + "' (" + TargetLeft + "," + TargetTop + ")");
    },

    CloseContextMenu: function () {
        const ContextMenuElement = $("#DesktopContextMenu");
        if (ContextMenuElement.length > 0 && !ContextMenuElement.hasClass("HiddenElement")) {
            SystemDebugger.LogDebugMessage("Context Menu Closed");
            ContextMenuElement.addClass("HiddenElement");
        }
    },

    ShowGuildMembershipWarning: function () {
        SystemDebugger.LogDebugMessage("Guild Membership Warning Displayed");
        this.PendingSystemAction = "GuildMembershipWarning";
        const TitleElement = $("#SystemConfirmationTitle");
        const MessageElement = $("#SystemConfirmationMessage");
        const ConfirmButtonLabel = $("#SystemConfirmationButtonConfirmLabel");
        const ConfirmButton = $("#SystemConfirmationButtonConfirm");
        const CancelButton = $("#SystemConfirmationButtonCancel");
        const JoinButton = $("#SystemConfirmationButtonJoin");

        TitleElement.text("Server Membership Required");
        MessageElement.empty();
        MessageElement.append(document.createTextNode("You are authenticated, but you are not in the "));

        const ServerNameElement = document.createElement("span");
        ServerNameElement.className = "ConfirmationUnderlineText";
        ServerNameElement.textContent = "[18+] Analogue Fantasies";
        MessageElement.append(ServerNameElement);

        MessageElement.append(document.createTextNode(" server."));

        CancelButton.addClass("HiddenElement");
        JoinButton.removeClass("HiddenElement");
        ConfirmButton.removeClass("ButtonPrimary ButtonDanger");
        ConfirmButtonLabel.text("No, Thanks");

        $("#SystemConfirmationModalContainer").removeClass("HiddenElement");
        JoinButton.trigger("focus");
    },

    HandleJoinServerClick: function () {
        let DiscordInviteURL = "";
        if (typeof SystemBootManager !== "undefined" && SystemBootManager.CurrentDiscordInviteURL) {
            DiscordInviteURL = SystemBootManager.CurrentDiscordInviteURL;
        }
        else {
            DiscordInviteURL = sessionStorage.getItem("CurrentDiscordInviteURL") || "";
        }
        SystemDebugger.LogDebugMessage("Join Server Invoked: URL='" + (DiscordInviteURL || "None") + "'");
        if (DiscordInviteURL) {
            window.open(DiscordInviteURL, "_blank", "noopener,noreferrer");
        }
        this.CloseSystemConfirmation();
    },

    HasGameMasterRole: function () {
        let UserRole = null;
        let UserRoles = [];
        if (typeof SystemBootManager !== "undefined" && SystemBootManager.CurrentAuthenticatedRole) {
            UserRole = SystemBootManager.CurrentAuthenticatedRole;
            UserRoles = SystemBootManager.CurrentAuthenticatedRoles || [];
        } else {
            UserRole = sessionStorage.getItem("CurrentAuthenticatedRole");
            const SerializedRoles = sessionStorage.getItem("CurrentAuthenticatedRoles");
            if (SerializedRoles) {
                try {
                    UserRoles = JSON.parse(SerializedRoles);
                }
                catch {
                    UserRoles = [];
                }
            }
        }
        if (UserRole === "Administrator" || UserRole === "GameMaster") {
            return true;
        }
        const PermittedRoles = ["Administrator", "GameMaster", "Story Manager"];
        if (Array.isArray(UserRoles)) {
            for (let Index = 0; Index < UserRoles.length; Index++) {
                if (PermittedRoles.includes(UserRoles[Index])) {
                    return true;
                }
            }
        }
        return false;
    },

    IsUserInGuild: function () {
        if (typeof SystemBootManager !== "undefined" && typeof SystemBootManager.CurrentAuthenticatedIsInGuild === "boolean") {
            return SystemBootManager.CurrentAuthenticatedIsInGuild;
        }
        const GuildMembershipStored = sessionStorage.getItem("CurrentAuthenticatedIsInGuild");
        return GuildMembershipStored === "true";
    },

    ShowPermissionDeniedAlert: function (Message) {
        if (Message && Message.includes("Server membership")) {
            this.ShowGuildMembershipWarning();
            return;
        }
        SystemDebugger.LogDebugMessage("Permission Denied Displayed: Message='" + Message + "'");
        this.PendingSystemAction = "PermissionDeniedAlert";
        const TitleElement = $("#SystemConfirmationTitle");
        const MessageElement = $("#SystemConfirmationMessage");
        const ConfirmButtonLabel = $("#SystemConfirmationButtonConfirmLabel");
        const ConfirmButton = $("#SystemConfirmationButtonConfirm");
        const CancelButton = $("#SystemConfirmationButtonCancel");

        $("#SystemConfirmationButtonJoin").addClass("HiddenElement");
        TitleElement.text("Access Restricted");
        MessageElement.text(Message);
        ConfirmButtonLabel.text("Acknowledge");
        ConfirmButton.removeClass("ButtonDanger").addClass("ButtonPrimary");
        CancelButton.addClass("HiddenElement");

        $("#SystemConfirmationModalContainer").removeClass("HiddenElement");
        ConfirmButton.trigger("focus");
    },

    ShowSystemConfirmation: function (ActionType) {
        SystemDebugger.LogDebugMessage("System Confirmation Displayed: Action='" + ActionType + "'");
        this.PendingSystemAction = ActionType;
        const TitleElement = $("#SystemConfirmationTitle");
        const MessageElement = $("#SystemConfirmationMessage");
        const ConfirmButtonLabel = $("#SystemConfirmationButtonConfirmLabel");
        const ConfirmButton = $("#SystemConfirmationButtonConfirm");
        const CancelButton = $("#SystemConfirmationButtonCancel");

        $("#SystemConfirmationButtonJoin").addClass("HiddenElement");
        CancelButton.removeClass("HiddenElement");
        if (ActionType === "Restart") {
            TitleElement.text("System Restart");
            MessageElement.text("Restart Marten's Information System?\nAny unsaved data will be lost!");
            ConfirmButtonLabel.text("Restart");
            ConfirmButton.removeClass("ButtonDanger").addClass("ButtonPrimary");
        } else if (ActionType === "Exit") {
            TitleElement.text("Exit to Console");
            MessageElement.text("Exit Marten's Information System?");
            ConfirmButtonLabel.text("Exit");
            ConfirmButton.removeClass("ButtonPrimary").addClass("ButtonDanger");
        }

        $("#SystemConfirmationModalContainer").removeClass("HiddenElement");
        $("#SystemConfirmationButtonConfirm").trigger("focus");
    },

    CloseSystemConfirmation: function () {
        SystemDebugger.LogDebugMessage("System Confirmation Closed: Action='" + (this.PendingSystemAction || "None") + "'");
        if (this.PendingSystemAction === "GuildMembershipWarning") {
            sessionStorage.setItem("GuildMembershipWarningDismissed", "true");
        }
        this.PendingSystemAction = null;
        $("#SystemConfirmationButtonCancel").removeClass("HiddenElement");
        $("#SystemConfirmationButtonJoin").addClass("HiddenElement");
        $("#SystemConfirmationButtonConfirm").removeClass("ButtonPrimary ButtonDanger");
        $("#SystemConfirmationButtonConfirmLabel").text("Confirm");
        $("#SystemConfirmationModalContainer").addClass("HiddenElement");
    },

    ConfirmPendingSystemAction: function () {
        SystemDebugger.LogDebugMessage("System Action Confirmed: Action='" + (this.PendingSystemAction || "None") + "'");
        const ActionToExecute = this.PendingSystemAction;
        this.CloseSystemConfirmation();
        if (ActionToExecute === "Restart") {
            SystemBootManager.RestartSystem();
        } else if (ActionToExecute === "Exit") {
            SystemBootManager.ExitToTeletype();
        }
    },

    ToggleIconManager: function () {
        this.CloseContextMenu();
        this.CloseLaunchpadSubmenus();
        const LauncherElement = $("#WindowApplicationLauncher");
        const IsLauncherOpen = LauncherElement.length > 0 && LauncherElement.is(":visible");
        SystemDebugger.LogDebugMessage("Launchpad Toggled: Open=" + (!IsLauncherOpen));
        if (IsLauncherOpen) {
            WindowManager.CloseWindow("WindowApplicationLauncher");
        } else {
            this.OpenApplicationLauncherWindow();
        }
    },

    IconifyContextTargetWindow: function () {
        this.CloseContextMenu();
        const TargetIdentifier = this.ContextMenuTargetWindow || WindowManager.LastActiveClientWindow;
        SystemDebugger.LogDebugMessage("Window Iconify Toggled: Target='" + (TargetIdentifier || "None") + "'");
        if (TargetIdentifier) {
            const WindowElement = $(`#${TargetIdentifier}`);
            if (WindowElement.hasClass("MinimizedWindow")) {
                WindowManager.RestoreWindow(TargetIdentifier);
            } else {
                WindowManager.MinimizeWindow(TargetIdentifier);
            }
        }
    },

    RaiseContextTargetWindow: function () {
        this.CloseContextMenu();
        const TargetIdentifier = this.ContextMenuTargetWindow || WindowManager.LastActiveClientWindow;
        SystemDebugger.LogDebugMessage("Window Raised: Target='" + (TargetIdentifier || "None") + "'");
        if (TargetIdentifier) {
            const WindowElement = $(`#${TargetIdentifier}`);
            if (WindowElement.hasClass("MinimizedWindow")) {
                WindowManager.RestoreWindow(TargetIdentifier);
            } else {
                WindowManager.FocusWindow(TargetIdentifier);
            }
        }
    },

    LowerContextTargetWindow: function () {
        this.CloseContextMenu();
        const TargetIdentifier = this.ContextMenuTargetWindow || WindowManager.LastActiveClientWindow;
        SystemDebugger.LogDebugMessage("Window Lowered: Target='" + (TargetIdentifier || "None") + "'");
        if (TargetIdentifier) {
            WindowManager.LowerWindow(TargetIdentifier);
        }
    },

    DeleteContextTargetWindow: function () {
        this.CloseContextMenu();
        const TargetIdentifier = this.ContextMenuTargetWindow || WindowManager.LastActiveClientWindow;
        SystemDebugger.LogDebugMessage("Window Deleted: Target='" + (TargetIdentifier || "Active") + "'");
        if (TargetIdentifier) {
            WindowManager.CloseWindow(TargetIdentifier);
        } else {
            WindowManager.DeleteTargetWindow();
        }
    },

    OpenApplicationLauncherWindow: function (ClickX, ClickY) {
        this.ZoomIntoScreen();
        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            left: 0,
            top: 0,
            width: 800,
            height: 600
        };
        const ScaleFactorX = DesktopElement ? DesktopElement.offsetWidth / (DesktopRectangle.width || 1) : 1;
        const ScaleFactorY = DesktopElement ? DesktopElement.offsetHeight / (DesktopRectangle.height || 1) : 1;
        let TargetLeft = 24;
        let TargetTop = 24;
        if (ClickX !== undefined && ClickY !== undefined) {
            TargetLeft = (ClickX - DesktopRectangle.left) * ScaleFactorX;
            TargetTop = (ClickY - DesktopRectangle.top) * ScaleFactorY;
            const DesktopWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
            const DesktopHeight = DesktopElement ? DesktopElement.offsetHeight : 600;
            TargetLeft = Math.max(0, Math.min(DesktopWidth - 200, TargetLeft));
            TargetTop = Math.max(0, Math.min(DesktopHeight - 236, TargetTop));
            TargetLeft = Math.round(TargetLeft / 4) * 4;
            TargetTop = Math.round(TargetTop / 4) * 4;
        }
        SystemDebugger.LogDebugMessage("Application Launcher Opened: Pos=" + TargetLeft + "," + TargetTop);
        const LauncherElement = $("#WindowApplicationLauncher");
        if (LauncherElement.length) {
            if (ClickX !== undefined && ClickY !== undefined) {
                LauncherElement.css({
                    "left": `${TargetLeft}px`,
                    "top": `${TargetTop}px`
                });
            }
            WindowManager.RestoreWindow("WindowApplicationLauncher");
            WindowManager.FocusWindow("WindowApplicationLauncher");
            return;
        }
        const Config = {
            Identifier: "WindowApplicationLauncher",
            Title: "Launchpad",
            Width: 200,
            Height: 236,
            MinWidth: 200,
            MinHeight: 236,
            Left: TargetLeft,
            Top: TargetTop,
            ContentURL: "/API/Desktop/Windows/ApplicationLauncher",
            BypassPlacement: true
        };
        WindowManager.OpenWindow(Config);
    },

    OpenLaunchpadCharactersSubmenu: function () {
        SystemDebugger.LogDebugMessage("Launchpad Submenu Opened: Characters");
        this.CloseLaunchpadToolsSubmenu();
        this.CloseLaunchpadSystemSubmenu();
        const LauncherWindow = $("#WindowApplicationLauncher");
        const SubmenuElement = $("#LauncherCharactersSubmenu");
        if (!LauncherWindow.length || !SubmenuElement.length) {
            return;
        }
        if (typeof WindowManager !== "undefined") {
            WindowManager.FocusWindow("WindowApplicationLauncher");
        }
        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            width: 800
        };
        const WindowOffset = LauncherWindow.position();
        const WindowWidth = LauncherWindow.outerWidth() || 200;
        const SubmenuWidth = 180;
        if (WindowOffset && (WindowOffset.left + WindowWidth + SubmenuWidth > DesktopRectangle.width)) {
            SubmenuElement.addClass("LauncherSubmenuLeft");
        } else {
            SubmenuElement.removeClass("LauncherSubmenuLeft");
        }
        SubmenuElement.removeClass("HiddenElement");
    },

    CloseLaunchpadCharactersSubmenu: function () {
        const SubmenuElement = $("#LauncherCharactersSubmenu");
        if (SubmenuElement.length > 0 && !SubmenuElement.hasClass("HiddenElement")) {
            SystemDebugger.LogDebugMessage("Launchpad Submenu Closed: Characters");
            SubmenuElement.addClass("HiddenElement");
            this.CloseLaunchpadCharactersNewSubmenu();
        }
    },

    ToggleLaunchpadCharacters: function () {
        const SubmenuElement = $("#LauncherCharactersSubmenu");
        if (SubmenuElement.hasClass("HiddenElement")) {
            this.OpenLaunchpadCharactersSubmenu();
        } else {
            this.CloseLaunchpadCharactersSubmenu();
        }
    },

    OpenLaunchpadCharactersNewSubmenu: function () {
        SystemDebugger.LogDebugMessage("Launchpad Submenu Opened: CharactersNew");
        const ParentSubmenu = $("#LauncherCharactersSubmenu");
        const SubmenuElement = $("#LauncherCharactersNewSubmenu");
        if (!ParentSubmenu.length || !SubmenuElement.length) {
            return;
        }
        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            width: 800
        };
        const SubmenuOffset = ParentSubmenu.offset();
        const SubmenuWidth = 180;
        if (ParentSubmenu.hasClass("LauncherSubmenuLeft") || (SubmenuOffset && (SubmenuOffset.left + SubmenuWidth + SubmenuWidth > DesktopRectangle.width))) {
            SubmenuElement.addClass("LauncherSubmenuLeft");
        } else {
            SubmenuElement.removeClass("LauncherSubmenuLeft");
        }
        SubmenuElement.removeClass("HiddenElement");
    },

    CloseLaunchpadCharactersNewSubmenu: function () {
        const SubmenuElement = $("#LauncherCharactersNewSubmenu");
        if (SubmenuElement.length > 0 && !SubmenuElement.hasClass("HiddenElement")) {
            SystemDebugger.LogDebugMessage("Launchpad Submenu Closed: CharactersNew");
            SubmenuElement.addClass("HiddenElement");
        }
    },

    ToggleLaunchpadCharactersNew: function () {
        const SubmenuElement = $("#LauncherCharactersNewSubmenu");
        if (SubmenuElement.hasClass("HiddenElement")) {
            this.OpenLaunchpadCharactersNewSubmenu();
        } else {
            this.CloseLaunchpadCharactersNewSubmenu();
        }
    },

    OpenLaunchpadToolsSubmenu: function () {
        SystemDebugger.LogDebugMessage("Launchpad Submenu Opened: Tools");
        this.CloseLaunchpadCharactersSubmenu();
        this.CloseLaunchpadSystemSubmenu();
        const LauncherWindow = $("#WindowApplicationLauncher");
        const SubmenuElement = $("#LauncherToolsSubmenu");
        if (!LauncherWindow.length || !SubmenuElement.length) {
            return;
        }
        if (typeof WindowManager !== "undefined") {
            WindowManager.FocusWindow("WindowApplicationLauncher");
        }
        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            width: 800
        };
        const WindowOffset = LauncherWindow.position();
        const WindowWidth = LauncherWindow.outerWidth() || 200;
        const SubmenuWidth = 180;
        if (WindowOffset && (WindowOffset.left + WindowWidth + SubmenuWidth > DesktopRectangle.width)) {
            SubmenuElement.addClass("LauncherSubmenuLeft");
        } else {
            SubmenuElement.removeClass("LauncherSubmenuLeft");
        }
        SubmenuElement.removeClass("HiddenElement");
    },

    CloseLaunchpadToolsSubmenu: function () {
        const SubmenuElement = $("#LauncherToolsSubmenu");
        if (SubmenuElement.length > 0 && !SubmenuElement.hasClass("HiddenElement")) {
            SystemDebugger.LogDebugMessage("Launchpad Submenu Closed: Tools");
            SubmenuElement.addClass("HiddenElement");
        }
    },

    ToggleLaunchpadTools: function () {
        const SubmenuElement = $("#LauncherToolsSubmenu");
        if (SubmenuElement.hasClass("HiddenElement")) {
            this.OpenLaunchpadToolsSubmenu();
        } else {
            this.CloseLaunchpadToolsSubmenu();
        }
    },

    OpenLaunchpadSystemSubmenu: function () {
        SystemDebugger.LogDebugMessage("Launchpad Submenu Opened: System");
        this.CloseLaunchpadCharactersSubmenu();
        this.CloseLaunchpadToolsSubmenu();
        const LauncherWindow = $("#WindowApplicationLauncher");
        const SubmenuElement = $("#LauncherSystemSubmenu");
        if (!LauncherWindow.length || !SubmenuElement.length) {
            return;
        }
        if (typeof WindowManager !== "undefined") {
            WindowManager.FocusWindow("WindowApplicationLauncher");
        }
        const DesktopElement = document.getElementById("DesktopContainer");
        const DesktopRectangle = DesktopElement ? DesktopElement.getBoundingClientRect() : {
            width: 800
        };
        const WindowOffset = LauncherWindow.position();
        const WindowWidth = LauncherWindow.outerWidth() || 200;
        const SubmenuWidth = 180;
        if (WindowOffset && (WindowOffset.left + WindowWidth + SubmenuWidth > DesktopRectangle.width)) {
            SubmenuElement.addClass("LauncherSubmenuLeft");
        } else {
            SubmenuElement.removeClass("LauncherSubmenuLeft");
        }
        SubmenuElement.removeClass("HiddenElement");
    },

    CloseLaunchpadSystemSubmenu: function () {
        const SubmenuElement = $("#LauncherSystemSubmenu");
        if (SubmenuElement.length > 0 && !SubmenuElement.hasClass("HiddenElement")) {
            SystemDebugger.LogDebugMessage("Launchpad Submenu Closed: System");
            SubmenuElement.addClass("HiddenElement");
        }
    },

    ToggleLaunchpadSystem: function () {
        const SubmenuElement = $("#LauncherSystemSubmenu");
        if (SubmenuElement.hasClass("HiddenElement")) {
            this.OpenLaunchpadSystemSubmenu();
        } else {
            this.CloseLaunchpadSystemSubmenu();
        }
    },

    CloseLaunchpadSubmenus: function () {
        const ToolsSubmenu = $("#LauncherToolsSubmenu");
        const SystemSubmenu = $("#LauncherSystemSubmenu");
        const CharactersSubmenu = $("#LauncherCharactersSubmenu");
        const ToolsSubmenuOpen = ToolsSubmenu.length > 0 && !ToolsSubmenu.hasClass("HiddenElement");
        const SystemSubmenuOpen = SystemSubmenu.length > 0 && !SystemSubmenu.hasClass("HiddenElement");
        const CharactersSubmenuOpen = CharactersSubmenu.length > 0 && !CharactersSubmenu.hasClass("HiddenElement");
        if (ToolsSubmenuOpen || SystemSubmenuOpen || CharactersSubmenuOpen) {
            SystemDebugger.LogDebugMessage("Launchpad Submenus Closed: All");
            this.CloseLaunchpadToolsSubmenu();
            this.CloseLaunchpadSystemSubmenu();
            this.CloseLaunchpadCharactersSubmenu();
        }
    },

    OpenAccountCentreWindow: function () {
        SystemDebugger.LogDebugMessage("Account Centre Window Opened: Width=1140, Height=560");
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowAccountCentre",
            Title: "Account Centre",
            Width: 1140,
            Height: 560,
            MinWidth: 380,
            MinHeight: 260,
            Left: 20,
            Top: 20,
            ContentURL: "/API/Desktop/Windows/AccountCentre"
        };
        WindowManager.OpenWindow(Config);
    },

    IsAdjustingNames: false,

    AdjustCharacterCardNames: function () {
        if (this.IsAdjustingNames) {
            return;
        }
        this.IsAdjustingNames = true;
        try {
            const NameElements = document.querySelectorAll(".CharacterCardName");
            SystemDebugger.LogDebugMessage("Character Card Names Adjusted: Count=" + NameElements.length);
            NameElements.forEach(Element => {
                const FullName = Element.getAttribute("data-full-name") || Element.textContent.trim();
                const FirstName = Element.getAttribute("data-first-name") || FullName.split(" ")[0];
                if (!FullName || !FirstName || FullName === FirstName) {
                    return;
                }
                Element.textContent = FullName;
                if (Element.scrollWidth > Element.clientWidth) {
                    Element.textContent = FirstName;
                }
            });
        } finally {
            this.IsAdjustingNames = false;
        }
    },

    EditCharacter: function (CharacterIdentifier) {
        SystemDebugger.LogDebugMessage("Character Edit Invoked: Character='" + CharacterIdentifier + "', System='DND5thEdition'");
        DesktopApplication.OpenCharacterSheetWindow("DND5thEdition");
    },

    OpenDiceRollerWindow: function () {
        SystemDebugger.LogDebugMessage("Dice Roller Window Opened: Width=520, Height=400");
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowDiceRoller",
            Title: "Dice Roller",
            Width: 520,
            Height: 400,
            MinWidth: 360,
            MinHeight: 280,
            Left: 240,
            Top: 60,
            ContentURL: "/API/Desktop/Windows/DiceRoller"
        };
        WindowManager.OpenWindow(Config);
    },

    OpenNPCGeneratorWindow: function () {
        if (!this.HasGameMasterRole()) {
            this.ShowPermissionDeniedAlert("You do not have the Game Master role required to use the NPC Generator.");
            return;
        }
        SystemDebugger.LogDebugMessage("NPC Generator Window Opened: Width=480, Height=460");
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowNPCGenerator",
            Title: "NPC Generator",
            Width: 480,
            Height: 460,
            MinWidth: 324,
            MinHeight: 440,
            Left: 260,
            Top: 80,
            ContentURL: "/API/Desktop/Windows/NPCGenerator"
        };
        WindowManager.OpenWindow(Config);
    },

    OpenCharacterSheetWindow: function (GameSystem) {
        if (!this.IsUserInGuild()) {
            this.ShowGuildMembershipWarning();
            return;
        }
        const SelectedGameSystem = GameSystem || "DND5thEdition";
        this.ZoomIntoScreen();
        const DesktopElement = document.getElementById("DesktopContainer");
        const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
        const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 600;
        SystemDebugger.LogDebugMessage("Character Sheet Window Opened: System='" + SelectedGameSystem + "', " + AvailableWidth + "x" + AvailableHeight);
        const Config = {
            Identifier: "WindowCharacterSheet",
            Title: "Character Sheet [ * ]",
            Width: AvailableWidth,
            Height: AvailableHeight,
            MinWidth: AvailableWidth,
            MinHeight: AvailableHeight,
            Left: 0,
            Top: 0,
            ContentURL: "/API/Desktop/Windows/CharacterSheet?GameSystem=" + encodeURIComponent(SelectedGameSystem),
            BypassPlacement: true
        };
        WindowManager.OpenWindow(Config);
    },

    OpenPortraitAssetPickerWindow: function () {
        this.ZoomIntoScreen();
        const DesktopElement = document.getElementById("DesktopContainer");
        const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
        const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 600;
        const WindowWidth = Math.min(540, AvailableWidth - 40);
        const WindowHeight = Math.min(440, AvailableHeight - 40);
        SystemDebugger.LogDebugMessage("Portrait Asset Picker Opened: " + WindowWidth + "x" + WindowHeight);
        const TargetLeft = Math.max(0, Math.floor((AvailableWidth - WindowWidth) / 2));
        const TargetTop = Math.max(0, Math.floor((AvailableHeight - WindowHeight) / 2));
        const Config = {
            Identifier: "WindowPortraitAssetPicker",
            Title: "Select Image...",
            Width: WindowWidth,
            Height: WindowHeight,
            MinWidth: 360,
            MinHeight: 300,
            Left: TargetLeft,
            Top: TargetTop,
            ContentURL: "/API/Desktop/Windows/PortraitAssetPicker",
            BypassPlacement: true
        };
        WindowManager.OpenWindow(Config);
    },

    SwitchCharacterSheetTab: function (TargetTab, ButtonElement) {
        SystemDebugger.LogDebugMessage("Character Sheet Tab Switched: Tab='" + TargetTab + "'");
        const ContainerElement = $(ButtonElement).closest(".WindowContainer");
        ContainerElement.find(".CharacterSheetTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
        ContainerElement.find(".CharacterSheetTabContent").addClass("HiddenElement");
        ContainerElement.find("#" + TargetTab).removeClass("HiddenElement");
        ContainerElement.find("#" + TargetTab).find("textarea").each(function () {
            DesktopApplication.AutoResizeTextarea(this);
        });
        if (TargetTab === "CharacterSheetAbilitiesTab") {
            DesktopApplication.InitializeAbilitiesTab(ContainerElement);
        }
    },

    AutoResizeTextarea: function (TextareaElement) {
        if (!TextareaElement) {
            return;
        }
        TextareaElement.style.height = "auto";
        const ScrollHeight = TextareaElement.scrollHeight;
        const MinimumHeight = 24;
        TextareaElement.style.height = Math.max(MinimumHeight, ScrollHeight) + "px";
    },

    InitializeAutoResizeTextareas: function (RootContainer) {
        const Container = RootContainer ? $(RootContainer) : $(document);
        const TextareaElements = Container.find("textarea");
        TextareaElements.each(function () {
            DesktopApplication.AutoResizeTextarea(this);
        });
    },

    SerializeCharacterSheetForm: function (FormElement) {
        if (!FormElement) {
            return "";
        }
        const FormDataInstance = new FormData(FormElement);
        const FormEntries = [];
        for (const [Key, Value] of FormDataInstance.entries()) {
            if (Key !== "File") {
                FormEntries.push([Key, Value]);
            }
        }
        FormEntries.sort(function (ItemA, ItemB) {
            if (ItemA[0] === ItemB[0]) {
                return ItemA[1] > ItemB[1] ? 1 : -1;
            }
            return ItemA[0] > ItemB[0] ? 1 : -1;
        });
        return JSON.stringify(FormEntries);
    },

    InitializeCharacterSheetBaseline: function (SavedName) {
        const FormElement = document.getElementById("CharacterSheetCreationForm");
        if (!FormElement) {
            return;
        }
        if (SavedName !== undefined) {
            FormElement._SavedCharacterName = SavedName;
            FormElement._BaselineFormData = this.SerializeCharacterSheetForm(FormElement);
        } else if (!FormElement._BaselineFormData) {
            const NameInput = document.getElementById("CharacterSheetNameInput");
            const InitialName = NameInput && NameInput.value ? NameInput.value.trim() : null;
            FormElement._SavedCharacterName = InitialName;
            FormElement._BaselineFormData = this.SerializeCharacterSheetForm(FormElement);
        }
    },

    EvaluateCharacterSheetDirtyState: function () {
        const FormElement = document.getElementById("CharacterSheetCreationForm");
        if (!FormElement) {
            return;
        }
        if (!FormElement._BaselineFormData) {
            this.InitializeCharacterSheetBaseline();
        }
        const NameInput = document.getElementById("CharacterSheetNameInput");
        const CurrentName = NameInput && NameInput.value ? NameInput.value.trim() : "";
        const CurrentSerializedState = this.SerializeCharacterSheetForm(FormElement);
        const SavedName = FormElement._SavedCharacterName;
        let TargetTitle = "Character Sheet [ * ]";
        if (SavedName) {
            if (CurrentSerializedState === FormElement._BaselineFormData) {
                TargetTitle = "Character Sheet [ " + SavedName + " ]";
            } else {
                const DisplayName = CurrentName || SavedName;
                TargetTitle = "Character Sheet [ " + DisplayName + " * ]";
            }
        } else {
            if (CurrentName) {
                TargetTitle = "Character Sheet [ " + CurrentName + " * ]";
            } else {
                TargetTitle = "Character Sheet [ * ]";
            }
        }
        WindowManager.SetWindowTitle("WindowCharacterSheet", TargetTitle);
    },

    HandleCharacterSavedEvent: function (Event) {
        const SavedName = Event && Event.detail && Event.detail.CharacterName ? Event.detail.CharacterName : null;
        SystemDebugger.LogDebugMessage("Character Saved: Name='" + (SavedName || "Unknown") + "', Payload=" + JSON.stringify(Event.detail));
        const FormElement = document.getElementById("CharacterSheetCreationForm");
        if (FormElement && SavedName) {
            this.InitializeCharacterSheetBaseline(SavedName);
            WindowManager.SetWindowTitle("WindowCharacterSheet", "Character Sheet [ " + SavedName + " ]");
            const SaveButton = document.getElementById("CharacterSheetSaveButton");
            if (SaveButton) {
                SaveButton.classList.add("ButtonSuccess");
                setTimeout(function () {
                    SaveButton.classList.remove("ButtonSuccess");
                }, 800);
            }
        }
    },

    HandlePortraitSelectedEvent: function () {
        SystemDebugger.LogDebugMessage("Portrait Selected: WindowClosed='WindowPortraitAssetPicker'");
        WindowManager.CloseWindow("WindowPortraitAssetPicker");
        if (document.getElementById("WindowCharacterSheet")) {
            WindowManager.FocusWindow("WindowCharacterSheet");
        }
        this.EvaluateCharacterSheetDirtyState();
    },

    OpenCalendarWindow: function () {
        SystemDebugger.LogDebugMessage("Calendar Window Opened: Width=600, Height=440");
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowCalendar",
            Title: "Date & Time",
            Width: 600,
            Height: 440,
            MinWidth: 480,
            MinHeight: 240,
            Left: 250,
            Top: 50,
            ContentURL: "/API/Desktop/Windows/Calendar"
        };
        WindowManager.OpenWindow(Config);
    },

    OpenStorageWindow: function () {
        SystemDebugger.LogDebugMessage("Storage Window Opened: Width=680, Height=480");
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowStorage",
            Title: "Files",
            Width: 680,
            Height: 480,
            MinWidth: 420,
            MinHeight: 220,
            Left: 230,
            Top: 40,
            ContentURL: "/API/Desktop/Windows/Storage"
        };
        WindowManager.OpenWindow(Config);
    },

    SwitchAccountTab: function (TabIdentifier, ButtonElement) {
        SystemDebugger.LogDebugMessage("Account Tab Switched: Tab='" + TabIdentifier + "'");
        $(".AccountTabContent").addClass("HiddenElement");
        $(`#${TabIdentifier}`).removeClass("HiddenElement");
        $(".AccountTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
    },

    SwitchCalendarTab: function (TabIdentifier, ButtonElement) {
        SystemDebugger.LogDebugMessage("Calendar Tab Switched: Tab='" + TabIdentifier + "'");
        $(".CalendarTabContent").addClass("HiddenElement");
        $(`#${TabIdentifier}`).removeClass("HiddenElement");
        $(".CalendarTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
    },

    SwitchCharacterGeneratorTab: function (TabIdentifier, ButtonElement) {
        SystemDebugger.LogDebugMessage("Character Generator Tab Switched: Tab='" + TabIdentifier + "'");
        $(".CharacterGeneratorTabContent").addClass("HiddenElement");
        $(`#${TabIdentifier}`).removeClass("HiddenElement");
        $(".CharacterGeneratorTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
    },

    UpdateCharacterGeneratorControls: function () {
        const SelectedSystem = $("#CharacterGeneratorSystemSelect").val();
        SystemDebugger.LogDebugMessage("Character Generator Controls Updated: System='" + SelectedSystem + "'");
        if (SelectedSystem === "Traveller2ndEdition") {
            $("#CharacterGeneratorClassLabel").text("Career");
            $("#CharacterGeneratorClassInput").attr("placeholder", "e.g. Navy, Scout, Marine, Agent");
        } else {
            $("#CharacterGeneratorClassLabel").text("Class");
            $("#CharacterGeneratorClassInput").attr("placeholder", "e.g. Fighter, Wizard, Rogue, Cleric");
        }
    },

    RandomizeCharacterName: function () {
        const SelectedSystem = $("#CharacterGeneratorSystemSelect").val();
        const DND5thEditionNames = [
            "Valen Starstrider",
            "Elidor Moonwhisper",
            "Thorgar Ironbreaker",
            "Lyra Nightingale",
            "Roland Highcliff",
            "Morwenna Duskweaver",
            "Branoc Strongbow",
            "Sylas Stormcaller",
            "Kaelen Dawnseeker",
            "Brynna Shadowmend"
        ];
        const Traveller2ndEditionNames = [
            "Sean Alvarez",
            "Marcus Vance",
            "Jacqueline Drake",
            "Elena Cross",
            "Victor Corvus",
            "Donald Stark",
            "Cassian Mercer",
            "Talia Sol",
            "Gideon Rayne",
            "Astrid Novak"
        ];
        const NamePool = (SelectedSystem === "Traveller2ndEdition") ? Traveller2ndEditionNames : DND5thEditionNames;
        const CurrentName = $("#CharacterGeneratorNameInput").val();
        let AvailableNames = NamePool.filter((Name) => Name !== CurrentName);
        if (AvailableNames.length === 0) {
            AvailableNames = NamePool;
        }
        const ChosenName = AvailableNames[Math.floor(Math.random() * AvailableNames.length)];
        $("#CharacterGeneratorNameInput").val(ChosenName);
        SystemDebugger.LogDebugMessage("Character Name Randomized: System='" + SelectedSystem + "', Name='" + ChosenName + "'");
    },

    UpdateDiceControls: function () {
        const SelectedSystem = $("#DiceSystemSelect").val();
        SystemDebugger.LogDebugMessage("Dice Controls Updated: System='" + SelectedSystem + "'");
        if (SelectedSystem === "Traveller2ndEdition") {
            $("#AdvantageCheckboxLabel, #DisadvantageCheckboxLabel, #DNDDiceInputsGroup").addClass("HiddenElement");
            $("#BoonCheckboxLabel, #BaneCheckboxLabel, #TravellerDiceInputsGroup").removeClass("HiddenElement");
            $("#DiceExpressionInput, #DiceDifficultyInput").prop("disabled", true);
            $("#DiceModifierInput, #DiceTargetDifficultyInput").prop("disabled", false);
        } else {
            $("#AdvantageCheckboxLabel, #DisadvantageCheckboxLabel, #DNDDiceInputsGroup").removeClass("HiddenElement");
            $("#BoonCheckboxLabel, #BaneCheckboxLabel, #TravellerDiceInputsGroup").addClass("HiddenElement");
            $("#DiceExpressionInput, #DiceDifficultyInput").prop("disabled", false);
            $("#DiceModifierInput, #DiceTargetDifficultyInput").prop("disabled", true);
        }
    },

    SubmitStorageUpload: function () {
        if (!this.IsUserInGuild()) {
            this.ShowGuildMembershipWarning();
            return;
        }
        const FileInput = document.getElementById("StorageFileInput");
        const UploadFileName = (FileInput && FileInput.files && FileInput.files[0]) ? FileInput.files[0].name : "Unknown";
        SystemDebugger.LogDebugMessage("Storage Upload Submitted: File='" + UploadFileName + "'");
        if (window.htmx) {
            htmx.trigger("#StorageUploadForm", "submit");
        }
    },

    HandleViewportInteraction: function (Event) {
        let TargetElement = Event.target;
        if (!document.body.contains(TargetElement)) {
            TargetElement = document.elementFromPoint(Event.clientX, Event.clientY);
        }
        if (!TargetElement || !document.body.contains(TargetElement)) {
            return;
        }
        if (WindowManager.IsPlacementActive || WindowManager.JustFinishedPlacement || WindowManager.IsDraggingWindow || WindowManager.JustFinishedDragging) {
            return;
        }
        const ClickedInsideScreen = Boolean($(TargetElement).closest("#DesktopScreenContainer").length > 0);
        const DragDistance = Math.hypot(Event.clientX - this.PointerDownPositionX, Event.clientY - this.PointerDownPositionY);
        if (DragDistance > 24) {
            return;
        }
        if (ClickedInsideScreen) {
            if (!this.PointerDownInsideScreen) {
                return;
            }
            this.ZoomIntoScreen();
        } else {
            if (this.PointerDownInsideScreen) {
                return;
            }
            this.ZoomOutOfScreen();
        }
    },

    ZoomIntoScreen: function () {
        if (!document.body.classList.contains("ZoomedIn")) {
            SystemDebugger.LogDebugMessage("Screen Zoom Toggled: ZoomedIn=true");
            document.body.classList.add("ZoomedIn");
            WorkstationTiltManager.DisableMotion();
        }
    },

    ZoomOutOfScreen: function () {
        if (document.body.classList.contains("ZoomedIn")) {
            SystemDebugger.LogDebugMessage("Screen Zoom Toggled: ZoomedIn=false");
            document.body.classList.remove("ZoomedIn");
            WorkstationTiltManager.EnableMotion();
        }
    },

    InitializeAbilitiesTab: function (RootElement) {
        const Scope = RootElement ? $(RootElement) : $(document);
        const AbilitiesTab = Scope.find("#CharacterSheetAbilitiesTab");
        if (AbilitiesTab.length === 0) {
            return;
        }

        const ContainerList = AbilitiesTab.find("#CharacterSheetClassContainerList")[0];
        if (ContainerList && ContainerList.children.length === 0) {
            this.AddClassContainer();
        } else if (ContainerList) {
            const InitialContainer = ContainerList.querySelector('.ClassContainer[data-initial-class="true"]') || ContainerList.children[0];
            if (InitialContainer) {
                this.SetInitialClass(InitialContainer);
            }
        }

        const SpellListContainer = AbilitiesTab.find("#CharacterSheetSpellListContainer")[0];
        if (SpellListContainer && SpellListContainer.children.length === 0) {
            this.CreateSpellList("Cantrips", "None", false);
            this.CreateSpellList("Prepared Spells", "None", false);
            this.CreateSpellList("Spellbook", "None", true);
        }

        this.UpdateAllClassSubclassStates();
        this.UpdateSpellSlotsFromClasses();
        this.UpdateSpellcastingAbilityFromInitialClass();
        this.RecalculateAllSpellListStats();
        this.RecalculateTotalExperience();

        const AppRef = this;
        this.LoadClassRulesData().then(function () {
            AppRef.UpdateSpellcastingAbilityFromInitialClass();
            AppRef.UpdateSpellSlotsFromClasses();
        });
    },

    UpdateClassSubclassState: function (ContainerElement) {
        if (!ContainerElement) {
            return;
        }
        const LevelInput = ContainerElement.querySelector(".ClassInputLevel");
        const SubclassInput = ContainerElement.querySelector(".ClassInputSubclass");
        if (LevelInput && SubclassInput) {
            const Level = parseInt(LevelInput.value, 10) || 1;
            if (Level < 3) {
                SubclassInput.disabled = true;
                SubclassInput.classList.add("InputDisabled");
            } else {
                SubclassInput.disabled = false;
                SubclassInput.classList.remove("InputDisabled");
            }
        }
    },

    UpdateAllClassSubclassStates: function () {
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const Containers = ContainerList.querySelectorAll(".ClassContainer");
        const AppRef = this;
        Containers.forEach(function (Container) {
            AppRef.UpdateClassSubclassState(Container);
        });
    },

    AddClassContainer: function () {
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const CurrentContainers = ContainerList.querySelectorAll(".ClassContainer");
        const NewIndex = CurrentContainers.length;
        const IsFirst = (NewIndex === 0);

        const ContainerDiv = document.createElement("div");
        ContainerDiv.className = "ClassContainer";
        ContainerDiv.setAttribute("data-class-index", NewIndex.toString());
        ContainerDiv.setAttribute("data-initial-class", IsFirst ? "true" : "false");

        ContainerDiv.innerHTML = `
            <input type="hidden" name="Classes[${NewIndex}].IsInitialClass" value="${IsFirst ? "true" : "false"}" class="ClassInitialInput" />
            <div class="ClassContainerFields">
                <div class="FormRow">
                    <div class="FormColumn">
                        <div class="FormGroup">
                            <label class="FormLabel">Class</label>
                            <input type="text" name="Classes[${NewIndex}].ClassName" class="ClassInputName" placeholder="e.g. Bard, Fighter, Rogue" />
                        </div>
                    </div>
                    <div class="FormColumn">
                        <div class="FormGroup">
                            <label class="FormLabel">Subclass</label>
                            <input type="text" name="Classes[${NewIndex}].Subclass" class="ClassInputSubclass InputDisabled" placeholder="e.g. Lore, Champion" disabled />
                        </div>
                    </div>
                </div>
                <div class="FormRow">
                    <div class="FormColumn">
                        <div class="FormGroup">
                            <label class="FormLabel">Level</label>
                            <input type="number" name="Classes[${NewIndex}].Level" class="ClassInputLevel" value="1" min="1" max="20" />
                        </div>
                    </div>
                    <div class="FormColumn">
                        <div class="FormGroup">
                            <label class="FormLabel">Experience Points</label>
                            <div class="ClassExperienceRow">
                                <input type="number" name="Classes[${NewIndex}].Experience" class="ClassInputExperience" value="0" min="0" />
                                <button type="button" class="Button ButtonSquare ButtonWarning ClassStarButton" title="${IsFirst ? "Initial Class" : "Set as Initial Class"}" aria-label="${IsFirst ? "Initial Class" : "Set as Initial Class"}"${IsFirst ? " disabled" : ""}>
                                    <span class="FunctionIcon FunctionIconStar" aria-hidden="true"></span>
                                </button>
                                <button type="button" class="Button ButtonSquare ButtonDanger ClassDeleteButton" title="Delete Class" aria-label="Delete Class"${IsFirst ? " disabled" : ""}>
                                    <span class="FunctionIcon FunctionIconDelete" aria-hidden="true"></span>
                                </button>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        `;

        ContainerList.appendChild(ContainerDiv);
        this.ReindexClassContainers();
        this.UpdateClassSubclassState(ContainerDiv);
        this.RecalculateTotalExperience();
        this.UpdateSpellSlotsFromClasses();
        this.UpdateSpellcastingAbilityFromInitialClass();
        this.EvaluateCharacterSheetDirtyState();
    },

    DeleteClassContainer: function (ContainerElement) {
        if (!ContainerElement) {
            return;
        }
        if (ContainerElement.getAttribute("data-initial-class") === "true") {
            return;
        }
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const AllContainers = ContainerList.querySelectorAll(".ClassContainer");
        if (AllContainers.length <= 1) {
            return;
        }

        ContainerElement.remove();
        this.ReindexClassContainers();
        this.RecalculateTotalExperience();
        this.UpdateSpellSlotsFromClasses();
        this.UpdateSpellcastingAbilityFromInitialClass();
        this.EvaluateCharacterSheetDirtyState();
    },

    SetInitialClass: function (ContainerElement) {
        if (!ContainerElement) {
            return;
        }
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const AllContainers = ContainerList.querySelectorAll(".ClassContainer");
        AllContainers.forEach(function (Container) {
            Container.setAttribute("data-initial-class", "false");
            const InitialInput = Container.querySelector(".ClassInitialInput");
            if (InitialInput) {
                InitialInput.value = "false";
            }
            const StarBtn = Container.querySelector(".ClassStarButton");
            if (StarBtn) {
                StarBtn.disabled = false;
                StarBtn.title = "Set as Initial Class";
                StarBtn.setAttribute("aria-label", "Set as Initial Class");
            }
            const DelBtn = Container.querySelector(".ClassDeleteButton");
            if (DelBtn) {
                DelBtn.disabled = false;
                DelBtn.title = "Delete Class";
                DelBtn.setAttribute("aria-label", "Delete Class");
            }
        });

        ContainerElement.setAttribute("data-initial-class", "true");
        const TargetInitialInput = ContainerElement.querySelector(".ClassInitialInput");
        if (TargetInitialInput) {
            TargetInitialInput.value = "true";
        }
        const TargetStarBtn = ContainerElement.querySelector(".ClassStarButton");
        if (TargetStarBtn) {
            TargetStarBtn.disabled = true;
            TargetStarBtn.title = "Initial Class";
            TargetStarBtn.setAttribute("aria-label", "Initial Class");
        }
        const TargetDelBtn = ContainerElement.querySelector(".ClassDeleteButton");
        if (TargetDelBtn) {
            TargetDelBtn.disabled = true;
            TargetDelBtn.title = "Delete Class";
            TargetDelBtn.setAttribute("aria-label", "Delete Class");
        }

        this.ReindexClassContainers();
        this.UpdateSpellcastingAbilityFromInitialClass();
        this.EvaluateCharacterSheetDirtyState();
    },

    ReindexClassContainers: function () {
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const Containers = ContainerList.querySelectorAll(".ClassContainer");
        let HasInitial = false;
        Containers.forEach(function (Container, Index) {
            Container.setAttribute("data-class-index", Index.toString());
            const IsInitial = (Container.getAttribute("data-initial-class") === "true");
            if (IsInitial) {
                HasInitial = true;
            }

            const InitialInput = Container.querySelector(".ClassInitialInput");
            if (InitialInput) {
                InitialInput.name = "Classes[" + Index + "].IsInitialClass";
            }
            const NameInput = Container.querySelector(".ClassInputName");
            if (NameInput) {
                NameInput.name = "Classes[" + Index + "].ClassName";
            }
            const SubclassInput = Container.querySelector(".ClassInputSubclass");
            if (SubclassInput) {
                SubclassInput.name = "Classes[" + Index + "].Subclass";
            }
            const LevelInput = Container.querySelector(".ClassInputLevel");
            if (LevelInput) {
                LevelInput.name = "Classes[" + Index + "].Level";
            }
            const ExpInput = Container.querySelector(".ClassInputExperience");
            if (ExpInput) {
                ExpInput.name = "Classes[" + Index + "].Experience";
            }
        });

        if (!HasInitial && Containers.length > 0) {
            this.SetInitialClass(Containers[Containers.length - 1]);
        }
    },

    LoadClassRulesData: function () {
        if (this.ClassRulesDataCache) {
            return Promise.resolve(this.ClassRulesDataCache);
        }
        const AppRef = this;
        return fetch("/API/Characters/Rules/Classes")
            .then(function (Response) {
                if (!Response.ok) {
                    return null;
                }
                return Response.json();
            })
            .then(function (Data) {
                if (Data) {
                    AppRef.ClassRulesDataCache = Data;
                }
                return Data;
            })
            .catch(function () {
                return null;
            });
    },

    GetSpellcastingAbilityForClass: function (ClassName, SubclassName) {
        if (!ClassName) {
            return "None";
        }
        const CleanClass = ClassName.trim().toLowerCase();
        const CleanSubclass = SubclassName ? SubclassName.trim().toLowerCase() : "";

        if (this.ClassRulesDataCache) {
            if (CleanSubclass && this.ClassRulesDataCache.Subclasses) {
                const Subclasses = this.ClassRulesDataCache.Subclasses;
                for (const Key in Subclasses) {
                    const LowerKey = Key.toLowerCase();
                    if (LowerKey.includes(CleanClass) && LowerKey.includes(CleanSubclass)) {
                        const SubAbility = Subclasses[Key].SpellcastingAbility;
                        if (SubAbility) {
                            return SubAbility;
                        }
                    }
                }
            }
            if (this.ClassRulesDataCache.Classes) {
                const Classes = this.ClassRulesDataCache.Classes;
                for (const Key in Classes) {
                    if (Key.toLowerCase() === CleanClass || CleanClass.includes(Key.toLowerCase())) {
                        const ClassAbility = Classes[Key].SpellcastingAbility;
                        if (ClassAbility) {
                            return ClassAbility;
                        }
                    }
                }
            }
        }
        return "None";
    },

    FetchSpellcastingAbilityForClass: function (ClassName, SubclassName, Callback) {
        const DirectResult = this.GetSpellcastingAbilityForClass(ClassName, SubclassName);
        if (DirectResult && DirectResult !== "None") {
            if (Callback) {
                Callback(DirectResult);
            }
            return;
        }
        const QueryParams = new URLSearchParams({
            ClassName: ClassName,
            SubclassName: SubclassName || ""
        });
        fetch("/API/Characters/Rules/SpellcastingAbility?" + QueryParams.toString())
            .then(function (Response) {
                if (!Response.ok) {
                    return null;
                }
                return Response.json();
            })
            .then(function (Data) {
                const Ability = (Data && Data.SpellcastingAbility) ? Data.SpellcastingAbility : "None";
                if (Callback) {
                    Callback(Ability);
                }
            })
            .catch(function () {
                if (Callback) {
                    Callback("None");
                }
            });
    },

    UpdateSpellcastingAbilityFromInitialClass: function () {
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const InitialContainer = ContainerList.querySelector('.ClassContainer[data-initial-class="true"]') || ContainerList.querySelector(".ClassContainer");
        if (!InitialContainer) {
            return;
        }
        const NameInput = InitialContainer.querySelector(".ClassInputName");
        const SubclassInput = InitialContainer.querySelector(".ClassInputSubclass");
        const ClassName = NameInput ? NameInput.value : "";
        const SubclassName = SubclassInput ? SubclassInput.value : "";
        const AppRef = this;

        const ApplyAbility = function (Ability) {
            if (!Ability || Ability === "None") {
                return;
            }
            const SpellListContainer = document.getElementById("CharacterSheetSpellListContainer");
            if (!SpellListContainer) {
                return;
            }
            const Containers = SpellListContainer.querySelectorAll(".SpellListContainer");
            Containers.forEach(function (Container) {
                if (Container.getAttribute("data-custom-list") === "true") {
                    return;
                }
                const Select = Container.querySelector(".SpellListAbilitySelect");
                const Input = Container.querySelector(".SpellListAbilityInput");
                if (Select) {
                    Select.value = Ability;
                }
                if (Input) {
                    Input.value = Ability;
                }
                AppRef.RecalculateSpellListStats(Container);
            });
        };

        const DirectAbility = this.GetSpellcastingAbilityForClass(ClassName, SubclassName);
        if (DirectAbility && DirectAbility !== "None") {
            ApplyAbility(DirectAbility);
        } else if (ClassName) {
            this.FetchSpellcastingAbilityForClass(ClassName, SubclassName, ApplyAbility);
        }
    },

    HandleClassFieldChange: function (InputElement) {
        if (!InputElement) {
            return;
        }
        const Container = InputElement.closest(".ClassContainer");
        if (!Container) {
            return;
        }
        this.UpdateClassSubclassState(Container);

        const LevelRequirements = {
            1: 0, 2: 300, 3: 900, 4: 2700, 5: 6500,
            6: 14000, 7: 23000, 8: 34000, 9: 48000, 10: 64000,
            11: 85000, 12: 100000, 13: 120000, 14: 140000, 15: 165000,
            16: 195000, 17: 225000, 18: 265000, 19: 305000, 20: 355000
        };

        const LevelInput = Container.querySelector(".ClassInputLevel");
        const ExpInput = Container.querySelector(".ClassInputExperience");
        if (LevelInput && ExpInput) {
            let LevelVal = parseInt(LevelInput.value, 10) || 1;
            LevelVal = Math.max(1, Math.min(20, LevelVal));
            LevelInput.value = LevelVal.toString();

            const MinExp = LevelRequirements[LevelVal] || 0;
            let ExpVal = parseInt(ExpInput.value, 10) || 0;
            if (ExpVal < MinExp) {
                ExpVal = MinExp;
                ExpInput.value = ExpVal.toString();
            }
        }

        this.RecalculateTotalExperience();
        this.UpdateSpellSlotsFromClasses();
        this.UpdateSpellcastingAbilityFromInitialClass();
        this.EvaluateCharacterSheetDirtyState();
    },

    RecalculateTotalExperience: function () {
        const ExpInputs = document.querySelectorAll(".ClassInputExperience");
        let TotalExp = 0;
        ExpInputs.forEach(function (Input) {
            TotalExp += parseInt(Input.value, 10) || 0;
        });
        const TotalExpInput = document.getElementById("CharacterSheetExperienceInput");
        if (TotalExpInput) {
            TotalExpInput.value = TotalExp.toString();
        }
    },

    UpdateSpellSlotsFromClasses: function () {
        const ContainerList = document.getElementById("CharacterSheetClassContainerList");
        if (!ContainerList) {
            return;
        }
        const Containers = ContainerList.querySelectorAll(".ClassContainer");
        const ClassEntries = [];

        Containers.forEach(function (Container) {
            const NameInput = Container.querySelector(".ClassInputName");
            const SubclassInput = Container.querySelector(".ClassInputSubclass");
            const LevelInput = Container.querySelector(".ClassInputLevel");
            const ClassName = NameInput && NameInput.value ? NameInput.value.trim().toLowerCase() : "";
            const SubclassName = SubclassInput && SubclassInput.value ? SubclassInput.value.trim().toLowerCase() : "";
            const Level = LevelInput ? (parseInt(LevelInput.value, 10) || 1) : 1;
            if (ClassName) {
                ClassEntries.push({
                    ClassName: ClassName,
                    SubclassName: SubclassName,
                    Level: Level
                });
            }
        });

        const MulticlassSlotTable = {
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
        };

        const ThirdCasterTable = {
            3: [2, 0, 0, 0, 0, 0, 0, 0, 0],
            4: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            5: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            6: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            7: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            8: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            9: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            10: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            11: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            12: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            13: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            14: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            15: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            16: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            17: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            18: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            19: [4, 3, 3, 1, 0, 0, 0, 0, 0],
            20: [4, 3, 3, 1, 0, 0, 0, 0, 0]
        };

        const HalfCasterTable = {
            2: [2, 0, 0, 0, 0, 0, 0, 0, 0],
            3: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            4: [3, 0, 0, 0, 0, 0, 0, 0, 0],
            5: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            6: [4, 2, 0, 0, 0, 0, 0, 0, 0],
            7: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            8: [4, 3, 0, 0, 0, 0, 0, 0, 0],
            9: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            10: [4, 3, 2, 0, 0, 0, 0, 0, 0],
            11: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            12: [4, 3, 3, 0, 0, 0, 0, 0, 0],
            13: [4, 3, 3, 1, 0, 0, 0, 0, 0],
            14: [4, 3, 3, 1, 0, 0, 0, 0, 0],
            15: [4, 3, 3, 2, 0, 0, 0, 0, 0],
            16: [4, 3, 3, 2, 0, 0, 0, 0, 0],
            17: [4, 3, 3, 3, 1, 0, 0, 0, 0],
            18: [4, 3, 3, 3, 1, 0, 0, 0, 0],
            19: [4, 3, 3, 3, 2, 0, 0, 0, 0],
            20: [4, 3, 3, 3, 2, 0, 0, 0, 0]
        };

        const PactCasterTable = {
            1: [1, 1],
            2: [1, 2],
            3: [2, 2],
            4: [2, 2],
            5: [3, 2],
            6: [3, 2],
            7: [4, 2],
            8: [4, 2],
            9: [5, 2],
            10: [5, 2],
            11: [5, 3],
            12: [5, 3],
            13: [5, 3],
            14: [5, 3],
            15: [5, 3],
            16: [5, 3],
            17: [5, 4],
            18: [5, 4],
            19: [5, 4],
            20: [5, 4]
        };

        const FullCasters = ["bard", "cleric", "druid", "sorcerer", "wizard"];
        const HalfCasters = ["paladin", "ranger"];

        let FinalSlots = [0, 0, 0, 0, 0, 0, 0, 0, 0];
        let PactMagicLevel = 0;

        const CastingClassList = [];
        const AppRef = this;
        ClassEntries.forEach(function (Entry) {
            let Progression = null;
            if (AppRef.ClassRulesDataCache) {
                if (Entry.SubclassName && AppRef.ClassRulesDataCache.Subclasses) {
                    const Subclasses = AppRef.ClassRulesDataCache.Subclasses;
                    for (const Key in Subclasses) {
                        const LowerKey = Key.toLowerCase();
                        if (LowerKey.includes(Entry.ClassName) && LowerKey.includes(Entry.SubclassName)) {
                            Progression = Subclasses[Key].CasterProgression;
                            if (Progression) {
                                break;
                            }
                        }
                    }
                }
                if (!Progression && AppRef.ClassRulesDataCache.Classes) {
                    const Classes = AppRef.ClassRulesDataCache.Classes;
                    for (const Key in Classes) {
                        if (Key.toLowerCase() === Entry.ClassName || Entry.ClassName.includes(Key.toLowerCase())) {
                            Progression = Classes[Key].CasterProgression;
                            if (Progression) {
                                break;
                            }
                        }
                    }
                }
            }

            if (Progression === "pact" || (!Progression && Entry.ClassName === "warlock")) {
                PactMagicLevel += Entry.Level;
            } else if (Progression === "full" || (!Progression && FullCasters.includes(Entry.ClassName))) {
                CastingClassList.push({ Type: "full", Level: Entry.Level });
            } else if (Progression === "1/2" || (!Progression && HalfCasters.includes(Entry.ClassName))) {
                CastingClassList.push({ Type: "half", Level: Entry.Level });
            } else if (Progression === "artificer" || (!Progression && Entry.ClassName === "artificer")) {
                CastingClassList.push({ Type: "artificer", Level: Entry.Level });
            } else if (Progression === "1/3" || (!Progression && (Entry.SubclassName === "arcane trickster" || Entry.SubclassName === "eldritch knight"))) {
                CastingClassList.push({ Type: "third", Level: Entry.Level });
            }
        });

        if (CastingClassList.length === 1) {
            const SingleCaster = CastingClassList[0];
            if (SingleCaster.Type === "full") {
                FinalSlots = MulticlassSlotTable[Math.min(20, Math.max(1, SingleCaster.Level))] || FinalSlots;
            } else if (SingleCaster.Type === "third") {
                FinalSlots = ThirdCasterTable[SingleCaster.Level] || FinalSlots;
            } else if (SingleCaster.Type === "half") {
                FinalSlots = HalfCasterTable[SingleCaster.Level] || FinalSlots;
            } else if (SingleCaster.Type === "artificer") {
                const EffectiveLevel = Math.max(1, Math.floor((SingleCaster.Level + 1) / 2));
                FinalSlots = MulticlassSlotTable[EffectiveLevel] || FinalSlots;
            }
        } else if (CastingClassList.length > 1) {
            let EffectiveLevel = 0;
            CastingClassList.forEach(function (Caster) {
                if (Caster.Type === "full") {
                    EffectiveLevel += Caster.Level;
                } else if (Caster.Type === "half" || Caster.Type === "artificer") {
                    EffectiveLevel += Math.floor(Caster.Level / 2);
                } else if (Caster.Type === "third") {
                    EffectiveLevel += Math.floor(Caster.Level / 3);
                }
            });
            if (EffectiveLevel > 0) {
                FinalSlots = MulticlassSlotTable[Math.min(20, Math.max(1, EffectiveLevel))] || FinalSlots;
            }
        }

        let PactSlotLevel = 0;
        let PactTotalSlots = 0;
        if (PactMagicLevel > 0) {
            const ClampedPactLevel = Math.min(20, Math.max(1, PactMagicLevel));
            const PactInfo = PactCasterTable[ClampedPactLevel];
            if (PactInfo) {
                PactSlotLevel = PactInfo[0];
                PactTotalSlots = PactInfo[1];
            }
        }

        const HasSpellcastingSlots = FinalSlots.some(function (Count) {
            return Count > 0;
        });
        const HasPactMagicSlots = (PactTotalSlots > 0);
        const HasAnySlots = HasSpellcastingSlots || HasPactMagicSlots;

        const SpellSlotsSection = document.getElementById("CharacterSheetSpellSlotsSection");
        const SpellcastingColumn = document.getElementById("CharacterSheetSpellcastingSlotsColumn");
        const PactMagicColumn = document.getElementById("CharacterSheetPactMagicSlotsColumn");

        if (SpellSlotsSection) {
            if (HasAnySlots) {
                SpellSlotsSection.classList.remove("HiddenElement");
            } else {
                SpellSlotsSection.classList.add("HiddenElement");
            }
        }

        if (SpellcastingColumn) {
            if (HasSpellcastingSlots) {
                SpellcastingColumn.classList.remove("HiddenElement");
            } else {
                SpellcastingColumn.classList.add("HiddenElement");
            }
        }

        if (PactMagicColumn) {
            if (HasPactMagicSlots) {
                PactMagicColumn.classList.remove("HiddenElement");
            } else {
                PactMagicColumn.classList.add("HiddenElement");
            }
        }

        const SlotsGrid = document.getElementById("CharacterSheetSpellSlotsContainer");
        if (SlotsGrid) {
            for (let SlotLevel = 1; SlotLevel <= 9; SlotLevel++) {
                const Row = SlotsGrid.querySelector('.SpellSlotRow[data-slot-level="' + SlotLevel + '"]');
                if (!Row) {
                    continue;
                }
                const Count = HasSpellcastingSlots ? (FinalSlots[SlotLevel - 1] || 0) : 0;
                const IconsContainer = Row.querySelector(".SpellSlotIcons");
                const TotalInput = Row.querySelector(".SpellSlotTotalInput");
                const UsedInput = Row.querySelector(".SpellSlotUsedInput");

                if (Count > 0) {
                    Row.classList.remove("HiddenElement");
                } else {
                    Row.classList.add("HiddenElement");
                }

                if (TotalInput) {
                    TotalInput.value = Count.toString();
                }

                if (IconsContainer) {
                    const CurrentIcons = IconsContainer.querySelectorAll(".SpellSlotIcon");
                    const PreviousUsed = [];
                    CurrentIcons.forEach(function (Icon, IconIndex) {
                        PreviousUsed[IconIndex] = Icon.getAttribute("data-slot-state") || "0";
                    });

                    IconsContainer.innerHTML = "";
                    let UsedCount = 0;
                    for (let SlotIndex = 0; SlotIndex < Count; SlotIndex++) {
                        const SlotState = (PreviousUsed[SlotIndex] === "1") ? "1" : "0";
                        if (SlotState === "1") {
                            UsedCount++;
                        }
                        const IconDiv = document.createElement("div");
                        IconDiv.className = "SpellSlotIcon";
                        IconDiv.setAttribute("data-slot-state", SlotState);
                        IconDiv.innerHTML = `
                            <div class="SpellSlotBackground"></div>
                            <div class="SpellSlotForeground"></div>
                        `;
                        IconsContainer.appendChild(IconDiv);
                    }

                    if (UsedInput) {
                        UsedInput.value = UsedCount.toString();
                    }
                }
            }
        }

        const PactGrid = document.getElementById("CharacterSheetPactMagicSlotsContainer");
        const PactSlotLevelInput = document.getElementById("CharacterSheetPactMagicSlotLevelInput");
        const PactTotalSlotsInput = document.getElementById("CharacterSheetPactMagicTotalSlotsInput");
        const PactUsedSlotsInput = document.getElementById("CharacterSheetPactMagicUsedSlotsInput");

        if (PactSlotLevelInput) {
            PactSlotLevelInput.value = PactSlotLevel.toString();
        }
        if (PactTotalSlotsInput) {
            PactTotalSlotsInput.value = PactTotalSlots.toString();
        }

        if (PactGrid) {
            let ActivePactUsedCount = 0;
            for (let SlotLevel = 1; SlotLevel <= 5; SlotLevel++) {
                const Row = PactGrid.querySelector('.SpellSlotRow[data-slot-level="' + SlotLevel + '"]');
                if (!Row) {
                    continue;
                }
                const IconsContainer = Row.querySelector(".SpellSlotIcons");
                if (HasPactMagicSlots && SlotLevel === PactSlotLevel) {
                    Row.classList.remove("HiddenElement");
                    if (IconsContainer) {
                        const CurrentIcons = IconsContainer.querySelectorAll(".SpellSlotIcon");
                        const PreviousUsed = [];
                        CurrentIcons.forEach(function (Icon, IconIndex) {
                            PreviousUsed[IconIndex] = Icon.getAttribute("data-slot-state") || "0";
                        });

                        IconsContainer.innerHTML = "";
                        for (let SlotIndex = 0; SlotIndex < PactTotalSlots; SlotIndex++) {
                            const SlotState = (PreviousUsed[SlotIndex] === "1") ? "1" : "0";
                            if (SlotState === "1") {
                                ActivePactUsedCount++;
                            }
                            const IconDiv = document.createElement("div");
                            IconDiv.className = "SpellSlotIcon";
                            IconDiv.setAttribute("data-slot-type", "pact");
                            IconDiv.setAttribute("data-slot-state", SlotState);
                            IconDiv.innerHTML = `
                                <div class="SpellSlotBackground"></div>
                                <div class="SpellSlotForeground"></div>
                            `;
                            IconsContainer.appendChild(IconDiv);
                        }
                    }
                } else {
                    Row.classList.add("HiddenElement");
                    if (IconsContainer) {
                        IconsContainer.innerHTML = "";
                    }
                }
            }
            if (PactUsedSlotsInput) {
                PactUsedSlotsInput.value = ActivePactUsedCount.toString();
            }
        }
    },

    ToggleSpellSlot: function (SlotElement) {
        if (!SlotElement) {
            return;
        }
        let CurrentState = parseInt(SlotElement.getAttribute("data-slot-state") || "0", 10);
        CurrentState = (CurrentState + 1) % 2;
        SlotElement.setAttribute("data-slot-state", CurrentState.toString());

        const PactContainer = SlotElement.closest("#CharacterSheetPactMagicSlotsContainer");
        if (PactContainer) {
            const UsedSlots = PactContainer.querySelectorAll('.SpellSlotIcon[data-slot-state="1"]').length;
            const PactUsedInput = document.getElementById("CharacterSheetPactMagicUsedSlotsInput");
            if (PactUsedInput) {
                PactUsedInput.value = UsedSlots.toString();
            }
        } else {
            const Row = SlotElement.closest(".SpellSlotRow");
            if (Row) {
                const TotalSlots = Row.querySelectorAll(".SpellSlotIcon").length;
                const UsedSlots = Row.querySelectorAll('.SpellSlotIcon[data-slot-state="1"]').length;
                const TotalInput = Row.querySelector(".SpellSlotTotalInput");
                const UsedInput = Row.querySelector(".SpellSlotUsedInput");
                if (TotalInput) {
                    TotalInput.value = TotalSlots.toString();
                }
                if (UsedInput) {
                    UsedInput.value = UsedSlots.toString();
                }
            }
        }
        this.EvaluateCharacterSheetDirtyState();
    },

    OpenCreateSpellListModal: function () {
        const Modal = $("#CharacterSheetCreateSpellListModal");
        if (Modal.length > 0) {
            $("#ModalSpellListNameInput").val("");
            $("#ModalSpellListAbilitySelect").val("None");
            Modal.removeClass("HiddenElement");
            $("#ModalSpellListNameInput").trigger("focus");
        }
    },

    CloseCreateSpellListModal: function () {
        $("#CharacterSheetCreateSpellListModal").addClass("HiddenElement");
    },

    ConfirmCreateSpellListModal: function () {
        const NameInput = document.getElementById("ModalSpellListNameInput");
        const AbilitySelect = document.getElementById("ModalSpellListAbilitySelect");
        if (NameInput && NameInput.value.trim()) {
            const ListName = NameInput.value.trim();
            const SelectedAbility = AbilitySelect ? AbilitySelect.value : "None";
            this.CreateSpellList(ListName, SelectedAbility, true, true);
            this.CloseCreateSpellListModal();
            this.EvaluateCharacterSheetDirtyState();
        }
    },

    CreateSpellList: function (ListName, AbilityName, IsDeletable, IsCustomList) {
        if (!ListName || !ListName.trim()) {
            return;
        }
        const CleanName = ListName.trim();
        const ListContainer = document.getElementById("CharacterSheetSpellListContainer");
        if (!ListContainer) {
            return;
        }

        const Existing = ListContainer.querySelector('.SpellListContainer[data-list-name="' + CleanName.toLowerCase() + '"]');
        if (Existing) {
            return;
        }

        const CurrentLists = ListContainer.querySelectorAll(".SpellListContainer");
        const Index = CurrentLists.length;
        let SelectedAbility = AbilityName || "None";
        if (!IsCustomList && SelectedAbility === "None") {
            const ContainerList = document.getElementById("CharacterSheetClassContainerList");
            if (ContainerList) {
                const InitialContainer = ContainerList.querySelector('.ClassContainer[data-initial-class="true"]') || ContainerList.querySelector(".ClassContainer");
                if (InitialContainer) {
                    const NameInput = InitialContainer.querySelector(".ClassInputName");
                    const SubclassInput = InitialContainer.querySelector(".ClassInputSubclass");
                    const ClassName = NameInput ? NameInput.value : "";
                    const SubclassName = SubclassInput ? SubclassInput.value : "";
                    const ComputedAbility = this.GetSpellcastingAbilityForClass(ClassName, SubclassName);
                    if (ComputedAbility && ComputedAbility !== "None") {
                        SelectedAbility = ComputedAbility;
                    }
                }
            }
        }
        const CanDelete = (IsDeletable !== undefined) ? IsDeletable : (CleanName !== "Cantrips" && CleanName !== "Prepared Spells");

        const ContainerDiv = document.createElement("div");
        ContainerDiv.className = "SpellListContainer";
        ContainerDiv.setAttribute("data-list-index", Index.toString());
        ContainerDiv.setAttribute("data-list-name", CleanName.toLowerCase());
        if (IsCustomList) {
            ContainerDiv.setAttribute("data-custom-list", "true");
        }

        const AbilityOptions = ["None", "Intelligence", "Wisdom", "Charisma", "Strength", "Dexterity", "Constitution"];
        let OptionsHTML = "";
        AbilityOptions.forEach(function (Opt) {
            const SelectedAttr = (Opt === SelectedAbility) ? " selected" : "";
            OptionsHTML += `<option value="${Opt}"${SelectedAttr}>${Opt}</option>`;
        });

        ContainerDiv.innerHTML = `
            <div class="SpellListHeader">
                <div class="SpellListTitle">${CleanName}</div>
                <div class="SpellListControls">
                    <select class="SpellListAbilitySelect" title="Spellcasting Ability">
                        ${OptionsHTML}
                    </select>
                    ${CanDelete ? `
                    <button type="button" class="Button ButtonSquare ButtonDanger DeleteSpellListButton" title="Delete Spell List (Hold Shift to discard spells)" aria-label="Delete Spell List">
                        <span class="FunctionIcon FunctionIconDelete" aria-hidden="true"></span>
                    </button>
                    ` : ""}
                </div>
            </div>
            <div class="SpellListStats">
                <div class="SpellListStatItem">Mod: <span class="SpellListStatModifier SpellListStatValue">—</span></div>
                <div class="SpellListStatItem">Atk: <span class="SpellListStatAttack SpellListStatValue">—</span></div>
                <div class="SpellListStatItem">DC: <span class="SpellListStatSaveDC SpellListStatValue">—</span></div>
            </div>
            <div class="SpellListSpells"></div>
            <input type="hidden" name="SpellLists[${Index}].Name" value="${CleanName}" class="SpellListNameInput" />
            <input type="hidden" name="SpellLists[${Index}].Ability" value="${SelectedAbility}" class="SpellListAbilityInput" />
            <input type="hidden" name="SpellLists[${Index}].Spells" value="" class="SpellListSpellsInput" />
        `;

        ListContainer.appendChild(ContainerDiv);

        const TargetSelect = document.getElementById("NewSpellTargetListSelect");
        if (TargetSelect) {
            const OptionExists = Array.from(TargetSelect.options).some(function (OptionElement) {
                return OptionElement.value.toLowerCase() === CleanName.toLowerCase();
            });
            if (!OptionExists) {
                const NewOption = document.createElement("option");
                NewOption.value = CleanName;
                NewOption.textContent = CleanName;
                TargetSelect.appendChild(NewOption);
            }
        }

        this.ReindexSpellLists();
        this.RecalculateSpellListStats(ContainerDiv);
        this.EvaluateCharacterSheetDirtyState();
    },

    DeleteSpellList: function (ListContainerElement, ShiftHeld) {
        if (!ListContainerElement) {
            return;
        }
        const CleanName = ListContainerElement.getAttribute("data-list-name");
        if (CleanName === "cantrips" || CleanName === "prepared spells") {
            return;
        }

        const Spells = [];
        const SpellEntries = ListContainerElement.querySelectorAll(".SpellListSpellEntry");
        SpellEntries.forEach(function (Entry) {
            const Label = Entry.querySelector("span");
            const Name = Label ? Label.textContent.trim() : Entry.getAttribute("data-spell-name");
            if (Name) {
                Spells.push(Name);
            }
        });

        if (!ShiftHeld && Spells.length > 0) {
            const ListContainer = document.getElementById("CharacterSheetSpellListContainer");
            let SpellbookList = ListContainer ? ListContainer.querySelector('.SpellListContainer[data-list-name="spellbook"]') : null;
            if (!SpellbookList) {
                this.CreateSpellList("Spellbook", "None", true);
                SpellbookList = ListContainer.querySelector('.SpellListContainer[data-list-name="spellbook"]');
            }
            if (SpellbookList) {
                const ApplicationReference = this;
                Spells.forEach(function (SpellName) {
                    ApplicationReference.AddSpellToList(SpellName, "Spellbook");
                });
            }
        }

        const DisplayName = ListContainerElement.querySelector(".SpellListTitle") ? ListContainerElement.querySelector(".SpellListTitle").textContent.trim() : "";
        ListContainerElement.remove();

        const TargetSelect = document.getElementById("NewSpellTargetListSelect");
        if (TargetSelect && DisplayName) {
            for (let OptionIndex = 0; OptionIndex < TargetSelect.options.length; OptionIndex++) {
                if (TargetSelect.options[OptionIndex].value.toLowerCase() === DisplayName.toLowerCase()) {
                    TargetSelect.remove(OptionIndex);
                    break;
                }
            }
        }

        this.ReindexSpellLists();
        this.EvaluateCharacterSheetDirtyState();
    },

    ReindexSpellLists: function () {
        const ListContainer = document.getElementById("CharacterSheetSpellListContainer");
        if (!ListContainer) {
            return;
        }
        const Containers = ListContainer.querySelectorAll(".SpellListContainer");
        Containers.forEach(function (Container, Index) {
            Container.setAttribute("data-list-index", Index.toString());
            const NameInput = Container.querySelector(".SpellListNameInput");
            if (NameInput) {
                NameInput.name = "SpellLists[" + Index + "].Name";
            }
            const AbilityInput = Container.querySelector(".SpellListAbilityInput");
            if (AbilityInput) {
                AbilityInput.name = "SpellLists[" + Index + "].Ability";
            }
            const SpellsInput = Container.querySelector(".SpellListSpellsInput");
            if (SpellsInput) {
                SpellsInput.name = "SpellLists[" + Index + "].Spells";
            }
        });
    },

    AddSpellToList: function (SpellName, TargetListName) {
        if (!SpellName || !SpellName.trim()) {
            return;
        }
        const CleanSpellName = SpellName.trim();
        const KnownCantrips = [
            "acid splash", "blade ward", "booming blade", "chill touch", "control flames",
            "create bonfire", "dancing lights", "druidcraft", "eldritch blast", "fire bolt",
            "friends", "frostbite", "green-flame blade", "guidance", "gust", "infestation",
            "light", "lightning lure", "mage hand", "magic stone", "mending", "message",
            "mind sliver", "minor illusion", "mold earth", "poison spray", "prestidigitation",
            "primal savagery", "produce flame", "ray of frost", "resistance", "sacred flame",
            "sapping sting", "shape water", "shillelagh", "shocking grasp", "spare the dying",
            "sword burst", "thaumaturgy", "thorn whip", "thunderclap", "toll the dead",
            "true strike", "vicious mockery", "word of radiance"
        ];

        let EffectiveListName = TargetListName || "Spellbook";
        const LowerName = CleanSpellName.toLowerCase();
        if (LowerName.includes("cantrip") || KnownCantrips.includes(LowerName)) {
            EffectiveListName = "Cantrips";
        }

        const ListContainer = document.getElementById("CharacterSheetSpellListContainer");
        if (!ListContainer) {
            return;
        }

        let TargetContainer = ListContainer.querySelector('.SpellListContainer[data-list-name="' + EffectiveListName.toLowerCase() + '"]');
        if (!TargetContainer) {
            this.CreateSpellList(EffectiveListName);
            TargetContainer = ListContainer.querySelector('.SpellListContainer[data-list-name="' + EffectiveListName.toLowerCase() + '"]');
        }
        if (!TargetContainer) {
            return;
        }

        const SpellsWrapper = TargetContainer.querySelector(".SpellListSpells");
        if (!SpellsWrapper) {
            return;
        }

        const ExistingEntry = SpellsWrapper.querySelector('.SpellListSpellEntry[data-spell-name="' + LowerName + '"]');
        if (ExistingEntry) {
            return;
        }

        const EntryDiv = document.createElement("div");
        EntryDiv.className = "SpellListSpellEntry";
        EntryDiv.setAttribute("data-spell-name", LowerName);
        EntryDiv.innerHTML = `
            <span>${CleanSpellName}</span>
            <button type="button" class="Button ButtonSquare ButtonDanger RemoveSpellButton" title="Remove Spell" aria-label="Remove Spell">
                <span class="FunctionIcon FunctionIconDelete" aria-hidden="true"></span>
            </button>
        `;

        SpellsWrapper.appendChild(EntryDiv);

        this.UpdateSpellListHiddenInput(TargetContainer);

        const TargetSelect = document.getElementById("NewSpellTargetListSelect");
        if (TargetSelect && EffectiveListName !== "Cantrips") {
            TargetSelect.value = EffectiveListName;
        }

        this.EvaluateCharacterSheetDirtyState();
    },

    RemoveSpellFromList: function (SpellEntryElement) {
        if (!SpellEntryElement) {
            return;
        }
        const TargetContainer = SpellEntryElement.closest(".SpellListContainer");
        SpellEntryElement.remove();
        if (TargetContainer) {
            this.UpdateSpellListHiddenInput(TargetContainer);
        }
        this.EvaluateCharacterSheetDirtyState();
    },

    UpdateSpellListHiddenInput: function (ListContainerElement) {
        if (!ListContainerElement) {
            return;
        }
        const SpellEntries = ListContainerElement.querySelectorAll(".SpellListSpellEntry");
        const Names = [];
        SpellEntries.forEach(function (Entry) {
            const Label = Entry.querySelector("span");
            if (Label && Label.textContent) {
                Names.push(Label.textContent.trim());
            }
        });
        const SpellsInput = ListContainerElement.querySelector(".SpellListSpellsInput");
        if (SpellsInput) {
            SpellsInput.value = Names.join(", ");
        }
    },

    RecalculateSpellListStats: function (ListContainerElement) {
        if (!ListContainerElement) {
            return;
        }
        const AbilitySelect = ListContainerElement.querySelector(".SpellListAbilitySelect");
        const AbilityInput = ListContainerElement.querySelector(".SpellListAbilityInput");
        const SelectedAbility = AbilitySelect ? AbilitySelect.value : "None";
        if (AbilityInput) {
            AbilityInput.value = SelectedAbility;
        }

        const ModElement = ListContainerElement.querySelector(".SpellListStatModifier");
        const AttackElement = ListContainerElement.querySelector(".SpellListStatAttack");
        const SaveElement = ListContainerElement.querySelector(".SpellListStatSaveDC");

        if (!SelectedAbility || SelectedAbility === "None") {
            if (ModElement) { ModElement.textContent = "—"; }
            if (AttackElement) { AttackElement.textContent = "—"; }
            if (SaveElement) { SaveElement.textContent = "—"; }
            return;
        }

        const ScoreField = document.getElementById("CharacterSheet" + SelectedAbility + "Input");
        const ScoreVal = ScoreField ? (parseInt(ScoreField.value, 10) || 10) : 10;
        const AbilityModifier = Math.floor((ScoreVal - 10) / 2);
        const ProfBonusField = document.getElementById("CharacterSheetProficiencyBonusInput");
        const ProficiencyBonus = ProfBonusField ? (parseInt(ProfBonusField.value, 10) || 2) : 2;

        const AttackBonus = ProficiencyBonus + AbilityModifier;
        const SaveDC = 8 + ProficiencyBonus + AbilityModifier;

        if (ModElement) {
            ModElement.textContent = (AbilityModifier >= 0 ? "+" : "") + AbilityModifier;
        }
        if (AttackElement) {
            AttackElement.textContent = (AttackBonus >= 0 ? "+" : "") + AttackBonus;
        }
        if (SaveElement) {
            SaveElement.textContent = SaveDC.toString();
        }
    },

    RecalculateAllSpellListStats: function () {
        const ListContainer = document.getElementById("CharacterSheetSpellListContainer");
        if (!ListContainer) {
            return;
        }
        const Containers = ListContainer.querySelectorAll(".SpellListContainer");
        const AppRef = this;
        Containers.forEach(function (Container) {
            AppRef.RecalculateSpellListStats(Container);
        });
    }
};

$(document).ready(function () {
    DesktopApplication.Initialize();
});
