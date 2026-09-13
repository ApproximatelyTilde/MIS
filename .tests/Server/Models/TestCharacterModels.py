import sqlalchemy                         as SQLAlchemy
import sqlalchemy.ext.asyncio             as AsyncIO
import Server.Models.Character            as Character
import Server.Models.DND5ECharacterSchema as DND5ECharacterSchema
import Server.Models.User                 as User

class TestCharacterModels:
    def TestGameSystemTypeEnumValues(self) -> None:
        assert (Character.GameSystemType.DND5E.value == "DND5E")
        assert (Character.GameSystemType.MGT2E.value == "MGT2E")

    def TestEntityTypeEnumValues(self) -> None:
        assert (Character.EntityType.Character.value == "Character")
        assert (Character.EntityType.Companion.value == "Companion")
        assert (Character.EntityType.Vehicle.value == "Vehicle")
        assert (Character.EntityType.Other.value == "Other")

    async def TestCharacterCreationAndDefaults(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        NewCharacter: Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Valeros", GameSystem = Character.GameSystemType.DND5E, SummaryData = {"Class": "Fighter", "Level": 3}, DetailData = {"Strength": 16, "Dexterity": 14})
        DatabaseSession.add(NewCharacter)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(NewCharacter)

        assert (NewCharacter.ID is not None)
        assert (NewCharacter.Name == "Valeros")
        assert (NewCharacter.GameSystem == Character.GameSystemType.DND5E)
        assert (NewCharacter.EntityType == Character.EntityType.Character)
        assert (NewCharacter.ParentCharacterID is None)
        assert (NewCharacter.IsPublic is True)
        assert (NewCharacter.IsArchived is False)
        assert (NewCharacter.IsPinned is False)
        assert (NewCharacter.IsAccepted is False)
        assert (NewCharacter.IsProtected is False)
        assert (NewCharacter.IsOverridden is False)
        assert (NewCharacter.SummaryData.get("Class") == "Fighter")
        assert (NewCharacter.DetailData.get("Strength") == 16)

    async def TestCompanionAndVehicleParentLinking(self, DatabaseSession: AsyncIO.AsyncSession, RegularUserRecord: User.User) -> None:
        ParentCharacter: Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Captain Vance", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Character)
        DatabaseSession.add(ParentCharacter)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(ParentCharacter)

        LinkedVehicle: Character.Character = Character.Character(OwnerID = RegularUserRecord.ID, Name = "Scout Courier", GameSystem = Character.GameSystemType.MGT2E, EntityType = Character.EntityType.Vehicle, ParentCharacterID = ParentCharacter.ID)
        DatabaseSession.add(LinkedVehicle)
        await DatabaseSession.commit()
        await DatabaseSession.refresh(LinkedVehicle)

        assert (LinkedVehicle.EntityType == Character.EntityType.Vehicle)
        assert (LinkedVehicle.ParentCharacterID == ParentCharacter.ID)

    def TestDND5ECharacterSchemaValidation(self) -> None:
        CurrenciesInstance   : DND5ECharacterSchema.CurrenciesData      = DND5ECharacterSchema.CurrenciesData(GoldPieces = 25, SilverPieces = 10, CopperPieces = 50)
        assert (CurrenciesInstance.TotalGoldValue == 26.5)

        InventoryItemInstance: DND5ECharacterSchema.InventoryItemEntry  = DND5ECharacterSchema.InventoryItemEntry(ID = "item-uuid-1", Name = "Longsword", Quantity = 3, WeightPounds = 3.0)
        assert (InventoryItemInstance.TotalWeightPounds == 9.0)

        SheetInstance        : DND5ECharacterSchema.DND5ECharacterSheet = DND5ECharacterSchema.DND5ECharacterSheet(Name = "Valeros", Species = DND5ECharacterSchema.SpeciesData(RaceName = "Human", FullName = "Human"), Background = DND5ECharacterSchema.BackgroundData(Name = "Soldier"))
        assert (SheetInstance.Name == "Valeros")
        assert (SheetInstance.Species.RaceName == "Human")
        assert (SheetInstance.Background.Name == "Soldier")
