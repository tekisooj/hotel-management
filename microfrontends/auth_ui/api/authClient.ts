import { useRuntimeConfig } from 'nuxt/app'
import { UserManager } from 'oidc-client-ts'

const config = useRuntimeConfig()

function trimTrailingSlash(value: string): string {
  return value.replace(/\/+$/, '')
}

const authBase = trimTrailingSlash((config.public.authUiUrl || '').trim())
const cognitoDomain = trimTrailingSlash((config.public.cognitoApiDomain || '').trim())

const cognitoAuthConfig = {
  authority: https://cognito-idp..amazonaws.com/,
  client_id: config.public.cognitoAppClientId,
  redirect_uri: ${authBase}/callback,
  post_logout_redirect_uri: ${authBase}/logout,
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
  window.location.href = ${cognitoDomain}/logout?client_id=&logout_uri=
}
