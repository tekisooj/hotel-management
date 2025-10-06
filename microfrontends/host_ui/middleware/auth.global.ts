import { useUserStore } from '@/stores/user'

export default defineNuxtRouteMiddleware((to) => {
  if (process.server) return
  if (to.path.startsWith('/auth/callback')) return

  const user = useUserStore()
  const config = useRuntimeConfig()
  if (!user.token) {
    const authUrl = new URL(config.public.authUiUrl || '/')
    authUrl.searchParams.set('app', 'host')
    const { pathname, search, hash } = window.location
    const redirectTarget = `${pathname}${search}${hash}` || '/'
    authUrl.searchParams.set('redirect', redirectTarget)
    return navigateTo(authUrl.toString(), { external: true })
  }
})

