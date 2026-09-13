import io                            as IO
import typing                        as Typing
import PIL.Image                     as PILImage
import fastapi                       as FastAPI
import Server.Services.DebugService   as DebugService

MAXIMUM_IMAGE_SIZE_BYTES: int = 10485760
MAXIMUM_IMAGE_DIMENSION: int = 1600
ALLOWED_IMAGE_FORMATS: Typing.Set[str] = {
    "JPEG",
    "PNG",
    "WEBP"
}

class ImageProcessingService:
    def SanitizeAndOptimizeImage(self, RawFileBytes: bytes, OriginalFileName: str) -> Typing.Tuple[bytes, str]:
        FileSizeBytes: int = len(RawFileBytes)
        if FileSizeBytes > MAXIMUM_IMAGE_SIZE_BYTES:
            DebugService.LogDebugMessage(f"Image Rejected: '{OriginalFileName}' Size {FileSizeBytes}B Exceeds Limit {MAXIMUM_IMAGE_SIZE_BYTES}B")
            raise FastAPI.HTTPException(status_code = 400, detail = "Image size exceeds maximum limit of 10MB")

        try:
            InputStream: IO.BytesIO = IO.BytesIO(RawFileBytes)
            ParsedImage: PILImage.Image = PILImage.open(InputStream)
            ImageFormat: Typing.Optional[str] = ParsedImage.format
            if not ImageFormat or ImageFormat.upper() not in ALLOWED_IMAGE_FORMATS:
                DebugService.LogDebugMessage(f"Image Format Unsupported: '{ImageFormat}' for '{OriginalFileName}'")
                raise FastAPI.HTTPException(status_code = 400, detail = "Unsupported image format. Permitted formats are JPEG, PNG, and WEBP")

            NormalizedFormat: str = ImageFormat.upper()
            TargetMode: str = "RGBA" if (NormalizedFormat in ["PNG", "WEBP"] and ParsedImage.mode in ["RGBA", "LA", "P"]) else "RGB"
            ConvertedImage: PILImage.Image = ParsedImage.convert(TargetMode)

            Width: int = ConvertedImage.width
            Height: int = ConvertedImage.height
            if Width > MAXIMUM_IMAGE_DIMENSION or Height > MAXIMUM_IMAGE_DIMENSION:
                ScaleRatio: float = min(MAXIMUM_IMAGE_DIMENSION / Width, MAXIMUM_IMAGE_DIMENSION / Height)
                NewWidth: int = max(1, int(Width * ScaleRatio))
                NewHeight: int = max(1, int(Height * ScaleRatio))
                ConvertedImage = ConvertedImage.resize((NewWidth, NewHeight), resample = PILImage.Resampling.LANCZOS)
                DebugService.LogDebugMessage(f"Image Resized: {Width}x{Height} -> {NewWidth}x{NewHeight} ('{OriginalFileName}')")

            CleanImage: PILImage.Image = PILImage.new(TargetMode, ConvertedImage.size)
            CleanImage.putdata(list(ConvertedImage.getdata()))

            OutputStream: IO.BytesIO = IO.BytesIO()
            if NormalizedFormat == "JPEG":
                CleanImage.save(OutputStream, format = "JPEG", quality = 85, optimize = True)
                ContentType: str = "image/jpeg"
            elif NormalizedFormat == "PNG":
                CleanImage.save(OutputStream, format = "PNG", optimize = True)
                ContentType: str = "image/png"
            else:
                CleanImage.save(OutputStream, format = "WEBP", quality = 85, method = 6)
                ContentType: str = "image/webp"

            OutputBytes: bytes = OutputStream.getvalue()
            DebugService.LogDebugMessage(f"Image Optimized: '{OriginalFileName}' ({FileSizeBytes}B -> {len(OutputBytes)}B, {ContentType})")
            return OutputBytes, ContentType
        except FastAPI.HTTPException:
            raise
        except Exception as ProcessingError:
            DebugService.LogDebugMessage(f"Image Processing Error ['{OriginalFileName}']: {ProcessingError}")
            raise FastAPI.HTTPException(status_code = 400, detail = "Failed to process and sanitize image")

GLOBAL_IMAGE_PROCESSING_SERVICE: ImageProcessingService = ImageProcessingService()
