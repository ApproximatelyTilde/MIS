import Server.Auth.DiscordOAuth           as DiscordOAuth
import Server.Auth.JWTManager             as JWTManager
import Server.Auth.RoleBasedAccessControl as RoleBasedAccessControl

CreateAccessToken = JWTManager.CreateAccessToken
DecodeAccessToken = JWTManager.DecodeAccessToken
GetCurrentUser           = RoleBasedAccessControl.GetCurrentUser
RequireAuthenticatedUser = RoleBasedAccessControl.RequireAuthenticatedUser
