const AudioPlayerManager = {
  CurrentAudio: new Audio(),
  IsPlaying: false,

  PlayFile: function (FileIdentifier, FileName) {
    SystemDebugger.LogDebugMessage("Playing Audio Track: " + FileName + " With Identifier: " + FileIdentifier);
    const StreamURL = `/API/Storage/Files/${FileIdentifier}/Stream`;
    this.CurrentAudio.src = StreamURL;
    this.CurrentAudio.play();
    this.IsPlaying = true;
    this.OpenPlayerWindow(FileName, StreamURL);
  },

  OpenPlayerWindow: function (FileName, StreamURL) {
    SystemDebugger.LogDebugMessage("Opening Audio Player Window For Track: " + FileName);
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
  }
};

$(document).on("click", ".PlayAudioButton", function () {
  const FileIdentifier = $(this).attr("data-file-identifier");
  const FileName = $(this).attr("data-file-name");
  SystemDebugger.LogDebugMessage("Audio Play Request Triggered For File: " + FileName);
  AudioPlayerManager.PlayFile(FileIdentifier, FileName);
});
