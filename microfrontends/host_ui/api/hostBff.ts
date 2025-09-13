import { Booking } from "types/Booking";
import { BookingStatus } from "types/BookingStatus"
import {Room} from "types/Room"
import { Review } from "types/Review";
import { NuxtAxiosInstance } from '@nuxtjs/axios';

interface HostBff {    
    getProperties(): any;
    addProperty(property: PropertyDetail): any;
    addRoom(room: Room): any;
    deleteRoom(roomUuid: string): any;
    deleteProperty(propertyUuid: string): any;
    getBookings(propertyUuid: string, checkInDate: Date, checkOutDate: Date): any;
    changeBookingStatus(bookingUuid: string, status: BookingStatus): any;
    getPropertyReviews(propertyUuid: string): any;
    }

declare module '@nuxt/types' {
    interface Context {
        $hostBff : HostBff;
    }
}

export default (axios: NuxtAxiosInstance): HostBff => ({

    getProperties: async () => axios.$get('properties'),
    addProperty: async (property: PropertyDetail) => axios.$post('property', property),
    addRoom: async (room: Room) => axios.$post('room', room),
    deleteRoom: async (roomUuid: string) => axios.$delete('room/${roomUuid}'),
    deleteProperty: async (propertyUuid: string) => axios.$delete('property/${propertyUuid}'),
    getBookings: async (propertyUuid: string, checkInDate: Date, checkOutDate: Date) => axios.$get('bookings', {property_uuid: propertyUuid, check_in: checkInDate, check_out: checkOutDate}),
    changeBookingStatus: async (bookingUuid: string, status: BookingStatus) => axios.$patch('booking/${bookingUuid}', {booking_status: status}),
    getPropertyReviews: async (propertyUuid: string) => axios.$get('reviews/{propertyUuid}'),
    
});
import { PropertyDetail } from '@/types/PropertyDetail'
import { useUserStore } from '@/stores/user'
import { useRuntimeConfig } from "nuxt/app";

export function useHostBff() {
  const config = useRuntimeConfig()
  const baseURL = (config.public.apiBase || '').replace(/\/$/, '')
  const user = useUserStore()

  function authHeaders() {
    return user.token ? { Authorization: `Bearer ${user.token}` } : {}
  }

  async function getProperties(): Promise<PropertyDetail[]> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/properties` as string)
  }

  async function addProperty(body: PropertyDetail): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/property` as string, {
      method: 'POST',
      body: body,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function addRoom(body: Room): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/room` as string, {
      method: 'POST',
      body: body,
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function deleteRoom(room_uuid: string): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/room/${room_uuid}` as string, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function deleteProperty(property_uuid: string): Promise<string> {
    const res = await $fetch<string | { uuid: string }>(`${baseURL}/room/${property_uuid}` as string, {
      method: 'DELETE',
      headers: authHeaders(),
    })
    return typeof res === 'string' ? res : res.uuid
  }

  async function getBookings(property_uuid: string, check_in: Date, check_out: Date): Promise<Booking[]> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/bookings` as string)
  }

  async function changeBookingStatus(booking_uuid: string, booking_status: BookingStatus): Promise<Booking> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/booking/${booking_uuid}` as string, {
      method: 'PATCH',
      body: {booking_status: booking_status}
    } )
  }

  async function getPropertyReviews(property_uuid: string): Promise<Review[]> {
    return await $fetch<PropertyDetail[]>(`${baseURL}/reviews/${property_uuid}` as string)
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
    async searchPlaces(text: string) {
      return await $fetch<any>(`${baseURL}/places/search-text`, {
        params: { text },
        headers: authHeaders(),
      })
    },
  }
}
