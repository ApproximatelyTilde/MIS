import os                              as OperatingSystem
import typing                          as Typing
import fastapi.responses               as Responses
import jinja2                          as Jinja2
import Server.Services.DebugService     as DebugService

PARTIALS_DIRECTORY_PATH: str = OperatingSystem.path.join(OperatingSystem.path.dirname(OperatingSystem.path.dirname(OperatingSystem.path.dirname(OperatingSystem.path.abspath(__file__)))), "Client", "Partials")

JINJA_ENVIRONMENT: Jinja2.Environment = Jinja2.Environment(loader = Jinja2.FileSystemLoader(PARTIALS_DIRECTORY_PATH), autoescape = Jinja2.select_autoescape(["html", "xml"]), trim_blocks = True, lstrip_blocks = True)

def RenderPartial(PartialName: str, Context: Typing.Optional[Typing.Dict[str, Typing.Any]] = None) -> str:
    TemplateContext: Typing.Dict[str, Typing.Any] = Context if (Context is not None) else {
    }
    PartialTemplate: Jinja2.Template = JINJA_ENVIRONMENT.get_template(PartialName)
    RenderedContent: str = PartialTemplate.render(TemplateContext)
    DebugService.LogDebugMessage(f"Rendered Partial: '{PartialName}' ({len(RenderedContent)} Chars, Keys={list(TemplateContext.keys())})")
    return RenderedContent

def RenderPartialResponse(PartialName: str, Context: Typing.Optional[Typing.Dict[str, Typing.Any]] = None, StatusCode: int = 200, Headers: Typing.Optional[Typing.Dict[str, str]] = None) -> Responses.HTMLResponse:
    RenderedContent: str = RenderPartial(PartialName, Context)
    DebugService.LogDebugMessage(f"Served Partial Response: '{PartialName}' (Status={StatusCode})")
    return Responses.HTMLResponse(content = RenderedContent, status_code = StatusCode, headers = Headers)
