import fastapi                           as FastAPI
import Server.Models.AutomationModels    as AutomationModels
import Server.Services.AutomationService as Automation

Router = FastAPI.APIRouter(prefix = "/API/Automations", tags = ["Automations"])

@Router.post("/Validate", response_model = AutomationModels.AutomationValidationResponse)
async def ValidateAutomationDocument(RequestPayload: AutomationModels.AutomationValidationRequest) -> AutomationModels.AutomationValidationResponse:
    ValidationOutcome: AutomationModels.AutomationValidationResponse = Automation.GLOBAL_AUTOMATION_SERVICE.ValidateAutomation(RequestPayload.Automation)
    return ValidationOutcome

