<template>
  <div class="logout">Signing out…</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { signOutRedirect } from '~/api/authClient'
import { useUserStore } from '~/stores/user'

onMounted(async () => {
  const store = useUserStore()
  store.clearUser()
  await signOutRedirect()
})
</script>

<style scoped>
.logout {
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 1.2rem;
}
</style>
