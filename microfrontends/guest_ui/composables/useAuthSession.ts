import { useUserStore } from '@/stores/user'

export function useAuthSession() {
  const user = useUserStore()
  const config = useRuntimeConfig()

  function logout() {
    user.clear()
    if (process.client) {
      window.localStorage.removeItem('id_token')
      const authUrl = new URL(config.public.authUiUrl || window.location.origin)
      const basePath = authUrl.pathname.replace(/\/$/, '')
      const nextPath = `${basePath}/logout`
      authUrl.pathname = nextPath.startsWith('/') ? nextPath : `/${nextPath}`
      authUrl.searchParams.set('app', 'guest')
      authUrl.searchParams.set('redirect', window.location.origin)
      window.location.href = authUrl.toString()
    }
  }

  return { logout }
}
