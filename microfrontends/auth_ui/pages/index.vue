<template>
  <div class="login-page">
    <div class="card">
      <h1 class="title">Sign in to Hotel Management</h1>
      <p class="subtitle">Choose the application you want to access.</p>

      <div class="selector">
        <label class="form-label" for="app">Application</label>
        <select id="app" v-model="selectedApp" class="form-select">
          <option value="guest">Guest experience</option>
          <option value="host">Host console</option>
        </select>
      </div>

      <button class="btn btn-primary w-100" @click="login">Sign in with Cognito</button>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { userManager } from '~/api/authClient'

const route = useRoute()
const router = useRouter()

const selectedApp = computed({
  get: () => (typeof route.query.app === 'string' ? route.query.app : 'guest'),
  set: (value: string) => {
    router.replace({ query: { ...route.query, app: value } })
  },
})

const redirectTarget = computed(() => (typeof route.query.redirect === 'string' ? route.query.redirect : ''))

async function login() {
  const state = {
    app: selectedApp.value,
    redirect: redirectTarget.value,
  }
  await userManager.signinRedirect({
    state: JSON.stringify(state),
  })
}
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: flex;
  justify-content: center;
  align-items: center;
  background: linear-gradient(135deg, #f4ede2, #f8f5ef);
  padding: 24px;
}

.card {
  background: #fff;
  padding: 32px;
  border-radius: 16px;
  box-shadow: 0 16px 40px rgba(0, 0, 0, 0.08);
  width: 100%;
  max-width: 420px;
}

.title {
  font-size: 1.8rem;
  margin-bottom: 8px;
}

.subtitle {
  color: #6b645c;
  margin-bottom: 24px;
}

.selector {
  margin-bottom: 24px;
}
</style>
