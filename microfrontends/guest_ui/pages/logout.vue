<template>
  <div class="logout">Signing out…</div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthSession } from '@/composables/useAuthSession'

const { logout } = useAuthSession()

onMounted(() => {
  logout()
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
