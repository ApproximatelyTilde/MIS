const SystemBootManager = {
    IsBooting: false,
    PreloadCompleted: false,
    IsDesktopUnlocked: false,
    CurrentAuthenticatedUsername: null,
    CurrentAuthenticatedRole: null,
    CurrentAuthenticatedRoles: [],
    CurrentAuthenticatedIsInGuild: false,
    CurrentDiscordInviteURL: null,

    Initialize: function () {
        window.SystemBootManager = this;
        this.BindEventListeners();

        const IsHardReload = Boolean(document.querySelector('meta[name="ClientHardReload"]'));
        SystemDebugger.LogDebugMessage("Boot Manager Initialized: HardReload=" + IsHardReload);
        if (IsHardReload) {
            sessionStorage.removeItem("SessionBootCompleted");
            sessionStorage.removeItem("SessionUnlocked");
            sessionStorage.removeItem("CurrentAuthenticatedRole");
            sessionStorage.removeItem("CurrentAuthenticatedRoles");
            sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
            sessionStorage.removeItem("CurrentDiscordInviteURL");
        }

        const URLParameters = new URLSearchParams(window.location.search);
        const IsAuthenticatedRedirect = URLParameters.get("Authenticated") === "True" || URLParameters.get("authenticated") === "true";
        const IsNotInGuildRedirect = URLParameters.get("NotInGuild") === "True" || URLParameters.get("not_in_guild") === "true";
        if (IsNotInGuildRedirect) {
            sessionStorage.setItem("PendingGuildMembershipWarning", "true");
        }
        const HasCompletedSessionBoot = sessionStorage.getItem("SessionBootCompleted") === "true";
        const HasUnlockedSession = sessionStorage.getItem("SessionUnlocked") === "true";
        const NavigationEntries = performance.getEntriesByType("navigation");
        const IsBrowserReload = (NavigationEntries.length > 0 && NavigationEntries[0].type === "reload") || (performance.navigation && performance.navigation.type === 1);
        if (IsBrowserReload) {
            sessionStorage.removeItem("GuildMembershipWarningDismissed");
            if (sessionStorage.getItem("CurrentAuthenticatedIsInGuild") === "false") {
                sessionStorage.setItem("PendingGuildMembershipWarning", "true");
            }
        }

        if (IsAuthenticatedRedirect) {
            $("#SystemBootScreenContainer").addClass("HiddenElement");
            sessionStorage.setItem("SessionBootCompleted", "true");
            window.history.replaceState({}, document.title, window.location.pathname);
            this.HandleOAuthReturnFlow();
            return;
        }

        if (!IsHardReload && (HasCompletedSessionBoot || IsBrowserReload)) {
            sessionStorage.setItem("SessionBootCompleted", "true");
            $("#SystemBootScreenContainer").addClass("HiddenElement");
            $("#SystemSplashScreenContainer").addClass("HiddenElement");
            if (HasUnlockedSession) {
                this.IsDesktopUnlocked = true;
                this.UnlockDesktopEnvironment();
                this.CheckSessionStatusOnReload();
            } else {
                this.CheckSessionAndProceed(false);
            }
            return;
        }

        this.StartBootSequence();
    },


    BindEventListeners: function () {
        $(document).on("click", "#LoginButtonNetworkSignIn", (Event) => {
            Event.preventDefault();
            this.HandleNetworkSignIn();
        });

        $(document).on("click", "#LoginButtonLocalSignIn", (Event) => {
            Event.preventDefault();
            this.PerformGuestLogin();
        });

        $(document).on("click", "#EmulatedTeletypeContainer", () => {
            $("#TeletypeInputField").focus();
        });

        $(document).on("keydown", "#TeletypeInputField", (Event) => {
            if (Event.key === "Enter") {
                const InputValue = $("#TeletypeInputField").val().trim();
                $("#TeletypeInputField").val("");
                this.HandleTeletypeCommand(InputValue);
            }
        });
    },

    GetOrCreateStationHardwareAddress: function () {
        const CookiePrefix = "StationHardwareAddress=";
        const DecodedCookie = decodeURIComponent(document.cookie);
        const CookieTokens = DecodedCookie.split(";");
        for (let Index = 0; Index < CookieTokens.length; Index++) {
            const Token = CookieTokens[Index].trim();
            if (Token.indexOf(CookiePrefix) === 0) {
                const ExistingAddress = Token.substring(CookiePrefix.length);
                SystemDebugger.LogDebugMessage("Station Hardware Address Found: " + ExistingAddress);
                return ExistingAddress;
            }
        }

        const GenerateHexByte = () => Math.floor(Math.random() * 256).toString(16).padStart(2, "0").toUpperCase();
        const AssignedAddress = `08:00:4E:${GenerateHexByte()}:${GenerateHexByte()}:${GenerateHexByte()}`;
        document.cookie = `StationHardwareAddress=${AssignedAddress}; path=/; max-age=31536000; SameSite=Lax`;
        SystemDebugger.LogDebugMessage("Station Hardware Address Generated: " + AssignedAddress);
        return AssignedAddress;
    },

    PreloadAssets: function () {
        const ImagePaths = [
            "/Resources/PNG/Computer.png",
            "/Resources/PNG/Splash.png",
            "/Resources/SVG/WindowButton-Iconify.svg",
            "/Resources/SVG/WindowButton-Resize.svg",
            "/Resources/SVG/LoginManagerButton-NetworkLogin.svg",
            "/Resources/SVG/LoginManagerButton-LocalLogin.svg",
            "/Resources/SVG/Function-Search.svg",
            "/Resources/SVG/Function-ShowItem.svg",
            "/Resources/SVG/Function-HideItem.svg",
            "/Resources/SVG/Function-Options.svg",
            "/Resources/SVG/Function-Star.svg"
        ];

        const ImagePromises = ImagePaths.map((Path) => {
            return new Promise((Resolve) => {
                const ImageElement = new Image();
                ImageElement.onload = () => Resolve(Path);
                ImageElement.onerror = () => Resolve(Path);
                ImageElement.src = Path;
            });
        });

        const FontPromises = [];
        if (document.fonts && document.fonts.load) {
            FontPromises.push(document.fonts.load("2rem ANK24"));
            FontPromises.push(document.fonts.load("2rem JPN12"));
        }

        return Promise.allSettled([...ImagePromises, ...FontPromises]).then(() => {
            this.PreloadCompleted = true;
            SystemDebugger.LogDebugMessage("System Assets Preloaded: " + ImagePaths.length + " Images, 2 Fonts");
        });
    },

    StartBootSequence: function () {
        SystemDebugger.LogDebugMessage("Boot Sequence Started");
        this.IsBooting = true;
        this.IsDesktopUnlocked = false;
        $(".DesktopWindow").remove();
        $(".DesktopIconBox").remove();
        $("#WindowPlacementGrid").remove();
        $("#DesktopContextMenu").addClass("HiddenElement");
        $("#SystemConfirmationModalContainer").addClass("HiddenElement");
        if (typeof WindowManager !== "undefined") {
            WindowManager.ResetWindowManager();
        }
        if (typeof DesktopApplication !== "undefined") {
            DesktopApplication.ContextMenuTargetWindow = null;
            DesktopApplication.PendingSystemAction = null;
        }
        $("#DesktopContainer").addClass("HiddenElement").addClass("InteractionDisabled");
        $("#SystemLoginScreenContainer").addClass("HiddenElement");
        $("#SystemSplashScreenContainer").addClass("HiddenElement");
        $("#EmulatedTeletypeContainer").addClass("HiddenElement");
        $("#SystemBootScreenContainer").removeClass("HiddenElement");
        $("#BootTerminalText").text("");

        const ScreenContainer = $("#DesktopScreenContainer");
        ScreenContainer.addClass("CRTIgnitionActive");
        setTimeout(() => {
            ScreenContainer.removeClass("CRTIgnitionActive");
        }, 1600);

        const StationHardwareAddress = this.GetOrCreateStationHardwareAddress();
        const PreloadPromise = this.PreloadAssets();

        const AppendLine = (LineText) => {
            const CurrentText = $("#BootTerminalText").text();
            $("#BootTerminalText").text(CurrentText + (CurrentText.length > 0 ? "\n" : "") + LineText);
        };

        const UpdateLastLine = (LineText) => {
            const CurrentText = $("#BootTerminalText").text();
            const LastNewlineIndex = CurrentText.lastIndexOf("\n");
            if (LastNewlineIndex === -1) {
                $("#BootTerminalText").text(LineText);
            } else {
                $("#BootTerminalText").text(CurrentText.substring(0, LastNewlineIndex + 1) + LineText);
            }
        };

        setTimeout(() => {
            AppendLine("SYMMETRIX WORKSTATION MONITOR V2.8");
            AppendLine("COPYRIGHT (C) 1985-1989 SYMMETRIX CORPORATION");
            AppendLine("ALL RIGHTS RESERVED.\n");

            setTimeout(() => {
                AppendLine("LOGIC BOARD: TYNE-TEES TT-030-IMB");
                AppendLine("CPU: SAMHWA SH-6830-16A @ 16.67 MHZ / FPU: SH-68882-16");

                setTimeout(() => {
                    let CurrentKilobytes = 0;
                    AppendLine("MEMORY TEST:       0 KB");

                    const MemoryInterval = setInterval(() => {
                        CurrentKilobytes += 128;
                        if (CurrentKilobytes <= 1024) {
                            const FormattedKilobytes = String(CurrentKilobytes).padStart(7, " ");
                            UpdateLastLine(`MEMORY TEST: ${FormattedKilobytes} KB`);
                        } else {
                            clearInterval(MemoryInterval);
                            UpdateLastLine("MEMORY TEST:    1024 KB OK (1x SHM-1024-MS)");

                            setTimeout(() => {
                                AppendLine("RTC/NVRAM: SH-3460 / SHM-2560N OK");

                                setTimeout(() => {
                                    AppendLine("DISPLAY: CDS-512M (1024x768 GRAPHICS)");

                                    setTimeout(() => {
                                        AppendLine("SCSI HBA: CMS-5000 INITIATOR READY");

                                        setTimeout(() => {
                                            AppendLine("  TARGET 0: NP-3105 FIXED DISK (105 MB)");

                                            setTimeout(() => {
                                                AppendLine("  TARGET 4: TM-1200 TAPE STREAMER READY");

                                                setTimeout(() => {
                                                    AppendLine(`NETWORK: TRI-8023 (STATION: ${StationHardwareAddress})\n`);

                                                    setTimeout(() => {
                                                        AppendLine("BOOTING MARTEN'S INFORMATION SYSTEM...");

                                                        setTimeout(() => {
                                                            AppendLine("MOUNTING ROOT: /dev/sd0a ... [ OK ]");

                                                            setTimeout(() => {
                                                                AppendLine("INIT: RUNLEVEL 3");

                                                                setTimeout(() => {
                                                                    AppendLine("  [ OK ] EVBD");

                                                                    setTimeout(() => {
                                                                        AppendLine("  [ OK ] SOCKD");

                                                                        setTimeout(() => {
                                                                            AppendLine("  [ OK ] DSPDAEMON");

                                                                            setTimeout(() => {
                                                                                AppendLine("  [ OK ] KEYRINGD");

                                                                                setTimeout(() => {
                                                                                    AppendLine("INIT: SWITCHING TO RUNLEVEL 5 (GRAPHICAL MODE)...");

                                                                                    PreloadPromise.then(() => {
                                                                                        setTimeout(() => {
                                                                                            this.ExecuteDisplayModeSwitch();
                                                                                        }, 900);
                                                                                    });
                                                                                }, 800);
                                                                            }, 600);
                                                                        }, 600);
                                                                    }, 600);
                                                                }, 600);
                                                            }, 850);
                                                        }, 1000);
                                                    }, 950);
                                                }, 700);
                                            }, 700);
                                        }, 450);
                                    }, 800);
                                }, 700);
                            }, 750);
                        }
                    }, 140);
                }, 1000);
            }, 1100);
        }, 1800);
    },

    ExecuteDisplayModeSwitch: function () {
        SystemDebugger.LogDebugMessage("Boot Display Switch: CRT Sync Relock Active");
        const ScreenContainer = $("#DesktopScreenContainer");
        ScreenContainer.addClass("CRTSyncRelockActive");

        setTimeout(() => {
            $("#SystemBootScreenContainer").addClass("HiddenElement");
            $("#DesktopContainer").removeClass("HiddenElement").addClass("DesktopStippleWipeActive");
            $("#SystemSplashScreenContainer").removeClass("HiddenElement");
        }, 350);

        setTimeout(() => {
            ScreenContainer.removeClass("CRTSyncRelockActive");
            this.ExecuteSplashScreenSequence();
        }, 850);
    },

    ExecuteSplashScreenSequence: function () {
        SystemDebugger.LogDebugMessage("Boot Splash Screen Sequence Started: 10 Steps");
        const ProgressFill = $("#SystemSplashProgressFill");
        ProgressFill.css("width", "0%");

        const StepWeights = [];
        const DurationWeights = [];
        for (let Index = 0; Index < 10; Index += 1) {
            StepWeights.push(Math.random() * 0.8 + 0.3);
            DurationWeights.push(Math.random() * 0.8 + 0.3);
        }

        let TotalStepWeight = 0;
        let TotalDurationWeight = 0;
        for (let Index = 0; Index < 10; Index += 1) {
            TotalStepWeight += StepWeights[Index];
            TotalDurationWeight += DurationWeights[Index];
        }

        const ProgressTargets = [];
        let AccumulatedPercentage = 0;
        let LastPercentage = 0;
        for (let Index = 0; Index < 9; Index += 1) {
            AccumulatedPercentage += (StepWeights[Index] / TotalStepWeight) * 100;
            const MinimumPercentage = LastPercentage + 1;
            const MaximumPercentage = 99 - (9 - Index);
            const TargetPercentage = Math.min(MaximumPercentage, Math.max(MinimumPercentage, Math.round(AccumulatedPercentage)));
            LastPercentage = TargetPercentage;
            ProgressTargets.push(TargetPercentage);
        }
        ProgressTargets.push(100);

        const StepDurations = [];
        let AccumulatedDuration = 0;
        for (let Index = 0; Index < 9; Index += 1) {
            const Duration = Math.round((DurationWeights[Index] / TotalDurationWeight) * 1800);
            StepDurations.push(Duration);
            AccumulatedDuration += Duration;
        }
        StepDurations.push(1800 - AccumulatedDuration);

        let CurrentStepIndex = 0;
        const ExecuteNextStep = () => {
            if (CurrentStepIndex < 10) {
                const TargetPercentage = ProgressTargets[CurrentStepIndex];
                const StepDelay = StepDurations[CurrentStepIndex];
                CurrentStepIndex += 1;
                setTimeout(() => {
                    ProgressFill.css("width", `${TargetPercentage}%`);
                    ExecuteNextStep();
                }, StepDelay);
            } else {
                setTimeout(() => {
                    $("#SystemSplashScreenContainer").addClass("HiddenElement");
                    $("#DesktopContainer").removeClass("DesktopStippleWipeActive");
                    this.FinishBootSequence();
                }, 200);
            }
        };

        ExecuteNextStep();
    },

    FinishBootSequence: function () {
        SystemDebugger.LogDebugMessage("Boot Sequence Finished");
        this.IsBooting = false;
        sessionStorage.setItem("SessionBootCompleted", "true");
        $("#SystemBootScreenContainer").addClass("HiddenElement");
        $("#SystemSplashScreenContainer").addClass("HiddenElement");
        this.CheckSessionAndProceed(true);
    },

    CheckSessionAndProceed: function (CameFromBoot) {
        fetch("/API/Auth/Session/Status")
            .then((Response) => Response.json())
            .then((SessionData) => {
                SystemDebugger.LogDebugMessage("Session Status Verified: Auth=" + Boolean(SessionData.IsAuthenticated) + ", User='" + (SessionData.Username || "Guest") + "', Role='" + (SessionData.Role || "Visitor") + "'");
                if (SessionData.IsAuthenticated && SessionData.Username) {
                    this.CurrentAuthenticatedUsername = SessionData.Username;
                    this.CurrentAuthenticatedRole = SessionData.Role;
                    this.CurrentAuthenticatedRoles = SessionData.Roles || [];
                    this.CurrentAuthenticatedIsInGuild = Boolean(SessionData.IsInGuild);
                    this.CurrentDiscordInviteURL = SessionData.DiscordInviteURL || null;
                    sessionStorage.setItem("CurrentAuthenticatedRole", SessionData.Role || "");
                    sessionStorage.setItem("CurrentAuthenticatedRoles", JSON.stringify(SessionData.Roles || []));
                    sessionStorage.setItem("CurrentAuthenticatedIsInGuild", Boolean(SessionData.IsInGuild) ? "true" : "false");
                    if (SessionData.DiscordInviteURL) {
                        sessionStorage.setItem("CurrentDiscordInviteURL", SessionData.DiscordInviteURL);
                    } else {
                        sessionStorage.removeItem("CurrentDiscordInviteURL");
                    }
                    localStorage.setItem("LastAuthenticatedUsername", SessionData.Username);
                    if (SessionData.AvatarURL) {
                        localStorage.setItem("LastAuthenticatedAvatarURL", SessionData.AvatarURL);
                    }
                    if (SessionData.IsInGuild === false && sessionStorage.getItem("GuildMembershipWarningDismissed") !== "true") {
                        sessionStorage.setItem("PendingGuildMembershipWarning", "true");
                    }
                } else {
                    this.CurrentAuthenticatedUsername = null;
                    this.CurrentAuthenticatedRole = null;
                    this.CurrentAuthenticatedRoles = [];
                    this.CurrentAuthenticatedIsInGuild = false;
                    this.CurrentDiscordInviteURL = null;
                    sessionStorage.removeItem("CurrentAuthenticatedRole");
                    sessionStorage.removeItem("CurrentAuthenticatedRoles");
                    sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
                    sessionStorage.removeItem("CurrentDiscordInviteURL");
                    localStorage.removeItem("LastAuthenticatedUsername");
                    localStorage.removeItem("LastAuthenticatedAvatarURL");
                }
                this.ShowLoginDialog();
            })
            .catch(() => {
                SystemDebugger.LogDebugMessage("Session Status Check Failed: Defaulting to Guest");
                this.CurrentAuthenticatedUsername = null;
                this.CurrentAuthenticatedRole = null;
                this.CurrentAuthenticatedRoles = [];
                this.CurrentAuthenticatedIsInGuild = false;
                this.CurrentDiscordInviteURL = null;
                sessionStorage.removeItem("CurrentAuthenticatedRole");
                sessionStorage.removeItem("CurrentAuthenticatedRoles");
                sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
                sessionStorage.removeItem("CurrentDiscordInviteURL");
                this.ShowLoginDialog();
            });
    },

    CheckSessionStatusOnReload: function () {
        fetch("/API/Auth/Session/Status")
            .then((Response) => Response.json())
            .then((SessionData) => {
                SystemDebugger.LogDebugMessage("Session Reload Verified: User='" + (SessionData.Username || "Guest") + "', Role='" + (SessionData.Role || "Visitor") + "'");
                if (SessionData.IsAuthenticated && SessionData.Username) {
                    this.CurrentAuthenticatedUsername = SessionData.Username;
                    this.CurrentAuthenticatedRole = SessionData.Role;
                    this.CurrentAuthenticatedRoles = SessionData.Roles || [];
                    this.CurrentAuthenticatedIsInGuild = Boolean(SessionData.IsInGuild);
                    this.CurrentDiscordInviteURL = SessionData.DiscordInviteURL || null;
                    sessionStorage.setItem("CurrentAuthenticatedRole", SessionData.Role || "");
                    sessionStorage.setItem("CurrentAuthenticatedRoles", JSON.stringify(SessionData.Roles || []));
                    sessionStorage.setItem("CurrentAuthenticatedIsInGuild", Boolean(SessionData.IsInGuild) ? "true" : "false");
                    if (SessionData.DiscordInviteURL) {
                        sessionStorage.setItem("CurrentDiscordInviteURL", SessionData.DiscordInviteURL);
                    }
                    else {
                        sessionStorage.removeItem("CurrentDiscordInviteURL");
                    }
                    localStorage.setItem("LastAuthenticatedUsername", SessionData.Username);
                    if (SessionData.AvatarURL) {
                        localStorage.setItem("LastAuthenticatedAvatarURL", SessionData.AvatarURL);
                    }
                    if (SessionData.IsInGuild === false) {
                        if (typeof DesktopApplication !== "undefined") {
                            DesktopApplication.ShowGuildMembershipWarning();
                        }
                    }
                    else {
                        if (typeof DesktopApplication !== "undefined" && DesktopApplication.PendingSystemAction === "GuildMembershipWarning") {
                            DesktopApplication.CloseSystemConfirmation();
                        }
                    }
                }
                else {
                    this.CurrentAuthenticatedUsername = null;
                    this.CurrentAuthenticatedRole = null;
                    this.CurrentAuthenticatedRoles = [];
                    this.CurrentAuthenticatedIsInGuild = false;
                    this.CurrentDiscordInviteURL = null;
                    sessionStorage.removeItem("CurrentAuthenticatedRole");
                    sessionStorage.removeItem("CurrentAuthenticatedRoles");
                    sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
                    sessionStorage.removeItem("CurrentDiscordInviteURL");
                    localStorage.removeItem("LastAuthenticatedUsername");
                    localStorage.removeItem("LastAuthenticatedAvatarURL");
                }
            })
            .catch(() => {
                SystemDebugger.LogDebugMessage("Session Reload Check Failed");
            });
    },

    HandleOAuthReturnFlow: function () {
        $("#DesktopContainer").removeClass("HiddenElement").addClass("InteractionDisabled");
        $("#SystemBootScreenContainer").addClass("HiddenElement");
        $("#SystemSplashScreenContainer").addClass("HiddenElement");
        $("#EmulatedTeletypeContainer").addClass("HiddenElement");

        this.PreloadAssets().then(() => {
            fetch("/API/Auth/Session/Status")
                .then((Response) => Response.json())
                .then((SessionData) => {
                    SystemDebugger.LogDebugMessage("OAuth Return Verified: User='" + (SessionData.Username || "Unknown") + "', Role='" + (SessionData.Role || "Visitor") + "'");
                    if (SessionData.IsAuthenticated && SessionData.Username) {
                        this.CurrentAuthenticatedUsername = SessionData.Username;
                        this.CurrentAuthenticatedRole = SessionData.Role;
                        this.CurrentAuthenticatedRoles = SessionData.Roles || [];
                        this.CurrentAuthenticatedIsInGuild = Boolean(SessionData.IsInGuild);
                        this.CurrentDiscordInviteURL = SessionData.DiscordInviteURL || null;
                        sessionStorage.setItem("CurrentAuthenticatedRole", SessionData.Role || "");
                        sessionStorage.setItem("CurrentAuthenticatedRoles", JSON.stringify(SessionData.Roles || []));
                        sessionStorage.setItem("CurrentAuthenticatedIsInGuild", Boolean(SessionData.IsInGuild) ? "true" : "false");
                        if (SessionData.DiscordInviteURL) {
                            sessionStorage.setItem("CurrentDiscordInviteURL", SessionData.DiscordInviteURL);
                        } else {
                            sessionStorage.removeItem("CurrentDiscordInviteURL");
                        }
                        localStorage.setItem("LastAuthenticatedUsername", SessionData.Username);
                        if (SessionData.AvatarURL) {
                            localStorage.setItem("LastAuthenticatedAvatarURL", SessionData.AvatarURL);
                        }
                        if (SessionData.IsInGuild === false) {
                            sessionStorage.setItem("PendingGuildMembershipWarning", "true");
                        }
                        this.ShowLoginDialog();
                        $("#LoginButtonNetworkSignIn").addClass("LoginOptionButtonActive");
                        setTimeout(() => {
                            $("#LoginButtonNetworkSignIn").removeClass("LoginOptionButtonActive");
                            this.UnlockDesktopEnvironment();
                        }, 800);
                    } else {
                        this.CurrentAuthenticatedUsername = null;
                        this.CurrentAuthenticatedRole = null;
                        this.CurrentAuthenticatedRoles = [];
                        this.CurrentAuthenticatedIsInGuild = false;
                        this.CurrentDiscordInviteURL = null;
                        sessionStorage.removeItem("CurrentAuthenticatedRole");
                        sessionStorage.removeItem("CurrentAuthenticatedRoles");
                        sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
                        sessionStorage.removeItem("CurrentDiscordInviteURL");
                        localStorage.removeItem("LastAuthenticatedUsername");
                        localStorage.removeItem("LastAuthenticatedAvatarURL");
                        this.ShowLoginDialog();
                    }
                })
                .catch(() => {
                    this.CurrentAuthenticatedUsername = null;
                    this.CurrentAuthenticatedRole = null;
                    this.CurrentAuthenticatedRoles = [];
                    this.CurrentAuthenticatedIsInGuild = false;
                    this.CurrentDiscordInviteURL = null;
                    sessionStorage.removeItem("CurrentAuthenticatedRole");
                    sessionStorage.removeItem("CurrentAuthenticatedRoles");
                    sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
                    sessionStorage.removeItem("CurrentDiscordInviteURL");
                    this.ShowLoginDialog();
                });
        });
    },

    ShowLoginDialog: function () {
        SystemDebugger.LogDebugMessage("Login Dialog Displayed: User='" + (this.CurrentAuthenticatedUsername || "None") + "'");
        $(".DesktopWindow").remove();
        $(".DesktopIconBox").remove();
        $("#WindowPlacementGrid").remove();
        $("#DesktopContextMenu").addClass("HiddenElement");
        $("#SystemConfirmationModalContainer").addClass("HiddenElement");
        $("#SystemBootScreenContainer").addClass("HiddenElement");
        $("#SystemSplashScreenContainer").addClass("HiddenElement");
        $("#DesktopContainer").removeClass("HiddenElement").addClass("InteractionDisabled");
        $("#SystemLoginScreenContainer").removeClass("HiddenElement");
        this.UpdateLoginPromptDisplay();
        this.UpdateAvatarDisplay();
    },

    UpdateLoginPromptDisplay: function () {
        const NetworkLabelElement = $("#LoginNetworkLabel");
        const NetworkIconElement = $("#LoginNetworkIcon");
        const LocalLabelElement = $("#LoginLocalLabel");
        const LocalIconElement = $("#LoginLocalIcon");

        if (this.CurrentAuthenticatedUsername) {
            NetworkLabelElement.text("Unlock");
            NetworkIconElement.attr("alt", "Unlock");
        } else {
            NetworkLabelElement.text("Authenticate");
            NetworkIconElement.attr("alt", "Authenticate");
        }

        LocalLabelElement.text("Guest Account");
        LocalIconElement.attr("alt", "Guest Account");
    },

    UpdateAvatarDisplay: function () {
        const AvatarURL = this.CurrentAuthenticatedUsername ? localStorage.getItem("LastAuthenticatedAvatarURL") : null;
        const NetworkIconElement = $("#LoginNetworkIcon");
        const AvatarCanvasElement = $("#LoginAvatarCanvas");
        const CanvasNativeElement = AvatarCanvasElement[0];

        if (!AvatarURL || !CanvasNativeElement) {
            NetworkIconElement.removeClass("HiddenElement");
            AvatarCanvasElement.addClass("HiddenElement");
            return;
        }

        const AvatarImage = new Image();
        AvatarImage.crossOrigin = "Anonymous";
        AvatarImage.onload = () => {
            const CanvasContext = CanvasNativeElement.getContext("2d");
            CanvasContext.imageSmoothingEnabled = false;
            CanvasContext.clearRect(0, 0, CanvasNativeElement.width, CanvasNativeElement.height);
            CanvasContext.save();
            CanvasContext.beginPath();
            CanvasContext.arc(CanvasNativeElement.width / 2, CanvasNativeElement.height / 2, CanvasNativeElement.width / 2, 0, Math.PI * 2);
            CanvasContext.closePath();
            CanvasContext.clip();
            CanvasContext.drawImage(AvatarImage, 0, 0, CanvasNativeElement.width, CanvasNativeElement.height);
            CanvasContext.restore();
            NetworkIconElement.addClass("HiddenElement");
            AvatarCanvasElement.removeClass("HiddenElement");
        };
        AvatarImage.onerror = () => {
            NetworkIconElement.removeClass("HiddenElement");
            AvatarCanvasElement.addClass("HiddenElement");
        };
        AvatarImage.src = AvatarURL;
    },

    HandleNetworkSignIn: function () {
        SystemDebugger.LogDebugMessage("Network Sign In Requested: User='" + (this.CurrentAuthenticatedUsername || "New") + "'");
        if (this.CurrentAuthenticatedUsername) {
            this.UnlockDesktopEnvironment();
        } else {
            window.location.href = "/API/Auth/Discord/Login";
        }
    },

    PerformGuestLogin: function () {
        SystemDebugger.LogDebugMessage("Guest Login Requested");
        fetch("/API/Auth/GuestLogin", {
            method: "POST"
        }).then(() => {
            this.CurrentAuthenticatedUsername = null;
            this.CurrentAuthenticatedRole = "Visitor";
            this.CurrentAuthenticatedRoles = [];
            this.CurrentAuthenticatedIsInGuild = false;
            this.CurrentDiscordInviteURL = null;
            sessionStorage.removeItem("CurrentAuthenticatedRole");
            sessionStorage.removeItem("CurrentAuthenticatedRoles");
            sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
            sessionStorage.removeItem("CurrentDiscordInviteURL");
            localStorage.removeItem("LastAuthenticatedUsername");
            localStorage.removeItem("LastAuthenticatedAvatarURL");
            this.UnlockDesktopEnvironment();
        }).catch(() => {
            this.CurrentAuthenticatedUsername = null;
            this.CurrentAuthenticatedRole = "Visitor";
            this.CurrentAuthenticatedRoles = [];
            this.CurrentAuthenticatedIsInGuild = false;
            this.CurrentDiscordInviteURL = null;
            sessionStorage.removeItem("CurrentAuthenticatedRole");
            sessionStorage.removeItem("CurrentAuthenticatedRoles");
            sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
            sessionStorage.removeItem("CurrentDiscordInviteURL");
            localStorage.removeItem("LastAuthenticatedUsername");
            localStorage.removeItem("LastAuthenticatedAvatarURL");
            this.UnlockDesktopEnvironment();
        });
    },

    UnlockDesktopEnvironment: function () {
        SystemDebugger.LogDebugMessage("Desktop Environment Unlocked: User='" + (this.CurrentAuthenticatedUsername || "Guest") + "', Role='" + (this.CurrentAuthenticatedRole || "Visitor") + "'");
        this.IsDesktopUnlocked = true;
        sessionStorage.setItem("SessionBootCompleted", "true");
        sessionStorage.setItem("SessionUnlocked", "true");
        $("#SystemBootScreenContainer").addClass("HiddenElement");
        $("#SystemLoginScreenContainer").addClass("HiddenElement");
        $("#DesktopContainer").removeClass("HiddenElement").removeClass("InteractionDisabled");
        if (typeof DesktopApplication !== "undefined") {
            DesktopApplication.OpenApplicationLauncherWindow();
            if (sessionStorage.getItem("PendingGuildMembershipWarning") === "true") {
                sessionStorage.removeItem("PendingGuildMembershipWarning");
                DesktopApplication.ShowGuildMembershipWarning();
            }
        }
    },

    RestartSystem: function () {
        SystemDebugger.LogDebugMessage("System Restart Triggered");
        sessionStorage.removeItem("SessionBootCompleted");
        sessionStorage.removeItem("SessionUnlocked");
        sessionStorage.removeItem("PendingGuildMembershipWarning");
        sessionStorage.removeItem("GuildMembershipWarningDismissed");
        sessionStorage.removeItem("CurrentAuthenticatedRole");
        sessionStorage.removeItem("CurrentAuthenticatedRoles");
        sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
        sessionStorage.removeItem("CurrentDiscordInviteURL");
        this.CurrentAuthenticatedRole = null;
        this.CurrentAuthenticatedRoles = [];
        this.CurrentAuthenticatedIsInGuild = false;
        this.CurrentDiscordInviteURL = null;
        this.IsDesktopUnlocked = false;
        $(".DesktopWindow").remove();
        $(".DesktopIconBox").remove();
        $("#WindowPlacementGrid").remove();
        $("#DesktopContextMenu").addClass("HiddenElement");
        $("#SystemConfirmationModalContainer").addClass("HiddenElement");
        if (typeof WindowManager !== "undefined") {
            WindowManager.ResetWindowManager();
        }
        if (typeof DesktopApplication !== "undefined") {
            DesktopApplication.ContextMenuTargetWindow = null;
            DesktopApplication.PendingSystemAction = null;
        }
        if (typeof AudioPlayerManager !== "undefined" && AudioPlayerManager.CurrentAudio) {
            AudioPlayerManager.CurrentAudio.pause();
            AudioPlayerManager.IsPlaying = false;
        }
        this.StartBootSequence();
    },

    TeletypeCurrentDirectory: "/home/user",

    TeletypeFileSystem: {
        "/": [
            {
                Name: "bin",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 512
            },
            {
                Name: "dev",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 512
            },
            {
                Name: "etc",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 1024
            },
            {
                Name: "home",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 512
            },
            {
                Name: "tmp",
                Type: "Directory",
                Permissions: "drwxrwxrwt",
                Owner: "root",
                Group: "wheel",
                Size: 512
            },
            {
                Name: "var",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 512
            }
        ],
        "/bin": [
            {
                Name: "cat",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 18432
            },
            {
                Name: "cd",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 12288
            },
            {
                Name: "clear",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 8192
            },
            {
                Name: "date",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 10240
            },
            {
                Name: "echo",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 6144
            },
            {
                Name: "hostname",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 8192
            },
            {
                Name: "ls",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 24576
            },
            {
                Name: "pwd",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 6144
            },
            {
                Name: "reboot",
                Type: "File",
                Permissions: "-rwsr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 14336
            },
            {
                Name: "sh",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 65536
            },
            {
                Name: "startx",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 16384
            },
            {
                Name: "uname",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 8192
            },
            {
                Name: "whoami",
                Type: "File",
                Permissions: "-rwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 8192
            }
        ],
        "/dev": [
            {
                Name: "console",
                Type: "File",
                Permissions: "crw-------",
                Owner: "root",
                Group: "wheel",
                Size: 0
            },
            {
                Name: "null",
                Type: "File",
                Permissions: "crw-rw-rw-",
                Owner: "root",
                Group: "wheel",
                Size: 0
            },
            {
                Name: "sd0a",
                Type: "File",
                Permissions: "brw-r-----",
                Owner: "root",
                Group: "operator",
                Size: 0
            },
            {
                Name: "sd0b",
                Type: "File",
                Permissions: "brw-r-----",
                Owner: "root",
                Group: "operator",
                Size: 0
            },
            {
                Name: "tty01",
                Type: "File",
                Permissions: "crw--w--w-",
                Owner: "user",
                Group: "tty",
                Size: 0
            },
            {
                Name: "zero",
                Type: "File",
                Permissions: "crw-rw-rw-",
                Owner: "root",
                Group: "wheel",
                Size: 0
            }
        ],
        "/etc": [
            {
                Name: "fstab",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 86
            },
            {
                Name: "hostname",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 6
            },
            {
                Name: "hosts",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 60
            },
            {
                Name: "motd",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 96
            },
            {
                Name: "os-release",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 98
            },
            {
                Name: "passwd",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 182
            }
        ],
        "/home": [
            {
                Name: "user",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "user",
                Group: "users",
                Size: 512
            }
        ],
        "/home/user": [
            {
                Name: "notes.txt",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "user",
                Group: "users",
                Size: 148
            },
            {
                Name: "projects",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "user",
                Group: "users",
                Size: 512
            },
            {
                Name: "system.conf",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "user",
                Group: "users",
                Size: 72
            }
        ],
        "/home/user/projects": [
            {
                Name: "core",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "user",
                Group: "users",
                Size: 512
            },
            {
                Name: "synthesizer",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "user",
                Group: "users",
                Size: 512
            }
        ],
        "/home/user/projects/core": [
            {
                Name: "README.md",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "user",
                Group: "users",
                Size: 114
            },
            {
                Name: "manifest.json",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "user",
                Group: "users",
                Size: 84
            }
        ],
        "/home/user/projects/synthesizer": [
            {
                Name: "config.ini",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "user",
                Group: "users",
                Size: 54
            }
        ],
        "/tmp": [],
        "/var": [
            {
                Name: "log",
                Type: "Directory",
                Permissions: "drwxr-xr-x",
                Owner: "root",
                Group: "wheel",
                Size: 512
            }
        ],
        "/var/log": [
            {
                Name: "boot.log",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 186
            },
            {
                Name: "messages",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 104
            },
            {
                Name: "syslog",
                Type: "File",
                Permissions: "-rw-r--r--",
                Owner: "root",
                Group: "wheel",
                Size: 248
            }
        ]
    },

    TeletypeFileContents: {
        "/etc/hostname": "tty01\n",
        "/etc/hosts": "127.0.0.1\tlocalhost\n192.168.1.42\ttty01\n",
        "/etc/motd": "Marten's Information System 3.2\nWelcome to workstation console.\n",
        "/etc/os-release": "NAME=\"Marten's Information System\"\nVERSION=\"3.2\"\nID=mis\nPRETTY_NAME=\"Marten's Information System 3.2\"\n",
        "/etc/fstab": "/dev/sd0a\t/\tufs\trw\t1 1\n/dev/sd0b\tnone\tswap\tsw\t0 0\n",
        "/etc/passwd": "root:*:0:0:System Administrator:/root:/bin/sh\nuser:*:1000:1000:User:/home/user:/bin/sh\noperator:*:1001:1001:Operator:/home/operator:/bin/sh\n",
        "/home/user/notes.txt": "Workstation maintenance scheduled for next quarter.\nCheck SCSI drive termination and backup tape rotation.\n",
        "/home/user/system.conf": "DISPLAY=:0.0\nTERMINAL=TTY01\nKEYBOARD=UK-ASCII\nAUDIO=DMA-8BIT\n",
        "/home/user/projects/core/README.md": "# Workstation Core\nDesktop environment and multi-window interface.\n",
        "/home/user/projects/core/manifest.json": "{\n  \"name\": \"SystemCore\",\n  \"version\": \"3.2\",\n  \"platform\": \"TT-030-IMB\"\n}\n",
        "/home/user/projects/synthesizer/config.ini": "[audio]\nchannels=2\nrate=44100\nsamples=16\n",
        "/var/log/boot.log": "Marten's Information System kernel initialisation complete.\nRoot filesystem mounted read-write.\nNetwork interface tri0 initialized.\n",
        "/var/log/messages": "System initialized successfully.\nRunlevel 3 active.\n",
        "/var/log/syslog": "syslogd started: Marten's Information System 3.2\nWorkstation monitor ready.\nAll daemons operational.\n"
    },

    GetTeletypeUsername: function () {
        const StoredUsername = localStorage.getItem("LastAuthenticatedUsername");
        if (!StoredUsername) {
            return "user";
        }
        const SanitizedUsername = StoredUsername.toLowerCase().replace(/[^a-z0-9_]/g, "");
        return SanitizedUsername.length > 0 ? SanitizedUsername : "user";
    },

    GetHomeDirectory: function () {
        return "/home/" + this.GetTeletypeUsername();
    },

    EnsureUserHomeDirectory: function () {
        const Username = this.GetTeletypeUsername();
        const UserHomePath = "/home/" + Username;
        if (!this.TeletypeFileSystem.hasOwnProperty(UserHomePath)) {
            const HomeEntries = this.TeletypeFileSystem["/home"];
            const ExistsInHome = HomeEntries.some((Item) => Item.Name === Username);
            if (!ExistsInHome) {
                HomeEntries.push({
                    Name: Username,
                    Type: "Directory",
                    Permissions: "drwxr-xr-x",
                    Owner: Username,
                    Group: "users",
                    Size: 512
                });
            }
            this.TeletypeFileSystem[UserHomePath] = [
                {
                    Name: "notes.txt",
                    Type: "File",
                    Permissions: "-rw-r--r--",
                    Owner: Username,
                    Group: "users",
                    Size: 148
                },
                {
                    Name: "projects",
                    Type: "Directory",
                    Permissions: "drwxr-xr-x",
                    Owner: Username,
                    Group: "users",
                    Size: 512
                },
                {
                    Name: "system.conf",
                    Type: "File",
                    Permissions: "-rw-r--r--",
                    Owner: Username,
                    Group: "users",
                    Size: 72
                }
            ];
            this.TeletypeFileSystem[UserHomePath + "/projects"] = [
                {
                    Name: "core",
                    Type: "Directory",
                    Permissions: "drwxr-xr-x",
                    Owner: Username,
                    Group: "users",
                    Size: 512
                },
                {
                    Name: "synthesizer",
                    Type: "Directory",
                    Permissions: "drwxr-xr-x",
                    Owner: Username,
                    Group: "users",
                    Size: 512
                }
            ];
            this.TeletypeFileContents[UserHomePath + "/notes.txt"] = "Workstation maintenance scheduled for next quarter.\nCheck SCSI drive termination and backup tape rotation.\n";
            this.TeletypeFileContents[UserHomePath + "/system.conf"] = "DISPLAY=:0.0\nTERMINAL=TTY01\nKEYBOARD=UK-ASCII\nAUDIO=DMA-8BIT\n";
        }
    },

    GetTeletypePromptString: function () {
        const Username = this.GetTeletypeUsername();
        const CurrentDirectory = this.TeletypeCurrentDirectory || this.GetHomeDirectory();
        let DisplayPath = CurrentDirectory;
        const HomePrefix = this.GetHomeDirectory();
        const DefaultHomePrefix = "/home/user";

        if (DisplayPath === HomePrefix || DisplayPath === DefaultHomePrefix) {
            DisplayPath = "~";
        } else if (DisplayPath.indexOf(HomePrefix + "/") === 0) {
            DisplayPath = "~" + DisplayPath.substring(HomePrefix.length);
        } else if (DisplayPath.indexOf(DefaultHomePrefix + "/") === 0) {
            DisplayPath = "~" + DisplayPath.substring(DefaultHomePrefix.length);
        }

        return `${Username}@tty01:${DisplayPath}$ `;
    },

    UpdateTeletypePromptDisplay: function () {
        const PromptText = this.GetTeletypePromptString();
        $("#TeletypePrompt").text(PromptText);
    },

    NormalizeTeletypePath: function (InputPath) {
        if (!InputPath || InputPath === "") {
            return this.TeletypeCurrentDirectory;
        }
        let WorkingPath = InputPath;
        const HomeDirectory = this.GetHomeDirectory();
        if (WorkingPath === "~" || WorkingPath.indexOf("~/") === 0) {
            WorkingPath = HomeDirectory + WorkingPath.substring(1);
        }
        if (WorkingPath.charAt(0) !== "/") {
            WorkingPath = (this.TeletypeCurrentDirectory === "/" ? "" : this.TeletypeCurrentDirectory) + "/" + WorkingPath;
        }

        const PathSegments = WorkingPath.split("/");
        const ResolvedSegments = [];
        for (let Index = 0; Index < PathSegments.length; Index++) {
            const Segment = PathSegments[Index];
            if (Segment === "" || Segment === ".") {
                continue;
            }
            if (Segment === "..") {
                if (ResolvedSegments.length > 0) {
                    ResolvedSegments.pop();
                }
            } else {
                ResolvedSegments.push(Segment);
            }
        }

        if (ResolvedSegments.length === 0) {
            return "/";
        }
        return "/" + ResolvedSegments.join("/");
    },

    ExitToTeletype: function () {
        SystemDebugger.LogDebugMessage("Teletype Terminal Opened: tty01");
        $("#DesktopContextMenu").addClass("HiddenElement");
        $("#SystemConfirmationModalContainer").addClass("HiddenElement");
        $("#DesktopContainer").addClass("HiddenElement").addClass("InteractionDisabled");
        $("#SystemLoginScreenContainer").addClass("HiddenElement");
        $("#SystemBootScreenContainer").addClass("HiddenElement");
        $("#EmulatedTeletypeContainer").removeClass("HiddenElement");
        this.EnsureUserHomeDirectory();
        this.TeletypeCurrentDirectory = this.GetHomeDirectory();
        this.UpdateTeletypePromptDisplay();
        $("#TeletypeOutputText").text("Marten's Information System 3.2 (tty01)\nType 'help' for available commands, or 'startx' to launch desktop.\n");
        $("#TeletypeInputField").val("").focus();
        const OutputArea = document.getElementById("TeletypeOutputArea");
        if (OutputArea) {
            OutputArea.scrollTop = OutputArea.scrollHeight;
        }
    },

    HandleTeletypeCommand: function (Command) {
        SystemDebugger.LogDebugMessage("Teletype Executed: '" + Command + "'");
        const OutputElement = $("#TeletypeOutputText");
        const CurrentPrompt = this.GetTeletypePromptString();
        let ExecutedLine = `${CurrentPrompt}${Command}\n`;

        const CommandTokens = Command.trim().split(/\s+/).filter(Boolean);
        const CommandName = CommandTokens.length > 0 ? CommandTokens[0].toLowerCase() : "";
        const CommandArguments = CommandTokens.slice(1);

        if (CommandName === "") {
            OutputElement.text(OutputElement.text() + ExecutedLine);
            const OutputArea = document.getElementById("TeletypeOutputArea");
            if (OutputArea) {
                OutputArea.scrollTop = OutputArea.scrollHeight;
            }
            $("#TeletypeInputField").val("").focus();
            return;
        }

        let CommandOutputText = "";

        if (CommandName === "help") {
            CommandOutputText += "Available Commands:\n  ls [path]     - List directory contents\n  cd [path]     - Change working directory\n  pwd           - Print working directory\n  cat [file]    - Display file contents\n  whoami        - Display effective username\n  uname [-a]    - Display operating system identification\n  hostname      - Display system network hostname\n  date          - Display system clock time\n  echo [text]   - Display line of text\n  clear         - Clear terminal display buffer\n  startx        - Launch graphical desktop environment\n  reboot        - Cold restart workstation monitor\n";
        } else if (CommandName === "startx" || CommandName === "exit") {
            this.ReturnToDesktop();
            return;
        } else if (CommandName === "reboot" || CommandName === "restart") {
            $("#EmulatedTeletypeContainer").addClass("HiddenElement");
            this.RestartSystem();
            return;
        } else if (CommandName === "clear") {
            OutputElement.text("");
            this.UpdateTeletypePromptDisplay();
            $("#TeletypeInputField").val("").focus();
            return;
        } else if (CommandName === "pwd") {
            CommandOutputText += `${this.TeletypeCurrentDirectory}\n`;
        } else if (CommandName === "cd") {
            const TargetArgument = CommandArguments[0];
            if (!TargetArgument || TargetArgument === "~") {
                this.TeletypeCurrentDirectory = this.GetHomeDirectory();
                this.UpdateTeletypePromptDisplay();
            } else {
                const TargetPath = this.NormalizeTeletypePath(TargetArgument);
                if (this.TeletypeFileSystem.hasOwnProperty(TargetPath)) {
                    this.TeletypeCurrentDirectory = TargetPath;
                    this.UpdateTeletypePromptDisplay();
                } else {
                    const ParentSlashIndex = TargetPath.lastIndexOf("/");
                    const ParentDirectory = ParentSlashIndex === 0 ? "/" : TargetPath.substring(0, ParentSlashIndex);
                    const EntryName = TargetPath.substring(ParentSlashIndex + 1);
                    if (this.TeletypeFileSystem.hasOwnProperty(ParentDirectory)) {
                        const DirectoryEntries = this.TeletypeFileSystem[ParentDirectory];
                        const MatchingEntry = DirectoryEntries.find((Item) => Item.Name === EntryName);
                        if (MatchingEntry && MatchingEntry.Type === "File") {
                            CommandOutputText += `cd: not a directory: ${TargetArgument}\n`;
                        } else {
                            CommandOutputText += `cd: no such file or directory: ${TargetArgument}\n`;
                        }
                    } else {
                        CommandOutputText += `cd: no such file or directory: ${TargetArgument}\n`;
                    }
                }
            }
        } else if (CommandName === "ls") {
            let TargetArgument = null;
            let LongListingMode = false;
            let ShowAllEntries = false;

            for (let Index = 0; Index < CommandArguments.length; Index++) {
                const Argument = CommandArguments[Index];
                if (Argument.charAt(0) === "-") {
                    if (Argument.indexOf("l") !== -1) {
                        LongListingMode = true;
                    }
                    if (Argument.indexOf("a") !== -1) {
                        ShowAllEntries = true;
                    }
                } else if (!TargetArgument) {
                    TargetArgument = Argument;
                }
            }

            const TargetPath = this.NormalizeTeletypePath(TargetArgument || "");
            if (this.TeletypeFileSystem.hasOwnProperty(TargetPath)) {
                const DirectoryEntries = [...this.TeletypeFileSystem[TargetPath]];
                if (ShowAllEntries) {
                    DirectoryEntries.unshift({
                        Name: "..",
                        Type: "Directory",
                        Permissions: "drwxr-xr-x",
                        Owner: "root",
                        Group: "wheel",
                        Size: 512
                    });
                    DirectoryEntries.unshift({
                        Name: ".",
                        Type: "Directory",
                        Permissions: "drwxr-xr-x",
                        Owner: "root",
                        Group: "wheel",
                        Size: 512
                    });
                }
                if (LongListingMode) {
                    const FormattedLines = DirectoryEntries.map((Entry) => {
                        const OwnerPadded = Entry.Owner.padEnd(8, " ");
                        const GroupPadded = Entry.Group.padEnd(8, " ");
                        const SizePadded = String(Entry.Size).padStart(6, " ");
                        return `${Entry.Permissions}  1 ${OwnerPadded} ${GroupPadded} ${SizePadded} Sep 14 12:00 ${Entry.Name}`;
                    });
                    CommandOutputText += FormattedLines.join("\n") + (FormattedLines.length > 0 ? "\n" : "");
                } else {
                    const EntryNames = DirectoryEntries.map((Entry) => Entry.Name);
                    CommandOutputText += EntryNames.join("  ") + (EntryNames.length > 0 ? "\n" : "");
                }
            } else {
                const ParentSlashIndex = TargetPath.lastIndexOf("/");
                const ParentDirectory = ParentSlashIndex === 0 ? "/" : TargetPath.substring(0, ParentSlashIndex);
                const EntryName = TargetPath.substring(ParentSlashIndex + 1);
                if (this.TeletypeFileSystem.hasOwnProperty(ParentDirectory)) {
                    const DirectoryEntries = this.TeletypeFileSystem[ParentDirectory];
                    const MatchingEntry = DirectoryEntries.find((Item) => Item.Name === EntryName);
                    if (MatchingEntry) {
                        if (LongListingMode) {
                            const OwnerPadded = MatchingEntry.Owner.padEnd(8, " ");
                            const GroupPadded = MatchingEntry.Group.padEnd(8, " ");
                            const SizePadded = String(MatchingEntry.Size).padStart(6, " ");
                            CommandOutputText += `${MatchingEntry.Permissions}  1 ${OwnerPadded} ${GroupPadded} ${SizePadded} Sep 14 12:00 ${MatchingEntry.Name}\n`;
                        } else {
                            CommandOutputText += `${MatchingEntry.Name}\n`;
                        }
                    } else {
                        CommandOutputText += `ls: cannot access '${TargetArgument}': No such file or directory\n`;
                    }
                } else {
                    CommandOutputText += `ls: cannot access '${TargetArgument}': No such file or directory\n`;
                }
            }
        } else if (CommandName === "cat") {
            const TargetArgument = CommandArguments[0];
            if (!TargetArgument) {
                CommandOutputText += "cat: missing file operand\n";
            } else {
                const TargetPath = this.NormalizeTeletypePath(TargetArgument);
                if (this.TeletypeFileSystem.hasOwnProperty(TargetPath)) {
                    CommandOutputText += `cat: ${TargetArgument}: Is a directory\n`;
                } else if (this.TeletypeFileContents.hasOwnProperty(TargetPath)) {
                    CommandOutputText += this.TeletypeFileContents[TargetPath];
                } else {
                    const ParentSlashIndex = TargetPath.lastIndexOf("/");
                    const ParentDirectory = ParentSlashIndex === 0 ? "/" : TargetPath.substring(0, ParentSlashIndex);
                    const EntryName = TargetPath.substring(ParentSlashIndex + 1);
                    if (this.TeletypeFileSystem.hasOwnProperty(ParentDirectory)) {
                        const DirectoryEntries = this.TeletypeFileSystem[ParentDirectory];
                        const MatchingEntry = DirectoryEntries.find((Item) => Item.Name === EntryName);
                        if (MatchingEntry) {
                            CommandOutputText += `[${MatchingEntry.Name}: stream device]\n`;
                        } else {
                            CommandOutputText += `cat: ${TargetArgument}: No such file or directory\n`;
                        }
                    } else {
                        CommandOutputText += `cat: ${TargetArgument}: No such file or directory\n`;
                    }
                }
            }
        } else if (CommandName === "whoami") {
            CommandOutputText += `${this.GetTeletypeUsername()}\n`;
        } else if (CommandName === "hostname") {
            CommandOutputText += "tty01\n";
        } else if (CommandName === "uname") {
            const FirstArgument = CommandArguments[0];
            if (FirstArgument === "-a") {
                CommandOutputText += "Marten's Information System tty01 3.2 m68k TT-030-IMB\n";
            } else {
                CommandOutputText += "Marten's Information System\n";
            }
        } else if (CommandName === "date") {
            CommandOutputText += `${new Date().toUTCString()}\n`;
        } else if (CommandName === "echo") {
            CommandOutputText += `${CommandArguments.join(" ")}\n`;
        } else if (CommandName.length > 0) {
            CommandOutputText += `${CommandName}: command not found\n`;
        }

        OutputElement.text(OutputElement.text() + ExecutedLine + CommandOutputText);
        this.UpdateTeletypePromptDisplay();
        $("#TeletypeInputField").val("").focus();
        const OutputArea = document.getElementById("TeletypeOutputArea");
        if (OutputArea) {
            OutputArea.scrollTop = OutputArea.scrollHeight;
        }
    },

    ReturnToDesktop: function () {
        SystemDebugger.LogDebugMessage("Teletype Terminal Closed: Returning To Desktop");
        $("#EmulatedTeletypeContainer").addClass("HiddenElement");
        this.UnlockDesktopEnvironment();
    },

    Logout: function () {
        SystemDebugger.LogDebugMessage("User Logout Triggered: User='" + (this.CurrentAuthenticatedUsername || "Guest") + "'");
        sessionStorage.removeItem("SessionBootCompleted");
        sessionStorage.removeItem("SessionUnlocked");
        sessionStorage.removeItem("PendingGuildMembershipWarning");
        sessionStorage.removeItem("GuildMembershipWarningDismissed");
        sessionStorage.removeItem("CurrentAuthenticatedRole");
        sessionStorage.removeItem("CurrentAuthenticatedRoles");
        sessionStorage.removeItem("CurrentAuthenticatedIsInGuild");
        sessionStorage.removeItem("CurrentDiscordInviteURL");
        this.CurrentAuthenticatedRole = null;
        this.CurrentAuthenticatedRoles = [];
        this.CurrentAuthenticatedIsInGuild = false;
        this.CurrentDiscordInviteURL = null;
        localStorage.removeItem("LastAuthenticatedUsername");
        localStorage.removeItem("LastAuthenticatedAvatarURL");
        fetch("/API/Auth/Logout", {
            method: "POST"
        }).then(() => {
            window.location.reload();
        }).catch(() => {
            window.location.reload();
        });
    }
};

$(document).ready(function () {
    SystemBootManager.Initialize();
});
