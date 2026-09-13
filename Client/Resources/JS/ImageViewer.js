const ImageViewerManager = {
  ViewFile: function (FileIdentifier, FileName) {
    SystemDebugger.LogDebugMessage("Displaying Image Asset: " + FileName + " With Identifier: " + FileIdentifier);
    const StreamURL = `/API/Storage/Files/${FileIdentifier}/Stream`;
    const WindowIdentifier = `WindowImage_${FileIdentifier.replace(/-/g, "_")}`;
    const ContentHTML = `
      <div class="ImageViewerContainer">
        <img src="${StreamURL}" alt="${FileName}" class="ImageViewerElement" />
        <div class="TextMuted SmallText MarginTopSmall">${FileName}</div>
      </div>
    `;
    const Config = {
      Identifier: WindowIdentifier,
      Title: `Image Viewer - ${FileName}`,
      Width: 500,
      Height: 400,
      Left: 260,
      Top: 140,
      ContentHTML: ContentHTML
    };
    WindowManager.OpenWindow(Config);
  }
};

$(document).on("click", ".ViewImageButton", function () {
  const FileIdentifier = $(this).attr("data-file-identifier");
  const FileName = $(this).attr("data-file-name");
  SystemDebugger.LogDebugMessage("Image View Request Triggered For File: " + FileName);
  ImageViewerManager.ViewFile(FileIdentifier, FileName);
});
