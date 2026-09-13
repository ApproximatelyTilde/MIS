import json   as JSONParser
import os     as OperatingSystem
import typing as Typing

class TestData:
    def TestGuildRolesCacheFileExists(self) -> None:
        CacheFilePath: str = OperatingSystem.path.join("Server", "Data", "GuildRolesCache.json")
        assert (OperatingSystem.path.exists(CacheFilePath) is True)

    def TestGuildRolesCacheStructureAndTypes(self) -> None:
        CacheFilePath: str = OperatingSystem.path.join("Server", "Data", "GuildRolesCache.json")
        with open(CacheFilePath, "r", encoding = "utf-8") as FileHandle:
            ParsedData: Typing.Dict[str, Typing.Any] = JSONParser.load(FileHandle)

        assert ("LastCheckedTimestamp" in ParsedData)
        assert ("LastUpdatedTimestamp" in ParsedData)
        assert ("RolesHash" in ParsedData)
        assert ("RoleMapping" in ParsedData)

        RoleMapping: Typing.Dict[str, Typing.Any] = ParsedData["RoleMapping"]
        assert (isinstance(RoleMapping, dict))
        assert (len(RoleMapping) > 0)

        for RoleID, RoleNames in RoleMapping.items():
            assert (isinstance(RoleID, str))
            assert (len(RoleID) > 0)
            assert (isinstance(RoleNames, list))
            assert (len(RoleNames) > 0)
            for RoleName in RoleNames:
                assert (isinstance(RoleName, str))
                assert (len(RoleName) > 0)
