<template>
  <div class="callback">Signing you in...</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const config = useRuntimeConfig()

async function redirectToDestination(target: unknown) {
  if (typeof window === 'undefined') return
  const raw = typeof target === 'string' ? target.trim() : ''
  const destination = raw || '/'
  if (/^https?:\/\//i.test(destination)) {
    window.location.replace(destination)
    return
  }
  const normalized = destination.startsWith('/') ? destination : `/${destination}`
  try {
    await router.replace(normalized)
  } catch {
    const absolute = new URL(normalized, window.location.origin)
    window.location.replace(absolute.toString())
  }
}

onMounted(async () => {
  const tokenParam = route.query.id_token
  const redirectParam = route.query.redirect

  if (typeof tokenParam !== 'string' || !tokenParam) {
    user.clear()
    const authUrl = new URL(config.public.authUiUrl || '/')
    authUrl.searchParams.set('app', 'guest')
    authUrl.searchParams.set('redirect', '/')
    window.location.href = authUrl.toString()
    return
  }

  user.setToken(tokenParam)
  await user.fetchProfile().catch(() => user.clear())

  await redirectToDestination(redirectParam)
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
