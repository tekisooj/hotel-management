import { defineStore } from 'pinia'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { Room } from '@/types/Room'

type SearchSnapshot = {
  country: string
  city: string
  state?: string
  checkIn?: string
  checkOut?: string
  capacity?: number
  maxPrice?: number
}

function pick<T>(obj: any, key: string, fallback?: T): T | undefined {
  if (obj && typeof obj === 'object') {
    if (key in obj) return obj[key]
    const snake = key.replace(/[A-Z]/g, m => '_' + m.toLowerCase())
    if (snake in obj) return obj[snake]
  }
  return fallback
}

function normalizeRoom(raw: any): Room | null {
  if (!raw) return null
  const r: Room = {
    uuid: String(pick<string>(raw, 'uuid', '')),
    propertyUuid: String(pick<string>(raw, 'propertyUuid') || pick<string>(raw, 'property_uuid') || ''),
    name: String(pick<string>(raw, 'name', '')),
    description: String(pick<string>(raw, 'description', '')),
    capacity: Number(pick<number>(raw, 'capacity', 0)),
    roomType: (pick<any>(raw, 'roomType') || pick<any>(raw, 'room_type') || '') as any,
    pricePerNight: Number(pick<number>(raw, 'pricePerNight') || pick<number>(raw, 'price_per_night') || 0),
    minPricePerNight: Number(pick<number>(raw, 'minPricePerNight') || pick<number>(raw, 'min_price_per_night') || 0),
    maxPricePerNight: Number(pick<number>(raw, 'maxPricePerNight') || pick<number>(raw, 'max_price_per_night') || 0),
    createdAt: pick<any>(raw, 'createdAt') as any,
    updatedAt: pick<any>(raw, 'updatedAt') as any,
    amenities: (pick<any>(raw, 'amenities') as any) || [],
    images: (pick<any>(raw, 'images') as any) || [],
  }
  return r
}

function normalizeProperty(raw: any): PropertyDetail | null {
  if (!raw) return null
  const p: PropertyDetail = {
    uuid: pick<string>(raw, 'uuid') || undefined,
    userUuid: String(pick<string>(raw, 'userUuid') || pick<string>(raw, 'user_uuid') || ''),
    name: String(pick<string>(raw, 'name', '')),
    description: pick<string>(raw, 'description') || undefined,
    country: String(pick<string>(raw, 'country', '')),
    state: pick<string>(raw, 'state') || undefined,
    city: String(pick<string>(raw, 'city', '')),
    county: pick<string>(raw, 'county') || undefined,
    address: String(pick<string>(raw, 'address', '')),
    fullAddress: pick<string>(raw, 'fullAddress') || pick<string>(raw, 'full_address') || undefined,
    latitude: (pick<any>(raw, 'latitude') as any) ?? undefined,
    longitude: (pick<any>(raw, 'longitude') as any) ?? undefined,
    createdAt: pick<any>(raw, 'createdAt') as any,
    updatedAt: pick<any>(raw, 'updatedAt') as any,
    averageRating: (pick<any>(raw, 'averageRating') as any) ?? (pick<any>(raw, 'average_rating') as any),
    stars: Number(pick<number>(raw, 'stars', 0)),
    placeId: pick<any>(raw, 'placeId') as any,
    images: (pick<any>(raw, 'images') as any) || [],
    rooms: Array.isArray(raw.rooms) ? raw.rooms.map(normalizeRoom).filter(Boolean) as Room[] : undefined,
  }
  return p
}

export const useSearchStore = defineStore('guest-search', {
  state: () => ({
    propertiesById: {} as Record<string, PropertyDetail>,
    roomsById: {} as Record<string, Room>,
    lastSearch: null as SearchSnapshot | null,
  }),
  actions: {
    ingestSearch(results: any[]) {
      for (const raw of results || []) {
        const prop = normalizeProperty(raw)
        if (prop?.uuid) this.propertiesById[prop.uuid] = prop
        for (const r of prop?.rooms || []) {
          if (r.uuid) this.roomsById[r.uuid] = r
        }
      }
    },
    setProperty(raw: any) {
      const p = normalizeProperty(raw)
      if (p?.uuid) {
        this.propertiesById[p.uuid] = p
        for (const r of p.rooms || []) {
          if (r.uuid) this.roomsById[r.uuid] = r
        }
      }
    },
    setRoom(raw: any) {
      const r = normalizeRoom(raw)
      if (r?.uuid) this.roomsById[r.uuid] = r
    },
    setLastSearch(snapshot: SearchSnapshot) {
      this.lastSearch = { ...snapshot }
    },
    clearLastSearch() {
      this.lastSearch = null
    },
  },
  getters: {
    getProperty: (state) => (uuid: string) => state.propertiesById[uuid],
    getRoom: (state) => (uuid: string) => state.roomsById[uuid],
  },
})
