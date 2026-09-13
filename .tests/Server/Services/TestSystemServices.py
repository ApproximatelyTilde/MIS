import io                                      as IO
import typing                                  as Typing
import unittest.mock                           as MockLibrary
import PIL.Image                               as PILImage
import pytest                                  as Pytest
import sqlalchemy.ext.asyncio                  as AsyncIO
import Server.Models.Mail                      as Mail
import Server.Models.User                      as User
import Server.Services.AutomationService       as AutomationService
import Server.Services.ImageProcessingService  as ImageProcessingService
import Server.Services.MailboxService          as MailboxService
import Server.Services.OracleStorageService    as OracleStorageService
import Server.Services.TemplateRendererService as TemplateRendererService

class TestSystemServices:
    def TestImageProcessingSanitizeAndOptimizePNG(self) -> None:
        RawImageBuffer : IO.BytesIO        = IO.BytesIO()
        SampleImage    : PILImage.Image    = PILImage.new("RGBA", (32, 32), (255, 0, 0, 255))

        SampleImage.save(RawImageBuffer, format = "PNG")

        ImageBytes                  : bytes                    = RawImageBuffer.getvalue()
        ImageResult                 : Typing.Tuple[bytes, str] = ImageProcessingService.GLOBAL_IMAGE_PROCESSING_SERVICE.SanitizeAndOptimizeImage(RawFileBytes = ImageBytes, OriginalFileName = "Icon.png")
        OptimizedBytes, ContentType                            = ImageResult
        assert (len(OptimizedBytes) > 0)
        assert (ContentType == "image/png")

    def TestMailboxGetCategoryDisplayLabel(self) -> None:
        assert (MailboxService.GetCategoryDisplayLabel(Mail.MailCategory.SystemAlert) == "System Alert")
        assert (MailboxService.GetCategoryDisplayLabel(Mail.MailCategory.CharacterReview) == "Character Review")
        assert (MailboxService.GetCategoryDisplayLabel(Mail.MailCategory.GeneralMessage) == "General")

    def TestMailboxRenderMarkdown(self) -> None:
        MarkdownText: str = "**Bold Text** and *Italic Text*"
        RenderedHTML: str = MailboxService.RenderMarkdown(ContentText = MarkdownText)
        assert ("<strong>Bold Text</strong>" in RenderedHTML)
        assert ("<em>Italic Text</em>" in RenderedHTML)

    async def TestMailboxDispatchAndInboxRetrieval(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        DispatchedMessage: Mail.MailMessage              = await MailboxService.DispatchAutomatedMail(DatabaseSession = DatabaseSession, RecipientUserID = RegularUserRecord.ID, Subject = "Account Verification", Body = "Welcome to the workstation environment.")
        assert (DispatchedMessage.ID is not None)
        assert (DispatchedMessage.IsAutomated is True)

        InboxList        : Typing.List[Mail.MailMessage] = await MailboxService.GetInboxMessages(DatabaseSession = DatabaseSession, RecipientUserID = RegularUserRecord.ID)
        assert (len(InboxList) > 0)
        assert (InboxList[0].Subject == "Account Verification")

    def TestOracleStorageCheckQuota(self, RegularUserRecord: User.User) -> None:
        StorageService: OracleStorageService.OracleStorageService = OracleStorageService.OracleStorageService()
        RegularUserRecord.StorageUsedBytes                        = 1000
        assert (StorageService.CheckQuotaAvailable(UserRecord = RegularUserRecord, IncomingFileSizeBytes = 500) is True)

    async def TestOracleStorageVirtualizedOperations(self, RegularUserRecord: User.User) -> None:
        StorageService: OracleStorageService.OracleStorageService = OracleStorageService.OracleStorageService()

        with MockLibrary.patch.object(StorageService.Client, "put_object", return_value = {}):
            UploadedKey: Typing.Optional[str] = await StorageService.UploadFile(UserRecord = RegularUserRecord, FileName = "TestDocument.txt", ContentType = "text/plain", FileBytes = b"Sample file payload bytes")
            assert (UploadedKey is not None)
            assert (RegularUserRecord.ID in UploadedKey)

        MockBodyResponse: MockLibrary.MagicMock = MockLibrary.MagicMock()
        MockBodyResponse.read.return_value      = b"Sample file payload bytes"
        with MockLibrary.patch.object(StorageService.Client, "get_object", return_value = {"Body": MockBodyResponse}):
            RetrievedBytes: Typing.Optional[bytes] = await StorageService.RetrieveFileBytes(ObjectKey = UploadedKey)
            assert (RetrievedBytes == b"Sample file payload bytes")

        with MockLibrary.patch.object(StorageService.Client, "delete_object", return_value = {}):
            DeleteOutcome: bool = await StorageService.DeleteFile(ObjectKey = UploadedKey)
            assert (DeleteOutcome is True)

    def TestTemplateRendererService(self) -> None:
        RenderedHTML: str = TemplateRendererService.RenderPartial(PartialName = "Characters/CharacterListPartial.html", Context = {"Characters": []})
        assert (isinstance(RenderedHTML, str))

    def TestAutomationValidateDiceExpression(self) -> None:
        AutomationServiceInstance: AutomationService.AutomationService = AutomationService.AutomationService()
        assert (AutomationServiceInstance.ValidateDiceExpression("1d20+5") is True)
        assert (AutomationServiceInstance.ValidateDiceExpression("2d6 + 3 - 1") is True)
        assert (AutomationServiceInstance.ValidateDiceExpression("(1d20+5") is False)
        assert (AutomationServiceInstance.ValidateDiceExpression("") is False)
