import typing as Typing
import httpx2 as HTTPClient

class TestMailRouter:
    async def TestMailStatusAnonymousReturnsZero(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response          = await AsyncTestClient.get("/API/Mail/Status")
        assert (ResponseInstance.status_code == 200)

        JSONContent     : Typing.Dict[str, Typing.Any] = ResponseInstance.json()
        assert (JSONContent.get("HasUnread") is False)
        assert (JSONContent.get("UnreadCount") == 0)

    async def TestMailStatusAuthenticated(self, AsyncTestClient: HTTPClient.AsyncClient, RegularUserToken: str) -> None:
        ResponseInstance: HTTPClient.Response          = await AsyncTestClient.get("/API/Mail/Status", headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ResponseInstance.status_code == 200)

        JSONContent     : Typing.Dict[str, Typing.Any] = ResponseInstance.json()
        assert ("HasUnread" in JSONContent)
        assert ("UnreadCount" in JSONContent)

    async def TestMailPlaceholderPartial(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Mail/Placeholder/Partial")
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))
