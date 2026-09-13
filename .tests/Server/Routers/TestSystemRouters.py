import httpx2 as HTTPClient

class TestSystemRouters:
    async def TestDesktopServeIndex(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/")
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))

    async def TestDesktopApplicationLauncherWindow(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Desktop/Windows/ApplicationLauncher")
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))

    async def TestDesktopAccountCentreWindow(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Desktop/Windows/AccountCentre")
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))

    async def TestDesktopDiceRollerWindow(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Desktop/Windows/DiceRoller")
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))

    async def TestToolsDiceRollPost(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.post("/API/Tools/Dice/Roll", data = {"GameSystem": "DND5E", "Expression": "1d20+4", "Format": "html"})
        assert (ResponseInstance.status_code == 200)

    async def TestToolsHarptosCalendarPartial(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Tools/Calendar/Harptos/Partial")
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))
