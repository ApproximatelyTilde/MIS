import datetime                     as DateTime
import jwt                          as PyJWT
import typing                       as Typing
import Server.Config                as Config
import Server.Services.DebugService as DebugService

def CreateAccessToken(PayloadData: Typing.Dict[str, Typing.Any], ExpiresDelta: Typing.Optional[DateTime.timedelta] = None) -> str:
    ToEncode: Typing.Dict[str, Typing.Any] = PayloadData.copy()
    if ExpiresDelta:
        ExpireTimestamp = DateTime.datetime.now(DateTime.timezone.utc) + ExpiresDelta

    else:
        ExpireTimestamp = DateTime.datetime.now(DateTime.timezone.utc) + DateTime.timedelta(minutes = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES)

    ToEncode.update({"exp": ExpireTimestamp})
    EncodedJWT: str = PyJWT.encode(ToEncode, Config.GLOBAL_SETTINGS.SECRET_KEY, algorithm = Config.GLOBAL_SETTINGS.ALGORITHM)
    DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Access Token Created for Subject=\"{PayloadData.get("sub")}\", Role=\"{PayloadData.get("role")}\"")
    return EncodedJWT

def DecodeAccessToken(Token: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    try:
        DecodedPayload: Typing.Dict[str, Typing.Any] = PyJWT.decode(Token, Config.GLOBAL_SETTINGS.SECRET_KEY, algorithms = [Config.GLOBAL_SETTINGS.ALGORITHM])
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Access Token Decoded for Subject=\"{DecodedPayload.get("sub")}\", Role=\"{DecodedPayload.get("role")}\"")
        return DecodedPayload

    except PyJWT.PyJWTError as TokenException:
        DebugService.LogMessage(Level = DebugService.LogLevel.Warning, Message = f"Access Token Decode Failed: {type(TokenException).__name__}")
        return None
