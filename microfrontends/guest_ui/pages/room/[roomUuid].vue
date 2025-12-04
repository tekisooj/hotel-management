<template>
  <div class="page">
    <div class="container">
      <div v-if="loading" class="room-card placeholder">
        <p>Loading room details...</p>
      </div>
      <div v-else-if="!room" class="room-card placeholder">
        <p>Room not found. Please return to the search results.</p>
        <button class="btn btn-outline-primary" @click="goBack">Back to search</button>
      </div>
      <div v-else class="card room-card">
        <img
          v-if="room.images?.length && room.images[0].url"
          :src="room.images[0].url"
          :alt="`${room.name || 'Room'} photo`"
          class="room-hero"
        />

        <div class="room-header">
          <div class="room-title">
            <h1>{{ room.name || 'Room' }}</h1>
            <p class="subtitle" v-if="room.description">{{ room.description }}</p>
          </div>
          <div class="room-rating" v-if="propertyRating != null">
            <div class="score">{{ propertyRating.toFixed(1) }}</div>
            <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9734;</div>
          </div>
        </div>

        <div class="room-tags">
          <span class="tag" v-if="room.capacity">Sleeps {{ room.capacity }}</span>
          <span class="tag" v-if="pricePerNight">From ${{ formatPrice(pricePerNight) }} per night</span>
        </div>

        <h3 class="section-title" v-if="room.description">Overview</h3>
        <p class="room-description" v-if="room.description">{{ room.description }}</p>

        <h3 class="section-title">Amenities</h3>
        <div class="amenities" v-if="room.amenities?.length">
          <ul>
            <li v-for="(a, i) in leftAmenities" :key="`l-${i}`">{{ a.name }}</li>
          </ul>
          <ul>
            <li v-for="(a, i) in rightAmenities" :key="`r-${i}`">{{ a.name }}</li>
          </ul>
        </div>
        <p v-else class="text-muted mb-0">No amenities listed for this room.</p>

        <h3 class="section-title">Booking</h3>
        <form class="booking-grid" @submit.prevent="reserve">
          <div class="field">
            <label>Check-in</label>
            <input v-model="checkIn" type="date" />
          </div>
          <div class="field">
            <label>Check-out</label>
            <input v-model="checkOut" type="date" />
          </div>
          <div class="field">
            <label>Guests</label>
            <input v-model.number="guests" type="number" min="1" />
          </div>
          <button class="reserve" :disabled="!canReserve">Proceed to payment</button>
        </form>
        <div class="booking-summary" v-if="canReserve">
          <span>{{ nights }} night<span v-if="nights !== 1">s</span> total: ${{ formatPrice(totalPrice) }}</span>
        </div>

        <h3 class="section-title">Address</h3>
        <p class="address" v-if="property">
          {{ property.fullAddress || formattedAddress }}
        </p>
        <p class="address" v-else>Property details unavailable.</p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGuestBff } from '@/api/guestBff'
import type { Room } from '@/types/Room'
import type { PropertyDetail } from '@/types/PropertyDetail'
import { useSearchStore } from '@/stores/search'

const route = useRoute()
const router = useRouter()
const { getRoom, getProperty } = useGuestBff()
const store = useSearchStore()

const loading = ref(true)
const room = ref<Room | null>(null)
const property = ref<PropertyDetail | null>(null)
const checkIn = ref('')
const checkOut = ref('')
const guests = ref(2)
const lastPricingCheckIn = ref<string | null>(null)
const initialLoadComplete = ref(false)
let pricingRequestToken = 0

const propertyRating = computed(() => {
  if (!property.value) return null
  const raw = (property.value as any).averageRating ?? (property.value as any).average_rating
  if (raw == null) return null
  const numeric = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(numeric) ? numeric : null
})

const pricePerNight = computed(() => {
  const raw = pick(room.value, 'pricePerNight', 'price_per_night')
  const numeric = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(numeric) ? numeric : 0
})

const nights = computed(() => {
  if (!checkIn.value || !checkOut.value) return 0
  const start = new Date(checkIn.value)
  const end = new Date(checkOut.value)
  const diff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
  return diff > 0 ? Math.floor(diff) : 0
})

const totalPrice = computed(() => pricePerNight.value * nights.value)

const canReserve = computed(() => Boolean(room.value?.uuid) && nights.value > 0 && guests.value > 0)

const leftAmenities = computed(() => (room.value?.amenities || []).filter((_, i) => i % 2 === 0))
const rightAmenities = computed(() => (room.value?.amenities || []).filter((_, i) => i % 2 === 1))

const formattedAddress = computed(() => {
  if (!property.value) return ''
  return [property.value.address, property.value.city, property.value.state, property.value.country]
    .filter(Boolean)
    .join(', ')
})

function pick(source: any, camel: string, snake: string) {
  if (!source) return undefined
  const camelValue = source[camel]
  if (camelValue !== undefined && camelValue !== null && camelValue !== '') return camelValue
  const snakeValue = source[snake]
  if (snakeValue !== undefined && snakeValue !== null && snakeValue !== '') return snakeValue
  return undefined
}

function formatPrice(value: number): string {
  if (!Number.isFinite(value)) return '--'
  return Number.isInteger(value) ? String(value) : value.toFixed(2)
}

function applyDefaults() {
  const query = route.query
  const qCheckIn = (query.checkIn as string) || (query.check_in as string)
  const qCheckOut = (query.checkOut as string) || (query.check_out as string)
  const qGuests = Number((query.guests as string) || (query.capacity as string) || '')

  if (qCheckIn) {
    checkIn.value = qCheckIn
  } else if (store.lastSearch?.checkIn) {
    checkIn.value = store.lastSearch.checkIn
  }

  if (qCheckOut) {
    checkOut.value = qCheckOut
  } else if (store.lastSearch?.checkOut) {
    checkOut.value = store.lastSearch.checkOut
  }

  if (!Number.isNaN(qGuests) && qGuests > 0) {
    guests.value = qGuests
  } else if (store.lastSearch?.capacity && store.lastSearch.capacity > 0) {
    guests.value = store.lastSearch.capacity
  }
}

async function load() {
  loading.value = true
  const roomUuid = route.params.roomUuid as string | undefined
  if (!roomUuid) {
    router.replace('/')
    loading.value = false
    return
  }

  applyDefaults()
  const normalizedCheckIn = (checkIn.value || '').trim()

  try {
    const storedRoom = store.getRoom(roomUuid)
    let resolvedRoom: Room | null = storedRoom || null
    let fetchedRoom: Room | null = null
    try {
      const data = await getRoom(
        roomUuid,
        normalizedCheckIn ? { checkInDate: normalizedCheckIn } : undefined,
      )
      if (data) {
        fetchedRoom = data as Room
        resolvedRoom = fetchedRoom
      }
    } catch (err) {
      console.error('Failed to fetch room', err)
    }

    if (resolvedRoom) {
      store.setRoom(resolvedRoom)
      room.value = store.getRoom(roomUuid) || resolvedRoom
    } else {
      room.value = storedRoom || null
    }

    const propUuid =
      (route.query.property as string) ||
      (resolvedRoom ? pick(resolvedRoom, 'propertyUuid', 'property_uuid') : undefined)

    if (propUuid) {
      const storedProperty = store.getProperty(propUuid)
      let resolvedProperty: PropertyDetail | null = storedProperty || null
      try {
      const data = await getProperty(
        propUuid,
        normalizedCheckIn || checkOut.value
          ? { checkInDate: normalizedCheckIn || undefined, checkOutDate: checkOut.value || undefined }
          : undefined,
      )
        if (data) {
          resolvedProperty = data as PropertyDetail
        }
      } catch (err) {
        console.error('Failed to fetch property', err)
      }
      if (resolvedProperty) {
        store.setProperty(resolvedProperty)
        property.value = store.getProperty(propUuid) || resolvedProperty
      }
    }

    if (fetchedRoom) {
      lastPricingCheckIn.value = normalizedCheckIn || null
    } else if (!normalizedCheckIn) {
      lastPricingCheckIn.value = null
    }
  } catch (err) {
    console.error('Failed to load room', err)
    room.value = room.value || null
  } finally {
    loading.value = false
    initialLoadComplete.value = true
  }
}

async function refreshRoomPricing(force = false) {
  if (!room.value?.uuid) return
  const normalized = (checkIn.value || '').trim()
  const target = normalized ? normalized : null

  if (!force && target === lastPricingCheckIn.value) {
    return
  }

  pricingRequestToken += 1
  const currentToken = pricingRequestToken
  try {
    const updatedRoom = await getRoom(
      room.value.uuid,
      normalized ? { checkInDate: normalized } : undefined,
    )
    if (pricingRequestToken !== currentToken || !updatedRoom) {
      return
    }
    store.setRoom(updatedRoom)
    room.value = store.getRoom(room.value.uuid) || updatedRoom
    lastPricingCheckIn.value = target
  } catch (err) {
    console.error('Failed to refresh room pricing', err)
  }
}

function reserve() {
  if (!canReserve.value || !room.value) return
  const query: Record<string, string> = {
    room: room.value.uuid,
    checkIn: checkIn.value,
    checkOut: checkOut.value,
  }
  if (guests.value > 0) {
    query.guests = String(guests.value)
  }
  const propertyQuery = route.query.property as string | undefined
  const propertyUuid = propertyQuery || pick(room.value, 'propertyUuid', 'property_uuid')
  if (propertyUuid) {
    query.property = String(propertyUuid)
  }
  router.push({ path: '/payment', query })
}

function goBack() {
  if (history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

watch(
  () => checkIn.value,
  () => {
    if (!initialLoadComplete.value) return
    refreshRoomPricing()
  },
)

onMounted(load)
</script>

<style scoped>
.page {
  padding: 32px 0;
  background: #f9f5ee;
  min-height: 100vh;
  color: #2f261a;
}

.container {
  max-width: 980px;
  margin: 0 auto;
  padding: 0 20px;
}

.room-card {
  border-radius: 24px;
  background: #fffdf8;
  padding: 20px;
  box-shadow: 0 20px 50px rgba(33, 20, 6, 0.12);
}

.room-card.placeholder {
  text-align: center;
}

.room-hero {
  width: 100%;
  height: 380px;
  object-fit: cover;
  border-radius: 18px;
  margin-bottom: 18px;
}

.room-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.room-title h1 {
  font-size: 2.2rem;
  margin: 0 0 6px;
}

.subtitle {
  color: #6f563c;
  margin: 0;
}

.room-rating {
  text-align: right;
  min-width: 120px;
}

.room-rating .score {
  font-size: 1.8rem;
  font-weight: 700;
}

.room-rating .stars {
  color: #1f140a;
}

.room-tags {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin: 12px 0 4px;
}

.tag {
  background: #f1e4d2;
  border-radius: 12px;
  padding: 6px 12px;
  font-size: 0.9rem;
  color: #4a3a27;
}

.room-description {
  margin: 0 0 16px;
  color: #4a3a27;
}

.section-title {
  margin: 12px 0 8px;
  font-size: 1.25rem;
}

.amenities {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 6px 24px;
  margin-bottom: 16px;
}

.amenities ul {
  margin: 0;
  padding-left: 18px;
}

.booking-grid {
  display: grid;
  grid-template-columns: 1fr 1fr auto;
  gap: 12px;
  align-items: end;
  margin: 8px 0 12px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field input {
  padding: 10px 12px;
  border-radius: 10px;
  border: 1px solid rgba(125, 102, 71, 0.25);
  background: #fffaf2;
}

.reserve {
  padding: 12px 20px;
  border-radius: 12px;
  border: none;
  background: #201309;
  color: #fff9f0;
  font-weight: 700;
  cursor: pointer;
}

.reserve[disabled] {
  opacity: 0.6;
  cursor: not-allowed;
}

.booking-summary {
  font-weight: 600;
  color: #2f261a;
}

.address {
  color: #4a3a27;
}

@media (max-width: 720px) {
  .room-header {
    flex-direction: column;
    align-items: stretch;
  }

  .booking-grid {
    grid-template-columns: 1fr;
  }

  .amenities {
    grid-template-columns: 1fr;
  }
}
</style>
