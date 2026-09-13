const DesktopMonitoringClients = {
    ClockTimerIntervalID    : null,
    MailAnimationIntervalID : null,
    MailCheckIntervalID     : null,
    CurrentMailSequenceIndex: 0,
    MailFrameSequence       : [0, 1, 2, 1],
    HasUnreadMail           : false,

    Initialize: function () {
        window.DesktopMonitoringClients = this;
        this.BindEventListeners();
        this.StartClockRoutine();
        this.StartMailCheckRoutine();
    },

    BindEventListeners: function () {
        $(document).on("click", "#DesktopMailIndicator", (Event) => {
            Event.stopPropagation();
            this.ResetMailboxAlert();
            if (typeof DesktopApplication !== "undefined" && DesktopApplication.OpenMailWindow) {
                DesktopApplication.OpenMailWindow();
            }
        });

        document.body.addEventListener("UpdateMailStatus", () => {
            this.CheckMailStatus();
        });
    },

    StartClockRoutine: function () {
        this.UpdateClockHands();
        this.ClockTimerIntervalID = setInterval(() => {
            this.UpdateClockHands();
        }, 1000);
    },

    StartMailCheckRoutine: function () {
        this.CheckMailStatus();
        this.MailCheckIntervalID = setInterval(() => {
            this.CheckMailStatus();
        }, 30000);
    },

    CheckMailStatus: async function () {
        try {
            const Response = await fetch("/API/Mail/Status");
            if (Response.ok) {
                const StatusPayload = await Response.json();
                if (StatusPayload.HasUnread && !this.HasUnreadMail) {
                    this.TriggerMailboxAlert();
                } else if (!StatusPayload.HasUnread && this.HasUnreadMail) {
                    this.ResetMailboxAlert();
                }
            }
        } catch (Exception) {
            return;
        }
    },

    UpdateClockHands: function () {
        const CurrentDate = new Date();
        const CurrentHours = CurrentDate.getUTCHours();
        const CurrentMinutes = CurrentDate.getUTCMinutes();
        const SnappedMinutes = Math.floor((CurrentMinutes / 5)) * 5;
        const HourAngleIndex = (((CurrentHours % 12) * 5) + Math.floor((SnappedMinutes / 12))) % 60;
        const MinuteAngleIndex = SnappedMinutes;
        this.AssignHandAngleClass("ClockHandHour", HourAngleIndex);
        this.AssignHandAngleClass("ClockHandMinute", MinuteAngleIndex);
        this.UpdateClockDate(CurrentDate);
    },

    UpdateClockDate: function (CurrentDate) {
        const DateElement = document.getElementById("ClockDateDisplay");
        if (!DateElement) {
            return;
        }

        const TargetYear = CurrentDate.getUTCFullYear() - 36;
        const TargetDate = new Date(Date.UTC(TargetYear, CurrentDate.getUTCMonth(), CurrentDate.getUTCDate()));
        const DateFormatOptions = {
            month   : "long",
            day     : "numeric",
            year    : "numeric",
            timeZone: "UTC"
        };
        const FormattedDateString = TargetDate.toLocaleDateString("en-US", DateFormatOptions);
        DateElement.textContent = FormattedDateString;
    },

    AssignHandAngleClass: function (ElementID, AngleIndex) {
        const HandElement = document.getElementById(ElementID);
        if (!HandElement) {
            return;
        }

        const ExistingClasses = Array.from(HandElement.classList).filter((Item) => Item.startsWith("ClockAngle"));
        ExistingClasses.forEach((Item) => {
            HandElement.classList.remove(Item);
        });

        HandElement.classList.add("ClockAngle" + AngleIndex);
    },

    StartMailAnimation: function () {
        if (this.MailAnimationIntervalID !== null) {
            return;
        }

        this.CurrentMailSequenceIndex = 0;
        this.DisplayMailFrame(this.MailFrameSequence[this.CurrentMailSequenceIndex]);
        this.MailAnimationIntervalID = setInterval(() => {
            this.CurrentMailSequenceIndex = (this.CurrentMailSequenceIndex + 1) % this.MailFrameSequence.length;
            this.DisplayMailFrame(this.MailFrameSequence[this.CurrentMailSequenceIndex]);
        }, 250);
    },

    StopMailAnimation: function () {
        if (this.MailAnimationIntervalID !== null) {
            clearInterval(this.MailAnimationIntervalID);
            this.MailAnimationIntervalID = null;
        }

        this.CurrentMailSequenceIndex = 0;
        this.DisplayMailFrame(0);
    },

    DisplayMailFrame: function (TargetFrameIndex) {
        for (let Index = 0; Index < 3; Index++) {
            const FrameElement = document.getElementById("DesktopMailFrame" + Index);
            if (FrameElement) {
                FrameElement.classList.toggle("HiddenElement", (Index !== TargetFrameIndex));
            }
        }
    },

    TriggerMailboxAlert: function () {
        this.HasUnreadMail = true;
        const MailIndicatorElement = $("#DesktopMailIndicator");
        MailIndicatorElement.removeClass("HiddenElement");
        this.StartMailAnimation();
        if (typeof SystemAudioFeedback !== "undefined") {
            SystemAudioFeedback.PlaySystemBell(920, 0.25);
        }
    },

    TriggerMailAlert: function () {
        this.TriggerMailboxAlert();
    },

    ResetMailboxAlert: function () {
        this.HasUnreadMail = false;
        const MailIndicatorElement = $("#DesktopMailIndicator");
        MailIndicatorElement.addClass("HiddenElement");
        this.StopMailAnimation();
    },

    ResetMailAlert: function () {
        this.ResetMailboxAlert();
    }
};

$(document).ready(function () {
    DesktopMonitoringClients.Initialize();
});
