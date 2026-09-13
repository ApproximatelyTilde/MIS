const MediaPlayerManager = {
  PlayFile: function (FileID, FileName) {
    this.PlayAudioFile(FileID, FileName);
  },

  PlayAudioFile: function (FileID, FileName) {
    SystemDebugger.LogMessage("DEBUG", "Opening Audio Track: \"" + FileName + "\" (" + FileID + ")");
    const StreamURL = `/API/Storage/Files/${FileID}/Stream`;
    this.OpenAudioPlayerWindow(FileName, StreamURL, FileID);
  },

  OpenAudioPlayerWindow: function (FileName, StreamURL, FileID) {
    const WindowID = "WindowAudioPlayer";
    const ContentHTML = `
      <div class="AudioPlayerContainer">
        <div class="AudioWaveSymbol">&#9835;</div>
        <div class="TextWarm AudioTrackTitle">${FileName}</div>
        <audio controls class="AudioControlElement" src="${StreamURL}" preload="metadata"></audio>
        <div class="TerminalPane AudioPlayerErrorPane HiddenElement MarginTopSmall">
          <div class="TextDanger HeaderText MarginBottomSmall">UNABLE TO PLAY AUDIO</div>
          <div class="TextMuted SmallText AudioPlayerErrorMessage">The requested audio file could not be retrieved from storage.</div>
        </div>
        <div class="TextMuted SmallText">Streaming from Oracle Object Storage</div>
      </div>
    `;
    const Config = {
      ID: WindowID,
      Title: `Audio Player - ${FileName}`,
      Width: 256,
      Height: 284,
      MinWidth: 256,
      MinHeight: 284,
      Left: 220,
      Top: 180,
      ContentHTML: ContentHTML,
      BypassPlacement: true
    };
    WindowManager.OpenWindow(Config);
  },

  PlayVideoFile: function (FileID, FileName) {
    SystemDebugger.LogMessage("DEBUG", "Opening Video Asset: \"" + FileName + "\" (" + FileID + ")");
    const StreamURL = `/API/Storage/Files/${FileID}/Stream`;
    this.OpenVideoPlayerWindow(FileName, StreamURL, FileID);
  },

  OpenVideoPlayerWindow: function (FileName, StreamURL, FileID) {
    const WindowID = `WindowVideo_${FileID.replace(/-/g, "_")}`;
    const ContentHTML = `
      <div class="VideoPlayerContainer">
        <video controls class="VideoControlElement" src="${StreamURL}" preload="metadata"></video>
        <div class="TerminalPane VideoPlayerErrorPane HiddenElement MarginTopSmall">
          <div class="TextDanger HeaderText MarginBottomSmall">UNABLE TO PLAY VIDEO</div>
          <div class="TextMuted SmallText VideoPlayerErrorMessage">The requested video file could not be retrieved from storage.</div>
        </div>
        <div class="TextMuted SmallText MarginTopSmall">${FileName}</div>
      </div>
    `;
    const Config = {
      ID: WindowID,
      Title: `Video Player - ${FileName}`,
      Width: 360,
      Height: 284,
      MinWidth: 256,
      MinHeight: 284,
      Left: 240,
      Top: 140,
      ContentHTML: ContentHTML,
      BypassPlacement: true
    };
    WindowManager.OpenWindow(Config);
  }
};

const AudioPlayerManager = MediaPlayerManager;

document.addEventListener("click", function (Event) {
  const Target = Event.target.closest(".PlayMediaButton");
  if (!Target) return;
  const FileID    = Target.getAttribute("data-file-id");
  const FileName  = Target.getAttribute("data-file-name");
  const MediaType = Target.getAttribute("data-media-type");
  if (MediaType === "video") {
    MediaPlayerManager.PlayVideoFile(FileID, FileName);
  } else {
    MediaPlayerManager.PlayAudioFile(FileID, FileName);
  }
});

document.addEventListener("click", function (Event) {
  const Target = Event.target.closest(".PlayAudioButton");
  if (!Target) return;
  const FileID   = Target.getAttribute("data-file-id");
  const FileName = Target.getAttribute("data-file-name");
  MediaPlayerManager.PlayAudioFile(FileID, FileName);
});

$(document).on("error", ".AudioControlElement", function () {
  const MediaElement = this;
  const MediaError = MediaElement.error;
  let ReasonMessage = "The audio file could not be retrieved.";
  let DiagnosticMessage = "Unknown Media Error";
  if (MediaError) {
    if (MediaError.code === MediaError.MEDIA_ERR_ABORTED) {
      ReasonMessage = "Audio playback was aborted.";
      DiagnosticMessage = "Playback aborted by user or agent";
    } else if (MediaError.code === MediaError.MEDIA_ERR_NETWORK) {
      ReasonMessage = "A network error occurred while loading audio.";
      DiagnosticMessage = "Network error during media download";
    } else if (MediaError.code === MediaError.MEDIA_ERR_DECODE) {
      ReasonMessage = "The audio file is corrupted or unsupported.";
      DiagnosticMessage = "Media decoding failure or corrupted stream";
    } else if (MediaError.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED) {
      ReasonMessage = "Audio format not supported or file not found.";
      DiagnosticMessage = "Format unsupported or source URL not found (404/MIME mismatch)";
    }
    if (MediaError.message) {
      DiagnosticMessage += ": " + MediaError.message;
    }
  }
  SystemDebugger.LogMessage("ERROR", "Audio Playback Failure: " + DiagnosticMessage + " (Source: " + MediaElement.src + ")");
  const ErrorPane = $(MediaElement).siblings(".AudioPlayerErrorPane");
  ErrorPane.find(".AudioPlayerErrorMessage").text(ReasonMessage);
  ErrorPane.removeClass("HiddenElement");
});

$(document).on("error", ".VideoControlElement", function () {
  const MediaElement = this;
  const MediaError = MediaElement.error;
  let ReasonMessage = "The video file could not be retrieved.";
  let DiagnosticMessage = "Unknown Media Error";
  if (MediaError) {
    if (MediaError.code === MediaError.MEDIA_ERR_ABORTED) {
      ReasonMessage = "Video playback was aborted.";
      DiagnosticMessage = "Playback aborted by user or agent";
    } else if (MediaError.code === MediaError.MEDIA_ERR_NETWORK) {
      ReasonMessage = "A network error occurred while loading video.";
      DiagnosticMessage = "Network error during media download";
    } else if (MediaError.code === MediaError.MEDIA_ERR_DECODE) {
      ReasonMessage = "The video file is corrupted or unsupported.";
      DiagnosticMessage = "Media decoding failure or corrupted stream";
    } else if (MediaError.code === MediaError.MEDIA_ERR_SRC_NOT_SUPPORTED) {
      ReasonMessage = "Video format not supported or file not found.";
      DiagnosticMessage = "Format unsupported or source URL not found (404/MIME mismatch)";
    }
    if (MediaError.message) {
      DiagnosticMessage += ": " + MediaError.message;
    }
  }
  SystemDebugger.LogMessage("ERROR", "Video Playback Failure: " + DiagnosticMessage + " (Source: " + MediaElement.src + ")");
  $(MediaElement).addClass("HiddenElement");
  const ErrorPane = $(MediaElement).siblings(".VideoPlayerErrorPane");
  ErrorPane.find(".VideoPlayerErrorMessage").text(ReasonMessage);
  ErrorPane.removeClass("HiddenElement");
});

document.body.addEventListener("FileShared", function (Event) {
  const FileID = Event.detail.FileID;
  const ShareURL = window.location.origin + "/Objects/" + FileID;
  SystemDebugger.LogMessage("DEBUG", "File Shared Event: ID=" + FileID + ", URL=" + ShareURL);
  if (navigator.clipboard && navigator.clipboard.writeText) {
    navigator.clipboard.writeText(ShareURL).catch(function (ClipboardError) {
      SystemDebugger.LogMessage("DEBUG", "Clipboard Write Failed: " + ClipboardError.message);
    });
  }
  const TargetButton = document.querySelector(`.ShareFileButton[data-file-id="${FileID}"]`);
  if (TargetButton) {
    TargetButton.classList.add("ButtonSuccess");
    setTimeout(function () {
      TargetButton.classList.remove("ButtonSuccess");
    }, 1000);
  }
});
