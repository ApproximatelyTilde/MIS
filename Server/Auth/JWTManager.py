import datetime      as DateTime
import jwt           as PyJWT
import typing        as Typing
import Server.Config as Config

def CreateAccessToken(PayloadData: Typing.Dict[str, Typing.Any], ExpiresDelta: Typing.Optional[DateTime.timedelta] = None) -> str:
    ToEncode: Typing.Dict[str, Typing.Any] = PayloadData.copy()
    if ExpiresDelta:
        ExpireTimestamp = DateTime.datetime.utcnow() + ExpiresDelta

    else:
        ExpireTimestamp = DateTime.datetime.utcnow() + DateTime.timedelta(minutes = Config.GLOBAL_SETTINGS.ACCESS_TOKEN_EXPIRE_MINUTES)

    ToEncode.update({"exp": ExpireTimestamp})
    EncodedJWT: str = PyJWT.encode(ToEncode, Config.GLOBAL_SETTINGS.SECRET_KEY, algorithm = Config.GLOBAL_SETTINGS.ALGORITHM)
    return EncodedJWT

def DecodeAccessToken(Token: str) -> Typing.Optional[Typing.Dict[str, Typing.Any]]:
    try:
        DecodedPayload: Typing.Dict[str, Typing.Any] = PyJWT.decode(Token, Config.GLOBAL_SETTINGS.SECRET_KEY, algorithms = [Config.GLOBAL_SETTINGS.ALGORITHM])
        return DecodedPayload

    except PyJWT.PyJWTError:
        return None
