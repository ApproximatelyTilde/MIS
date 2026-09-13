import typing                       as Typing
import httpx2                       as HTTPClient
import Server.Auth.JWTManager       as JWTManager
import Server.Models.CombatEncounter as CombatEncounter
import Server.Routers.CombatRouter  as CombatRouter

class TestCombatRouter:
    async def TestCombatEncounterRoundTripWithMGT2EAndPopcorn(self, AsyncTestClient: HTTPClient.AsyncClient) -> None:
        TallyToken: str = JWTManager.CreateAccessToken(PayloadData = {"sub": "Tally", "role": "Administrator", "in_guild": True})
        Headers   : Typing.Dict[str, str] = {"Authorization": f"Bearer {TallyToken}"}

        SavePayload: Typing.Dict[str, Typing.Any] = {
            "GuildID"             : "guild-999",
            "GameSystem"          : "MGT2E",
            "InitiativeMode"      : "Popcorn",
            "RoundNumber"         : 2,
            "ActiveCombatantIndex": 1,
            "RemainingInRound"    : ["c-2"],
            "Combatants"          : [
                {
                    "ID"                : "c-1",
                    "Name"              : "Traveller One",
                    "Initiative"        : 9,
                    "CurrentHitPoints"  : 8,
                    "MaxHitPoints"      : 10,
                    "ArmorProtection"   : 5,
                    "EntityType"        : "Character",
                    "Characteristics"   : {"Endurance": 8, "Strength": 7, "Dexterity": 8},
                    "MaxCharacteristics": {"Endurance": 10, "Strength": 7, "Dexterity": 8}
                },
                {
                    "ID"              : "c-2",
                    "Name"            : "Type-S Scout",
                    "Initiative"      : 11,
                    "CurrentHitPoints": 35,
                    "MaxHitPoints"    : 40,
                    "ArmorProtection" : 4,
                    "EntityType"      : "Vehicle",
                    "VehicleStats"    : {"HullPoints": 35, "MaxHullPoints": 40}
                }
            ],
            "ActiveEffects"       : []
        }

        PutResponse: HTTPClient.Response = await AsyncTestClient.put("/API/Combat/Encounters/channel-mgt2e-1", json = SavePayload, headers = Headers)
        assert (PutResponse.status_code == 200)
        PutBody: Typing.Dict[str, Typing.Any] = PutResponse.json()
        assert (PutBody["GameSystem"] == "MGT2E")
        assert (PutBody["InitiativeMode"] == "Popcorn")
        assert (PutBody["RemainingInRound"] == ["c-2"])

        GetResponse: HTTPClient.Response = await AsyncTestClient.get("/API/Combat/Encounters/channel-mgt2e-1", headers = Headers)
        assert (GetResponse.status_code == 200)
        GetBody: Typing.Dict[str, Typing.Any] = GetResponse.json()
        assert (GetBody["GameSystem"] == "MGT2E")
        assert (GetBody["InitiativeMode"] == "Popcorn")
        assert (GetBody["RemainingInRound"] == ["c-2"])

        DeleteResponse: HTTPClient.Response = await AsyncTestClient.delete("/API/Combat/Encounters/channel-mgt2e-1", headers = Headers)
        assert (DeleteResponse.status_code == 200)
        assert (DeleteResponse.json()["IsSuccess"] is True)

    def TestBuildCombatEncounterLogMGT2EAndDND5E(self) -> None:
        TravellerEncounter: CombatEncounter.CombatEncounter = CombatEncounter.CombatEncounter(
            ChannelID            = "ch-1",
            GuildID              = "g-1",
            GameSystem           = "MGT2E",
            InitiativeMode       = "Popcorn",
            RoundNumber          = 3,
            ActiveCombatantIndex = 0,
            Combatants           = [
                {
                    "Name"              : "Kael",
                    "Initiative"        : 8,
                    "EntityType"        : "Character",
                    "ArmorProtection"   : 5,
                    "Characteristics"   : {"Endurance": 6},
                    "MaxCharacteristics": {"Endurance": 9}
                },
                {
                    "Name"            : "Free Trader",
                    "Initiative"      : 10,
                    "EntityType"      : "Vehicle",
                    "ArmorProtection" : 4,
                    "VehicleStats"    : {"HullPoints": 32, "MaxHullPoints": 40}
                }
            ]
        )
        TravellerLog: str = CombatRouter.BuildCombatEncounterLog(TravellerEncounter)
        assert ("- **Initiative Mode**: Popcorn" in TravellerLog)
        assert ("END 6/9 | Armor 5" in TravellerLog)
        assert ("Hull 32/40 | Armor 4" in TravellerLog)

        DND5EEncounter: CombatEncounter.CombatEncounter = CombatEncounter.CombatEncounter(
            ChannelID            = "ch-2",
            GuildID              = "g-1",
            GameSystem           = "DND5E",
            InitiativeMode       = "Standard",
            RoundNumber          = 2,
            ActiveCombatantIndex = 0,
            Combatants           = [
                {
                    "Name"            : "Valeros",
                    "Initiative"      : 16,
                    "EntityType"      : "Character",
                    "CurrentHitPoints": 22,
                    "MaxHitPoints"    : 28,
                    "ArmorClass"      : 17
                }
            ]
        )
        DND5ELog: str = CombatRouter.BuildCombatEncounterLog(DND5EEncounter)
        assert ("- **Initiative Mode**: Standard" in DND5ELog)
        assert ("22/28 HP | AC 17" in DND5ELog)
