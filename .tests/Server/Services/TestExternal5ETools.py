import typing                          as Typing
import Server.Services.External5ETools as External5ETools

class TestExternal5ETools:
    def TestCompendiumDataInitialization(self) -> None:
        ToolsInstance: External5ETools.External5ETools = External5ETools.External5ETools()
        assert (ToolsInstance.DataDirectoryPath.exists() is True)

    def TestFindCanonicalClassName(self) -> None:
        ToolsInstance: External5ETools.External5ETools = External5ETools.External5ETools()
        assert (ToolsInstance.FindCanonicalClassName("wizard") == "Wizard")
        assert (ToolsInstance.FindCanonicalClassName("FIGHTER") == "Fighter")
        assert (ToolsInstance.FindCanonicalClassName("rogue") == "Rogue")

    def TestGetClassHitDie(self) -> None:
        ToolsInstance: External5ETools.External5ETools = External5ETools.External5ETools()
        assert (ToolsInstance.GetClassHitDie("Wizard") == 6)
        assert (ToolsInstance.GetClassHitDie("Fighter") == 10)
        assert (ToolsInstance.GetClassHitDie("Barbarian") == 12)

    def TestFindCanonicalWeaponName(self) -> None:
        ToolsInstance: External5ETools.External5ETools = External5ETools.External5ETools()
        CanonicalName: Typing.Optional[str]            = ToolsInstance.FindCanonicalWeaponName("dagger")
        assert (CanonicalName == "Dagger")

    def TestFindCanonicalSpellName(self) -> None:
        ToolsInstance : External5ETools.External5ETools = External5ETools.External5ETools()
        CanonicalSpell: Typing.Optional[str]            = ToolsInstance.FindCanonicalSpellName("fireball")
        assert (CanonicalSpell == "Fireball")
