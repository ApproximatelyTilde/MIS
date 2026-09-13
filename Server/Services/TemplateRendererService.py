import os                              as OperatingSystem
import typing                          as Typing
import fastapi.responses               as Responses
import jinja2                          as Jinja2
import Server.Services.DebugService     as DebugService

PARTIALS_DIRECTORY_PATH: str = OperatingSystem.path.join(OperatingSystem.path.dirname(OperatingSystem.path.dirname(OperatingSystem.path.dirname(OperatingSystem.path.abspath(__file__)))), "Client", "Partials")

JINJA_ENVIRONMENT: Jinja2.Environment = Jinja2.Environment(
    loader = Jinja2.FileSystemLoader(PARTIALS_DIRECTORY_PATH),
    autoescape = Jinja2.select_autoescape(["html", "xml"]),
    trim_blocks = True,
    lstrip_blocks = True
)

def RenderPartial(PartialName: str, Context: Typing.Optional[Typing.Dict[str, Typing.Any]] = None) -> str:
    TemplateContext: Typing.Dict[str, Typing.Any] = Context if (Context is not None) else {}
    DebugService.LogDebugMessage(f"Rendering Partial Template: {PartialName} With Context Keys: {list(TemplateContext.keys())}")
    PartialTemplate: Jinja2.Template = JINJA_ENVIRONMENT.get_template(PartialName)
    RenderedContent: str = PartialTemplate.render(TemplateContext)
    DebugService.LogDebugMessage(f"Successfully Rendered Partial Template: {PartialName}")
    return RenderedContent

def RenderPartialResponse(PartialName: str, Context: Typing.Optional[Typing.Dict[str, Typing.Any]] = None, StatusCode: int = 200) -> Responses.HTMLResponse:
    DebugService.LogDebugMessage(f"Rendering Partial Response For Template: {PartialName} With Status Code: {StatusCode}")
    RenderedContent: str = RenderPartial(PartialName, Context)
    return Responses.HTMLResponse(content = RenderedContent, status_code = StatusCode)
