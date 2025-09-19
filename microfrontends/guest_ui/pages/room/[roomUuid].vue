<template>
  <div class="page">
    <div class="container">
      <div class="card room-card">
        <img
          v-if="room?.images?.length && room.images[0].url"
          :src="room.images[0].url"
          :alt="`${room?.name || 'Room'} photo`"
          class="room-hero"
        />

        <div class="room-header">
          <div class="room-title">
            <h1>{{ room?.name || 'Room' }}</h1>
            <p class="subtitle" v-if="room?.description">{{ room.description }}</p>
          </div>
          <div class="room-rating" v-if="property?.averageRating != null">
            <div class="score">{{ Number(property.averageRating).toFixed(1) }}</div>
            <div class="stars">&#9733;&#9733;&#9733;&#9733;&#9734;</div>
          </div>
        </div>

        <div class="room-icons">
          <span v-if="hasAmenity('Free Wi-Fi')">📶 Free Wi‑Fi</span>
          <span>📺 TV</span>
          <span>💻 {{ roomArea }}</span>
          <span v-if="hasAmenity('Free Wi-Fi')">📶 Free Wi‑Fi</span>
        </div>

        <h3 class="section-title">Amenities</h3>
        <div class="amenities">
          <ul>
            <li v-for="(a, i) in leftAmenities" :key="`l-${i}`">{{ a.name }}</li>
          </ul>
          <ul>
            <li v-for="(a, i) in rightAmenities" :key="`r-${i}`">{{ a.name }}</li>
          </ul>
        </div>

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
          <button class="reserve" :disabled="!canReserve">Reserve</button>
        </form>

        <h3 class="section-title">Address</h3>
        <p class="address" v-if="property">
          {{ property.fullAddress || `${property.address}, ${property.city}${property.state ? ', ' + property.state : ''}, ${property.country}` }}
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useGuestBff } from '@/api/guestBff'
import type { Room } from '@/types/Room'
import type { PropertyDetail } from '@/types/PropertyDetail'
import { useSearchStore } from '@/stores/search'

const route = useRoute()
const router = useRouter()
const { getRoom, getProperty } = useGuestBff() as any
const store = useSearchStore()

const room = ref<Room | null>(null)
const property = ref<PropertyDetail | null>(null)
const checkIn = ref('')
const checkOut = ref('')
const guests = ref(2)

const canReserve = computed(() => !!checkIn.value && !!checkOut.value && guests.value > 0)
const roomArea = computed(() => '398 sq·ft')

const leftAmenities = computed(() => (room.value?.amenities || []).filter((_, i) => i % 2 === 0))
const rightAmenities = computed(() => (room.value?.amenities || []).filter((_, i) => i % 2 === 1))

function hasAmenity(name: string): boolean {
  return !!(room.value?.amenities || []).find(a => a.name.toLowerCase() === name.toLowerCase())
}

async function load() {
  const roomUuid = route.params.roomUuid as string
  if (!roomUuid) {
    router.replace('/')
    return
  }
  try {
    room.value = store.getRoom(roomUuid) || (typeof getRoom === 'function' ? await getRoom(roomUuid) : null)
    if (room.value) store.setRoom(room.value)

    const propUuid = (route.query.property as string) || (room.value as any)?.propertyUuid || (room.value as any)?.property_uuid
    if (propUuid) {
      property.value = store.getProperty(propUuid) || (typeof getProperty === 'function' ? await getProperty(propUuid) : null)
      if (property.value) store.setProperty(property.value)
    }
  } catch {
    router.replace('/')
  }
}

async function reserve() {
  alert('Reservation flow to implement')
}

onMounted(load)
</script>

<style scoped>
.page { padding: 32px 0; background: #f9f5ee; min-height: 100vh; color: #2f261a; }
.container { max-width: 980px; margin: 0 auto; padding: 0 20px; }
.room-card { border-radius: 24px; background: #fffdf8; padding: 20px; box-shadow: 0 20px 50px rgba(33,20,6,.12); }
.room-hero { width: 100%; height: 380px; object-fit: cover; border-radius: 18px; margin-bottom: 18px; }
.room-header { display: flex; align-items: start; justify-content: space-between; gap: 16px; }
.room-title h1 { font-size: 2.2rem; margin: 0 0 6px; }
.subtitle { color: #6f563c; margin: 0; }
.room-rating { text-align: right; min-width: 120px; }
.room-rating .score { font-size: 1.8rem; font-weight: 700; }
.room-rating .stars { color: #1f140a; }
.room-icons { display: flex; flex-wrap: wrap; gap: 14px 20px; padding: 14px 0 6px; color: #4a3a27; }
.section-title { margin: 12px 0 8px; font-size: 1.25rem; }
.amenities { display: grid; grid-template-columns: 1fr 1fr; gap: 6px 24px; margin-bottom: 16px; }
.amenities ul { margin: 0; padding-left: 18px; }
.booking-grid { display: grid; grid-template-columns: 1fr 1fr auto; gap: 12px; align-items: end; margin: 8px 0 18px; }
.field { display: flex; flex-direction: column; gap: 6px; }
.field input { padding: 10px 12px; border-radius: 10px; border: 1px solid rgba(125, 102, 71, 0.25); background: #fffaf2; }
.reserve { padding: 12px 20px; border-radius: 12px; border: none; background: #201309; color: #fff9f0; font-weight: 700; cursor: pointer; }
.address { color: #4a3a27; }
@media (max-width: 720px) {
  .room-header { flex-direction: column; align-items: stretch; }
  .booking-grid { grid-template-columns: 1fr; }
  .amenities { grid-template-columns: 1fr; }
}
</style>
