import { useRuntimeConfig } from "nuxt/app"
import { UserManager, WebStorageStateStore } from "oidc-client-ts"

let _userManager: UserManager | null = null

function trimTrailingSlash(value?: string): string {
  return (value ?? "").replace(/\/+$/, "")
}

function ensure(value: string, message: string): string {
  if (!value) throw new Error(message)
  return value
}

export function getUserManager(): UserManager {
  if (process.server) {
    throw new Error("UserManager must be created on the client")
  }
  if (_userManager) return _userManager

  const config = useRuntimeConfig()

  const fallbackOrigin = typeof window === "undefined" ? "" : window.location.origin
  const authBase = trimTrailingSlash((config.public.authUiUrl || fallbackOrigin).trim())

  const hostedUiDomain = trimTrailingSlash((config.public.cognitoHostedUiDomain || "").trim())
  const authority = trimTrailingSlash((config.public.cognitoOidcAuthority || "").trim())
  const clientId = (config.public.cognitoAppClientId || "").trim()
  const scope = (config.public.cognitoScope || "openid email profile").trim()

  const redirectUri = `${authBase}/callback`
  const postLogoutRedirectUri = `${authBase}/logout`

  const ensuredAuthority = ensure(authority, "Missing Cognito OIDC authority")
  const ensuredDomain = ensure(hostedUiDomain, "Missing Cognito hosted UI domain")
  const ensuredClientId = ensure(clientId, "Missing Cognito app client ID")
  const ensuredScope = scope || "openid email profile"

  _userManager = new UserManager({
    authority: ensuredAuthority,
    client_id: ensuredClientId,
    redirect_uri: redirectUri,
    post_logout_redirect_uri: postLogoutRedirectUri,
    response_type: "code",
    scope: ensuredScope,

    userStore: new WebStorageStateStore({ store: window.localStorage }),

    monitorSession: false,
    loadUserInfo: false,
  })

  ;(_userManager as unknown as { __cognitoDomain: string }).__cognitoDomain = ensuredDomain

  return _userManager
}

export async function signInRedirect(options?: { state?: unknown }) {
  const um = getUserManager()
  await um.clearStaleState().catch(() => undefined)
  await um.removeUser().catch(() => undefined)
  return um.signinRedirect(options)
}

export async function signOutRedirect() {
  const um = getUserManager()
  const settings = um.settings
  const domain: string = (um as unknown as { __cognitoDomain: string }).__cognitoDomain

  const clientId = settings.client_id!
  const logoutUri = settings.post_logout_redirect_uri!

  const url = `${domain}/logout?client_id=${encodeURIComponent(clientId)}&logout_uri=${encodeURIComponent(logoutUri)}`
  window.location.href = url
}

export const userManager = undefined as unknown as UserManager
