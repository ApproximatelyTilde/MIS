import boto3 as Boto3
import botocore.exceptions as BotoCoreExceptions
import typing as Typing
import uuid as UniversallyUniqueIdentifier
import Server.Config as Config
import Server.Models.StorageFile as StorageFile
import Server.Models.User as User

class OracleStorageService:
    def __init__(self) -> None:
        self.EndpointURL: str = Config.GLOBAL_SETTINGS.OCI_S3_ENDPOINT_URL
        self.AccessKeyID: str = Config.GLOBAL_SETTINGS.OCI_S3_ACCESS_KEY_ID
        self.SecretAccessKey: str = Config.GLOBAL_SETTINGS.OCI_S3_SECRET_ACCESS_KEY
        self.BucketName: str = Config.GLOBAL_SETTINGS.OCI_S3_BUCKET_NAME
        self.Region: str = Config.GLOBAL_SETTINGS.OCI_S3_REGION
        self.Client: Typing.Any = Boto3.client("s3", endpoint_url = self.EndpointURL, aws_access_key_id = self.AccessKeyID, aws_secret_access_key = self.SecretAccessKey, region_name = self.Region)

    def CheckQuotaAvailable(self, UserRecord: User.User, IncomingFileSizeBytes: int) -> bool:
        ProjectedTotalBytes: int = UserRecord.StorageUsedBytes + IncomingFileSizeBytes
        return ProjectedTotalBytes <= Config.GLOBAL_SETTINGS.USER_STORAGE_QUOTA_BYTES

    async def UploadFile(self, UserRecord: User.User, FileName: str, ContentType: str, FileBytes: bytes) -> Typing.Optional[str]:
        FileSizeBytes: int = len(FileBytes)
        if not self.CheckQuotaAvailable(UserRecord, FileSizeBytes):
            return None

        UniqueObjectKey: str = f"users/{UserRecord.Identifier}/{UniversallyUniqueIdentifier.uuid4()}_{FileName}"
        try:
            self.Client.put_object(Bucket = self.BucketName, Key = UniqueObjectKey, Body = FileBytes, ContentType = ContentType)
            return UniqueObjectKey
        except BotoCoreExceptions.ClientError:
            return None

    async def RetrieveFileBytes(self, ObjectKey: str) -> Typing.Optional[bytes]:
        try:
            Response = self.Client.get_object(Bucket = self.BucketName, Key = ObjectKey)
            return Response["Body"].read()
        except BotoCoreExceptions.ClientError:
            return None

    async def DeleteFile(self, ObjectKey: str) -> bool:
        try:
            self.Client.delete_object(Bucket = self.BucketName, Key = ObjectKey)
            return True
        except BotoCoreExceptions.ClientError:
            return False

GLOBAL_STORAGE_SERVICE: OracleStorageService = OracleStorageService()
