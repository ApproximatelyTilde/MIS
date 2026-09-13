import typing as Typing
import httpx2 as HTTPClient

class TestAuthRouter:
    async def TestDiscordLoginRedirect(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Auth/Discord/Login", follow_redirects = False)
        assert ((ResponseInstance.status_code == 307) or (ResponseInstance.status_code == 302))
        assert ("discord.com/oauth2/authorize" in ResponseInstance.headers.get("location", ""))

    async def TestSessionStatusAnonymous(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response          = await AsyncTestClient.get("/API/Auth/Session/Status")
        assert (ResponseInstance.status_code == 200)

        JSONContent     : Typing.Dict[str, Typing.Any] = ResponseInstance.json()
        assert (JSONContent.get("IsAuthenticated") is False)

    async def TestSessionStatusAuthenticated(self, AsyncTestClient: HTTPClient.AsyncClient, RegularUserToken: str) -> None:
        ResponseInstance: HTTPClient.Response          = await AsyncTestClient.get("/API/Auth/Session/Status", headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ResponseInstance.status_code == 200)

        JSONContent     : Typing.Dict[str, Typing.Any] = ResponseInstance.json()
        assert (JSONContent.get("IsAuthenticated") is True)
        assert (JSONContent.get("Role") == "NormalUser")

    async def TestLogoutClearsSessionCookie(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.post("/API/Auth/Logout")
        assert (ResponseInstance.status_code == 200)

    async def TestGuestLogin(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response          = await AsyncTestClient.post("/API/Auth/GuestLogin")
        assert (ResponseInstance.status_code == 200)

        JSONContent     : Typing.Dict[str, Typing.Any] = ResponseInstance.json()
        assert (JSONContent.get("Role") == "Visitor")
