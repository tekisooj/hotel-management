import { NuxtAxiosInstance } from '@nuxtjs/axios'
import { useRuntimeConfig } from 'nuxt/app'
import { useUserStore, isTokenExpired } from '@/stores/user'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { Booking } from 'types/Booking'
import type { Review } from 'types/Review'

type RoomPricingOptions = {
  checkInDate?: string | null
  checkOutDate?: string | null
  capacity?: number | null
}

interface GuestBff {
  addReview(body: Review): Promise<any>
  getPropertyReviews(propertyUuid: string): Promise<any>
  getUserReviews(userUuid: string): Promise<any>
  addBooking(body: Booking): Promise<any>
  getUserBookings(): Promise<any>
  cancelUserBooking(bookingUuid: string): Promise<any>
  getFilteredRooms(params: Record<string, unknown>): Promise<any>
  getRoom(roomUuid: string, options?: RoomPricingOptions): Promise<any>
  getProperty(propertyUuid: string, options?: RoomPricingOptions): Promise<any>
  createPaymentOrder(payload: PaymentOrderRequest): Promise<PaymentOrderResponse>
  capturePayment(payload: CapturePaymentRequest): Promise<CapturePaymentResponse>
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
  getRoom: async (roomUuid: string, options?: RoomPricingOptions) =>
    axios.$get(`room/${roomUuid}`, {
      params: options?.checkInDate ? { check_in_date: options.checkInDate } : undefined,
    }),
  getProperty: async (propertyUuid: string, options?: RoomPricingOptions) => {
    const params: Record<string, string | number> = {}
    if (options?.checkInDate) {
      params.check_in_date = options.checkInDate
    }
    if (options?.checkOutDate) {
      params.check_out_date = options.checkOutDate
    }
    if (options?.capacity && options.capacity > 0) {
      params.capacity = options.capacity
    }
    return axios.$get(`property/${propertyUuid}`, {
      params: Object.keys(params).length ? params : undefined,
    })
  },
  createPaymentOrder: async (payload: PaymentOrderRequest) => axios.$post('booking/payment/order', payload),
  capturePayment: async (payload: CapturePaymentRequest) => axios.$post('booking/payment/capture', payload),
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
  country?: string
  city?: string
  state?: string
  latitude?: number
  longitude?: number
  radius_km?: number
  check_in_date: string
  check_out_date: string
  capacity?: number
  max_price?: number
}

type PaymentOrderRequest = {
  room_uuid: string
  check_in: string
  check_out: string
  guests: number
}

interface PaymentAmount {
  currency_code: string
  value: string
}

type PaymentOrderResponse = {
  order_id: string
  amount: PaymentAmount
  nights: number
  nightly_rate: string
  room_name: string
  paypal_client_id?: string | null
}

type CapturePaymentRequest = PaymentOrderRequest & {
  order_id: string
}

type CapturePaymentResponse = {
  booking_uuid: string
  payment_status: string
  amount: PaymentAmount
}

function normalizeBooking(raw: any): Booking {
  return {
    uuid: raw.uuid || raw.id,
    userUuid: raw.user_uuid || raw.userUuid,
    roomUuid: raw.room_uuid || raw.roomUuid,
    checkIn: raw.check_in ? new Date(raw.check_in) : raw.checkIn ? new Date(raw.checkIn) : undefined as any,
    checkOut: raw.check_out ? new Date(raw.check_out) : raw.checkOut ? new Date(raw.checkOut) : undefined as any,
    totalPrice: Number(raw.total_price ?? raw.totalPrice ?? 0),
    status: raw.status,
    createdAt: raw.created_at ? new Date(raw.created_at) : raw.createdAt ? new Date(raw.createdAt) : undefined as any,
    updatedAt: raw.updated_at ? new Date(raw.updated_at) : raw.updatedAt ? new Date(raw.updatedAt) : undefined as any,
  }
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
      check_in_date: params.check_in_date,
      check_out_date: params.check_out_date,
    }
    if (params.country) {
      query.country = params.country
    }
    if (params.city) {
      query.city = params.city
    }
    if (params.state) {
      query.state = params.state
    }
    if (typeof params.latitude === 'number' && typeof params.longitude === 'number') {
      query.latitude = params.latitude
      query.longitude = params.longitude
      if (typeof params.radius_km === 'number' && params.radius_km > 0) {
        query.radius_km = params.radius_km
      }
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
    const res = await $fetch<any[]>(`${baseURL}/my/bookings`, {
      headers: authHeaders(),
    })
    if (!Array.isArray(res)) return []
    return res.map(normalizeBooking)
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

  async function getRoom(roomUuid: string, options: RoomPricingOptions = {}) {
    const requestOptions: { headers: Record<string, string>; params?: Record<string, string> } = {
      headers: authHeaders(),
    }
    const trimmedCheckIn = options.checkInDate?.trim()
    if (trimmedCheckIn) {
      requestOptions.params = { check_in_date: trimmedCheckIn }
    }
    return await $fetch(`${baseURL}/room/${roomUuid}`, requestOptions)
  }

  async function getProperty(propertyUuid: string, options: RoomPricingOptions = {}) {
    const requestOptions: { headers: Record<string, string>; params?: Record<string, string | number> } = {
      headers: authHeaders(),
    }
    const params: Record<string, string | number> = {}
    const trimmedCheckIn = options.checkInDate?.trim()
    const trimmedCheckOut = options.checkOutDate?.trim()
    if (trimmedCheckIn) {
      params.check_in_date = trimmedCheckIn
    }
    if (trimmedCheckOut) {
      params.check_out_date = trimmedCheckOut
    }
    if (options.capacity && options.capacity > 0) {
      params.capacity = options.capacity
    }
    if (Object.keys(params).length) {
      requestOptions.params = params
    }
    return await $fetch(`${baseURL}/property/${propertyUuid}`, requestOptions)
  }

  async function searchPlaces(text: string) {
    return await $fetch(`${baseURL}/places/search-text`, {
      params: { text },
      headers: authHeaders(),
    })
  }

  async function createPaymentOrder(payload: PaymentOrderRequest): Promise<PaymentOrderResponse> {
    return await $fetch<PaymentOrderResponse>(`${baseURL}/booking/payment/order`, {
      method: 'POST',
      body: payload,
      headers: authHeaders(),
    })
  }

  async function capturePayment(payload: CapturePaymentRequest): Promise<CapturePaymentResponse> {
    return await $fetch<CapturePaymentResponse>(`${baseURL}/booking/payment/capture`, {
      method: 'POST',
      body: payload,
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
    createPaymentOrder,
    capturePayment,
  }
}
