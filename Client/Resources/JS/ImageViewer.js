const ImageViewerManager = {
  ViewFile: function (FileID, FileName) {
    const StreamURL = `/API/Storage/Files/${FileID}/Stream`;
    const WindowID = `WindowImage_${FileID.replace(/-/g, "_")}`;
    SystemDebugger.LogMessage("DEBUG", "Displaying Image: \"" + FileName + "\" (" + FileID + ", Window=" + WindowID + ")");
    const ContentHTML = `
      <div class="ImageViewerContainer">
        <img src="${StreamURL}" alt="${FileName}" class="ImageViewerElement" />
        <div class="TerminalPane ImageViewerErrorPane HiddenElement MarginTopMedium">
          <div class="TextDanger HeaderText MarginBottomSmall">UNABLE TO LOAD IMAGE</div>
          <div class="TextMuted ImageViewerErrorMessage">The image file could not be retrieved from storage or is in an unsupported format.</div>
        </div>
        <div class="TextMuted SmallText MarginTopSmall">${FileName}</div>
      </div>
    `;
    const Config = {
      ID: WindowID,
      Title: `Image Viewer - ${FileName}`,
      Width: 500,
      Height: 400,
      Left: 260,
      Top: 140,
      ContentHTML: ContentHTML,
      BypassPlacement: true
    };
    WindowManager.OpenWindow(Config);
  }
};

$(document).on("click", ".ViewImageButton", function () {
  const FileID = $(this).attr("data-file-id");
  const FileName = $(this).attr("data-file-name");
  if (!FileID) {
    return;
  }
  ImageViewerManager.ViewFile(FileID, FileName);
});

$(document).on("error", ".ImageViewerElement", function () {
  const ImageElement = this;
  const ImageSource = ImageElement.src;
  const ImageAlt = ImageElement.alt || "Unknown";
  SystemDebugger.LogMessage("ERROR", "Image Load Failure: Unable to load or decode image \"" + ImageAlt + "\" (Source: " + ImageSource + ")");
  $(ImageElement).addClass("HiddenElement");
  const ErrorPane = $(ImageElement).siblings(".ImageViewerErrorPane");
  ErrorPane.removeClass("HiddenElement");
});
