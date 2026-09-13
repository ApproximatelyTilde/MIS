const WindowManager = {
    TopZIndex: 100,
    BottomZIndex: 90,
    ActiveWindow: null,
    LastActiveClientWindow: null,
    WindowInteractionHistory: [],
    Windows: {},
    IsPlacementActive: false,
    JustFinishedPlacement: false,
    IsDraggingWindow: false,
    JustFinishedDragging: false,
    PlacementConfig: null,
    LastPointerX: 100,
    LastPointerY: 60,

    Initialize: function () {
        SystemDebugger.LogMessage("DEBUG", "Window Manager Initialized: ZRange=" + this.BottomZIndex + ".." + this.TopZIndex);
        window.WindowManager = this;
        $(document).on("mousemove", function (Event) {
            WindowManager.LastPointerX = Event.clientX;
            WindowManager.LastPointerY = Event.clientY;
        });


        $(document).on("mousedown", ".DesktopWindow", function (Event) {
            if (Event.button !== 0) {
                return;
            }
            if ($(Event.target).closest(".WindowTitlebar").length > 0) {
                return;
            }
            const WindowID = $(this).attr("id");
            if (WindowID) {
                WindowManager.RecordWindowInteraction(WindowID);
                if (WindowManager.ActiveWindow !== WindowID) {
                    WindowManager.FocusWindow(WindowID);
                }
            }
        });

        $(document).on("click", ".WindowControlMinimizeButton", function (Event) {
            Event.stopPropagation();
            const WindowID = $(this).closest(".DesktopWindow").attr("id");
            WindowManager.MinimizeWindow(WindowID);
        });

        $(document).on("dblclick", ".WindowTitlebar", function (Event) {
            if ($(Event.target).closest(".WindowControlButton").length > 0) {
                return;
            }
            const WindowID = $(this).closest(".DesktopWindow").attr("id");
            WindowManager.ToggleMaximizeWindow(WindowID);
        });
    },

    RecordWindowInteraction: function (WindowID) {
        if (!WindowID) {
            return;
        }
        this.WindowInteractionHistory = this.WindowInteractionHistory.filter(function (ExistingID) {
            return ExistingID !== WindowID;
        });
        this.WindowInteractionHistory.push(WindowID);
    },

    ActivateLastInteractedWindow: function () {
        for (let Index = this.WindowInteractionHistory.length - 1; Index >= 0; Index -= 1) {
            const CandidateID = this.WindowInteractionHistory[Index];
            const CandidateElement = $(`#${CandidateID}`);
            if (CandidateElement.length > 0 && !CandidateElement.hasClass("MinimizedWindow") && CandidateElement.is(":visible")) {
                this.FocusWindow(CandidateID);
                return;
            }
        }
    },

    FocusWindow: function (WindowID) {
        const WindowElement = $(`#${WindowID}`);
        if (!WindowElement.length) {
            return;
        }
        this.RecordWindowInteraction(WindowID);
        this.TopZIndex += 1;
        SystemDebugger.LogMessage("DEBUG", "Window Focused: \"" + WindowID + "\" (ZIndex=" + this.TopZIndex + ")");
        WindowElement.css("z-index", this.TopZIndex);
        $(".DesktopWindow").removeClass("ActiveWindow");
        WindowElement.removeClass("MinimizedWindow").show().addClass("ActiveWindow");
        this.ActiveWindow = WindowID;
        if (WindowID !== "WindowApplicationLauncher") {
            this.LastActiveClientWindow = WindowID;
            if (window.DesktopApplication) {
                DesktopApplication.CloseLaunchpadSubmenus();
            }
        }
        this.RemoveIconBox(WindowID);
        if (window.DesktopApplication) {
            DesktopApplication.ZoomIntoScreen();
        }
    },

    LowerWindow: function (WindowID) {
        const WindowElement = $(`#${WindowID}`);
        if (!WindowElement.length) {
            return;
        }
        this.BottomZIndex -= 1;
        SystemDebugger.LogMessage("DEBUG", "Window Lowered: \"" + WindowID + "\" (ZIndex=" + this.BottomZIndex + ")");
        WindowElement.css("z-index", this.BottomZIndex);
        WindowElement.removeClass("ActiveWindow");
        if (this.ActiveWindow === WindowID) {
            this.ActiveWindow = null;
            const OpenWindows = $(".DesktopWindow").not(".MinimizedWindow").not(`#${WindowID}`);
            if (OpenWindows.length > 0) {
                let HighestZIndex = -Infinity;
                let TopWindowID = null;
                OpenWindows.each(function () {
                    const CurrentZIndex = parseInt($(this).css("z-index"), 10) || 0;
                    if (CurrentZIndex > HighestZIndex) {
                        HighestZIndex = CurrentZIndex;
                        TopWindowID = $(this).attr("id");
                    }
                });
                if (TopWindowID) {
                    $(`#${TopWindowID}`).addClass("ActiveWindow");
                    this.ActiveWindow = TopWindowID;
                    this.RecordWindowInteraction(TopWindowID);
                    if (TopWindowID !== "WindowApplicationLauncher") {
                        this.LastActiveClientWindow = TopWindowID;
                    }
                }
            }
        }
    },

    CancelWindowPlacement: function () {
        if (!this.IsPlacementActive) {
            return;
        }
        SystemDebugger.LogMessage("DEBUG", "Window Placement Cancelled: \"" + (this.PlacementConfig ? this.PlacementConfig.ID : "None") + "\"");
        this.IsPlacementActive = false;
        this.JustFinishedPlacement = true;
        setTimeout(() => {
            WindowManager.JustFinishedPlacement = false;
        }, 150);
        this.PlacementConfig = null;
        $("#WindowPlacementGrid").remove();
        $("#WindowResizeGrid").remove();
        $(document).off(".WindowPlacementNamespace");
        $(window).off(".WindowPlacementNamespace");
    },

    BeginWindowPlacement: function (Config) {
        this.CancelWindowPlacement();
        this.IsPlacementActive = true;
        this.PlacementConfig = Config;

        const DesktopElement = document.getElementById("DesktopContainer");
        const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 960;
        const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 720;

        let CurrentWidth = Math.floor(Math.min(Config.Width || 640, Math.max(Config.MinWidth || 200, AvailableWidth - 40)) / 4) * 4;
        let CurrentHeight = Math.floor(Math.min(Config.Height || 480, Math.max(Config.MinHeight || 150, AvailableHeight - 40)) / 4) * 4;
        SystemDebugger.LogMessage("DEBUG", "Window Placement Started: \"" + Config.ID + "\" (Initial=" + CurrentWidth + "x" + CurrentHeight + ")");

        const ComputeDesktopCoordinates = (ClientX, ClientY) => {
            if (!DesktopElement) {
                return {
                    RelativeX: ClientX,
                    RelativeY: ClientY
                };
            }
            const DesktopRectangle = DesktopElement.getBoundingClientRect();
            const ScaleFactorX = DesktopElement.offsetWidth / (DesktopRectangle.width || 1);
            const ScaleFactorY = DesktopElement.offsetHeight / (DesktopRectangle.height || 1);
            const RelativeX = (ClientX - DesktopRectangle.left) * ScaleFactorX;
            const RelativeY = (ClientY - DesktopRectangle.top) * ScaleFactorY;
            return {
                RelativeX: RelativeX,
                RelativeY: RelativeY
            };
        };

        let InitialCoordinates = ComputeDesktopCoordinates(this.LastPointerX, this.LastPointerY);
        let CurrentLeft = Math.max(0, Math.min(AvailableWidth - 40, Math.round(InitialCoordinates.RelativeX / 4) * 4));
        let CurrentTop = Math.max(0, Math.min(AvailableHeight - 40, Math.round(InitialCoordinates.RelativeY / 4) * 4));

        const IsResizable = Config.IsResizable !== false;
        let IsMiddleResizing = false;
        let IsInteractiveSizing = false;
        let HasMiddleResized = false;
        let ResizeAnchorLeft = CurrentLeft;
        let ResizeAnchorTop = CurrentTop;
        let IsPlacementReady = false;

        setTimeout(() => {
            IsPlacementReady = true;
        }, 10);

        const GridHTML = `
      <div id="WindowPlacementGrid" class="WindowPlacementGrid">
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
        <div class="WindowPlacementGridCell"></div>
      </div>
    `;

        $("#DesktopContainer").append(GridHTML);
        const PlacementGrid = document.getElementById("WindowPlacementGrid");

        function UpdateGridGeometry() {
            if (!PlacementGrid) {
                return;
            }
            PlacementGrid.style.width = CurrentWidth + "px";
            PlacementGrid.style.height = CurrentHeight + "px";
            PlacementGrid.style.left = CurrentLeft + "px";
            PlacementGrid.style.top = CurrentTop + "px";
        }

        UpdateGridGeometry();

        $(window).on("mousemove.WindowPlacementNamespace", (Event) => {
            WindowManager.LastPointerX = Event.clientX;
            WindowManager.LastPointerY = Event.clientY;
            const Coordinates = ComputeDesktopCoordinates(Event.clientX, Event.clientY);

            if (IsResizable && (IsMiddleResizing || IsInteractiveSizing)) {
                HasMiddleResized = true;
                const DeltaWidth = Coordinates.RelativeX - ResizeAnchorLeft;
                const DeltaHeight = Coordinates.RelativeY - ResizeAnchorTop;
                const MaximumWidth = AvailableWidth - ResizeAnchorLeft;
                const MaximumHeight = AvailableHeight - ResizeAnchorTop;
                const WindowConfiguration = Config || {};
                const MinimumWidth = WindowConfiguration.MinWidth || 200;
                const MinimumHeight = WindowConfiguration.MinHeight || 150;
                CurrentWidth = Math.max(MinimumWidth, Math.min(MaximumWidth, Math.round(DeltaWidth / 4) * 4));
                CurrentHeight = Math.max(MinimumHeight, Math.min(MaximumHeight, Math.round(DeltaHeight / 4) * 4));
            } else {
                const MaximumLeft = AvailableWidth - 40;
                const MaximumTop = AvailableHeight - 40;
                CurrentLeft = Math.max(0, Math.min(MaximumLeft, Math.round(Coordinates.RelativeX / 4) * 4));
                CurrentTop = Math.max(0, Math.min(MaximumTop, Math.round(Coordinates.RelativeY / 4) * 4));
                ResizeAnchorLeft = CurrentLeft;
                ResizeAnchorTop = CurrentTop;
            }
            UpdateGridGeometry();
        });

        $(window).on("mousedown.WindowPlacementNamespace", (Event) => {
            if (!IsPlacementReady) {
                return;
            }
            Event.preventDefault();
            Event.stopPropagation();

            if (Event.button === 1 && IsResizable) {
                IsMiddleResizing = true;
                HasMiddleResized = false;
                ResizeAnchorLeft = CurrentLeft;
                ResizeAnchorTop = CurrentTop;
                return;
            }

            if (Event.button === 0) {
                WindowManager.FinalizeWindowPlacement(Config, CurrentLeft, CurrentTop, CurrentWidth, CurrentHeight);
                return;
            }

            if (Event.button === 2) {
                if (IsResizable) {
                    const MaximumVerticalHeight = AvailableHeight - CurrentTop;
                    CurrentHeight = Math.max(160, Math.floor(MaximumVerticalHeight / 4) * 4);
                }
                WindowManager.FinalizeWindowPlacement(Config, CurrentLeft, CurrentTop, CurrentWidth, CurrentHeight);
                return;
            }
        });

        $(window).on("mouseup.WindowPlacementNamespace", (Event) => {
            if (!IsPlacementReady) {
                return;
            }
            if (Event.button === 1 && IsMiddleResizing) {
                Event.preventDefault();
                Event.stopPropagation();
                IsMiddleResizing = false;
                if (HasMiddleResized) {
                    WindowManager.FinalizeWindowPlacement(Config, ResizeAnchorLeft, ResizeAnchorTop, CurrentWidth, CurrentHeight);
                } else {
                    IsInteractiveSizing = !IsInteractiveSizing;
                }
            }
        });

        $(window).on("contextmenu.WindowPlacementNamespace", (Event) => {
            Event.preventDefault();
            Event.stopPropagation();
        });

        $(window).on("keydown.WindowPlacementNamespace", (Event) => {
            if (Event.key === "Escape") {
                WindowManager.CancelWindowPlacement();
            }
        });
    },

    FinalizeWindowPlacement: function (Config, Left, Top, Width, Height) {
        this.CancelWindowPlacement();
        this.InstantiateWindow(Config, Left, Top, Width, Height);
    },

    InstantiateWindow: function (Config, Left, Top, Width, Height) {
        const {
            ID,
            Title,
            ContentHTML = "",
            ContentURL = null
        } = Config;
        const IsResizable = Config.IsResizable !== false;
        const ResizeButtonHTML = IsResizable ? `
          <button class="WindowControlButton WindowControlResizeButton" type="button" title="Resize">
            <span class="WindowButtonIcon WindowButtonIconResize" aria-hidden="true"></span>
          </button>
        ` : "";
        const WindowHTML = `
      <div id="${ID}" class="DesktopWindow ActiveWindow">
        <div class="WindowTitlebar" id="WindowTitlebar_${ID}">
          <button class="WindowControlButton WindowControlMinimizeButton" type="button" title="Iconify">
            <span class="WindowButtonIcon WindowButtonIconMinimize" aria-hidden="true"></span>
          </button>
          <span class="WindowTitle">${Title}</span>
          ${ResizeButtonHTML}
        </div>
        <div class="WindowTitleDivider"></div>
        <div class="WindowContent" id="WindowContent_${ID}">
          ${ContentHTML}
        </div>
      </div>
    `;

        $("#DesktopContainer").append(WindowHTML);
        const WindowElement = $(`#${ID}`);
        WindowElement.css({
            "width": `${Width}px`,
            "height": `${Height}px`,
            "left": `${Left}px`,
            "top": `${Top}px`,
            "--WindowLeft": `${Left}px`,
            "--WindowTop": `${Top}px`,
            "z-index": ++this.TopZIndex
        });
        SystemDebugger.LogMessage("DEBUG", "Window Instantiated: \"" + ID + "\" (" + Width + "x" + Height + "@" + Left + "," + Top + ", Z=" + this.TopZIndex + ")");
        if (Config.MinWidth) {
            WindowElement.css("min-width", `${Config.MinWidth}px`);
        }
        if (Config.MinHeight) {
            WindowElement.css("min-height", `${Config.MinHeight}px`);
        }
        const WindowDomNode = document.getElementById(ID);
        if (window.htmx && WindowDomNode) {
            htmx.process(WindowDomNode);
        }
        this.Windows[ID] = Config;
        this.MakeDraggable(ID);
        if (IsResizable) {
            this.MakeResizable(ID);
        }
        this.FocusWindow(ID);
        if (ContentURL) {
            this.LoadWindowContent(ID, ContentURL);
        }
    },

    OpenWindow: function (Config) {
        SystemDebugger.LogMessage("DEBUG", "Window Open Requested: \"" + Config.ID + "\" (BypassPlacement=" + (!!Config.BypassPlacement) + ")");
        const {
            ID,
            Width = 640,
            Height = 480,
            Left = 100,
            Top = 60
        } = Config;
        if ($(`#${ID}`).length) {
            if (Config.ContentURL && (!this.Windows[ID] || (this.Windows[ID].ContentURL !== Config.ContentURL) || (ID === "WindowCharacterSheet"))) {
                this.Windows[ID] = Config;
                if (Config.Title) {
                    this.SetWindowTitle(ID, Config.Title);
                }

                this.LoadWindowContent(ID, Config.ContentURL);
            }

            else if (Config.ContentHTML) {
                this.Windows[ID] = Config;
                if (Config.Title) {
                    this.SetWindowTitle(ID, Config.Title);
                }

                $(`#WindowContent_${ID}`).html(Config.ContentHTML);
            }

            this.RestoreWindow(ID);
            return;
        }

        if (Config.BypassPlacement) {
            const OffsetShift = (Object.keys(this.Windows).length % 6) * 24;
            const DesktopElement = document.getElementById("DesktopContainer");
            const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 960;
            const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 720;
            const TargetWidth = Math.floor(Math.min(Width, Math.max(Config.MinWidth || 160, AvailableWidth - 40)) / 4) * 4;
            const TargetHeight = Math.floor(Math.min(Height, Math.max(Config.MinHeight || 120, AvailableHeight - 40)) / 4) * 4;
            const TargetLeft = Math.floor(Math.min(Left + OffsetShift, Math.max(0, AvailableWidth - TargetWidth - 20)) / 4) * 4;
            const TargetTop = Math.floor(Math.min(Top + OffsetShift, Math.max(0, AvailableHeight - TargetHeight - 20)) / 4) * 4;
            this.InstantiateWindow(Config, TargetLeft, TargetTop, TargetWidth, TargetHeight);
            return;
        }

        this.BeginWindowPlacement(Config);
    },

    LoadWindowContent: async function (ID, URL) {
        try {
            const Response = await fetch(URL);
            const HTML = await Response.text();
            const ContentTarget = $(`#WindowContent_${ID}`);
            ContentTarget.html(HTML);
            const ContentDomNode = document.getElementById(`WindowContent_${ID}`);
            if (window.htmx && ContentDomNode) {
                htmx.process(ContentDomNode);
            }
            if (window.DesktopApplication && ContentDomNode) {
                DesktopApplication.InitializeAutoResizeTextareas(ContentDomNode);
                if (ID === "WindowCharacterSheet") {
                    DesktopApplication.InitializeAbilitiesTab(ContentDomNode);
                    DesktopApplication.InitializeInventoryTab(ContentDomNode);
                    DesktopApplication.InitializeCharacterSheetBaseline();
                    DesktopApplication.EvaluateCharacterSheetDirtyState();
                }
                if (ID === "WindowSearchCharacters") {
                    DesktopApplication.AdjustSearchCharactersSortSelectWidth();
                }
                if (ID === "WindowClock") {
                    if (window.DesktopMonitoringClients) {
                        DesktopMonitoringClients.UpdateClockHands();
                    }
                }
            }
            if (window.CharacterSheetFuzzySearch && ContentDomNode) {
                CharacterSheetFuzzySearch.InitializeAllTagContainers(ContentDomNode);
            }
            SystemDebugger.LogMessage("DEBUG", "Window Content Loaded: \"" + ID + "\" (" + HTML.length + " Chars, URL=\"" + URL + "\")");
        } catch (Error) {
            SystemDebugger.LogMessage("DEBUG", "Window Content Failed: \"" + ID + "\" (URL=\"" + URL + "\", Error=" + Error.message + ")");
            $(`#WindowContent_${ID}`).html('<div class="TerminalPane MarginTopMedium"><div class="TextDanger HeaderText MarginBottomSmall">CONNECTION FAILED</div><div class="TextMuted">Unable to establish connection to load window content.</div></div>');
        }
    },

    CloseWindow: function (WindowID) {
        SystemDebugger.LogMessage("DEBUG", "Window Closed: \"" + WindowID + "\"");
        this.RemoveIconBox(WindowID);
        if (WindowID === "WindowSearchCharacters") {
            $("#SearchCharactersFilterModal").remove();
        }
        $("#WindowResizeGrid").remove();
        $(`#${WindowID}`).remove();
        delete this.Windows[WindowID];
        this.WindowInteractionHistory = this.WindowInteractionHistory.filter(function (ExistingID) {
            return ExistingID !== WindowID;
        });
        if (this.ActiveWindow === WindowID) {
            this.ActiveWindow = null;
            this.ActivateLastInteractedWindow();
        }
        if (this.LastActiveClientWindow === WindowID) {
            const RemainingWindows = $(".DesktopWindow").not("#WindowApplicationLauncher");
            if (RemainingWindows.length > 0) {
                this.LastActiveClientWindow = RemainingWindows.last().attr("id");
            } else {
                this.LastActiveClientWindow = null;
            }
        }
    },

    MinimizeWindow: function (WindowID) {
        SystemDebugger.LogMessage("DEBUG", "Window Minimized: \"" + WindowID + "\"");
        const WindowElement = $(`#${WindowID}`);
        if (!WindowElement.length) {
            return;
        }
        WindowElement.hide().addClass("MinimizedWindow").removeClass("ActiveWindow");
        if (this.ActiveWindow === WindowID) {
            this.ActiveWindow = null;
        }
        const Config = this.Windows[WindowID];
        const WindowTitle = Config && Config.Title ? Config.Title : WindowID;
        this.CreateIconBox(WindowID, WindowTitle);
        if (!this.ActiveWindow) {
            this.ActivateLastInteractedWindow();
        }
    },

    RestoreWindow: function (WindowID) {
        SystemDebugger.LogMessage("DEBUG", "Window Restored: \"" + WindowID + "\"");
        const WindowElement = $(`#${WindowID}`);
        if (!WindowElement.length) {
            return;
        }
        this.RemoveIconBox(WindowID);
        this.FocusWindow(WindowID);
    },

    SetWindowTitle: function (WindowID, NewTitle) {
        SystemDebugger.LogMessage("DEBUG", "Window Title Updated: \"" + WindowID + "\" -> \"" + NewTitle + "\"");
        const WindowElement = $(`#${WindowID}`);
        if (!WindowElement.length) {
            return;
        }
        WindowElement.find(".WindowTitle").first().text(NewTitle);
        if (this.Windows[WindowID]) {
            this.Windows[WindowID].Title = NewTitle;
        }
        $(`#iconbox-${WindowID} .DesktopIconBoxTitle`).text(NewTitle);
    },

    DeleteTargetWindow: function () {
        let TargetID = this.LastActiveClientWindow;
        if (!TargetID || !$(`#${TargetID}`).length) {
            const OpenWindows = $(".DesktopWindow").not("#WindowApplicationLauncher");
            if (OpenWindows.length > 0) {
                TargetID = OpenWindows.last().attr("id");
            }
        }
        if (TargetID && $(`#${TargetID}`).length) {
            this.CloseWindow(TargetID);
        }
    },

    CreateIconBox: function (WindowID, WindowTitle) {
        if ($(`#DesktopIcon_${WindowID}`).length) {
            return;
        }
        const ExistingIcons = $(".DesktopIconBox");
        const OccupiedTops = new Set();
        ExistingIcons.each(function () {
            OccupiedTops.add(parseInt($(this).css("top"), 10));
        });
        const DesktopElement = document.getElementById("DesktopContainer");
        const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 960;
        const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 720;
        let TargetLeft = Math.max(300, AvailableWidth - 200);
        TargetLeft = Math.round(TargetLeft / 4) * 4;
        let SlotIndex = 0;
        let TargetTop = 24;
        while (OccupiedTops.has(TargetTop)) {
            SlotIndex += 1;
            TargetTop = 24 + SlotIndex * 36;
        }
        TargetTop = Math.round(Math.min(AvailableHeight - 40, TargetTop) / 4) * 4;
        const IconHTML = `
      <div id="DesktopIcon_${WindowID}" class="DesktopIconBox" data-window-id="${WindowID}">
        <button class="WindowControlButton WindowControlRestoreButton" type="button" title="Restore">
          <span class="WindowButtonIcon WindowButtonIconMinimize" aria-hidden="true"></span>
        </button>
        <span class="DesktopIconBoxTitle">${WindowTitle}</span>
      </div>
    `;
        $("#DesktopContainer").append(IconHTML);
        const IconElement = $(`#DesktopIcon_${WindowID}`);
        IconElement.css({
            "left": `${TargetLeft}px`,
            "top": `${TargetTop}px`,
            "--IconLeft": `${TargetLeft}px`,
            "--IconTop": `${TargetTop}px`
        });
        SystemDebugger.LogMessage("DEBUG", "Icon Box Created: Window=\"" + WindowID + "\", Pos=" + TargetLeft + "," + TargetTop);
        this.MakeIconDraggable(`DesktopIcon_${WindowID}`);
    },

    RemoveIconBox: function (WindowID) {
        SystemDebugger.LogMessage("DEBUG", "Icon Box Removed: Window=\"" + WindowID + "\"");
        $(`#DesktopIcon_${WindowID}`).remove();
    },

    ResetWindowManager: function () {
        SystemDebugger.LogMessage("DEBUG", "Window Manager State Reset: " + Object.keys(this.Windows).length + " Windows Cleared");
        this.CancelWindowPlacement();
        $(".DesktopWindow").remove();
        $(".DesktopIconBox").remove();
        $("#WindowPlacementGrid").remove();
        $("#WindowResizeGrid").remove();
        this.Windows = {};
        this.WindowInteractionHistory = [];
        this.ActiveWindow = null;
        this.LastActiveClientWindow = null;
        this.TopZIndex = 100;
        this.BottomZIndex = 90;
        this.IsPlacementActive = false;
        this.JustFinishedPlacement = false;
        this.IsDraggingWindow = false;
        this.JustFinishedDragging = false;
        this.PlacementConfig = null;
        $(document).off(".WindowPlacementNamespace");
    },

    MakeIconDraggable: function (IconID) {
        const IconDOMElement = document.getElementById(IconID);
        if (!IconDOMElement) {
            return;
        }
        let StartMouseX = 0;
        let StartMouseY = 0;
        let StartLeft = 0;
        let StartTop = 0;

        IconDOMElement.onmousedown = function (Event) {
            if ($(Event.target).closest(".WindowControlRestoreButton").length > 0) {
                return;
            }
            WindowManager.IsDraggingWindow = true;
            StartMouseX = Event.clientX;
            StartMouseY = Event.clientY;
            StartLeft = IconDOMElement.offsetLeft;
            StartTop = IconDOMElement.offsetTop;

            document.onmousemove = function (MoveEvent) {
                MoveEvent.preventDefault();
                WindowManager.IsDraggingWindow = true;
                const DeltaX = MoveEvent.clientX - StartMouseX;
                const DeltaY = MoveEvent.clientY - StartMouseY;
                const DesktopElement = document.getElementById("DesktopContainer");
                const MaximumLeft = Math.max(0, DesktopElement.offsetWidth - IconDOMElement.offsetWidth);
                const MaximumTop = Math.max(0, DesktopElement.offsetHeight - IconDOMElement.offsetHeight);
                let NewLeft = Math.max(0, Math.min(MaximumLeft, StartLeft + DeltaX));
                let NewTop = Math.max(0, Math.min(MaximumTop, StartTop + DeltaY));
                NewLeft = Math.min(MaximumLeft, Math.max(0, Math.round(NewLeft / 4) * 4));
                NewTop = Math.min(MaximumTop, Math.max(0, Math.round(NewTop / 4) * 4));
                IconDOMElement.style.left = NewLeft + "px";
                IconDOMElement.style.top = NewTop + "px";
                IconDOMElement.style.setProperty("--IconLeft", NewLeft + "px");
                IconDOMElement.style.setProperty("--IconTop", NewTop + "px");
            };

            document.onmouseup = function () {
                document.onmousemove = null;
                document.onmouseup = null;
                WindowManager.IsDraggingWindow = false;
                WindowManager.JustFinishedDragging = true;
                setTimeout(() => {
                    WindowManager.JustFinishedDragging = false;
                }, 150);
            };
        };

        $(IconDOMElement).find(".WindowControlRestoreButton").on("click", function (Event) {
            Event.stopPropagation();
            const WindowID = $(IconDOMElement).attr("data-window-id");
            WindowManager.RestoreWindow(WindowID);
        });
    },

    ToggleMaximizeWindow: function (WindowID) {
        const WindowElement = $(`#${WindowID}`);
        const IsCurrentlyMaximized = WindowElement.hasClass("MaximizedWindow");
        SystemDebugger.LogMessage("DEBUG", "Window Maximize Toggled: \"" + WindowID + "\" (Maximized=" + (!IsCurrentlyMaximized) + ")");
        if (IsCurrentlyMaximized) {
            const PreviousPosition = WindowElement.data("prev-pos");
            WindowElement.css({
                "left": PreviousPosition.left,
                "top": PreviousPosition.top,
                "--WindowLeft": PreviousPosition.left,
                "--WindowTop": PreviousPosition.top,
                "width": PreviousPosition.width,
                "height": PreviousPosition.height
            }).removeClass("MaximizedWindow");
        } else {
            WindowElement.data("prev-pos", {
                "left": WindowElement.css("left"),
                "top": WindowElement.css("top"),
                "width": WindowElement.css("width"),
                "height": WindowElement.css("height")
            });
            WindowElement.css({
                "left": "0px",
                "top": "0px",
                "--WindowLeft": "0px",
                "--WindowTop": "0px",
                "width": "100%",
                "height": "100%"
            }).addClass("MaximizedWindow");
        }
        this.FocusWindow(WindowID);
    },

    MakeDraggable: function (ID) {
        const WindowDOMElement = document.getElementById(ID);
        const TitlebarElement = document.getElementById(`WindowTitlebar_${ID}`);
        let StartMouseX = 0;
        let StartMouseY = 0;
        let StartWindowLeft = 0;
        let StartWindowTop = 0;

        TitlebarElement.onmousedown = DragMouseDown;

        function DragMouseDown(Event) {
            if (Event.button !== 0) {
                return;
            }
            if ($(Event.target).closest(".WindowControlButton").length > 0) {
                return;
            }
            WindowManager.RecordWindowInteraction(ID);
            if (WindowManager.ActiveWindow !== ID) {
                WindowManager.FocusWindow(ID);
            }
            WindowManager.IsDraggingWindow = true;
            Event.preventDefault();
            StartMouseX = Event.clientX;
            StartMouseY = Event.clientY;
            StartWindowLeft = WindowDOMElement.offsetLeft;
            StartWindowTop = WindowDOMElement.offsetTop;
            document.onmouseup = CloseDragElement;
            document.onmousemove = ElementDrag;
        }

        function ElementDrag(Event) {
            Event.preventDefault();
            WindowManager.IsDraggingWindow = true;
            const DeltaX = Event.clientX - StartMouseX;
            const DeltaY = Event.clientY - StartMouseY;
            const DesktopElement = document.getElementById("DesktopContainer");
            const MaximumLeft = Math.max(0, DesktopElement.offsetWidth - WindowDOMElement.offsetWidth);
            const MaximumTop = Math.max(0, DesktopElement.offsetHeight - WindowDOMElement.offsetHeight);
            let NewLeft = Math.max(0, Math.min(MaximumLeft, StartWindowLeft + DeltaX));
            let NewTop = Math.max(0, Math.min(MaximumTop, StartWindowTop + DeltaY));
            NewLeft = Math.min(MaximumLeft, Math.max(0, Math.round(NewLeft / 4) * 4));
            NewTop = Math.min(MaximumTop, Math.max(0, Math.round(NewTop / 4) * 4));
            WindowDOMElement.style.left = NewLeft + "px";
            WindowDOMElement.style.top = NewTop + "px";
            WindowDOMElement.style.setProperty("--WindowLeft", NewLeft + "px");
            WindowDOMElement.style.setProperty("--WindowTop", NewTop + "px");
        }

        function CloseDragElement() {
            document.onmouseup = null;
            document.onmousemove = null;
            WindowManager.IsDraggingWindow = false;
            WindowManager.JustFinishedDragging = true;
            setTimeout(() => {
                WindowManager.JustFinishedDragging = false;
            }, 150);
        }
    },

    MakeResizable: function (ID) {
        const WindowDOMElement = document.getElementById(ID);
        const ResizeButton = WindowDOMElement.querySelector(".WindowControlResizeButton");

        if (ResizeButton) {
            ResizeButton.addEventListener("mousedown", StartResizeFromButton);
        }

        function StartResizeFromButton(Event) {
            Event.preventDefault();
            Event.stopPropagation();
            WindowManager.FocusWindow(ID);
            WindowManager.IsDraggingWindow = true;
            ResizeButton.classList.add("WindowControlButtonActive");
            const StartMouseX = Event.clientX;
            const StartMouseY = Event.clientY;
            const StartWidth = WindowDOMElement.offsetWidth;
            const StartHeight = WindowDOMElement.offsetHeight;
            const WindowLeft = WindowDOMElement.offsetLeft;
            const WindowTop = WindowDOMElement.offsetTop;
            const DesktopElement = document.getElementById("DesktopContainer");
            const DesktopRectangle = (DesktopElement !== null) ? DesktopElement.getBoundingClientRect() : { width: 1, height: 1 };
            const ScaleFactorX = (DesktopElement !== null) ? (DesktopElement.offsetWidth / (DesktopRectangle.width || 1)) : 1;
            const ScaleFactorY = (DesktopElement !== null) ? (DesktopElement.offsetHeight / (DesktopRectangle.height || 1)) : 1;
            const MaximumWidth = (DesktopElement !== null) ? (DesktopElement.offsetWidth - WindowLeft) : 960;
            const MaximumHeight = (DesktopElement !== null) ? (DesktopElement.offsetHeight - WindowTop) : 720;
            const WindowConfiguration = WindowManager.Windows[ID] || {};
            const MinimumWidth = WindowConfiguration.MinWidth || 200;
            const MinimumHeight = WindowConfiguration.MinHeight || 150;
            let CurrentWidth = StartWidth;
            let CurrentHeight = StartHeight;
            document.body.style.cursor = "se-resize";

            $("#WindowResizeGrid").remove();
            const GridHTML = `
      <div id="WindowResizeGrid" class="WindowResizeGrid">
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div class="WindowResizeGridCell"></div>
        <div id="WindowResizeGeometryBadge" class="WindowResizeGeometryBadge">${CurrentWidth} × ${CurrentHeight}</div>
      </div>
    `;

            $("#DesktopContainer").append(GridHTML);
            const ResizeGrid = document.getElementById("WindowResizeGrid");
            const GeometryBadge = document.getElementById("WindowResizeGeometryBadge");

            function UpdateGridGeometry() {
                if (!ResizeGrid) {
                    return;
                }

                ResizeGrid.style.left = WindowLeft + "px";
                ResizeGrid.style.top = WindowTop + "px";
                ResizeGrid.style.width = CurrentWidth + "px";
                ResizeGrid.style.height = CurrentHeight + "px";
                if (GeometryBadge) {
                    GeometryBadge.textContent = CurrentWidth + " × " + CurrentHeight;
                }
            }

            UpdateGridGeometry();

            function PerformResize(MoveEvent) {
                MoveEvent.preventDefault();
                WindowManager.IsDraggingWindow = true;
                const DeltaX = (MoveEvent.clientX - StartMouseX) * ScaleFactorX;
                const DeltaY = (MoveEvent.clientY - StartMouseY) * ScaleFactorY;
                CurrentWidth = Math.max(MinimumWidth, Math.min(MaximumWidth, Math.round((StartWidth + DeltaX) / 4) * 4));
                CurrentHeight = Math.max(MinimumHeight, Math.min(MaximumHeight, Math.round((StartHeight + DeltaY) / 4) * 4));
                UpdateGridGeometry();
            }

            function StopResize() {
                document.body.style.cursor = "";
                window.removeEventListener("mousemove", PerformResize);
                window.removeEventListener("mouseup", StopResize);
                window.removeEventListener("keydown", HandleKeyDown);
                ResizeButton.classList.remove("WindowControlButtonActive");
                if (ResizeGrid) {
                    ResizeGrid.remove();
                }

                WindowDOMElement.style.width = CurrentWidth + "px";
                WindowDOMElement.style.height = CurrentHeight + "px";
                SystemDebugger.LogMessage("DEBUG", "Window Resized: \"" + ID + "\" (" + CurrentWidth + "x" + CurrentHeight + ")");
                WindowManager.IsDraggingWindow = false;
                WindowManager.JustFinishedDragging = true;
                setTimeout(() => {
                    WindowManager.JustFinishedDragging = false;
                }, 150);
            }

            function HandleKeyDown(KeyEvent) {
                if (KeyEvent.key === "Escape") {
                    document.body.style.cursor = "";
                    window.removeEventListener("mousemove", PerformResize);
                    window.removeEventListener("mouseup", StopResize);
                    window.removeEventListener("keydown", HandleKeyDown);
                    ResizeButton.classList.remove("WindowControlButtonActive");
                    if (ResizeGrid) {
                        ResizeGrid.remove();
                    }

                    WindowManager.IsDraggingWindow = false;
                    WindowManager.JustFinishedDragging = true;
                    setTimeout(() => {
                        WindowManager.JustFinishedDragging = false;
                    }, 150);
                }
            }

            window.addEventListener("mousemove", PerformResize);
            window.addEventListener("mouseup", StopResize);
            window.addEventListener("keydown", HandleKeyDown);
        }
    }
};

$(document).ready(function () {
    WindowManager.Initialize();
});
