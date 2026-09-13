import fastapi                            as FastAPI
import pytest                             as Pytest
import Server.Auth.RoleBasedAccessControl as RoleBasedAccessControl
import Server.Models.Character            as Character
import Server.Models.Story                as Story
import Server.Models.User                 as User

class TestRoleBasedAccessControl:
    def TestIsGameMasterEvaluation(self, GameMasterUserRecord: User.User, AdministratorUserRecord: User.User, RegularUserRecord: User.User) -> None:
        assert (RoleBasedAccessControl.IsGameMaster(None) is False)
        assert (RoleBasedAccessControl.IsGameMaster(RegularUserRecord) is False)
        assert (RoleBasedAccessControl.IsGameMaster(GameMasterUserRecord) is True)
        assert (RoleBasedAccessControl.IsGameMaster(AdministratorUserRecord) is True)

    def TestHasUserRole(self, AdministratorUserRecord: User.User, RegularUserRecord: User.User) -> None:
        assert (RoleBasedAccessControl.HasUserRole(None, "Administrator") is False)
        assert (RoleBasedAccessControl.HasUserRole(AdministratorUserRecord, "Administrator") is True)
        assert (RoleBasedAccessControl.HasUserRole(RegularUserRecord, "Administrator") is False)

    def TestCanViewCharacterOwnerAndPublic(self, RegularUserRecord: User.User, AdministratorUserRecord: User.User) -> None:
        OwnedCharacter : Character.Character = Character.Character(ID = "owned-character-uuid-1", OwnerID = RegularUserRecord.ID, Name = "OwnedHero", GameSystem = Character.GameSystemType.DND5E, IsPublic = False, IsArchived = False)
        assert (RoleBasedAccessControl.CanViewCharacter(RegularUserRecord, OwnedCharacter) is True)
        assert (RoleBasedAccessControl.CanViewCharacter(AdministratorUserRecord, OwnedCharacter) is True)
        assert (RoleBasedAccessControl.CanViewCharacter(None, OwnedCharacter) is False)

        PublicCharacter: Character.Character = Character.Character(ID = "public-character-uuid-2", OwnerID = "foreign-user-id", Name = "PublicHero", GameSystem = Character.GameSystemType.DND5E, IsPublic = True, IsArchived = False)
        assert (RoleBasedAccessControl.CanViewCharacter(None, PublicCharacter) is True)
        assert (RoleBasedAccessControl.CanViewCharacter(RegularUserRecord, PublicCharacter) is True)

    def TestCanModifyCharacterPermissions(self, RegularUserRecord: User.User, AdministratorUserRecord: User.User) -> None:
        OwnedCharacter: Character.Character = Character.Character(ID = "owned-character-uuid-3", OwnerID = RegularUserRecord.ID, Name = "OwnedHero", GameSystem = Character.GameSystemType.DND5E)
        assert (RoleBasedAccessControl.CanModifyCharacter(RegularUserRecord, OwnedCharacter) is True)
        assert (RoleBasedAccessControl.CanModifyCharacter(AdministratorUserRecord, OwnedCharacter) is True)

        ForeignUser   : User.User           = User.User(ID = "foreign-user-uuid-4", DiscordID = "999999999999999999", Username = "ForeignUser", DisplayName = "Foreign", Role = User.UserRole.NormalUser, Roles = [])
        assert (RoleBasedAccessControl.CanModifyCharacter(ForeignUser, OwnedCharacter) is False)

    def TestCanOverrideCharacterAdministratorOnly(self, AdministratorUserRecord: User.User, RegularUserRecord: User.User) -> None:
        assert (RoleBasedAccessControl.CanOverrideCharacter(AdministratorUserRecord) is True)
        assert (RoleBasedAccessControl.CanOverrideCharacter(RegularUserRecord) is False)
        assert (RoleBasedAccessControl.CanOverrideCharacter(None) is False)

    async def TestRequireAuthenticatedUserPresent(self, RegularUserRecord: User.User) -> None:
        ResolvedUser: User.User = await RoleBasedAccessControl.RequireAuthenticatedUser(CurrentUser = RegularUserRecord)
        assert (ResolvedUser.ID == RegularUserRecord.ID)

    async def TestRequireAuthenticatedUserMissingRaisesUnauthorized(self) -> None:
        with Pytest.raises(FastAPI.HTTPException) as ExceptionInfo:
            await RoleBasedAccessControl.RequireAuthenticatedUser(CurrentUser = None)

        assert (ExceptionInfo.value.status_code == FastAPI.status.HTTP_401_UNAUTHORIZED)

    def TestIsUserInGuildEvaluation(self, RegularUserRecord: User.User, AdministratorUserRecord: User.User) -> None:
        assert (RoleBasedAccessControl.IsUserInGuild(None) is False)

        VisitorRecord: User.User = User.User(DiscordID = "444444444444444444", Username = "VisitorUser", DisplayName = "Visitor", Role = User.UserRole.Visitor, Roles = [])
        assert (RoleBasedAccessControl.IsUserInGuild(VisitorRecord) is False)
        assert (RoleBasedAccessControl.IsUserInGuild(AdministratorUserRecord) is True)
