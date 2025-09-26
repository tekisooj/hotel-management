<template>
  <div class="callback">Redirecting…</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRuntimeConfig } from 'nuxt/app'
import { userManager } from '~/api/authClient'
import { useUserStore } from '~/stores/user'
import type { User } from '~/types/User'

function buildTargetUrl(base: string, token: string, refreshToken?: string, redirect?: string) {
  const resolvedBase = base || window.location.origin
  const url = new URL(resolvedBase)
  const basePath = url.pathname.replace(/\/$/, '')
  const nextPath = `${basePath}/auth/callback`
  url.pathname = nextPath.startsWith('/') ? nextPath : `/${nextPath}`
  url.searchParams.set('id_token', token)
  if (refreshToken) {
    url.searchParams.set('refresh_token', refreshToken)
  }
  if (redirect) {
    url.searchParams.set('redirect', redirect)
  }
  return url.toString()
}

onMounted(async () => {
  const config = useRuntimeConfig()
  const store = useUserStore()
  await userManager.clearStaleState().catch(() => undefined)
  const signinResponse = await userManager.signinCallback(window.location.href)
  const state = (() => {
    try {
      return signinResponse.state ? JSON.parse(signinResponse.state) : {}
    } catch {
      return {}
    }
  })() as { app?: string; redirect?: string }

  const idToken = signinResponse.id_token
  const refreshToken = signinResponse.refresh_token || undefined

  const me = await $fetch<User>(`${config.public.userApiBase}/me`, {
    headers: { Authorization: `Bearer ${idToken}` },
  })
  store.setUser(me, idToken)

  const targetApp = state.app === 'host' || me.user_type === 'staff' ? 'host' : 'guest'
  const targetBase = targetApp === 'host' ? config.public.hostUiUrl : config.public.guestUiUrl
  const redirectUrl = buildTargetUrl(targetBase, idToken, refreshToken, state.redirect)
  window.location.href = redirectUrl
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
