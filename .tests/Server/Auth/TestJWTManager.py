import datetime               as DateTime
import jwt                    as PyJWT
import typing                 as Typing
import Server.Auth.JWTManager as JWTManager
import Server.Config          as Config

class TestJWTManager:
    def TestCreateAccessTokenDefaultExpiration(self) -> None:
        GeneratedToken : str                                           = JWTManager.CreateAccessToken(PayloadData = {"sub": "user-uuid-1", "role": "NormalUser"})
        assert (isinstance(GeneratedToken, str) and (len(GeneratedToken) > 0))

        DecodedData    : Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(GeneratedToken)
        assert (DecodedData is not None)
        assert (DecodedData.get("sub") == "user-uuid-1")
        assert (DecodedData.get("role") == "NormalUser")
        assert ("exp" in DecodedData)

    def TestCreateAccessTokenCustomExpiration(self) -> None:
        CustomDelta    : DateTime.timedelta                            = DateTime.timedelta(minutes = 15)
        GeneratedToken : str                                           = JWTManager.CreateAccessToken(PayloadData = {"sub": "user-uuid-2", "role": "Administrator"}, ExpiresDelta = CustomDelta)
        DecodedData    : Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(GeneratedToken)
        assert (DecodedData is not None)
        assert (DecodedData.get("sub") == "user-uuid-2")
        assert (DecodedData.get("role") == "Administrator")

    def TestDecodeAccessTokenExpiredToken(self) -> None:
        NegativeDelta : DateTime.timedelta                            = DateTime.timedelta(seconds = -10)
        ExpiredToken  : str                                           = JWTManager.CreateAccessToken(PayloadData = {"sub": "user-uuid-3", "role": "NormalUser"}, ExpiresDelta = NegativeDelta)
        DecodedData   : Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(ExpiredToken)
        assert (DecodedData is None)

    def TestDecodeAccessTokenMalformedToken(self) -> None:
        MalformedToken : str                                           = "Invalid.Malformed.TokenString"
        DecodedData    : Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(MalformedToken)
        assert (DecodedData is None)

    def TestDecodeAccessTokenInvalidSignature(self) -> None:
        ForeignSecret : str                                           = "DifferentSecretKeyForSigningJWT123456789"
        ForgedToken   : str                                           = PyJWT.encode({"sub": "user-uuid-4", "role": "NormalUser"}, ForeignSecret, algorithm = Config.GLOBAL_SETTINGS.ALGORITHM)
        DecodedData   : Typing.Optional[Typing.Dict[str, Typing.Any]] = JWTManager.DecodeAccessToken(ForgedToken)
        assert (DecodedData is None)
