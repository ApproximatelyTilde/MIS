import sqlalchemy              as SQLAlchemy
import sqlalchemy.ext.asyncio  as AsyncIO
import Server.Models.Character as Character
import Server.Models.Economy   as Economy
import Server.Models.Story     as Story
import Server.Models.User      as User

class TestStoryAndEconomyModels:
    def TestStoryMembershipStatusEnumValues(self) -> None:
        assert (Story.StoryMembershipStatus.Requested.value == "Requested")
        assert (Story.StoryMembershipStatus.Invited.value == "Invited")
        assert (Story.StoryMembershipStatus.Active.value == "Active")
        assert (Story.StoryMembershipStatus.Rejected.value == "Rejected")

    async def TestStoryCreationAndRelationships(self, DatabaseSession: AsyncIO.AsyncSession, GameMasterUserRecord: User.User, RegularUserRecord: User.User) -> None:
        StoryInstance: Story.Story = Story.Story(GameMasterID = GameMasterUserRecord.ID, Title = "Chronicles of Eldoria", Description = "A realm in conflict", GameSystem = Character.GameSystemType.DND5E, IsPublic = True)
        DatabaseSession.add(StoryInstance)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(StoryInstance)

        assert (StoryInstance.ID is not None)
        assert (StoryInstance.Title == "Chronicles of Eldoria")
        assert (StoryInstance.GameSystem == Character.GameSystemType.DND5E)
        assert (StoryInstance.IsArchived is False)

        MembershipInstance: Story.StoryMember = Story.StoryMember(StoryID = StoryInstance.ID, UserID = RegularUserRecord.ID, MembershipStatus = Story.StoryMembershipStatus.Active)
        DatabaseSession.add(MembershipInstance)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(MembershipInstance)

        assert (MembershipInstance.ID is not None)
        assert (MembershipInstance.MembershipStatus == Story.StoryMembershipStatus.Active)

    async def TestEconomyTransactionCreation(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        CharacterRecord  : Character.Character        = Character.Character(OwnerID = RegularUserRecord.ID, Name = "MerchantHero", GameSystem = Character.GameSystemType.DND5E)
        DatabaseSession.add(CharacterRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(CharacterRecord)

        TransactionRecord: Economy.EconomyTransaction = Economy.EconomyTransaction(CharacterID = CharacterRecord.ID, InitiatorID = RegularUserRecord.ID, GameSystem = Character.GameSystemType.DND5E, AmountChange = 125.5, CurrencyType = "Gold", ItemName = "Healing Potion", QuantityChange = 2, TransactionReason = "Purchase from Alchemist")
        DatabaseSession.add(TransactionRecord)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(TransactionRecord)

        assert (TransactionRecord.ID is not None)
        assert (TransactionRecord.AmountChange == 125.5)
        assert (TransactionRecord.CurrencyType == "Gold")
        assert (TransactionRecord.ItemName == "Healing Potion")
        assert (TransactionRecord.QuantityChange == 2)
