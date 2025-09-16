import { useRuntimeConfig } from "nuxt/app";
import { UserManager } from "oidc-client-ts";

const config = useRuntimeConfig();


const cognitoAuthConfig = {
  authority: `https://cognito-idp.${config.public.awsRegion}.amazonaws.com/${config.public.congitoUserPoolID}`,
  client_id: config.public.cognitoAppClientId,
  redirect_uri: `${config.public.authUiUrl}/callback`,
  response_type: "code",
  scope: "openid email profile",
};

export const userManager = new UserManager(cognitoAuthConfig);

export async function signOutRedirect() {
  const clientId = cognitoAuthConfig.client_id;
  const logoutUri = config.public.authUiUrl;
  const cognitoDomain = config.public.cognitoApiDomain;
  window.location.href = `${cognitoDomain}/logout?client_id=${clientId}&logout_uri=${encodeURIComponent(
    logoutUri
  )}`;
}