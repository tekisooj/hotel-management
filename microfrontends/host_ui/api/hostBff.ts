import { NuxtAxiosInstance } from '@nuxtjs/axios';

import { PropertyDetail } from '@/types/PropertyDetail';
import { useRuntimeConfig } from 'nuxt/app';
import { useUserStore } from '@/stores/user';
import { Booking } from 'types/Booking';
import { BookingStatus } from 'types/BookingStatus';
import { Review } from 'types/Review';
import { Room } from '@/types/Room';

interface AssetUploadResponse {
  key: string
  uploadUrl: string
  fields: Record<string, string>
}

interface HostBff {
  getProperties(): Promise<any>
  addProperty(property: PropertyDetail): Promise<any>
  addRoom(room: Room): Promise<any>
  deleteRoom(roomUuid: string): Promise<any>
  deleteProperty(propertyUuid: string): Promise<any>
  getBookings(propertyUuid: string, checkInDate: Date, checkOutDate: Date): Promise<any>
  changeBookingStatus(bookingUuid: string, status: BookingStatus): Promise<any>
  getPropertyReviews(propertyUuid: string): Promise<any>
  createAssetUploadUrl(prefix: string, contentType: string, extension?: string): Promise<AssetUploadResponse>
}

declare module '@nuxt/types' {
  interface Context {
    $hostBff: HostBff
  }
}

export default (axios: NuxtAxiosInstance): HostBff => ({
  getProperties: async () => axios.$get('properties'),
  addProperty: async (property: PropertyDetail) => axios.$post('property', property),
  addRoom: async (room: Room) => axios.$post('room', room),
  deleteRoom: async (roomUuid: string) => axios.$delete(`room/${roomUuid}`),
  deleteProperty: async (propertyUuid: string) => axios.$delete(`property/${propertyUuid}`),
  getBookings: async (propertyUuid: string, checkInDate: Date, checkOutDate: Date) =>
    axios.$get('bookings', { property_uuid: propertyUuid, check_in: checkInDate, check_out: checkOutDate }),
  changeBookingStatus: async (bookingUuid: string, status: BookingStatus) =>
    axios.$patch(`booking/${bookingUuid}`, { booking_status: status }),
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
    if (user.token) {
      return { Authorization: `Bearer ${user.token}` }
    }
    const devUserId = (config.public as any).devUserId as string | undefined
    return devUserId ? { 'X-User-Id': devUserId } : {}
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

  async function getProperties(): Promise<PropertyDetail[]> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/properties`, {
      headers: authHeaders(),
    })
  }

  async function addProperty(body: PropertyDetail): Promise<string> {
    const devUserId = (config.public as any).devUserId as string | undefined
    const payload: any = {
      user_uuid: body.userUuid || devUserId,
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

  async function getBookings(property_uuid: string, check_in: Date, check_out: Date): Promise<Booking[]> {
    return await $fetch<Booking[]>(`${baseURL}/bookings`, {
      headers: authHeaders(),
      params: { property_uuid, check_in, check_out },
    })
  }

  async function changeBookingStatus(booking_uuid: string, booking_status: BookingStatus): Promise<Booking> {
    return await $fetch<Booking>(`${baseURL}/booking/${booking_uuid}`, {
      method: 'PATCH',
      body: { booking_status },
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
    addProperty,
    addRoom,
    deleteRoom,
    deleteProperty,
    getBookings,
    changeBookingStatus,
    getPropertyReviews,
    createAssetUploadUrl,
    searchPlaces,
  }
}

