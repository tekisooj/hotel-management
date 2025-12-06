import { NuxtAxiosInstance } from '@nuxtjs/axios'

import { PropertyDetail } from '@/types/PropertyDetail'
import { useRuntimeConfig } from 'nuxt/app'
import { useUserStore, isTokenExpired } from '@/stores/user'
import { Booking } from 'types/Booking'
import { BookingStatus } from 'types/BookingStatus'
import { Review } from 'types/Review'
import { Room } from '@/types/Room'
import { RoomAvailability } from '@/types/Availability'

interface AssetUploadResponse {
  key: string
  uploadUrl: string
  fields: Record<string, string>
}

interface HostBff {
  getProperties(): Promise<any>
  getProperty(propertyUuid: string): Promise<PropertyDetail>
  addProperty(property: PropertyDetail): Promise<any>
  updateProperty(propertyUuid: string, property: PropertyDetail): Promise<PropertyDetail>
  addRoom(room: Room): Promise<any>
  updateRoom(roomUuid: string, room: Room): Promise<Room>
  deleteRoom(roomUuid: string): Promise<any>
  deleteProperty(propertyUuid: string): Promise<any>
  getBookings(propertyUuid: string, checkInDate: Date, checkOutDate: Date): Promise<RoomAvailability[]>
  changeBookingStatus(bookingUuid: string, status: BookingStatus): Promise<any>
  cancelBooking(bookingUuid: string): Promise<any>
  getPropertyReviews(propertyUuid: string): Promise<any>
  createAssetUploadUrl(prefix: string, contentType: string, extension?: string): Promise<AssetUploadResponse>
}

declare module '@nuxt/types' {
  interface Context {
    $hostBff: HostBff
  }
}

function mapAvailability(raw: any): RoomAvailability {
  return {
    uuid: raw.uuid,
    property_uuid: raw.property_uuid,
    name: raw.name,
    description: raw.description,
    capacity: raw.capacity,
    room_type: raw.room_type,
    price_per_night: raw.price_per_night,
    min_price_per_night: raw.min_price_per_night,
    max_price_per_night: raw.max_price_per_night,
    property: raw.property
      ? {
          uuid: raw.property.uuid,
          name: raw.property.name,
          address: raw.property.address,
        }
      : undefined,
    bookings: Array.isArray(raw.bookings)
      ? raw.bookings.map((booking: any) => ({
          uuid: booking.uuid,
          user_uuid: booking.user_uuid,
          room_uuid: booking.room_uuid,
          check_in: booking.check_in,
          check_out: booking.check_out,
          total_price: booking.total_price,
          status: booking.status,
          created_at: booking.created_at,
          updated_at: booking.updated_at,
          guest_name: booking.guest_name,
          guest_last_name: booking.guest_last_name,
          guest_email: booking.guest_email,
          guest_phone: booking.guest_phone,
        }))
      : [],
  }
}

function mapAvailabilityList(list: any[]): RoomAvailability[] {
  return Array.isArray(list) ? list.map(mapAvailability) : []
}

function normalizeImages(images?: Array<{ key?: string | null }>) {
  if (!images) {
    return undefined
  }
  const normalized = images
    .map((image) => (image?.key ?? '').trim())
    .filter((key): key is string => key.length > 0)
    .map((key) => ({ key }))
  return normalized.length ? normalized : undefined
}
function mapPropertyDetailToPayload(body: PropertyDetail, ownerId?: string | null) {
  return {
    uuid: body.uuid || undefined,
    user_uuid: ownerId || body.userUuid || undefined,
    name: body.name,
    description: body.description,
    country: body.country,
    state: body.state,
    city: body.city,
    county: body.county,
    address: body.address,
    full_address: body.fullAddress,
    latitude: body.latitude,
    longitude: body.longitude,
    stars: body.stars,
    place_id: (body as any).placeId,
    images: normalizeImages(body.images),
  }
}

export default (axios: NuxtAxiosInstance): HostBff => ({
  getProperties: async () => axios.$get('properties'),
  getProperty: async (propertyUuid: string) => axios.$get(`property/${propertyUuid}`),
  addProperty: async (property: PropertyDetail) => axios.$post('property', property),
  addRoom: async (room: Room) => axios.$post('room', room),
  deleteRoom: async (roomUuid: string) => axios.$delete(`room/${roomUuid}`),
  deleteProperty: async (propertyUuid: string) => axios.$delete(`property/${propertyUuid}`),
  getBookings: async (propertyUuid: string, checkInDate: Date, checkOutDate: Date) => {
    const res = await axios.$get<any[]>('bookings', {
      params: {
        property_uuid: propertyUuid,
        check_in: checkInDate.toISOString(),
        check_out: checkOutDate.toISOString(),
      },
      headers: authHeaders(),
    })
    return mapAvailabilityList(res)
  },
  changeBookingStatus: async (bookingUuid: string, status: BookingStatus) =>
    axios.$patch(`booking/${bookingUuid}`, { booking_status: status }),
  cancelBooking: async (bookingUuid: string) => axios.$delete(`booking/${bookingUuid}`),
  getPropertyReviews: async (propertyUuid: string) => axios.$get(`reviews/${propertyUuid}`),
  createAssetUploadUrl: async (prefix: string, contentType: string, extension?: string) => {
    const res = await axios.$post('assets/upload-url', { prefix, content_type: contentType, extension })
    return { key: res.key, uploadUrl: res.upload_url, fields: res.fields }
  },
})

export function useHostBff() {
  const config = useRuntimeConfig()
  const baseURL = (config.public.apiBase || '').replace(/\/$/, '')
  const user = useUserStore()

  function authHeaders() {
    let token = user.token
    if (!token && typeof window !== 'undefined') {
      const stored = window.localStorage.getItem('id_token')
      if (stored && !isTokenExpired(stored)) {
        user.setToken(stored)
        token = stored
      } else if (stored) {
        window.localStorage.removeItem('id_token')
      }
    }
    if (token && isTokenExpired(token)) {
      user.clear()
      token = null
    }
    if (token) {
      return { Authorization: `Bearer ${token}` }
    }
    const devUserId = (config.public as any).devUserId as string | undefined
    return devUserId ? { 'X-User-Id': devUserId } : {}
  }


  async function getProperties(): Promise<PropertyDetail[]> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/properties`, {
      headers: authHeaders(),
    })
  }

  async function getProperty(propertyUuid: string): Promise<PropertyDetail> {
    return await $fetch<PropertyDetail>(`${baseURL}/property/${propertyUuid}`, {
      headers: authHeaders(),
    })
  }

  async function addProperty(body: PropertyDetail): Promise<string> {
    const devUserId = (config.public as any).devUserId as string | undefined
    const payload: any = {
      ...mapPropertyDetailToPayload(body, devUserId ?? null),
      rooms: body.rooms?.map((room) => ({
        uuid: room.uuid,
        property_uuid: room.propertyUuid,
        name: room.name,
        description: room.description,
        capacity: room.capacity,
        room_type: room.roomType,
        price_per_night: room.pricePerNight,
        min_price_per_night: room.minPricePerNight,
        max_price_per_night: room.maxPricePerNight,
        amenities: room.amenities,
        images: normalizeImages(room.images),
      })),
    }
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/property`, {
      method: 'POST',
      body: payload,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function updateProperty(propertyUuid: string, body: PropertyDetail): Promise<PropertyDetail> {
    const payload = mapPropertyDetailToPayload(body, null)
    payload.uuid = propertyUuid
    return await $fetch<PropertyDetail>(`${baseURL}/property/${propertyUuid}`, {
      method: 'PATCH',
      body: payload,
      headers: authHeaders(),
    })
  }

  async function addRoom(body: Room): Promise<string> {
    const payload: any = {
      uuid: body.uuid || undefined,
      property_uuid: body.propertyUuid,
      name: body.name,
      description: body.description,
      capacity: body.capacity,
      room_type: body.roomType,
      price_per_night: body.pricePerNight,
      min_price_per_night: body.minPricePerNight,
      max_price_per_night: body.maxPricePerNight,
      amenities: body.amenities,
      images: normalizeImages(body.images),
    }
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/room`, {
      method: 'POST',
      body: payload,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function updateRoom(roomUuid: string, body: Room): Promise<Room> {
    const payload: any = {
      uuid: roomUuid,
      property_uuid: body.propertyUuid,
      name: body.name,
      description: body.description,
      capacity: body.capacity,
      room_type: body.roomType,
      price_per_night: body.pricePerNight,
      min_price_per_night: body.minPricePerNight,
      max_price_per_night: body.maxPricePerNight,
      amenities: body.amenities,
      images: normalizeImages(body.images),
    }
    return await $fetch<Room>(`${baseURL}/room/${roomUuid}`, {
      method: 'PUT',
      body: payload,
      headers: authHeaders(),
    })
  }

  async function deleteRoom(room_uuid: string): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/room/${room_uuid}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function deleteProperty(property_uuid: string): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/property/${property_uuid}`, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function getBookings(property_uuid: string, check_in: Date, check_out: Date): Promise<RoomAvailability[]> {
    const response = await $fetch<any[]>(`${baseURL}/bookings`, {
      headers: authHeaders(),
      params: { property_uuid, check_in: check_in.toISOString(), check_out: check_out.toISOString() },
    })
    return mapAvailabilityList(response)
  }

  async function changeBookingStatus(booking_uuid: string, booking_status: BookingStatus): Promise<Booking> {
    return await $fetch<Booking>(`${baseURL}/booking/${booking_uuid}`, {
      method: 'PATCH',
      body: { booking_status },
      headers: authHeaders(),
    })
  }

  async function cancelBooking(booking_uuid: string): Promise<Booking> {
    return await $fetch<Booking>(`${baseURL}/booking/${booking_uuid}/cancel`, {
      method: 'PATCH',
      headers: authHeaders(),
    })
  }

  async function getPropertyReviews(property_uuid: string): Promise<Review[]> {
    return await $fetch<Review[]>(`${baseURL}/reviews/${property_uuid}`, {
      headers: authHeaders(),
    })
  }

  async function createAssetUploadUrl(prefix: string, contentType: string, extension?: string): Promise<AssetUploadResponse> {
    const res = await $fetch<{ key: string; upload_url: string; fields: Record<string, string> }>(`${baseURL}/assets/upload-url`, {
      method: 'POST',
      body: {
        prefix,
        content_type: contentType,
        ...(extension ? { extension } : {}),
      },
      headers: authHeaders(),
    })
    return { key: res.key, uploadUrl: res.upload_url, fields: res.fields }
  }

  async function searchPlaces(text: string) {
    return await $fetch<any>(`${baseURL}/places/search-text`, {
      params: { text, index: (config.public as any).awsPlaceIndex },
      headers: authHeaders(),
    })
  }

  return {
    getProperties,
    getProperty,
    addProperty,
    updateProperty,
    addRoom,
    updateRoom,
    deleteRoom,
    deleteProperty,
    getBookings,
    changeBookingStatus,
    cancelBooking,
    getPropertyReviews,
    createAssetUploadUrl,
    searchPlaces,
  }
}

