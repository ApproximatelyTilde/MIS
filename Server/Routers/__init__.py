import Server.Routers.AliasingRouter       as AliasingRouter
import Server.Routers.AuthRouter           as AuthRouter
import Server.Routers.AutomationRouter     as AutomationRouter
import Server.Routers.CharacterRouter      as CharacterRouter
import Server.Routers.CombatRouter         as CombatRouter
import Server.Routers.DesktopWindowRouter  as DesktopWindowRouter
import Server.Routers.EconomyRouter        as EconomyRouter
import Server.Routers.MailRouter           as MailRouter
import Server.Routers.ServerSettingsRouter as ServerSettingsRouter
import Server.Routers.StorageRouter        as StorageRouter
import Server.Routers.StoryRouter          as StoryRouter
import Server.Routers.ToolsRouter          as ToolsRouter
import Server.Routers.VariableRouter       as VariableRouter

AliasingAPIRouter               = AliasingRouter.Router
AuthAPIRouter                   = AuthRouter.Router
AuthenticationCallbackAPIRouter = AuthRouter.AuthenticationCallbackRouter
AutomationAPIRouter             = AutomationRouter.Router
CharacterAPIRouter              = CharacterRouter.Router
CombatAPIRouter                 = CombatRouter.Router
DesktopWindowAPIRouter          = DesktopWindowRouter.Router
EconomyAPIRouter                = EconomyRouter.Router
MailAPIRouter                   = MailRouter.Router
PublicObjectAPIRouter           = StorageRouter.PublicObjectRouter
ServerSettingsAPIRouter         = ServerSettingsRouter.Router
StorageAPIRouter                = StorageRouter.Router
StoryAPIRouter                  = StoryRouter.Router
ToolsAPIRouter                  = ToolsRouter.Router
VariableAPIRouter               = VariableRouter.Router
