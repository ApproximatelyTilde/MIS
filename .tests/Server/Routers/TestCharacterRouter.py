import typing                   as Typing
import httpx2                   as HTTPClient
import sqlalchemy.ext.asyncio   as AsyncIO
import Server.Auth.JWTManager   as JWTManager
import Server.Models.Character  as Character
import Server.Models.User       as User

class TestCharacterRouter:
    async def TestGetClassRules(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance : HTTPClient.Response          = await AsyncTestClient.get("/API/Characters/Rules/Classes")
        assert (ResponseInstance.status_code == 200)

        ClassesDictionary: Typing.Dict[str, Typing.Any] = ResponseInstance.json()
        assert (isinstance(ClassesDictionary, dict))
        assert ("Classes" in ClassesDictionary)

    async def TestGetCantrips(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        ResponseInstance: HTTPClient.Response     = await AsyncTestClient.get("/API/Characters/Rules/Cantrips")
        assert (ResponseInstance.status_code == 200)

        CantripsList    : Typing.List[Typing.Any] = ResponseInstance.json()
        assert (isinstance(CantripsList, list))

    async def TestGetCharactersListEmpty(self, AsyncTestClient: HTTPClient.AsyncClient, RegularUserToken: str) -> None:
        ResponseInstance: HTTPClient.Response     = await AsyncTestClient.get("/API/Characters", headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ResponseInstance.status_code == 200)

        CharactersList  : Typing.List[Typing.Any] = ResponseInstance.json()
        assert (isinstance(CharactersList, list))

    async def TestGetCharacterPartial(self, AsyncTestClient: HTTPClient.AsyncClient, RegularUserToken: str) -> None:
        ResponseInstance: HTTPClient.Response = await AsyncTestClient.get("/API/Characters/Partial", headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ResponseInstance.status_code == 200)
        assert ("text/html" in ResponseInstance.headers.get("content-type", ""))

    async def TestListCharactersGuestVsTallyServiceVisibilityAndFilters(self, AsyncTestClient: HTTPClient.AsyncClient, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        PublicHero      : Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Public Hero", GameSystem = Character.GameSystemType.DND5E, EntityType = Character.EntityType.Character, IsPublic = True, IsArchived = False)
        PrivateOther    : Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Private Pirate", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Other, IsPublic = False, IsArchived = False)
        ArchivedEntity  : Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Archived Ghost", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Other, IsPublic = True, IsArchived = True)
        DatabaseSession.add_all([PublicHero, PrivateOther, ArchivedEntity])
        await DatabaseSession.commit()

        GuestResponse: HTTPClient.Response = await AsyncTestClient.get("/API/Characters?ShowArchived=true")
        assert (GuestResponse.status_code == 200)
        GuestList: Typing.List[Typing.Dict[str, Typing.Any]] = GuestResponse.json()
        assert (len(GuestList) == 1)
        assert (GuestList[0]["Name"] == "Public Hero")
        assert (GuestList[0]["EntityType"] == "Character")
        assert ("DiscordID" not in (GuestList[0].get("Owner") or {}))

        TallyToken   : str                 = JWTManager.CreateAccessToken(PayloadData = {"sub": "Tally", "role": "Administrator", "in_guild": True})
        ServiceResp  : HTTPClient.Response = await AsyncTestClient.get("/API/Characters?EntityType=Other&GameSystem=MGT2E", headers = {"Authorization": f"Bearer {TallyToken}"})
        assert (ServiceResp.status_code == 200)
        ServiceList  : Typing.List[Typing.Dict[str, Typing.Any]] = ServiceResp.json()
        assert (len(ServiceList) == 1)
        assert (ServiceList[0]["Name"] == "Private Pirate")
        assert (ServiceList[0]["EntityType"] == "Other")
        assert (ServiceList[0]["Owner"]["DiscordID"] == RegularUserRecord.DiscordID)

    async def TestCompanionsEndpointsAndTransferAndStatePatch(self, AsyncTestClient: HTTPClient.AsyncClient, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User, GameMasterUserRecord: User.User, RegularUserToken: str, GameMasterToken: str) -> None:
        ParentHero: Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Vance", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Character, DetailData = {"Characteristics": {"Strength": 7, "Endurance": 9}, "Currency": {"Credits": 1200}})
        DatabaseSession.add(ParentHero)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(ParentHero)

        TallyToken: str = JWTManager.CreateAccessToken(PayloadData = {"sub": "Tally", "role": "Administrator", "in_guild": True})
        EmptyResp : HTTPClient.Response = await AsyncTestClient.get(f"/API/Characters/{ParentHero.ID}/Companions", headers = {"Authorization": f"Bearer {TallyToken}"})
        assert (EmptyResp.status_code == 200)
        assert (EmptyResp.json() == [])

        CreateCompResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{ParentHero.ID}/Companions", json = {"Name": "Scout Drone", "EntityType": "Companion", "DetailData": {"Characteristics": {"Endurance": 4}}}, headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (CreateCompResp.status_code == 201)
        CreatedComp: Typing.Dict[str, Typing.Any] = CreateCompResp.json()
        assert (CreatedComp["ParentCharacterID"] == ParentHero.ID)
        assert (CreatedComp["EntityType"] == "Companion")

        ListCompResp: HTTPClient.Response = await AsyncTestClient.get(f"/API/Characters/{ParentHero.ID}/Companions", headers = {"Authorization": f"Bearer {TallyToken}"})
        assert (ListCompResp.status_code == 200)
        assert (len(ListCompResp.json()) == 1)
        assert (ListCompResp.json()[0]["Name"] == "Scout Drone")

        PatchStateResp: HTTPClient.Response = await AsyncTestClient.patch(f"/API/Characters/{ParentHero.ID}/State", json = {"DetailData": {"Currency": {"Credits": 900}}}, headers = {"Authorization": f"Bearer {TallyToken}"})
        assert (PatchStateResp.status_code == 200)
        PatchedBody: Typing.Dict[str, Typing.Any] = PatchStateResp.json()
        assert (PatchedBody["DetailData"]["Currency"]["Credits"] == 900)
        assert (PatchedBody["DetailData"]["Characteristics"]["Endurance"] == 9)

        UnlinkResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{CreatedComp["ID"]}/Transfer", json = {"ParentCharacterID": None}, headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (UnlinkResp.status_code == 200)
        assert (UnlinkResp.json()["ParentCharacterID"] is None)

        ForbiddenOwnerResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{ParentHero.ID}/Transfer", json = {"OwnerID": GameMasterUserRecord.ID}, headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ForbiddenOwnerResp.status_code == 403)

        GMTransferResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{ParentHero.ID}/Transfer", json = {"OwnerID": GameMasterUserRecord.ID}, headers = {"Authorization": f"Bearer {GameMasterToken}"})
        assert (GMTransferResp.status_code == 200)
        assert (GMTransferResp.json()["OwnerID"] == GameMasterUserRecord.ID)

    async def TestManualCreationMGT2EAndVehicleAndPersonaGeneratorRoute(self, AsyncTestClient: HTTPClient.AsyncClient, RegularUserToken: str, GameMasterToken: str) -> None:
        ManualMGT2EResp: HTTPClient.Response = await AsyncTestClient.post("/API/Characters/Manual/Partial", data = {"GameSystem": "MGT2E", "EntityType": "Character", "Name": "Sera Vance", "Career": "Scout", "Terms": "3", "Homeworld": "Terra", "MGT2EStrength": "8", "MGT2EDexterity": "9", "MGT2EEndurance": "10", "MGT2EIntelligence": "8", "MGT2EEducation": "9", "MGT2ESocialStanding": "6", "MGT2EArmorName": "Cloth Armor", "MGT2EArmorProtection": "5", "MGT2ECredits": "12500", "MGT2ESkills": "pilot: 2\nastrogation: 1", "MGT2EInventory": "Gauss Rifle\nMedkit"}, headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ManualMGT2EResp.status_code == 200)
        assert ("Sera Vance" in ManualMGT2EResp.text)

        VehicleMGT2EResp: HTTPClient.Response = await AsyncTestClient.post("/API/Characters/Manual/Partial", data = {"GameSystem": "MGT2E", "EntityType": "Vehicle", "Name": "Free Trader", "VehicleType": "Type-A Free Trader", "HullPoints": "80", "MaxHullPoints": "80", "VehicleArmor": "2", "Thrust": "1", "JumpRating": "1", "PowerPoints": "40", "Fuel": "30", "MaxFuel": "30", "CrewCapacity": "4", "VehicleWeapons": "Pulse Laser | 2D"}, headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (VehicleMGT2EResp.status_code == 200)
        assert ("Free Trader" in VehicleMGT2EResp.text)

        TallyToken: str                 = JWTManager.CreateAccessToken(PayloadData = {"sub": "Tally", "role": "Administrator", "in_guild": True})
        ListResp  : HTTPClient.Response = await AsyncTestClient.get("/API/Characters?GameSystem=MGT2E", headers = {"Authorization": f"Bearer {TallyToken}"})
        assert (ListResp.status_code == 200)
        Records   : Typing.List[Typing.Dict[str, Typing.Any]] = ListResp.json()
        ByName    : Typing.Dict[str, Typing.Dict[str, Typing.Any]] = {R["Name"]: R for R in Records}
        assert (ByName["Sera Vance"]["DetailData"]["Characteristics"]["Endurance"] == 10)
        assert (ByName["Sera Vance"]["DetailData"]["Skills"]["pilot"] == 2)
        assert (ByName["Sera Vance"]["DetailData"]["Currency"]["Credits"] == 12500)
        assert (ByName["Free Trader"]["EntityType"] == "Vehicle")
        assert (ByName["Free Trader"]["DetailData"]["HullPoints"] == 80)
        assert (ByName["Free Trader"]["DetailData"]["Weapons"][0]["Damage"] == "2D")

        ForbiddenPersonaResp: HTTPClient.Response = await AsyncTestClient.get("/API/Desktop/Windows/PersonaGenerator", headers = {"Authorization": f"Bearer {RegularUserToken}"})
        assert (ForbiddenPersonaResp.status_code == 403)

        GMPersonaResp: HTTPClient.Response = await AsyncTestClient.get("/API/Desktop/Windows/PersonaGenerator", headers = {"Authorization": f"Bearer {GameMasterToken}"})
        assert (GMPersonaResp.status_code == 200)

    async def TestWebUIPartialsCompanionsTabsSearchAndSheetContext(self, AsyncTestClient: HTTPClient.AsyncClient, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User, RegularUserToken: str) -> None:
        ParentHero: Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Captain Kael", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Character, IsPublic = True, SummaryData = {"Career": "Navy", "Terms": 2, "Homeworld": "Core"}, DetailData = {"Characteristics": {"Strength": 7, "Dexterity": 8, "Endurance": 9, "Intelligence": 8, "Education": 9, "SocialStanding": 7}, "Skills": {"pilot": 2}, "Currency": {"Credits": 5000}})
        UnlinkedVeh: Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Type-S Scout", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Vehicle, IsPublic = True, DetailData = {"VehicleType": "Scout/Courier", "HullPoints": 40, "MaxHullPoints": 40, "Armor": 4})
        DatabaseSession.add_all([ParentHero, UnlinkedVeh])
        await DatabaseSession.commit()
        await DatabaseSession.refresh(ParentHero)
        await DatabaseSession.refresh(UnlinkedVeh)

        Headers: Typing.Dict[str, str] = {"Authorization": f"Bearer {RegularUserToken}"}

        SheetResp: HTTPClient.Response = await AsyncTestClient.get(f"/API/Desktop/Windows/CharacterSheet?CharacterID={ParentHero.ID}", headers = Headers)
        assert (SheetResp.status_code == 200)
        assert ("CharacterSheetCompanionsTab" in SheetResp.text)
        assert ("CharacterSheetMGT2ESection" in SheetResp.text)
        assert ("MGT2ECredits" in SheetResp.text)

        SearchVehResp: HTTPClient.Response = await AsyncTestClient.get("/API/Characters/Search/Partial?GameSystem=MGT2E&EntityType=Vehicle", headers = Headers)
        assert (SearchVehResp.status_code == 200)
        assert ("Type-S Scout" in SearchVehResp.text)
        assert ("Captain Kael" not in SearchVehResp.text)
        assert ("Hull: 40/40" in SearchVehResp.text)

        ListVehResp: HTTPClient.Response = await AsyncTestClient.get("/API/Characters/Partial?EntityType=Vehicle", headers = Headers)
        assert (ListVehResp.status_code == 200)
        assert ("Type-S Scout" in ListVehResp.text)
        assert ("BadgeEntityVehicle" in ListVehResp.text)

        LinkResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{ParentHero.ID}/Companions/Link/Partial", data = {"CompanionID": UnlinkedVeh.ID}, headers = Headers)
        assert (LinkResp.status_code == 200)
        assert ("Type-S Scout" in LinkResp.text)

        ProtectTabResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{ParentHero.ID}/Protect/Partial", data = {"ActiveTab": "CharacterSheetCompanionsTab"}, headers = Headers)
        assert (ProtectTabResp.status_code == 200)
        assert ("value=\"CharacterSheetCompanionsTab\"" in ProtectTabResp.text)

        UnlinkResp: HTTPClient.Response = await AsyncTestClient.post(f"/API/Characters/{ParentHero.ID}/Companions/{UnlinkedVeh.ID}/Unlink/Partial", headers = Headers)
        assert (UnlinkResp.status_code == 200)
        assert ("No companions or vehicles are currently linked" in UnlinkResp.text)
