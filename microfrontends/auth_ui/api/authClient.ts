import { useRuntimeConfig } from "nuxt/app"
import { UserManager } from "oidc-client-ts"

const config = useRuntimeConfig()

function trimTrailingSlash(value?: string): string {
  return (value ?? '').replace(/\/+$/, '')
}

const fallbackOrigin = typeof window === 'undefined' ? '' : window.location.origin
const authBase = trimTrailingSlash(config.public.authUiUrl || fallbackOrigin)
const cognitoDomain = trimTrailingSlash(config.public.cognitoApiDomain)

const cognitoAuthConfig = {
  authority: `https://cognito-idp.${config.public.awsRegion}.amazonaws.com/${config.public.congitoUserPoolID}`,
  client_id: config.public.cognitoAppClientId,
  redirect_uri: `${authBase}/callback`,
  post_logout_redirect_uri: `${authBase}/logout`,
  response_type: 'code',
  scope: 'openid email profile',
}

export const userManager = new UserManager(cognitoAuthConfig)

export async function signInRedirect(options?: { state?: unknown }) {
  await userManager.clearStaleState().catch(() => undefined)
  return userManager.signinRedirect(options)
}

export async function signOutRedirect() {
  const clientId = cognitoAuthConfig.client_id
  const logoutUri = cognitoAuthConfig.post_logout_redirect_uri
  const domain = cognitoDomain || authBase
  window.location.href = `${domain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(logoutUri)}`
}
