import Server.Routers.AuthRouter          as AuthRouter
import Server.Routers.CharacterRouter     as CharacterRouter
import Server.Routers.StoryRouter         as StoryRouter
import Server.Routers.EconomyRouter       as EconomyRouter
import Server.Routers.StorageRouter       as StorageRouter
import Server.Routers.ToolsRouter         as ToolsRouter
import Server.Routers.DesktopWindowRouter as DesktopWindowRouter

AuthAPIRouter          = AuthRouter.Router
CharacterAPIRouter     = CharacterRouter.Router
StoryAPIRouter         = StoryRouter.Router
EconomyAPIRouter       = EconomyRouter.Router
StorageAPIRouter       = StorageRouter.Router
ToolsAPIRouter         = ToolsRouter.Router
DesktopWindowAPIRouter          = DesktopWindowRouter.Router
AuthenticationCallbackAPIRouter = AuthRouter.AuthenticationCallbackRouter
PublicObjectAPIRouter           = StorageRouter.PublicObjectRouter
