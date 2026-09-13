const MediaPlayerManager = {
  CurrentAudio: new Audio(),
  IsPlaying: false,

  PlayFile: function (FileIdentifier, FileName) {
    this.PlayAudioFile(FileIdentifier, FileName);
  },

  PlayAudioFile: function (FileIdentifier, FileName) {
    SystemDebugger.LogDebugMessage("Playing Audio Track: '" + FileName + "' (" + FileIdentifier + ")");
    const StreamURL = `/API/Storage/Files/${FileIdentifier}/Stream`;
    this.CurrentAudio.src = StreamURL;
    this.CurrentAudio.play();
    this.IsPlaying = true;
    this.OpenAudioPlayerWindow(FileName, StreamURL);
  },

  OpenAudioPlayerWindow: function (FileName, StreamURL) {
    const WindowIdentifier = "WindowAudioPlayer";
    const ContentHTML = `
      <div class="AudioPlayerContainer">
        <div class="AudioWaveSymbol">&#9835;</div>
        <div class="TextWarm AudioTrackTitle">${FileName}</div>
        <audio controls class="AudioControlElement" src="${StreamURL}" autoplay></audio>
        <div class="TextMuted SmallText">Streaming from Oracle Object Storage</div>
      </div>
    `;
    const Config = {
      Identifier: WindowIdentifier,
      Title: `Audio Player - ${FileName}`,
      Width: 380,
      Height: 220,
      Left: 220,
      Top: 180,
      ContentHTML: ContentHTML
    };
    WindowManager.OpenWindow(Config);
  },

  PlayVideoFile: function (FileIdentifier, FileName) {
    SystemDebugger.LogDebugMessage("Playing Video Asset: '" + FileName + "' (" + FileIdentifier + ")");
    const StreamURL = `/API/Storage/Files/${FileIdentifier}/Stream`;
    this.OpenVideoPlayerWindow(FileName, StreamURL, FileIdentifier);
  },

  OpenVideoPlayerWindow: function (FileName, StreamURL, FileIdentifier) {
    const WindowIdentifier = `WindowVideo_${FileIdentifier.replace(/-/g, "_")}`;
    const ContentHTML = `
      <div class="VideoPlayerContainer">
        <video controls autoplay class="VideoControlElement" src="${StreamURL}"></video>
        <div class="TextMuted SmallText MarginTopSmall">${FileName}</div>
      </div>
    `;
    const Config = {
      Identifier: WindowIdentifier,
      Title: `Video Player - ${FileName}`,
      Width: 480,
      Height: 360,
      Left: 240,
      Top: 140,
      ContentHTML: ContentHTML
    };
    WindowManager.OpenWindow(Config);
  }
};

const AudioPlayerManager = MediaPlayerManager;

$(document).on("click", ".PlayMediaButton", function () {
  const FileIdentifier = $(this).attr("data-file-identifier");
  const FileName = $(this).attr("data-file-name");
  const MediaType = $(this).attr("data-media-type");
  if (MediaType === "video") {
    MediaPlayerManager.PlayVideoFile(FileIdentifier, FileName);
  } else {
    MediaPlayerManager.PlayAudioFile(FileIdentifier, FileName);
  }
});

$(document).on("click", ".PlayAudioButton", function () {
  const FileIdentifier = $(this).attr("data-file-identifier");
  const FileName = $(this).attr("data-file-name");
  MediaPlayerManager.PlayAudioFile(FileIdentifier, FileName);
});

document.body.addEventListener("fileShared", function (Event) {
  const FileIdentifier = Event.detail.FileIdentifier;
  const ShareURL = window.location.origin + "/Objects/" + FileIdentifier;
  SystemDebugger.LogDebugMessage("File Shared Event: ID=" + FileIdentifier + ", URL=" + ShareURL);
  navigator.clipboard.writeText(ShareURL);
  const TargetButton = document.querySelector(`.ShareFileButton[data-file-identifier="${FileIdentifier}"]`);
  if (TargetButton) {
    TargetButton.classList.add("ButtonSuccess");
    setTimeout(function () {
      TargetButton.classList.remove("ButtonSuccess");
    }, 1000);
  }
});
