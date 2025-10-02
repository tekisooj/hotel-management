<template>
  <div class="callback">Redirecting…</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue"
import { useRoute } from "vue-router"
import { useRuntimeConfig } from "nuxt/app"
import { getUserManager, signInRedirect } from "~/api/authClient"
import { useUserStore } from "~/stores/user"
import type { User } from "~/types/User"

function buildTargetUrl(base: string, token: string, refreshToken?: string, redirect?: string) {
  const resolvedBase = base || window.location.origin
  const url = new URL(resolvedBase)
  const basePath = url.pathname.replace(/\/$/, "")
  const nextPath = `${basePath}/auth/callback`
  url.pathname = nextPath.startsWith("/") ? nextPath : `/${nextPath}`
  url.searchParams.set("id_token", token)
  if (refreshToken) url.searchParams.set("refresh_token", refreshToken)
  if (redirect) url.searchParams.set("redirect", redirect)
  return url.toString()
}

onMounted(async () => {
  const config = useRuntimeConfig()
  const store = useUserStore()
  const route = useRoute()
  const userManager = getUserManager()

  const retriesKey = "auth_retries"
  const retries = Number(localStorage.getItem(retriesKey) || "0")

  const restartLogin = async () => {
    await userManager.clearStaleState().catch(() => undefined)
    await userManager.removeUser().catch(() => undefined)
    store.clearUser?.()

    const app = typeof route.query.app === "string" ? route.query.app : undefined
    const redirect = typeof route.query.redirect === "string" ? route.query.redirect : undefined

    localStorage.setItem(retriesKey, String(retries + 1))
    await signInRedirect({ state: JSON.stringify({ app, redirect }) })
  }

  try {
    const signinResponse = await userManager.signinCallback(window.location.href)
    localStorage.removeItem(retriesKey)

    const state = (() => {
      try { return signinResponse.state ? JSON.parse(signinResponse.state) : {} }
      catch { return {} }
    })() as { app?: string; redirect?: string }

    const idToken = signinResponse.id_token
    const refreshToken = signinResponse.refresh_token || undefined
    const authHeaders = { Authorization: `Bearer ${idToken}` }

    const profile = (signinResponse.profile || {}) as Record<string, unknown>
    const getClaim = (key: string) => {
      const value = profile[key]
      return typeof value === "string" ? value : ""
    }

    const selectedApp = state.app === "host" ? "host" : "guest"
    const desiredUserType = selectedApp === "host" ? "staff" : "guest"

    const emailClaim = getClaim("email")
    const emailLocalPart = emailClaim ? emailClaim.split("@")[0] : ""
    const baseName = getClaim("given_name") || getClaim("name") || emailLocalPart
    const familyName = getClaim("family_name")
    const resolvedName = baseName || "New"
    const resolvedLastName = familyName || resolvedName

    const postPayload = {
      name: resolvedName,
      last_name: resolvedLastName,
      email: emailClaim,
      user_type: desiredUserType,
    }

    let me: User
    try {
      me = await $fetch<User>(`${config.public.userApiBase}/me`, {
        headers: authHeaders,
      })
    } catch (getError: any) {
      const status = Number(
        getError?.status ??
        getError?.response?.status ??
        getError?.data?.status ??
        getError?.cause?.status ??
        0,
      )

      const isNotFound = status === 404
      const canAttemptCreate = Boolean(postPayload.email)

      if (!isNotFound || !canAttemptCreate) {
        throw getError
      }

      try {
        me = await $fetch<User>(`${config.public.userApiBase}/me`, {
          method: "POST",
          body: postPayload,
          headers: authHeaders,
        })
      } catch (postError: any) {
        const postStatus = Number(
          postError?.status ??
          postError?.response?.status ??
          postError?.data?.status ??
          postError?.cause?.status ??
          0,
        )

        if (postStatus === 409) {
          me = await $fetch<User>(`${config.public.userApiBase}/me`, {
            headers: authHeaders,
          })
        } else {
          throw postError
        }
      }
    }

    store.setUser(me, idToken)

    const targetApp = selectedApp === "host" || me.user_type === "staff" ? "host" : "guest"
    const targetBase = targetApp === "host" ? config.public.hostUiUrl : config.public.guestUiUrl
    const redirectUrl = buildTargetUrl(targetBase, idToken, refreshToken, state.redirect)
    window.location.href = redirectUrl
  } catch (error: any) {
    await userManager.clearStaleState().catch(() => undefined)
    await userManager.removeUser().catch(() => undefined)

    const msg = String(error?.message || "")
    if (msg.includes("No matching state") && retries < 2) {
      await restartLogin()
      return
    }

    if (retries < 2) {
      await restartLogin()
      return
    }

  }
})
</script>

<style scoped>
.callback {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}
</style>
