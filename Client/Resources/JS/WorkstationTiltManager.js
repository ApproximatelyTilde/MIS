class WorkstationMotionTilt extends VanillaTilt {
    constructor(Element, Settings) {
        super(Element, Settings);
        SystemDebugger.LogDebugMessage("Initializing Workstation Motion Tilt Stage");
        this.IsMotionDisabled = false;
        this.CurrentPanX = 0.0;
        this.CurrentPanY = 0.0;
        this.CurrentTiltX = 0.0;
        this.CurrentTiltY = 0.0;
        this.TargetPanX = 0.0;
        this.TargetPanY = 0.0;
        this.TargetTiltX = 0.0;
        this.TargetTiltY = 0.0;
        this.AnimationFrameIdentifier = null;
        this.MaximumPanPixelsX = 42.0;
        this.MaximumPanPixelsY = 28.0;
        this.SmoothingFactor = 0.08;
        this.DisabledSmoothingFactor = 0.14;
        this.BindWindowFocusListeners();
        this.StartAnimationLoop();
    }

    BindWindowFocusListeners() {
        this.OnWindowBlurBind = this.HandleFocusLoss.bind(this);
        this.OnWindowFocusBind = this.HandleFocusGain.bind(this);
        window.addEventListener("blur", this.OnWindowBlurBind);
        window.addEventListener("focus", this.OnWindowFocusBind);
        document.addEventListener("mouseleave", this.OnWindowBlurBind);
    }

    HandleFocusLoss() {
        SystemDebugger.LogDebugMessage("Window Focus Lost, Resetting Tilt Targets");
        this.TargetPanX = 0.0;
        this.TargetPanY = 0.0;
        this.TargetTiltX = 0.0;
        this.TargetTiltY = 0.0;
    }

    HandleFocusGain() {
        SystemDebugger.LogDebugMessage("Window Focus Gained, Resetting Tilt Targets");
        this.TargetPanX = 0.0;
        this.TargetPanY = 0.0;
        this.TargetTiltX = 0.0;
        this.TargetTiltY = 0.0;
    }

    setTransition() {
        this.element.style.transition = "";
    }

    update() {
    }

    onMouseMove(Event) {
        if (this.IsMotionDisabled) {
            return;
        }
        this.event = Event;
        this.CalculateTargetValues();
    }

    onMouseEnter(Event) {
        if (this.IsMotionDisabled) {
            return;
        }
        this.updateElementPosition();
        this.event = Event;
        this.CalculateTargetValues();
    }

    onMouseLeave() {
        this.HandleFocusLoss();
    }

    onDeviceOrientation(Event) {
        if (this.IsMotionDisabled) {
            return;
        }
        super.onDeviceOrientation(Event);
        this.CalculateTargetValues();
    }

    CalculateTargetValues() {
        if (!this.event) {
            return;
        }
        const Values = this.getValues();
        const PercentageX = Values.percentageX;
        const PercentageY = Values.percentageY;
        const OffsetX = (PercentageX - 50.0) / 50.0;
        const OffsetY = (PercentageY - 50.0) / 50.0;

        this.TargetPanX = -(OffsetX * this.MaximumPanPixelsX);
        this.TargetPanY = -(OffsetY * this.MaximumPanPixelsY);
        this.TargetTiltX = parseFloat(Values.tiltX);
        this.TargetTiltY = parseFloat(Values.tiltY);
    }

    StartAnimationLoop() {
        const RenderStep = () => {
            this.InterpolateMotion();
            this.AnimationFrameIdentifier = requestAnimationFrame(RenderStep);
        };
        this.AnimationFrameIdentifier = requestAnimationFrame(RenderStep);
    }

    InterpolateMotion() {
        const Factor = this.IsMotionDisabled ? this.DisabledSmoothingFactor : this.SmoothingFactor;
        const TargetX = this.IsMotionDisabled ? 0.0 : this.TargetPanX;
        const TargetY = this.IsMotionDisabled ? 0.0 : this.TargetPanY;
        const TargetTiltAngleX = this.IsMotionDisabled ? 0.0 : this.TargetTiltX;
        const TargetTiltAngleY = this.IsMotionDisabled ? 0.0 : this.TargetTiltY;

        this.CurrentPanX += (TargetX - this.CurrentPanX) * Factor;
        this.CurrentPanY += (TargetY - this.CurrentPanY) * Factor;
        this.CurrentTiltX += (TargetTiltAngleX - this.CurrentTiltX) * Factor;
        this.CurrentTiltY += (TargetTiltAngleY - this.CurrentTiltY) * Factor;

        if (Math.abs(this.CurrentPanX - TargetX) < 0.02) {
            this.CurrentPanX = TargetX;
        }
        if (Math.abs(this.CurrentPanY - TargetY) < 0.02) {
            this.CurrentPanY = TargetY;
        }
        if (Math.abs(this.CurrentTiltX - TargetTiltAngleX) < 0.02) {
            this.CurrentTiltX = TargetTiltAngleX;
        }
        if (Math.abs(this.CurrentTiltY - TargetTiltAngleY) < 0.02) {
            this.CurrentTiltY = TargetTiltAngleY;
        }

        if (this.IsMotionDisabled && this.CurrentPanX === 0.0 && this.CurrentPanY === 0.0 && this.CurrentTiltX === 0.0 && this.CurrentTiltY === 0.0) {
            if (this.element.style.transform !== "") {
                this.element.style.transform = "";
            }
            return;
        }

        const RoundedPanX = this.CurrentPanX.toFixed(2);
        const RoundedPanY = this.CurrentPanY.toFixed(2);
        const RoundedTiltX = this.CurrentTiltX.toFixed(2);
        const RoundedTiltY = this.CurrentTiltY.toFixed(2);

        this.element.style.transform = "perspective(" + this.settings.perspective + "px) translate3d(" + RoundedPanX + "px, " + RoundedPanY + "px, 0px) rotateX(" + RoundedTiltY + "deg) rotateY(" + RoundedTiltX + "deg) scale3d(" + this.settings.scale + ", " + this.settings.scale + ", " + this.settings.scale + ")";
    }

    DisableMotion() {
        if (!this.IsMotionDisabled) {
            SystemDebugger.LogDebugMessage("Disabling Workstation Tilt Motion");
            this.IsMotionDisabled = true;
            this.TargetPanX = 0.0;
            this.TargetPanY = 0.0;
            this.TargetTiltX = 0.0;
            this.TargetTiltY = 0.0;
        }
    }

    EnableMotion() {
        if (this.IsMotionDisabled) {
            SystemDebugger.LogDebugMessage("Enabling Workstation Tilt Motion");
            this.IsMotionDisabled = false;
            this.TargetPanX = 0.0;
            this.TargetPanY = 0.0;
            this.TargetTiltX = 0.0;
            this.TargetTiltY = 0.0;
        }
    }

    destroy() {
        if (this.AnimationFrameIdentifier) {
            cancelAnimationFrame(this.AnimationFrameIdentifier);
        }
        window.removeEventListener("blur", this.OnWindowBlurBind);
        window.removeEventListener("focus", this.OnWindowFocusBind);
        document.removeEventListener("mouseleave", this.OnWindowBlurBind);
        super.destroy();
    }
}

const WorkstationTiltManager = {
    TiltInstance: null,

    Initialize: function () {
        SystemDebugger.LogDebugMessage("Initializing Workstation Tilt Manager");
        const MotionStageElement = document.getElementById("WorkstationMotionStage");
        if (!MotionStageElement) {
            return;
        }
        const Configuration = {
            "reverse": true,
            "max": 1.5,
            "perspective": 1400,
            "speed": 800,
            "easing": "cubic-bezier(0.03, 0.98, 0.52, 0.99)",
            "full-page-listening": true,
            "reset": false
        };
        this.TiltInstance = new WorkstationMotionTilt(MotionStageElement, Configuration);
        if (document.body.classList.contains("ZoomedIn")) {
            this.TiltInstance.DisableMotion();
        }
    },

    DisableMotion: function () {
        if (this.TiltInstance) {
            this.TiltInstance.DisableMotion();
        }
    },

    EnableMotion: function () {
        if (this.TiltInstance) {
            this.TiltInstance.EnableMotion();
        }
    }
};
