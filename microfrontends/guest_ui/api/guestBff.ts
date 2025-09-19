import { Booking } from "types/Booking";
import { Review } from "types/Review";
import { NuxtAxiosInstance } from '@nuxtjs/axios';

interface GuestBff {
    addReview(review: Review): any;
    getPropertyReviews(propertyUuid: string): any;
    getUserReviews(userUuid: string): any;
    addBooking(booking: Booking): any;
    getUserBookings(): any;
    cancelUserBooking(bookingUuid: string): any;
    getFilteredRooms(checkInDate?: Date, checkOutDate?: Date, amenities?: string[], capacity?: number, maxPrice?: number, country?: string, state?: string, city?: string, ratingAbove?: number): any;
}

declare module '@nuxt/types' {
    interface Context {
        $guestBff : GuestBff;
    }
}

export default (axios: NuxtAxiosInstance): GuestBff => ({
    addReview: async (review: Review) => axios.$post('review', review),
    getPropertyReviews: async (propertyUuid: string) => axios.$get('reviews/${propertyUuid}'),
    getUserReviews: async (userUuid: string) => axios.$get('reviews/${userUuid}'),
    addBooking: async (booking: Booking) => axios.$post('booking', booking),
    getUserBookings: async () => axios.$get('my/bookings'),
    cancelUserBooking: async (bookingUuid: string) => axios.$delete('my/booking/${bookingUuid}'),
    getFilteredRooms: async (checkInDate?: Date, checkOutDate?: Date, amenities?: string[], capacity?: number, maxPrice?: number, country?: string, state?: string, city?: string, ratingAbove?: number) => axios.$get('rooms', {check_in_date:checkInDate, check_out_date:checkOutDate, amenities:amenities, capacity:capacity, max_price:maxPrice, country:country, state:state, city:city, rating_aboce:ratingAbove})

});
import type { PropertyDetail } from '@/types/PropertyDetail'
import { useUserStore } from '@/stores/user'
import { useRuntimeConfig } from "nuxt/app";

export function useGuestBff() {
  const config = useRuntimeConfig()
  const baseURL = (config.public.apiBase || '').replace(/\/$/, '')
  const user = useUserStore()

  function authHeaders() {
    if (user.token) {
      return { Authorization: `Bearer ${user.token}` }
    }
    const devUserId = (config.public as any).devUserId as string | undefined
    return devUserId ? { 'X-User-Id': devUserId } : {}
  }

  // Search rooms (returns PropertyDetail[] with rooms + average_rating)
  async function searchRooms(params: {
    country: string
    city: string
    state?: string
    check_in_date: string
    check_out_date: string
    capacity?: number
    max_price?: number
  }): Promise<PropertyDetail[]> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/rooms`, { params })
  }

  // Reviews
  async function addReview(body: {
    property_uuid: string
    rating: number
    commet?: string
  }): Promise<string> {
    // BFF takes property_uuid in path and body with other fields
    const { property_uuid, ...rest } = body
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/review/${property_uuid}` as string, {
      method: 'POST',
      body: rest,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function getPropertyReviews(property_uuid: string) {
    return await $fetch(`${baseURL}/reviews/${property_uuid}`)
  }

  // Bookings
  async function addBooking(body: Record<string, unknown>): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/booking`, {
      method: 'POST',
      body,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function getMyBookings() {
    return await $fetch(`${baseURL}/my/bookings`, { headers: authHeaders() })
  }

  async function cancelMyBooking(booking_uuid: string): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/my/booking/${booking_uuid}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  // Current user
  async function getMe() {
    return await $fetch(`${baseURL}/me`, { headers: authHeaders() })
  }

  async function updateMe(update: Record<string, unknown>) {
    return await $fetch(`${baseURL}/me`, {
      method: 'PATCH',
      body: update,
      headers: authHeaders(),
    })
  }

  async function getRoom(room_uuid: string) {
      const url = `${baseURL}/room/${room_uuid}` as string
      return await $fetch<any>(url, { headers: authHeaders() })
    }
  async function getProperty(property_uuid: string) {
    const url = `${baseURL}/property/${property_uuid}` as string
    return await $fetch<any>(url, { headers: authHeaders() })
  }
  async function searchPlaces(text: string) {
    return await $fetch<any>(`${baseURL}/places/search-text`, {
      params: { text},
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
    searchPlaces
  }
}
