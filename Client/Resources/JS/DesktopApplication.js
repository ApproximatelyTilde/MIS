const DesktopApplication = {
    ContextMenuTargetWindow: null,
    PendingSystemAction: null,
    LastDesktopClickTimestamp: 0,
    PointerDownInsideScreen: false,
    PointerDownPositionX: 0,
    PointerDownPositionY: 0,

    Initialize: function () {
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

        $(document).on("click", ".OpenCharacterGeneratorButton", function () {
            DesktopApplication.OpenCharacterGeneratorWindow();
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
            $("#StorageFileInput").trigger("click");
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
    },

    CloseContextMenu: function () {
        $("#DesktopContextMenu").addClass("HiddenElement");
    },

    ShowSystemConfirmation: function (ActionType) {
        this.PendingSystemAction = ActionType;
        const TitleElement = $("#SystemConfirmationTitle");
        const MessageElement = $("#SystemConfirmationMessage");
        const ConfirmButtonLabel = $("#SystemConfirmationButtonConfirmLabel");
        const ConfirmButton = $("#SystemConfirmationButtonConfirm");

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
        this.PendingSystemAction = null;
        $("#SystemConfirmationModalContainer").addClass("HiddenElement");
    },

    ConfirmPendingSystemAction: function () {
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
        if (IsLauncherOpen) {
            WindowManager.CloseWindow("WindowApplicationLauncher");
        } else {
            this.OpenApplicationLauncherWindow();
        }
    },

    IconifyContextTargetWindow: function () {
        this.CloseContextMenu();
        const TargetIdentifier = this.ContextMenuTargetWindow || WindowManager.LastActiveClientWindow;
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
        if (TargetIdentifier) {
            WindowManager.LowerWindow(TargetIdentifier);
        }
    },

    DeleteContextTargetWindow: function () {
        this.CloseContextMenu();
        const TargetIdentifier = this.ContextMenuTargetWindow || WindowManager.LastActiveClientWindow;
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
            TargetTop = Math.max(0, Math.min(DesktopHeight - 192, TargetTop));
            TargetLeft = Math.round(TargetLeft / 4) * 4;
            TargetTop = Math.round(TargetTop / 4) * 4;
        }
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
            Height: 192,
            MinWidth: 200,
            MinHeight: 192,
            Left: TargetLeft,
            Top: TargetTop,
            ContentURL: "/API/Desktop/Windows/ApplicationLauncher",
            BypassPlacement: true
        };
        WindowManager.OpenWindow(Config);
    },

    OpenLaunchpadToolsSubmenu: function () {
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
        $("#LauncherToolsSubmenu").addClass("HiddenElement");
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
        $("#LauncherSystemSubmenu").addClass("HiddenElement");
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
        this.CloseLaunchpadToolsSubmenu();
        this.CloseLaunchpadSystemSubmenu();
    },

    OpenAccountCentreWindow: function () {
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowAccountCentre",
            Title: "Account Centre",
            Width: 700,
            Height: 500,
            MinWidth: 368,
            MinHeight: 252,
            Left: 220,
            Top: 30,
            ContentURL: "/API/Desktop/Windows/AccountCentre"
        };
        WindowManager.OpenWindow(Config);
    },

    OpenDiceRollerWindow: function () {
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

    OpenCharacterGeneratorWindow: function () {
        this.ZoomIntoScreen();
        const Config = {
            Identifier: "WindowCharacterGenerator",
            Title: "Character Generator",
            Width: 480,
            Height: 460,
            MinWidth: 324,
            MinHeight: 440,
            Left: 260,
            Top: 80,
            ContentURL: "/API/Desktop/Windows/CharacterGenerator"
        };
        WindowManager.OpenWindow(Config);
    },

    OpenCalendarWindow: function () {
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
        $(".AccountTabContent").addClass("HiddenElement");
        $(`#${TabIdentifier}`).removeClass("HiddenElement");
        $(".AccountTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
    },

    SwitchCalendarTab: function (TabIdentifier, ButtonElement) {
        $(".CalendarTabContent").addClass("HiddenElement");
        $(`#${TabIdentifier}`).removeClass("HiddenElement");
        $(".CalendarTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
    },

    SwitchCharacterGeneratorTab: function (TabIdentifier, ButtonElement) {
        $(".CharacterGeneratorTabContent").addClass("HiddenElement");
        $(`#${TabIdentifier}`).removeClass("HiddenElement");
        $(".CharacterGeneratorTabButton").removeClass("ActiveTab");
        $(ButtonElement).addClass("ActiveTab");
    },

    UpdateCharacterGeneratorControls: function () {
        const SelectedSystem = $("#CharacterGeneratorSystemSelect").val();
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
        const DNDNames = [
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
        const TravellerNames = [
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
        const NamePool = (SelectedSystem === "Traveller2ndEdition") ? TravellerNames : DNDNames;
        const CurrentName = $("#CharacterGeneratorNameInput").val();
        let AvailableNames = NamePool.filter((Name) => Name !== CurrentName);
        if (AvailableNames.length === 0) {
            AvailableNames = NamePool;
        }
        const ChosenName = AvailableNames[Math.floor(Math.random() * AvailableNames.length)];
        $("#CharacterGeneratorNameInput").val(ChosenName);
    },

    UpdateDiceControls: function () {
        const SelectedSystem = $("#DiceSystemSelect").val();
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
            document.body.classList.add("ZoomedIn");
            WorkstationTiltManager.DisableMotion();
        }
    },

    ZoomOutOfScreen: function () {
        if (document.body.classList.contains("ZoomedIn")) {
            document.body.classList.remove("ZoomedIn");
            WorkstationTiltManager.EnableMotion();
        }
    }
};

$(document).ready(function () {
    DesktopApplication.Initialize();
});
