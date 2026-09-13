const AudioPlayerManager = {
  CurrentAudio: new Audio(),
  IsPlaying: false,

  PlayFile: function(FileIdentifier, FileName) {
    const StreamURL = `/API/Storage/Files/${FileIdentifier}/Stream`;
    this.CurrentAudio.src = StreamURL;
    this.CurrentAudio.play();
    this.IsPlaying = true;
    this.OpenPlayerWindow(FileName, StreamURL);
  },

  OpenPlayerWindow: function(FileName, StreamURL) {
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

$(document).on("click", ".PlayAudioButton", function() {
  const FileIdentifier = $(this).attr("data-file-identifier");
  const FileName = $(this).attr("data-file-name");
  AudioPlayerManager.PlayFile(FileIdentifier, FileName);
});
