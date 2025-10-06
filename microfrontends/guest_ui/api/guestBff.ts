import { NuxtAxiosInstance } from '@nuxtjs/axios'
import { useRuntimeConfig } from 'nuxt/app'
import { useUserStore, isTokenExpired } from '@/stores/user'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { Booking } from 'types/Booking'
import type { Review } from 'types/Review'

interface GuestBff {
  addReview(body: Review): Promise<any>
  getPropertyReviews(propertyUuid: string): Promise<any>
  getUserReviews(userUuid: string): Promise<any>
  addBooking(body: Booking): Promise<any>
  getUserBookings(): Promise<any>
  cancelUserBooking(bookingUuid: string): Promise<any>
  getFilteredRooms(params: Record<string, unknown>): Promise<any>
}

declare module '@nuxt/types' {
  interface Context {
    $guestBff: GuestBff
  }
}

export default (axios: NuxtAxiosInstance): GuestBff => ({
  addReview: async (review: Review) => axios.$post('review', review),
  getPropertyReviews: async (propertyUuid: string) => axios.$get(`reviews/${propertyUuid}`),
  getUserReviews: async (userUuid: string) => axios.$get(`reviews/${userUuid}`),
  addBooking: async (booking: Booking) => axios.$post('booking', booking),
  getUserBookings: async () => axios.$get('my/bookings'),
  cancelUserBooking: async (bookingUuid: string) => axios.$delete(`my/booking/${bookingUuid}`),
  getFilteredRooms: async (params: Record<string, unknown>) => axios.$get('rooms', { params }),
})

function buildAuthHeaders(userStore: ReturnType<typeof useUserStore>, devUserId?: string) {
  let token = userStore.token
  if (!token && typeof window !== 'undefined') {
    const stored = window.localStorage.getItem('id_token')
    if (stored && !isTokenExpired(stored)) {
      userStore.setToken(stored)
      token = stored
    } else if (stored) {
      window.localStorage.removeItem('id_token')
    }
  }
  if (token && isTokenExpired(token)) {
    userStore.clear()
    token = null
  }
  if (token) {
    return { Authorization: `Bearer ${token}` }
  }
  return devUserId ? { 'X-User-Id': devUserId } : {}
}

type SearchRoomsParams = {
  country: string
  city: string
  state?: string
  check_in_date: string
  check_out_date: string
  capacity?: number
  max_price?: number
}

export function useGuestBff() {
  const config = useRuntimeConfig()
  const baseURL = (config.public.apiBase || '').replace(/\/$/, '')
  const user = useUserStore()
  const devUserId = (config.public as any).devUserId as string | undefined

  function authHeaders() {
    return buildAuthHeaders(user, devUserId)
  }

  async function searchRooms(params: SearchRoomsParams): Promise<PropertyDetail[]> {
    const query: Record<string, string | number> = {
      country: params.country,
      city: params.city,
      check_in_date: params.check_in_date,
      check_out_date: params.check_out_date,
    }
    if (params.state) {
      query.state = params.state
    }
    if (typeof params.capacity === 'number' && params.capacity > 0) {
      query.capacity = params.capacity
    }
    if (typeof params.max_price === 'number' && params.max_price > 0) {
      query.max_price = params.max_price
    }

    return await $fetch<PropertyDetail[]>(`${baseURL}/rooms`, {
      params: query,
      headers: authHeaders(),
    })
  }

  async function addReview(body: { property_uuid: string; rating: number; comment?: string }) {
    const { property_uuid, ...rest } = body
    return await $fetch(`${baseURL}/review/${property_uuid}`, {
      method: 'POST',
      body: rest,
      headers: authHeaders(),
    })
  }

  async function getPropertyReviews(propertyUuid: string) {
    return await $fetch(`${baseURL}/reviews/${propertyUuid}`, {
      headers: authHeaders(),
    })
  }

  async function addBooking(body: Record<string, unknown>): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/booking`, {
      method: 'POST',
      body,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function getMyBookings() {
    return await $fetch(`${baseURL}/my/bookings`, {
      headers: authHeaders(),
    })
  }

  async function cancelMyBooking(bookingUuid: string): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/my/booking/${bookingUuid}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function getMe() {
    return await $fetch(`${baseURL}/me`, {
      headers: authHeaders(),
    })
  }

  async function updateMe(update: Record<string, unknown>) {
    return await $fetch(`${baseURL}/me`, {
      method: 'PATCH',
      body: update,
      headers: authHeaders(),
    })
  }

  async function getRoom(roomUuid: string) {
    return await $fetch(`${baseURL}/room/${roomUuid}`, {
      headers: authHeaders(),
    })
  }

  async function getProperty(propertyUuid: string) {
    return await $fetch(`${baseURL}/property/${propertyUuid}`, {
      headers: authHeaders(),
    })
  }

  async function searchPlaces(text: string) {
    return await $fetch(`${baseURL}/places/search-text`, {
      params: { text },
      headers: authHeaders(),
    })
  }

  return {
    searchRooms,
    addReview,
    getPropertyReviews,
    addBooking,
    getMyBookings,
    cancelMyBooking,
    getMe,
    updateMe,
    getRoom,
    getProperty,
    searchPlaces,
  }
}