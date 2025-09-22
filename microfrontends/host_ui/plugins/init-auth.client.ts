import { useUserStore } from '@/stores/user'

export default defineNuxtPlugin(() => {
  if (process.server) return
  const user = useUserStore()
  const stored = window.localStorage.getItem('id_token')
  if (stored && !user.token) {
    user.setToken(stored)
  }
})
