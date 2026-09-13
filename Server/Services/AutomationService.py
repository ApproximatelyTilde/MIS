import re                             as RegularExpressions
import typing                         as Typing
import Server.Models.AutomationModels as AutomationModels
import Server.Services.DebugService   as DebugService

MAX_RECURSION_DEPTH: int = 10

VALID_ABILITY_NAMES: Typing.Set[str] = {
    "Strength",
    "Dexterity",
    "Constitution",
    "Intelligence",
    "Wisdom",
    "Charisma"
}

DICE_EXPRESSION_PATTERN: RegularExpressions.Pattern = RegularExpressions.compile(r"^[\d\s\+\-\*\/\(\)dD\.\{\}\w]+$")

class AutomationService:
    def __init__(self) -> None:
        self.AllowedTypes: Typing.Set[str] = {EffectType.value for EffectType in AutomationModels.AutomationEffectType}

    def ValidateDiceExpression(self, ExpressionText: str) -> bool:
        StrippedExpression: str = ExpressionText.strip()
        if (len(StrippedExpression) == 0):
            return False

        if not DICE_EXPRESSION_PATTERN.match(StrippedExpression):
            return False

        OpenParenCount  : int = StrippedExpression.count("(")
        CloseParenCount : int = StrippedExpression.count(")")
        if (OpenParenCount != CloseParenCount):
            return False

        OpenBraceCount  : int = StrippedExpression.count("{")
        CloseBraceCount : int = StrippedExpression.count("}")
        if (OpenBraceCount != CloseBraceCount):
            return False

        return True

    def ValidateNode(self, NodeData: Typing.Dict[str, Typing.Any] | AutomationModels.EffectNode, CurrentDepth: int, PathPrefix: str, ErrorsList: Typing.List[str], WarningsList: Typing.List[str]) -> None:
        if (CurrentDepth > MAX_RECURSION_DEPTH):
            ErrorsList.append(f"{PathPrefix}: Maximum automation recursion depth of {MAX_RECURSION_DEPTH} exceeded.")
            return

        NodeDictionary: Typing.Dict[str, Typing.Any] = NodeData.model_dump(mode = "json") if isinstance(NodeData, AutomationModels.EffectNode) else NodeData
        RawType = NodeDictionary.get("Type")
        if (RawType is None):
            ErrorsList.append(f"{PathPrefix}: Node missing mandatory 'Type' attribute.")
            return

        TypeString: str = RawType.value if hasattr(RawType, "value") else str(RawType)
        if (TypeString not in self.AllowedTypes):
            ErrorsList.append(f"{PathPrefix}: Unrecognized effect type '{TypeString}'.")
            return

        if (TypeString == "Target"):
            TargetValue = NodeDictionary.get("Target")
            if (TargetValue is None) or (str(TargetValue).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Target node requires a non-empty 'Target' field.")

            ChildEffects = NodeDictionary.get("Effects")
            if (ChildEffects is not None):
                if not isinstance(ChildEffects, list):
                    ErrorsList.append(f"{PathPrefix}: 'Effects' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(ChildEffects):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.Effects[{ChildIndex}]", ErrorsList, WarningsList)

        elif (TypeString == "Attack"):
            HitBranch = NodeDictionary.get("Hit")
            if (HitBranch is not None):
                if not isinstance(HitBranch, list):
                    ErrorsList.append(f"{PathPrefix}: 'Hit' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(HitBranch):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.Hit[{ChildIndex}]", ErrorsList, WarningsList)

            MissBranch = NodeDictionary.get("Miss")
            if (MissBranch is not None):
                if not isinstance(MissBranch, list):
                    ErrorsList.append(f"{PathPrefix}: 'Miss' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(MissBranch):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.Miss[{ChildIndex}]", ErrorsList, WarningsList)

        elif (TypeString == "Damage"):
            DamageExpression = NodeDictionary.get("Damage")
            if (DamageExpression is None) or (str(DamageExpression).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Damage node requires a non-empty 'Damage' expression.")

            elif not self.ValidateDiceExpression(str(DamageExpression)):
                ErrorsList.append(f"{PathPrefix}: Invalid damage dice expression '{DamageExpression}'.")

        elif (TypeString == "TempHP"):
            AmountValue = NodeDictionary.get("Amount")
            if (AmountValue is None) or (str(AmountValue).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: TempHP node requires a non-empty 'Amount' value.")

            elif isinstance(AmountValue, str) and (not self.ValidateDiceExpression(AmountValue)):
                ErrorsList.append(f"{PathPrefix}: Invalid TempHP expression '{AmountValue}'.")

        elif (TypeString == "Heal"):
            AmountValue = NodeDictionary.get("Amount")
            if (AmountValue is None) or (str(AmountValue).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Heal node requires a non-empty 'Amount' value.")

            elif isinstance(AmountValue, str) and (not self.ValidateDiceExpression(AmountValue)):
                ErrorsList.append(f"{PathPrefix}: Invalid Heal expression '{AmountValue}'.")

        elif (TypeString == "Save"):
            StatValue = NodeDictionary.get("Stat")
            if (StatValue is None) or (str(StatValue).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Save node requires a non-empty 'Stat' attribute.")

            elif (str(StatValue) not in VALID_ABILITY_NAMES):
                WarningsList.append(f"{PathPrefix}: Non-standard ability stat '{StatValue}'.")

            FailBranch = NodeDictionary.get("Fail")
            if (FailBranch is not None):
                if not isinstance(FailBranch, list):
                    ErrorsList.append(f"{PathPrefix}: 'Fail' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(FailBranch):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.Fail[{ChildIndex}]", ErrorsList, WarningsList)

            SuccessBranch = NodeDictionary.get("Success")
            if (SuccessBranch is not None):
                if not isinstance(SuccessBranch, list):
                    ErrorsList.append(f"{PathPrefix}: 'Success' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(SuccessBranch):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.Success[{ChildIndex}]", ErrorsList, WarningsList)

        elif (TypeString == "Check"):
            AbilityValue = NodeDictionary.get("Ability")
            if (AbilityValue is None) or (str(AbilityValue).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Check node requires a non-empty 'Ability' attribute.")

        elif (TypeString == "Text"):
            TextContent = NodeDictionary.get("Text")
            if (TextContent is None) or (str(TextContent).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Text node requires a non-empty 'Text' string.")

        elif (TypeString == "InitiativeEffect"):
            EffectName = NodeDictionary.get("Name")
            if (EffectName is None) or (str(EffectName).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: InitiativeEffect node requires a non-empty 'Name' attribute.")

        elif (TypeString == "Condition"):
            ConditionExpression = NodeDictionary.get("Condition")
            if (ConditionExpression is None) or (str(ConditionExpression).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Condition node requires a non-empty 'Condition' expression.")

            TrueBranch = NodeDictionary.get("TrueEffects")
            if (TrueBranch is not None):
                if not isinstance(TrueBranch, list):
                    ErrorsList.append(f"{PathPrefix}: 'TrueEffects' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(TrueBranch):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.TrueEffects[{ChildIndex}]", ErrorsList, WarningsList)

            FalseBranch = NodeDictionary.get("FalseEffects")
            if (FalseBranch is not None):
                if not isinstance(FalseBranch, list):
                    ErrorsList.append(f"{PathPrefix}: 'FalseEffects' must be a list of effect nodes.")

                else:
                    for ChildIndex, ChildItem in enumerate(FalseBranch):
                        self.ValidateNode(ChildItem, CurrentDepth + 1, f"{PathPrefix}.FalseEffects[{ChildIndex}]", ErrorsList, WarningsList)

        elif (TypeString == "Variable"):
            VariableName = NodeDictionary.get("Name")
            if (VariableName is None) or (str(VariableName).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Variable node requires a non-empty 'Name' attribute.")

            if ("Value" not in NodeDictionary):
                ErrorsList.append(f"{PathPrefix}: Variable node requires a 'Value' attribute.")

        elif (TypeString == "Counter"):
            CounterName = NodeDictionary.get("Counter")
            if (CounterName is None) or (str(CounterName).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Counter node requires a non-empty 'Counter' attribute.")

            AmountValue = NodeDictionary.get("Amount")
            if (AmountValue is None) or (str(AmountValue).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Counter node requires a non-empty 'Amount' attribute.")

        elif (TypeString == "Cast"):
            SpellName = NodeDictionary.get("Spell")
            if (SpellName is None) or (str(SpellName).strip() == ""):
                ErrorsList.append(f"{PathPrefix}: Cast node requires a non-empty 'Spell' attribute.")

    def ValidateAutomation(self, AutomationNodes: Typing.List[Typing.Dict[str, Typing.Any] | AutomationModels.EffectNode]) -> AutomationModels.AutomationValidationResponse:
        ErrorsList   : Typing.List[str] = []
        WarningsList : Typing.List[str] = []
        if not isinstance(AutomationNodes, list):
            ErrorsList.append("Automation document root must be a list of effect nodes.")
            return AutomationModels.AutomationValidationResponse(IsValid = False, Errors = ErrorsList, Warnings = WarningsList)

        for NodeIndex, NodeItem in enumerate(AutomationNodes):
            self.ValidateNode(NodeItem, CurrentDepth = 1, PathPrefix = f"Root[{NodeIndex}]", ErrorsList = ErrorsList, WarningsList = WarningsList)

        IsValidResult: bool = (len(ErrorsList) == 0)
        DebugService.LogMessage(Level = DebugService.LogLevel.Debug, Message = f"Validated Automation Document: Valid={IsValidResult}, Errors={len(ErrorsList)}, Warnings={len(WarningsList)}")
        return AutomationModels.AutomationValidationResponse(IsValid = IsValidResult, Errors = ErrorsList, Warnings = WarningsList)

GLOBAL_AUTOMATION_SERVICE: AutomationService = AutomationService()
