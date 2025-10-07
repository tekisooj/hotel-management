import { defineStore } from 'pinia'
import { jwtDecode } from 'jwt-decode'

type DecodedToken = {
  [key: string]: unknown
  exp?: number
  'custom:user_uuid'?: string
  sub?: string
}

export function isTokenExpired(token?: string | null): boolean {
  if (!token) return true
  try {
    const payload = jwtDecode<DecodedToken>(token)
    if (payload.exp == null) return false
    return Date.now() >= payload.exp * 1000
  } catch {
    return true
  }
}

export function getUserUuidFromToken(token: string): string | null {
  try {
    if (!token || isTokenExpired(token)) return null
    const payload = jwtDecode<DecodedToken>(token)
    return payload['custom:user_uuid'] || payload.sub || null
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
      if (token && isTokenExpired(token)) {
        this.clear()
        return
      }
      this.token = token
      this.uuid = token ? getUserUuidFromToken(token) : null
      if (typeof window !== 'undefined') {
        if (token) {
          window.localStorage.setItem('id_token', token)
        } else {
          window.localStorage.removeItem('id_token')
        }
      }
    },
    clear() {
      this.token = null
      this.uuid = null
      this.profile = null
      if (typeof window !== 'undefined') {
        window.localStorage.removeItem('id_token')
      }
    },
    async fetchProfile() {
      const config = useRuntimeConfig()
      if (!this.token || isTokenExpired(this.token)) {
        this.clear()
        return
      }
      const me = await $fetch<UserProfile>(`${config.public.apiBase}/me`, {
        headers: { Authorization: `Bearer ${this.token}` },
      })
      this.profile = me
      if (me?.uuid) this.uuid = me.uuid
    },
  },
})
