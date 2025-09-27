import { useRuntimeConfig } from "nuxt/app"
import { UserManager, WebStorageStateStore } from "oidc-client-ts"

let _userManager: UserManager | null = null

function trimTrailingSlash(value?: string): string {
  return (value ?? "").replace(/\/+$/, "")
}

export function getUserManager(): UserManager {
  if (process.server) {
    throw new Error("UserManager must be created on the client")
  }
  if (_userManager) return _userManager

  const config = useRuntimeConfig()

  const fallbackOrigin = typeof window === "undefined" ? "" : window.location.origin
  const authBase = trimTrailingSlash((config.public.authUiUrl || fallbackOrigin).trim())

  const cognitoDomain = trimTrailingSlash((config.public.cognitoApiDomain || "").trim())

  const redirectUri = `${authBase}/callback`
  const postLogoutRedirectUri = `${authBase}/logout`

  _userManager = new UserManager({
    authority: `https://cognito-idp.${config.public.awsRegion}.amazonaws.com/${config.public.congitoUserPoolID}`,
    client_id: config.public.cognitoAppClientId,
    redirect_uri: redirectUri,
    post_logout_redirect_uri: postLogoutRedirectUri,
    response_type: "code",
    scope: "openid email profile",

    userStore: new WebStorageStateStore({ store: window.localStorage }),

    monitorSession: false,
    loadUserInfo: false,
  })

  // @ts-expect-error attach custom prop
  _userManager.__cognitoDomain = cognitoDomain || authBase

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
  // @ts-expect-error read custom prop
  const domain: string = um.__cognitoDomain

  const clientId = settings.client_id!
  const logoutUri = settings.post_logout_redirect_uri!

  const url = `${domain}/logout?client_id=${encodeURIComponent(clientId)}&logout_uri=${encodeURIComponent(logoutUri)}`
  window.location.href = url
}

export const userManager = undefined as unknown as UserManager