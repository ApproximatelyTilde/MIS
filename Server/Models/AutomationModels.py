import enum     as Enumeration
import pydantic as Pydantic
import typing   as Typing
import uuid     as UUID

class CustomActionActivationType(str, Enumeration.Enum):
    Action      = "Action"
    BonusAction = "BonusAction"
    Reaction    = "Reaction"
    NoAction    = "NoAction"
    Attack      = "Attack"
    Minute      = "Minute"
    Hour        = "Hour"
    Special     = "Special"

class AutomationEffectType(str, Enumeration.Enum):
    Target           = "Target"
    Attack           = "Attack"
    Damage           = "Damage"
    TempHP           = "TempHP"
    Heal             = "Heal"
    Save             = "Save"
    Check            = "Check"
    Text             = "Text"
    InitiativeEffect = "InitiativeEffect"
    Condition        = "Condition"
    Variable         = "Variable"
    Counter          = "Counter"
    Cast             = "Cast"

class CounterResetScheduleType(str, Enumeration.Enum):
    ShortRest = "ShortRest"
    LongRest  = "LongRest"
    Dawn      = "Dawn"
    Manual    = "Manual"
    Other     = "Other"

class CounterData(Pydantic.BaseModel):
    Value        : int                                       = 0
    MaxValue     : Typing.Optional[int]                      = None
    MinValue     : Typing.Optional[int]                      = 0
    ResetSchedule: Typing.Optional[CounterResetScheduleType] = CounterResetScheduleType.LongRest
    Description  : Typing.Optional[str]                      = None

class EffectNode(Pydantic.BaseModel):
    model_config = Pydantic.ConfigDict(extra = "allow")
    Type         : AutomationEffectType
    Target       : Typing.Optional[Typing.Union[str, int]]              = None
    Effects      : Typing.Optional[Typing.List["EffectNode"]]           = None
    Hit          : Typing.Optional[Typing.List["EffectNode"]]           = None
    Miss         : Typing.Optional[Typing.List["EffectNode"]]           = None
    Damage       : Typing.Optional[str]                                 = None
    DamageType   : Typing.Optional[str]                                 = None
    Higher       : Typing.Optional[Typing.Dict[str, str]]               = None
    Amount       : Typing.Optional[Typing.Union[str, int]]              = None
    Stat         : Typing.Optional[str]                                 = None
    DC           : Typing.Optional[Typing.Union[str, int]]              = None
    Fail         : Typing.Optional[Typing.List["EffectNode"]]           = None
    Success      : Typing.Optional[Typing.List["EffectNode"]]           = None
    Ability      : Typing.Optional[str]                                 = None
    Contest      : Typing.Optional[bool]                                = None
    Text         : Typing.Optional[str]                                 = None
    Name         : Typing.Optional[str]                                 = None
    Duration     : Typing.Optional[int]                                 = None
    TickOn       : Typing.Optional[str]                                 = None
    End          : Typing.Optional[bool]                                = None
    Condition    : Typing.Optional[str]                                 = None
    TrueEffects  : Typing.Optional[Typing.List["EffectNode"]]           = None
    FalseEffects : Typing.Optional[Typing.List["EffectNode"]]           = None
    Value        : Typing.Optional[Typing.Union[str, int, float, bool]] = None
    Counter      : Typing.Optional[str]                                 = None
    Operation    : Typing.Optional[str]                                 = None
    Spell        : Typing.Optional[str]                                 = None
    Level        : Typing.Optional[int]                                 = None

EffectNode.model_rebuild()

class CustomAttackEntry(Pydantic.BaseModel):
    ID            : str                                = Pydantic.Field(default_factory = lambda: str(UUID.uuid4()))
    Name          : str
    ActivationType: CustomActionActivationType
    Phrase        : Typing.Optional[str]               = None
    ThumbnailURL  : Typing.Optional[str]               = None
    Automation    : Typing.List[EffectNode]            = Pydantic.Field(default_factory = list)
    IsDirty       : bool                               = False

class UnifiedActionEntry(Pydantic.BaseModel):
    ID              : str
    Name            : str
    SourceType      : str
    ActivationType  : str
    AttackBonus     : Typing.Optional[int]               = None
    DamageExpression: Typing.Optional[str]               = None
    DamageType      : Typing.Optional[str]               = None
    RangeDescription: Typing.Optional[str]               = None
    Phrase          : Typing.Optional[str]               = None
    ThumbnailURL    : Typing.Optional[str]               = None
    Automation      : Typing.List[EffectNode]            = Pydantic.Field(default_factory = list)

class CustomAttackCreateRequest(Pydantic.BaseModel):
    ID            : Typing.Optional[str]               = None
    Name          : str
    ActivationType: CustomActionActivationType
    Phrase        : Typing.Optional[str]               = None
    ThumbnailURL  : Typing.Optional[str]               = None
    Automation    : Typing.List[EffectNode]            = Pydantic.Field(default_factory = list)

class CustomAttackUpdateRequest(Pydantic.BaseModel):
    Name          : Typing.Optional[str]                        = None
    ActivationType: Typing.Optional[CustomActionActivationType] = None
    Phrase        : Typing.Optional[str]                        = None
    ThumbnailURL  : Typing.Optional[str]                        = None
    Automation    : Typing.Optional[Typing.List[EffectNode]]    = None

class CounterCreateOrUpdateRequest(Pydantic.BaseModel):
    Name         : str
    Value        : int                                       = 0
    MaxValue     : Typing.Optional[int]                      = None
    MinValue     : Typing.Optional[int]                      = 0
    ResetSchedule: Typing.Optional[CounterResetScheduleType] = CounterResetScheduleType.LongRest
    Description  : Typing.Optional[str]                      = None

class CounterMutationRequest(Pydantic.BaseModel):
    Delta    : Typing.Optional[int] = None
    Value    : Typing.Optional[int] = None
    Operation: Typing.Optional[str] = None

class VariableSetRequest(Pydantic.BaseModel):
    Name     : Typing.Optional[str]                                                    = None
    Value    : Typing.Optional[Typing.Union[str, int, float, bool]]                    = None
    Variables: Typing.Optional[Typing.Dict[str, Typing.Union[str, int, float, bool]]] = None

class AutomationValidationRequest(Pydantic.BaseModel):
    Automation: Typing.List[Typing.Dict[str, Typing.Any]]

class AutomationValidationResponse(Pydantic.BaseModel):
    IsValid : bool             = True
    Errors  : Typing.List[str] = Pydantic.Field(default_factory = list)
    Warnings: Typing.List[str] = Pydantic.Field(default_factory = list)

