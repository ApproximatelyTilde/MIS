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
    SystemDebugger.LogDebugMessage("Window Manager Initialized: ZRange=" + this.BottomZIndex + ".." + this.TopZIndex);
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
      const WindowIdentifier = $(this).attr("id");
      if (WindowIdentifier) {
        WindowManager.RecordWindowInteraction(WindowIdentifier);
        if (WindowManager.ActiveWindow !== WindowIdentifier) {
          WindowManager.FocusWindow(WindowIdentifier);
        }
      }
    });

    $(document).on("click", ".WindowControlMinimizeButton", function (Event) {
      Event.stopPropagation();
      const WindowIdentifier = $(this).closest(".DesktopWindow").attr("id");
      WindowManager.MinimizeWindow(WindowIdentifier);
    });

    $(document).on("dblclick", ".WindowTitlebar", function (Event) {
      if ($(Event.target).closest(".WindowControlButton").length > 0) {
        return;
      }
      const WindowIdentifier = $(this).closest(".DesktopWindow").attr("id");
      WindowManager.ToggleMaximizeWindow(WindowIdentifier);
    });
  },

  RecordWindowInteraction: function (WindowIdentifier) {
    if (!WindowIdentifier) {
      return;
    }
    this.WindowInteractionHistory = this.WindowInteractionHistory.filter(function (ExistingIdentifier) {
      return ExistingIdentifier !== WindowIdentifier;
    });
    this.WindowInteractionHistory.push(WindowIdentifier);
  },

  ActivateLastInteractedWindow: function () {
    for (let Index = this.WindowInteractionHistory.length - 1; Index >= 0; Index -= 1) {
      const CandidateIdentifier = this.WindowInteractionHistory[Index];
      const CandidateElement = $(`#${CandidateIdentifier}`);
      if (CandidateElement.length > 0 && !CandidateElement.hasClass("MinimizedWindow") && CandidateElement.is(":visible")) {
        this.FocusWindow(CandidateIdentifier);
        return;
      }
    }
  },

  FocusWindow: function (WindowIdentifier) {
    const WindowElement = $(`#${WindowIdentifier}`);
    if (!WindowElement.length) {
      return;
    }
    this.RecordWindowInteraction(WindowIdentifier);
    this.TopZIndex += 1;
    SystemDebugger.LogDebugMessage("Window Focused: '" + WindowIdentifier + "' (ZIndex=" + this.TopZIndex + ")");
    WindowElement.css("z-index", this.TopZIndex);
    $(".DesktopWindow").removeClass("ActiveWindow");
    WindowElement.removeClass("MinimizedWindow").show().addClass("ActiveWindow");
    this.ActiveWindow = WindowIdentifier;
    if (WindowIdentifier !== "WindowApplicationLauncher") {
      this.LastActiveClientWindow = WindowIdentifier;
    }
    this.RemoveIconBox(WindowIdentifier);
    if (window.DesktopApplication) {
      DesktopApplication.ZoomIntoScreen();
    }
  },

  LowerWindow: function (WindowIdentifier) {
    const WindowElement = $(`#${WindowIdentifier}`);
    if (!WindowElement.length) {
      return;
    }
    this.BottomZIndex -= 1;
    SystemDebugger.LogDebugMessage("Window Lowered: '" + WindowIdentifier + "' (ZIndex=" + this.BottomZIndex + ")");
    WindowElement.css("z-index", this.BottomZIndex);
    WindowElement.removeClass("ActiveWindow");
    if (this.ActiveWindow === WindowIdentifier) {
      this.ActiveWindow = null;
      const OpenWindows = $(".DesktopWindow").not(".MinimizedWindow").not(`#${WindowIdentifier}`);
      if (OpenWindows.length > 0) {
        let HighestZIndex = -Infinity;
        let TopWindowIdentifier = null;
        OpenWindows.each(function () {
          const CurrentZIndex = parseInt($(this).css("z-index"), 10) || 0;
          if (CurrentZIndex > HighestZIndex) {
            HighestZIndex = CurrentZIndex;
            TopWindowIdentifier = $(this).attr("id");
          }
        });
        if (TopWindowIdentifier) {
          $(`#${TopWindowIdentifier}`).addClass("ActiveWindow");
          this.ActiveWindow = TopWindowIdentifier;
          this.RecordWindowInteraction(TopWindowIdentifier);
          if (TopWindowIdentifier !== "WindowApplicationLauncher") {
            this.LastActiveClientWindow = TopWindowIdentifier;
          }
        }
      }
    }
  },

  CancelWindowPlacement: function () {
    if (!this.IsPlacementActive) {
      return;
    }
    SystemDebugger.LogDebugMessage("Window Placement Cancelled: '" + (this.PlacementConfig ? this.PlacementConfig.Identifier : "None") + "'");
    this.IsPlacementActive = false;
    this.JustFinishedPlacement = true;
    setTimeout(() => {
      WindowManager.JustFinishedPlacement = false;
    }, 150);
    this.PlacementConfig = null;
    $("#WindowPlacementGrid").remove();
    $(document).off(".WindowPlacementNamespace");
    $(window).off(".WindowPlacementNamespace");
  },

  BeginWindowPlacement: function (Config) {
    this.CancelWindowPlacement();
    this.IsPlacementActive = true;
    this.PlacementConfig = Config;

    const DesktopElement = document.getElementById("DesktopContainer");
    const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
    const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 600;

    let CurrentWidth = Math.floor(Math.min(Config.Width || 640, Math.max(Config.MinWidth || 200, AvailableWidth - 40)) / 4) * 4;
    let CurrentHeight = Math.floor(Math.min(Config.Height || 480, Math.max(Config.MinHeight || 150, AvailableHeight - 40)) / 4) * 4;
    SystemDebugger.LogDebugMessage("Window Placement Started: '" + Config.Identifier + "' (Initial=" + CurrentWidth + "x" + CurrentHeight + ")");

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

      if (IsMiddleResizing || IsInteractiveSizing) {
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

      if (Event.button === 1) {
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
        const MaximumVerticalHeight = AvailableHeight - CurrentTop;
        CurrentHeight = Math.max(160, Math.floor(MaximumVerticalHeight / 4) * 4);
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
      Identifier,
      Title,
      ContentHTML = "",
      ContentURL = null
    } = Config;
    const WindowHTML = `
      <div id="${Identifier}" class="DesktopWindow ActiveWindow">
        <div class="WindowTitlebar" id="WindowTitlebar_${Identifier}">
          <button class="WindowControlButton WindowControlMinimizeButton" type="button" title="Iconify">
            <span class="WindowButtonIcon WindowButtonIconMinimize" aria-hidden="true"></span>
          </button>
          <span class="WindowTitle">${Title}</span>
          <button class="WindowControlButton WindowControlResizeButton" type="button" title="Resize">
            <span class="WindowButtonIcon WindowButtonIconResize" aria-hidden="true"></span>
          </button>
        </div>
        <div class="WindowTitleDivider"></div>
        <div class="WindowContent" id="WindowContent_${Identifier}">
          ${ContentHTML}
        </div>
      </div>
    `;

    $("#DesktopContainer").append(WindowHTML);
    const WindowElement = $(`#${Identifier}`);
    WindowElement.css({
      "width": `${Width}px`,
      "height": `${Height}px`,
      "left": `${Left}px`,
      "top": `${Top}px`,
      "z-index": ++this.TopZIndex
    });
    SystemDebugger.LogDebugMessage("Window Instantiated: '" + Identifier + "' (" + Width + "x" + Height + "@" + Left + "," + Top + ", Z=" + this.TopZIndex + ")");
    if (Config.MinWidth) {
      WindowElement.css("min-width", `${Config.MinWidth}px`);
    }
    if (Config.MinHeight) {
      WindowElement.css("min-height", `${Config.MinHeight}px`);
    }
    const WindowDomNode = document.getElementById(Identifier);
    if (window.htmx && WindowDomNode) {
      htmx.process(WindowDomNode);
    }
    this.Windows[Identifier] = Config;
    this.MakeDraggable(Identifier);
    this.MakeResizable(Identifier);
    this.FocusWindow(Identifier);
    if (ContentURL) {
      this.LoadWindowContent(Identifier, ContentURL);
    }
  },

  OpenWindow: function (Config) {
    SystemDebugger.LogDebugMessage("Window Open Requested: '" + Config.Identifier + "' (BypassPlacement=" + (!!Config.BypassPlacement) + ")");
    const {
      Identifier,
      Width = 640,
      Height = 480,
      Left = 100,
      Top = 60
    } = Config;
    if ($(`#${Identifier}`).length) {
      this.RestoreWindow(Identifier);
      return;
    }
    if (Config.BypassPlacement) {
      const OffsetShift = (Object.keys(this.Windows).length % 6) * 24;
      const DesktopElement = document.getElementById("DesktopContainer");
      const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
      const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 600;
      const TargetWidth = Math.floor(Math.min(Width, Math.max(Config.MinWidth || 160, AvailableWidth - 40)) / 4) * 4;
      const TargetHeight = Math.floor(Math.min(Height, Math.max(Config.MinHeight || 120, AvailableHeight - 40)) / 4) * 4;
      const TargetLeft = Math.floor(Math.min(Left + OffsetShift, Math.max(0, AvailableWidth - TargetWidth - 20)) / 4) * 4;
      const TargetTop = Math.floor(Math.min(Top + OffsetShift, Math.max(0, AvailableHeight - TargetHeight - 20)) / 4) * 4;
      this.InstantiateWindow(Config, TargetLeft, TargetTop, TargetWidth, TargetHeight);
      return;
    }
    this.BeginWindowPlacement(Config);
  },

  LoadWindowContent: async function (Identifier, URL) {
    try {
      const Response = await fetch(URL);
      const HTML = await Response.text();
      const ContentTarget = $(`#WindowContent_${Identifier}`);
      ContentTarget.html(HTML);
      const ContentDomNode = document.getElementById(`WindowContent_${Identifier}`);
      if (window.htmx && ContentDomNode) {
        htmx.process(ContentDomNode);
      }
      if (window.DesktopApplication && ContentDomNode) {
        DesktopApplication.InitializeAutoResizeTextareas(ContentDomNode);
      }
      SystemDebugger.LogDebugMessage("Window Content Loaded: '" + Identifier + "' (" + HTML.length + " Chars, URL='" + URL + "')");
    } catch (Error) {
      SystemDebugger.LogDebugMessage("Window Content Failed: '" + Identifier + "' (URL='" + URL + "', Error=" + Error.message + ")");
      $(`#WindowContent_${Identifier}`).html(`<div class="TextDanger">Failed to load content from ${URL}</div>`);
    }
  },

  CloseWindow: function (WindowIdentifier) {
    SystemDebugger.LogDebugMessage("Window Closed: '" + WindowIdentifier + "'");
    this.RemoveIconBox(WindowIdentifier);
    $(`#${WindowIdentifier}`).remove();
    delete this.Windows[WindowIdentifier];
    this.WindowInteractionHistory = this.WindowInteractionHistory.filter(function (ExistingIdentifier) {
      return ExistingIdentifier !== WindowIdentifier;
    });
    if (this.ActiveWindow === WindowIdentifier) {
      this.ActiveWindow = null;
      this.ActivateLastInteractedWindow();
    }
    if (this.LastActiveClientWindow === WindowIdentifier) {
      const RemainingWindows = $(".DesktopWindow").not("#WindowApplicationLauncher");
      if (RemainingWindows.length > 0) {
        this.LastActiveClientWindow = RemainingWindows.last().attr("id");
      } else {
        this.LastActiveClientWindow = null;
      }
    }
  },

  MinimizeWindow: function (WindowIdentifier) {
    SystemDebugger.LogDebugMessage("Window Minimized: '" + WindowIdentifier + "'");
    const WindowElement = $(`#${WindowIdentifier}`);
    if (!WindowElement.length) {
      return;
    }
    WindowElement.hide().addClass("MinimizedWindow").removeClass("ActiveWindow");
    if (this.ActiveWindow === WindowIdentifier) {
      this.ActiveWindow = null;
    }
    const Config = this.Windows[WindowIdentifier];
    const WindowTitle = Config && Config.Title ? Config.Title : WindowIdentifier;
    this.CreateIconBox(WindowIdentifier, WindowTitle);
    if (!this.ActiveWindow) {
      this.ActivateLastInteractedWindow();
    }
  },

  RestoreWindow: function (WindowIdentifier) {
    SystemDebugger.LogDebugMessage("Window Restored: '" + WindowIdentifier + "'");
    const WindowElement = $(`#${WindowIdentifier}`);
    if (!WindowElement.length) {
      return;
    }
    this.RemoveIconBox(WindowIdentifier);
    this.FocusWindow(WindowIdentifier);
  },

  SetWindowTitle: function (WindowIdentifier, NewTitle) {
    SystemDebugger.LogDebugMessage("Window Title Updated: '" + WindowIdentifier + "' -> '" + NewTitle + "'");
    const WindowElement = $(`#${WindowIdentifier}`);
    if (!WindowElement.length) {
      return;
    }
    WindowElement.find(".WindowTitle").first().text(NewTitle);
    if (this.Windows[WindowIdentifier]) {
      this.Windows[WindowIdentifier].Title = NewTitle;
    }
    $(`#iconbox-${WindowIdentifier} .DesktopIconBoxTitle`).text(NewTitle);
  },

  DeleteTargetWindow: function () {
    let TargetIdentifier = this.LastActiveClientWindow;
    if (!TargetIdentifier || !$(`#${TargetIdentifier}`).length) {
      const OpenWindows = $(".DesktopWindow").not("#WindowApplicationLauncher");
      if (OpenWindows.length > 0) {
        TargetIdentifier = OpenWindows.last().attr("id");
      }
    }
    if (TargetIdentifier && $(`#${TargetIdentifier}`).length) {
      this.CloseWindow(TargetIdentifier);
    }
  },

  CreateIconBox: function (WindowIdentifier, WindowTitle) {
    if ($(`#DesktopIcon_${WindowIdentifier}`).length) {
      return;
    }
    const ExistingIcons = $(".DesktopIconBox");
    const OccupiedTops = new Set();
    ExistingIcons.each(function () {
      OccupiedTops.add(parseInt($(this).css("top"), 10));
    });
    const DesktopElement = document.getElementById("DesktopContainer");
    const AvailableWidth = DesktopElement ? DesktopElement.offsetWidth : 800;
    const AvailableHeight = DesktopElement ? DesktopElement.offsetHeight : 600;
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
      <div id="DesktopIcon_${WindowIdentifier}" class="DesktopIconBox" data-window-identifier="${WindowIdentifier}">
        <button class="WindowControlButton WindowControlRestoreButton" type="button" title="De-iconify">
          <span class="WindowButtonIcon WindowButtonIconMinimize" aria-hidden="true"></span>
        </button>
        <span class="DesktopIconBoxTitle">${WindowTitle}</span>
      </div>
    `;
    $("#DesktopContainer").append(IconHTML);
    const IconElement = $(`#DesktopIcon_${WindowIdentifier}`);
    IconElement.css({"left": `${TargetLeft}px`, "top": `${TargetTop}px`});
    SystemDebugger.LogDebugMessage("Icon Box Created: Window='" + WindowIdentifier + "', Pos=" + TargetLeft + "," + TargetTop);
    this.MakeIconDraggable(`DesktopIcon_${WindowIdentifier}`);
  },

  RemoveIconBox: function (WindowIdentifier) {
    SystemDebugger.LogDebugMessage("Icon Box Removed: Window='" + WindowIdentifier + "'");
    $(`#DesktopIcon_${WindowIdentifier}`).remove();
  },

  ResetWindowManager: function () {
    SystemDebugger.LogDebugMessage("Window Manager State Reset: " + Object.keys(this.Windows).length + " Windows Cleared");
    this.CancelWindowPlacement();
    $(".DesktopWindow").remove();
    $(".DesktopIconBox").remove();
    $("#WindowPlacementGrid").remove();
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

  MakeIconDraggable: function (IconIdentifier) {
    const IconDOMElement = document.getElementById(IconIdentifier);
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
      const WindowIdentifier = $(IconDOMElement).attr("data-window-identifier");
      WindowManager.RestoreWindow(WindowIdentifier);
    });
  },

  ToggleMaximizeWindow: function (WindowIdentifier) {
    const WindowElement = $(`#${WindowIdentifier}`);
    const IsCurrentlyMaximized = WindowElement.hasClass("MaximizedWindow");
    SystemDebugger.LogDebugMessage("Window Maximize Toggled: '" + WindowIdentifier + "' (Maximized=" + (!IsCurrentlyMaximized) + ")");
    if (IsCurrentlyMaximized) {
      const PreviousPosition = WindowElement.data("prev-pos");
      WindowElement.css({"left": PreviousPosition.left, "top": PreviousPosition.top, "width": PreviousPosition.width, "height": PreviousPosition.height}).removeClass("MaximizedWindow");
    } else {
      WindowElement.data("prev-pos", {"left": WindowElement.css("left"), "top": WindowElement.css("top"), "width": WindowElement.css("width"), "height": WindowElement.css("height")});
      WindowElement.css({"left": "0px", "top": "0px", "width": "100%", "height": "100%"}).addClass("MaximizedWindow");
    }
    this.FocusWindow(WindowIdentifier);
  },

  MakeDraggable: function (Identifier) {
    const WindowDOMElement = document.getElementById(Identifier);
    const TitlebarElement = document.getElementById(`WindowTitlebar_${Identifier}`);
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
      WindowManager.RecordWindowInteraction(Identifier);
      if (WindowManager.ActiveWindow !== Identifier) {
        WindowManager.FocusWindow(Identifier);
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

  MakeResizable: function (Identifier) {
    const WindowDOMElement = document.getElementById(Identifier);
    const ResizeButton = WindowDOMElement.querySelector(".WindowControlResizeButton");

    if (ResizeButton) {
      ResizeButton.addEventListener("mousedown", StartResizeFromButton);
    }

    function StartResizeFromButton(Event) {
      Event.preventDefault();
      Event.stopPropagation();
      WindowManager.FocusWindow(Identifier);
      WindowManager.IsDraggingWindow = true;
      const StartMouseX = Event.clientX;
      const StartMouseY = Event.clientY;
      const StartWidth = WindowDOMElement.offsetWidth;
      const StartHeight = WindowDOMElement.offsetHeight;
      const DesktopElement = document.getElementById("DesktopContainer");
      const MaximumWidth = DesktopElement.offsetWidth - WindowDOMElement.offsetLeft;
      const MaximumHeight = DesktopElement.offsetHeight - WindowDOMElement.offsetTop;
      const WindowConfiguration = WindowManager.Windows[Identifier] || {};
      const MinimumWidth = WindowConfiguration.MinWidth || 200;
      const MinimumHeight = WindowConfiguration.MinHeight || 150;
      document.body.style.cursor = "se-resize";

      function PerformResize(MoveEvent) {
        MoveEvent.preventDefault();
        WindowManager.IsDraggingWindow = true;
        const DeltaX = MoveEvent.clientX - StartMouseX;
        const DeltaY = MoveEvent.clientY - StartMouseY;
        let NewWidth = Math.max(MinimumWidth, Math.min(MaximumWidth, StartWidth + DeltaX));
        let NewHeight = Math.max(MinimumHeight, Math.min(MaximumHeight, StartHeight + DeltaY));
        NewWidth = Math.round(NewWidth / 4) * 4;
        NewHeight = Math.round(NewHeight / 4) * 4;
        WindowDOMElement.style.width = NewWidth + "px";
        WindowDOMElement.style.height = NewHeight + "px";
      }

      function StopResize() {
        document.body.style.cursor = "";
        window.removeEventListener("mousemove", PerformResize);
        window.removeEventListener("mouseup", StopResize);
        WindowManager.IsDraggingWindow = false;
        WindowManager.JustFinishedDragging = true;
        setTimeout(() => {
          WindowManager.JustFinishedDragging = false;
        }, 150);
      }

      window.addEventListener("mousemove", PerformResize);
      window.addEventListener("mouseup", StopResize);
    }
  }
};

$(document).ready(function () {
  WindowManager.Initialize();
});
