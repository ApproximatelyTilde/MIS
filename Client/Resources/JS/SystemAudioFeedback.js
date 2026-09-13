const SystemAudioFeedback = {
    AudioContextInstance: null,
    FloppySeekIntervalID: null,

    Initialize: function () {
        window.SystemAudioFeedback = this;
        $(document).on("pointerdown", ".Button, .LauncherItemButton, .DesktopMenuItemButton", () => {
            this.PlayMechanicalClick();
        });

        document.body.addEventListener("htmx:beforeRequest", () => {
            this.PlayFloppySeek();
        });

        document.body.addEventListener("htmx:afterRequest", () => {
            this.StopFloppySeek();
        });
    },

    GetAudioContext: function () {
        if (!this.AudioContextInstance) {
            const AudioContextConstructor = window.AudioContext || window.webkitAudioContext;
            if (AudioContextConstructor) {
                this.AudioContextInstance = new AudioContextConstructor();
            }
        }

        if ((this.AudioContextInstance) && (this.AudioContextInstance.state === "suspended")) {
            this.AudioContextInstance.resume();
        }

        return this.AudioContextInstance;
    },

    PlaySystemBell: function (Frequency = 800, Duration = 0.15) {
        const AudioContextInstance = this.GetAudioContext();
        if (!AudioContextInstance) {
            return;
        }

        const CurrentTime = AudioContextInstance.currentTime;
        const OscillatorNodeInstance = AudioContextInstance.createOscillator();
        const GainNodeInstance = AudioContextInstance.createGain();
        OscillatorNodeInstance.type = "square";
        OscillatorNodeInstance.frequency.setValueAtTime(Frequency, CurrentTime);
        GainNodeInstance.gain.setValueAtTime(0.2, CurrentTime);
        GainNodeInstance.gain.exponentialRampToValueAtTime(0.001, (CurrentTime + Duration));
        OscillatorNodeInstance.connect(GainNodeInstance);
        GainNodeInstance.connect(AudioContextInstance.destination);
        OscillatorNodeInstance.start(CurrentTime);
        OscillatorNodeInstance.stop((CurrentTime + Duration));
    },

    PlayMechanicalClick: function () {
        const AudioContextInstance = this.GetAudioContext();
        if (!AudioContextInstance) {
            return;
        }

        const CurrentTime = AudioContextInstance.currentTime;
        const ClickDuration = 0.012;
        const OscillatorNodeInstance = AudioContextInstance.createOscillator();
        const GainNodeInstance = AudioContextInstance.createGain();
        OscillatorNodeInstance.type = "square";
        OscillatorNodeInstance.frequency.setValueAtTime(1400, CurrentTime);
        OscillatorNodeInstance.frequency.exponentialRampToValueAtTime(300, (CurrentTime + ClickDuration));
        GainNodeInstance.gain.setValueAtTime(0.12, CurrentTime);
        GainNodeInstance.gain.exponentialRampToValueAtTime(0.001, (CurrentTime + ClickDuration));
        OscillatorNodeInstance.connect(GainNodeInstance);
        GainNodeInstance.connect(AudioContextInstance.destination);
        OscillatorNodeInstance.start(CurrentTime);
        OscillatorNodeInstance.stop((CurrentTime + ClickDuration));
    },

    PlayFloppySeek: function () {
        if (this.FloppySeekIntervalID !== null) {
            return;
        }

        const StepFrequencies = [90, 110, 130, 150, 170];
        const ExecuteStepPulse = () => {
            const AudioContextInstance = this.GetAudioContext();
            if (!AudioContextInstance) {
                return;
            }

            const CurrentTime = AudioContextInstance.currentTime;
            const PulseDuration = 0.02;
            const SelectedFrequency = StepFrequencies[Math.floor((Math.random() * StepFrequencies.length))];
            const OscillatorNodeInstance = AudioContextInstance.createOscillator();
            const GainNodeInstance = AudioContextInstance.createGain();
            OscillatorNodeInstance.type = "square";
            OscillatorNodeInstance.frequency.setValueAtTime(SelectedFrequency, CurrentTime);
            GainNodeInstance.gain.setValueAtTime(0.08, CurrentTime);
            GainNodeInstance.gain.exponentialRampToValueAtTime(0.001, (CurrentTime + PulseDuration));
            OscillatorNodeInstance.connect(GainNodeInstance);
            GainNodeInstance.connect(AudioContextInstance.destination);
            OscillatorNodeInstance.start(CurrentTime);
            OscillatorNodeInstance.stop((CurrentTime + PulseDuration));
        };

        ExecuteStepPulse();
        this.FloppySeekIntervalID = setInterval(ExecuteStepPulse, 70);
    },

    StopFloppySeek: function () {
        if (this.FloppySeekIntervalID !== null) {
            clearInterval(this.FloppySeekIntervalID);
            this.FloppySeekIntervalID = null;
        }
    }
};

$(document).ready(function () {
    SystemAudioFeedback.Initialize();
});
