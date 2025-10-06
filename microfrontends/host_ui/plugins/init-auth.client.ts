import { useUserStore, isTokenExpired } from '@/stores/user'

export default defineNuxtPlugin(() => {
  if (process.server) return
  const user = useUserStore()
  const stored = window.localStorage.getItem('id_token')
  if (!stored) return
  if (isTokenExpired(stored)) {
    window.localStorage.removeItem('id_token')
    return
  }
  if (!user.token) {
    user.setToken(stored)
  }
})
