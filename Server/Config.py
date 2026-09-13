import pydantic as Pydantic
import pydantic_settings as PydanticSettings
import typing as Typing

class Settings(PydanticSettings.BaseSettings):
    ENVIRONMENT: str = Pydantic.Field(..., min_length = 1)
    HOST: str = Pydantic.Field(..., min_length = 1)
    PORT: int = Pydantic.Field(...)
    SECRET_KEY: str = Pydantic.Field(..., min_length = 32)
    ALGORITHM: str = Pydantic.Field(..., min_length = 1)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Pydantic.Field(...)
    DATABASE_URL: str = Pydantic.Field(..., min_length = 1)
    DISCORD_CLIENT_ID: str = Pydantic.Field(..., min_length = 1)
    DISCORD_CLIENT_SECRET: str = Pydantic.Field(..., min_length = 1)
    DISCORD_BOT_TOKEN: Typing.Optional[str] = Pydantic.Field(default = None)
    DISCORD_REDIRECT_URI: str = Pydantic.Field(..., min_length = 1)
    DISCORD_GUILD_ID: str = Pydantic.Field(..., min_length = 1)
    DISCORD_INVITE_URL: Typing.Optional[str] = Pydantic.Field(default = None)
    OCI_S3_ENDPOINT_URL: str = Pydantic.Field(..., validation_alias = Pydantic.AliasChoices("OCI_S3_ENDPOINT_URL", "S3_ENDPOINT_URL"), min_length = 1)
    OCI_S3_ACCESS_KEY_ID: str = Pydantic.Field(..., validation_alias = Pydantic.AliasChoices("OCI_S3_ACCESS_KEY_ID", "S3_ACCESS_KEY_ID"), min_length = 1)
    OCI_S3_SECRET_ACCESS_KEY: str = Pydantic.Field(..., validation_alias = Pydantic.AliasChoices("OCI_S3_SECRET_ACCESS_KEY", "S3_SECRET_ACCESS_KEY"), min_length = 1)
    OCI_S3_BUCKET_NAME: str = Pydantic.Field(..., validation_alias = Pydantic.AliasChoices("OCI_S3_BUCKET_NAME", "S3_BUCKET_NAME"), min_length = 1)
    OCI_S3_REGION: str = Pydantic.Field(..., validation_alias = Pydantic.AliasChoices("OCI_S3_REGION", "S3_REGION"), min_length = 1)
    USER_STORAGE_QUOTA_BYTES: int = Pydantic.Field(..., validation_alias = Pydantic.AliasChoices("USER_STORAGE_QUOTA_BYTES", "STORAGE_QUOTA_BYTES"))
    model_config = PydanticSettings.SettingsConfigDict(env_file = ".env", env_file_encoding = "utf-8", extra = "ignore")

GLOBAL_SETTINGS: Settings = Settings()
