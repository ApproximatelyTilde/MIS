import json                     as JSONParser
import typing                   as Typing
import unittest.mock            as MockLibrary
import urllib.parse             as URLParse
import httpx2                   as HTTPClient
import Server.Auth.DiscordOAuth as DiscordOAuth
import Server.Config            as Config

class TestDiscordOAuth:
    def TestGenerateDiscordAuthorizeURL(self) -> None:
        StateToken           : str                                    = "random-state-token-value"
        AuthorizeURL         : str                                    = DiscordOAuth.GenerateDiscordAuthorizeURL(StateToken = StateToken)
        ParsedURL            : URLParse.ParseResult                   = URLParse.urlparse(AuthorizeURL)
        ParsedQueryParameters: Typing.Dict[str, Typing.List[str]]     = URLParse.parse_qs(ParsedURL.query)

        assert (ParsedURL.scheme == "https")
        assert (ParsedURL.netloc == "discord.com")
        assert (ParsedURL.path == "/oauth2/authorize")
        assert (ParsedQueryParameters["client_id"][0] == Config.GLOBAL_SETTINGS.DISCORD_CLIENT_ID)
        assert (ParsedQueryParameters["redirect_uri"][0] == Config.GLOBAL_SETTINGS.DISCORD_REDIRECT_URI)
        assert (ParsedQueryParameters["response_type"][0] == "code")
        assert (ParsedQueryParameters["state"][0] == StateToken)
        assert (ParsedQueryParameters["scope"][0] == DiscordOAuth.DISCORD_OAUTH_SCOPES)

    async def TestExchangeDiscordCodeSuccess(self) -> None:
        MockResponsePayload: Typing.Dict[str, Typing.Any] = {
            "access_token" : "mock-access-token-12345",
            "token_type"   : "Bearer",
            "expires_in"   : 604800,
            "refresh_token": "mock-refresh-token-67890",
            "scope"        : "identify guilds guilds.members.read"
        }
        MockHTTPResponse   : HTTPClient.Response          = HTTPClient.Response(status_code = 200, content = JSONParser.dumps(MockResponsePayload).encode("utf-8"))

        with MockLibrary.patch("httpx2.AsyncClient.post", return_value = MockHTTPResponse):
            ExchangeResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.ExchangeDiscordCode(Code = "valid-authorization-code")
            assert (ExchangeResult is not None)
            assert (ExchangeResult.get("access_token") == "mock-access-token-12345")

    async def TestExchangeDiscordCodeFailureStatus(self) -> None:
        MockHTTPResponse: HTTPClient.Response = HTTPClient.Response(status_code = 400, content = b"{}")

        with MockLibrary.patch("httpx2.AsyncClient.post", return_value = MockHTTPResponse):
            ExchangeResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.ExchangeDiscordCode(Code = "invalid-code")
            assert (ExchangeResult is None)

    async def TestExchangeDiscordCodeTransportException(self) -> None:
        with MockLibrary.patch("httpx2.AsyncClient.post", side_effect = HTTPClient.RequestError("Connection failed")):
            ExchangeResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.ExchangeDiscordCode(Code = "code-with-transport-error")
            assert (ExchangeResult is None)

    async def TestFetchDiscordUserProfileSuccess(self) -> None:
        MockProfilePayload: Typing.Dict[str, Typing.Any] = {
            "id"           : "123456789012345678",
            "username"     : "DiscordTestUser",
            "discriminator": "0",
            "avatar"       : "abcdef123456"
        }
        MockHTTPResponse  : HTTPClient.Response          = HTTPClient.Response(status_code = 200, content = JSONParser.dumps(MockProfilePayload).encode("utf-8"))

        with MockLibrary.patch("httpx2.AsyncClient.get", return_value = MockHTTPResponse):
            ProfileResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.FetchDiscordUserProfile(AccessToken = "valid-token")
            assert (ProfileResult is not None)
            assert (ProfileResult.get("username") == "DiscordTestUser")
            assert (ProfileResult.get("id") == "123456789012345678")

    async def TestFetchDiscordUserProfileFailure(self) -> None:
        MockHTTPResponse: HTTPClient.Response = HTTPClient.Response(status_code = 401, content = b"{}")

        with MockLibrary.patch("httpx2.AsyncClient.get", return_value = MockHTTPResponse):
            ProfileResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.FetchDiscordUserProfile(AccessToken = "unauthorized-token")
            assert (ProfileResult is None)

    async def TestFetchDiscordGuildMemberProfileSuccess(self) -> None:
        MockMemberPayload: Typing.Dict[str, Typing.Any] = {
            "roles": ["1549159643396178052", "1549126097331949618"],
            "nick" : "GuildNickname"
        }
        MockHTTPResponse : HTTPClient.Response          = HTTPClient.Response(status_code = 200, content = JSONParser.dumps(MockMemberPayload).encode("utf-8"))

        with MockLibrary.patch("httpx2.AsyncClient.get", return_value = MockHTTPResponse):
            MemberResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.FetchDiscordGuildMemberProfile(AccessToken = "valid-token", DiscordUserID = "123456789012345678")
            assert (MemberResult is not None)
            assert ("roles" in MemberResult)
            assert (len(MemberResult["roles"]) == 2)

    async def TestFetchDiscordGuildMemberProfileUnconfiguredGuild(self) -> None:
        OriginalGuildID: str = Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID
        try:
            Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID = ""

            MemberResult: Typing.Optional[Typing.Dict[str, Typing.Any]] = await DiscordOAuth.FetchDiscordGuildMemberProfile(AccessToken = "valid-token", DiscordUserID = "123456789012345678")
            assert (MemberResult is None)

        finally:
            Config.GLOBAL_SETTINGS.DISCORD_GUILD_ID = OriginalGuildID
