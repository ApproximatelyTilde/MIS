import boto3                           as Boto3
import botocore.exceptions             as BotoCoreExceptions
import typing                          as Typing
import uuid                            as UniversallyUniqueIdentifier
import Server.Config                   as Config
import Server.Models.StorageFile       as StorageFile
import Server.Models.User              as User
import Server.Services.DebugService     as DebugService

class OracleStorageService:
    def __init__(self) -> None:
        self.EndpointURL: str = Config.GLOBAL_SETTINGS.OCI_S3_ENDPOINT_URL
        self.AccessKeyID: str = Config.GLOBAL_SETTINGS.OCI_S3_ACCESS_KEY_ID
        self.SecretAccessKey: str = Config.GLOBAL_SETTINGS.OCI_S3_SECRET_ACCESS_KEY
        self.BucketName: str = Config.GLOBAL_SETTINGS.OCI_S3_BUCKET_NAME
        self.Region: str = Config.GLOBAL_SETTINGS.OCI_S3_REGION
        self.Client: Typing.Any = Boto3.client("s3", endpoint_url = self.EndpointURL, aws_access_key_id = self.AccessKeyID, aws_secret_access_key = self.SecretAccessKey, region_name = self.Region)

    def CheckQuotaAvailable(self, UserRecord: User.User, IncomingFileSizeBytes: int) -> bool:
        DebugService.LogDebugMessage(f"Checking Storage Quota For User: {UserRecord.Identifier}, Incoming File Size Bytes: {IncomingFileSizeBytes}")
        ProjectedTotalBytes: int = UserRecord.StorageUsedBytes + IncomingFileSizeBytes
        QuotaAvailable: bool = ProjectedTotalBytes <= Config.GLOBAL_SETTINGS.USER_STORAGE_QUOTA_BYTES
        DebugService.LogDebugMessage(f"Storage Quota Evaluation Result: {QuotaAvailable}")
        return QuotaAvailable

    async def UploadFile(self, UserRecord: User.User, FileName: str, ContentType: str, FileBytes: bytes) -> Typing.Optional[str]:
        FileSizeBytes: int = len(FileBytes)
        DebugService.LogDebugMessage(f"Uploading File {FileName} With Content Type: {ContentType}, Size Bytes: {FileSizeBytes} For User: {UserRecord.Identifier}")
        if not self.CheckQuotaAvailable(UserRecord, FileSizeBytes):
            DebugService.LogDebugMessage(f"Upload Aborted Due To Storage Quota Exceeded For User: {UserRecord.Identifier}")
            return None

        UniqueObjectKey: str = f"users/{UserRecord.Identifier}/{UniversallyUniqueIdentifier.uuid4()}_{FileName}"
        try:
            self.Client.put_object(Bucket = self.BucketName, Key = UniqueObjectKey, Body = FileBytes, ContentType = ContentType)
            DebugService.LogDebugMessage(f"Successfully Uploaded File With Object Key: {UniqueObjectKey}")
            return UniqueObjectKey
        except BotoCoreExceptions.ClientError:
            DebugService.LogDebugMessage(f"Failed To Upload File To Object Storage Due To Client Error For Object Key: {UniqueObjectKey}")
            return None

    async def RetrieveFileBytes(self, ObjectKey: str) -> Typing.Optional[bytes]:
        DebugService.LogDebugMessage(f"Retrieving File Bytes For Object Key: {ObjectKey}")
        try:
            Response = self.Client.get_object(Bucket = self.BucketName, Key = ObjectKey)
            DebugService.LogDebugMessage(f"Successfully Retrieved File Bytes For Object Key: {ObjectKey}")
            return Response["Body"].read()
        except BotoCoreExceptions.ClientError:
            DebugService.LogDebugMessage(f"Failed To Retrieve File Bytes For Object Key: {ObjectKey}")
            return None

    async def DeleteFile(self, ObjectKey: str) -> bool:
        DebugService.LogDebugMessage(f"Deleting Object From Storage For Object Key: {ObjectKey}")
        try:
            self.Client.delete_object(Bucket = self.BucketName, Key = ObjectKey)
            DebugService.LogDebugMessage(f"Successfully Deleted Object From Storage For Object Key: {ObjectKey}")
            return True
        except BotoCoreExceptions.ClientError:
            DebugService.LogDebugMessage(f"Failed To Delete Object From Storage For Object Key: {ObjectKey}")
            return False

GLOBAL_STORAGE_SERVICE: OracleStorageService = OracleStorageService()
