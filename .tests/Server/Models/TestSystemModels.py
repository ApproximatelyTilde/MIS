import sqlalchemy                     as SQLAlchemy
import sqlalchemy.ext.asyncio         as AsyncIO
import Server.Models.Aliasing         as Aliasing
import Server.Models.AutomationModels as AutomationModels
import Server.Models.CombatEncounter  as CombatEncounter
import Server.Models.Mail             as Mail
import Server.Models.ServerSettings   as ServerSettings
import Server.Models.StorageFile      as StorageFile
import Server.Models.User             as User
import Server.Models.Variable         as Variable

class TestSystemModels:
    def TestMailCategoryEnumValues(self) -> None:
        assert (Mail.MailCategory.SystemAlert.value == "SystemAlert")
        assert (Mail.MailCategory.CharacterReview.value == "CharacterReview")
        assert (Mail.MailCategory.StoryNotice.value == "StoryNotice")
        assert (Mail.MailCategory.Administrative.value == "Administrative")
        assert (Mail.MailCategory.GeneralMessage.value == "GeneralMessage")

    async def TestMailMessageCreation(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User, GameMasterUserRecord: User.User) -> None:
        MessageRecord: Mail.MailMessage = Mail.MailMessage(SenderUserID = GameMasterUserRecord.ID, RecipientUserID = RegularUserRecord.ID, Subject = "Story Invitation", Body = "You have been invited to join the adventure.", Category = Mail.MailCategory.StoryNotice)
        DatabaseSession.add(MessageRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(MessageRecord)

        assert (MessageRecord.ID is not None)
        assert (MessageRecord.Subject == "Story Invitation")
        assert (MessageRecord.IsRead is False)
        assert (MessageRecord.IsAutomated is False)

    async def TestStorageFileCreation(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        FileRecord: StorageFile.StorageFile = StorageFile.StorageFile(OwnerID = RegularUserRecord.ID, FileName = "Avatar.png", ContentType = "image/png", FileSizeBytes = 2048, ObjectKey = "users/111/Avatar.png", IsPublic = True)
        DatabaseSession.add(FileRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(FileRecord)

        assert (FileRecord.ID is not None)
        assert (FileRecord.FileName == "Avatar.png")
        assert (FileRecord.FileSizeBytes == 2048)
        assert (FileRecord.IsPublic is True)

    async def TestAliasingModels(self, DatabaseSession: AsyncIO.AsyncSession) -> None:
        AliasRecord: Aliasing.Alias = Aliasing.Alias(Name = "fireball", Content = "8d6 fire damage in 20ft sphere", Scope = "User", OwnerID = "1234567890")
        DatabaseSession.add(AliasRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(AliasRecord)

        assert (AliasRecord.ID is not None)
        assert (AliasRecord.Name == "fireball")
        assert (AliasRecord.Scope == "User")

    async def TestVariableModels(self, DatabaseSession: AsyncIO.AsyncSession) -> None:
        UserVariableRecord: Variable.UserVariable = Variable.UserVariable(UserID = "1234567890", Variables = {"HeroLevel": 5, "Inspiration": True})
        DatabaseSession.add(UserVariableRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(UserVariableRecord)

        assert (UserVariableRecord.UserID == "1234567890")
        assert (UserVariableRecord.Variables.get("HeroLevel") == 5)

    async def TestCombatEncounterModel(self, DatabaseSession: AsyncIO.AsyncSession) -> None:
        EncounterRecord: CombatEncounter.CombatEncounter = CombatEncounter.CombatEncounter(ChannelID = "combat-channel-12345", GameSystem = "MGT2E", InitiativeMode = "Popcorn", RoundNumber = 1, Combatants = [{"Name": "Goblin", "Initiative": 15}], RemainingInRound = ["combatant-1"])
        DatabaseSession.add(EncounterRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(EncounterRecord)

        assert (EncounterRecord.ID is not None)
        assert (EncounterRecord.ChannelID == "combat-channel-12345")
        assert (EncounterRecord.GameSystem == "MGT2E")
        assert (EncounterRecord.InitiativeMode == "Popcorn")
        assert (EncounterRecord.RemainingInRound == ["combatant-1"])
        assert (EncounterRecord.RoundNumber == 1)
        assert (EncounterRecord.IsActive is True)

    async def TestServerSettingsModel(self, DatabaseSession: AsyncIO.AsyncSession) -> None:
        SettingsRecord: ServerSettings.ServerSettings = ServerSettings.ServerSettings(GuildID = "guild-123456789", CommandPrefixDND5E = "!", CommandPrefixMGT2E = ".")
        DatabaseSession.add(SettingsRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(SettingsRecord)

        assert (SettingsRecord.ID is not None)
        assert (SettingsRecord.GuildID == "guild-123456789")
        assert (SettingsRecord.CommandPrefixDND5E == "!")
        assert (SettingsRecord.CommandPrefixMGT2E == ".")

    def TestAutomationEffectTypes(self) -> None:
        assert (AutomationModels.CustomActionActivationType.Action.value == "Action")
        assert (AutomationModels.CustomActionActivationType.BonusAction.value == "BonusAction")
        assert (AutomationModels.AutomationEffectType.Attack.value == "Attack")
        assert (AutomationModels.AutomationEffectType.Damage.value == "Damage")
        assert (AutomationModels.AutomationEffectType.Heal.value == "Heal")
