import { defineStore, storeToRefs } from 'pinia'
import { jwtDecode } from 'jwt-decode'

export function getUserUuidFromToken(token: string): string | null {
  try {
    if (!token) return null
    const payload: any = jwtDecode(token)
    return (payload['custom:user_uuid'] as string) || (payload['sub'] as string) || null
  } catch {
    return null
  }
}

interface UserProfile {
  uuid?: string
  name?: string
  last_name?: string
  email?: string
}

interface UserState {
  token: string | null
  uuid: string | null
  profile: UserProfile | null
}

export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    token: null,
    uuid: null,
    profile: null,
  }),
  getters: {
    isAuthenticated: (s) => !!s.token && !!s.uuid,
  },
  actions: {
    setToken(token: string | null) {
      this.token = token
      this.uuid = token ? getUserUuidFromToken(token) : null
    },
    clear() {
      this.token = null
      this.uuid = null
      this.profile = null
    },
    async fetchProfile() {
      const config = useRuntimeConfig()
      if (!this.token) return
      const me = await $fetch<UserProfile>(`${config.public.apiBase}/me`, {
        headers: { Authorization: `Bearer ${this.token}` },
      })
      this.profile = me
      if (me?.uuid) this.uuid = me.uuid
    },
  },
})

