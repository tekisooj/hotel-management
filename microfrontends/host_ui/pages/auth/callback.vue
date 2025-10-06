<template>
  <div class="callback">Signing you in…</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const route = useRoute()
const router = useRouter()
const user = useUserStore()
const config = useRuntimeConfig()

onMounted(async () => {
  const tokenParam = route.query.id_token
  const redirectParam = route.query.redirect

  if (typeof tokenParam !== 'string' || !tokenParam) {
    user.clear()
    const authUrl = new URL(config.public.authUiUrl || '/')
    authUrl.searchParams.set('app', 'host')
    authUrl.searchParams.set('redirect', window.location.origin)
    window.location.href = authUrl.toString()
    return
  }

  user.setToken(tokenParam)
  await user.fetchProfile().catch(() => user.clear())

  const destination = typeof redirectParam === 'string' && redirectParam.length
    ? redirectParam
    : '/'

  if (/^https?:\/\//i.test(destination)) {
    window.location.replace(destination)
  } else {
    router.replace(destination)
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
