import boto3                           as Boto3
import botocore.config                    as BotoCoreConfig
import botocore.exceptions                as BotoCoreExceptions
import typing                             as Typing
import uuid                               as UUID
import Server.Config                      as Config
import Server.Models.StorageFile          as StorageFile
import Server.Models.User                 as User
import Server.Services.DebugService        as DebugService

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
        DebugService.LogDebugMessage(f"Storage Quota Evaluated: User={UserRecord.Identifier}, Incoming={IncomingFileSizeBytes}B, Allowed={QuotaAvailable}")
        return QuotaAvailable

    async def UploadFile(self, UserRecord: User.User, FileName: str, ContentType: str, FileBytes: bytes) -> Typing.Optional[str]:
        FileSizeBytes: int = len(FileBytes)
        if not self.CheckQuotaAvailable(UserRecord, FileSizeBytes):
            DebugService.LogDebugMessage(f"Upload Quota Exceeded: User={UserRecord.Identifier}, File='{FileName}' ({FileSizeBytes}B)")
            return None

        UniqueObjectKey: str = f"users/{UserRecord.Identifier}/{UUID.uuid4()}_{FileName}"
        try:
            self.Client.put_object(Bucket = self.BucketName, Key = UniqueObjectKey, Body = FileBytes, ContentType = ContentType)
            DebugService.LogDebugMessage(f"Upload Succeeded: Key='{UniqueObjectKey}' ({FileSizeBytes}B, {ContentType})")
            return UniqueObjectKey
        except (BotoCoreExceptions.ClientError, BotoCoreExceptions.BotoCoreError) as StorageError:
            DebugService.LogDebugMessage(f"Upload Failed: Key='{UniqueObjectKey}': {StorageError}")
            return None

    async def RetrieveFileBytes(self, ObjectKey: str) -> Typing.Optional[bytes]:
        try:
            Response = self.Client.get_object(Bucket = self.BucketName, Key = ObjectKey)
            RetrievedBytes: bytes = Response["Body"].read()
            DebugService.LogDebugMessage(f"Retrieved Object: Key='{ObjectKey}' ({len(RetrievedBytes)}B)")
            return RetrievedBytes
        except (BotoCoreExceptions.ClientError, BotoCoreExceptions.BotoCoreError) as StorageError:
            DebugService.LogDebugMessage(f"Retrieve Failed: Key='{ObjectKey}': {StorageError}")
            return None

    async def DeleteFile(self, ObjectKey: str) -> bool:
        try:
            self.Client.delete_object(Bucket = self.BucketName, Key = ObjectKey)
            DebugService.LogDebugMessage(f"Deleted Object: Key='{ObjectKey}'")
            return True
        except (BotoCoreExceptions.ClientError, BotoCoreExceptions.BotoCoreError) as StorageError:
            DebugService.LogDebugMessage(f"Delete Failed: Key='{ObjectKey}': {StorageError}")
            return False

GLOBAL_STORAGE_SERVICE: OracleStorageService = OracleStorageService()
