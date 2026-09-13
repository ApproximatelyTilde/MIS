import asyncio                      as AsyncIOBuiltin
import boto3                        as Boto3
import botocore.config              as BotoCoreConfig
import botocore.exceptions          as BotoCoreExceptions
import typing                       as Typing
import uuid                         as UUID
import Server.Config                as Config
import Server.Models.StorageFile    as StorageFile
import Server.Models.User           as User
import Server.Services.DebugService as DebugService

class OracleStorageService:
    def __init__(self) -> None:
        self.EndpointURL: str = Config.GLOBAL_SETTINGS.OCI_S3_ENDPOINT_URL
        self.AccessKeyID: str = Config.GLOBAL_SETTINGS.OCI_S3_ACCESS_KEY_ID
        self.SecretAccessKey: str = Config.GLOBAL_SETTINGS.OCI_S3_SECRET_ACCESS_KEY
        self.BucketName: str = Config.GLOBAL_SETTINGS.OCI_S3_BUCKET_NAME
        self.Region: str = Config.GLOBAL_SETTINGS.OCI_S3_REGION
        ClientConfiguration = BotoCoreConfig.Config(s3 = {"addressing_style": "path", "payload_signing_enabled": False}, request_checksum_calculation = "when_required", response_checksum_validation = "when_required")
        self.Client: Typing.Any = Boto3.client("s3", endpoint_url = self.EndpointURL, aws_access_key_id = self.AccessKeyID, aws_secret_access_key = self.SecretAccessKey, region_name = self.Region, config = ClientConfiguration)

    def CheckQuotaAvailable(self, UserRecord: User.User, IncomingFileSizeBytes: int) -> bool:
        ProjectedTotalBytes: int = UserRecord.StorageUsedBytes + IncomingFileSizeBytes
        QuotaAvailable: bool = ProjectedTotalBytes <= Config.GLOBAL_SETTINGS.USER_STORAGE_QUOTA_BYTES
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Evaluated Storage Quota: UserID=\"{UserRecord.ID[:8]}…\", Allowed={QuotaAvailable}")
        return QuotaAvailable

    async def UploadFile(self, UserRecord: User.User, FileName: str, ContentType: str, FileBytes: bytes) -> Typing.Optional[str]:
        FileSizeBytes: int = len(FileBytes)
        if not self.CheckQuotaAvailable(UserRecord, FileSizeBytes):
            DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Upload Quota Exceeded: UserID=\"{UserRecord.ID[:8]}…\", File=\"{FileName}\"")
            return None

        UniqueObjectKey: str = f"users/{UserRecord.ID}/{UUID.uuid4()}_{FileName}"
        try:
            await AsyncIOBuiltin.to_thread(self.Client.put_object, Bucket = self.BucketName, Key = UniqueObjectKey, Body = FileBytes, ContentType = ContentType)
            DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = f"Upload Succeeded: Size={FileSizeBytes}B, Type=\"{ContentType}\"")
            return UniqueObjectKey

        except (BotoCoreExceptions.ClientError, BotoCoreExceptions.BotoCoreError) as StorageError:
            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Upload Failed: Error={type(StorageError).__name__}")
            return None

    async def RetrieveFileBytes(self, ObjectKey: str) -> Typing.Optional[bytes]:
        try:
            Response = await AsyncIOBuiltin.to_thread(self.Client.get_object, Bucket = self.BucketName, Key = ObjectKey)
            RetrievedBytes: bytes = await AsyncIOBuiltin.to_thread(Response["Body"].read)
            DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Retrieved Object: Size={len(RetrievedBytes)}B")
            return RetrievedBytes

        except (BotoCoreExceptions.ClientError, BotoCoreExceptions.BotoCoreError) as StorageError:
            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Retrieve Failed: Error={type(StorageError).__name__}")
            return None

    async def DeleteFile(self, ObjectKey: str) -> bool:
        try:
            await AsyncIOBuiltin.to_thread(self.Client.delete_object, Bucket = self.BucketName, Key = ObjectKey)
            DebugService.LogMessage(Level = DebugService.LogLevel.Info, Message = "Deleted Object from Storage Provider")
            return True

        except (BotoCoreExceptions.ClientError, BotoCoreExceptions.BotoCoreError) as StorageError:
            DebugService.LogMessage(Level = DebugService.LogLevel.Error, Message = f"Delete Failed: Error={type(StorageError).__name__}")
            return False

GLOBAL_STORAGE_SERVICE: OracleStorageService = OracleStorageService()
