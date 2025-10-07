<template>
  <div v-if="rooms && rooms.length" :id="carouselId" class="carousel slide" data-bs-ride="carousel">
    <div class="carousel-indicators" v-if="rooms.length > 1">
      <button
        v-for="(r, i) in rooms"
        :key="r.uuid || i"
        type="button"
        :data-bs-target="'#' + carouselId"
        :data-bs-slide-to="i"
        :class="{ active: i === 0 }"
        :aria-current="i === 0 ? 'true' : undefined"
        :aria-label="`Slide ${i + 1}`"
      ></button>
    </div>

    <div class="carousel-inner">
      <div
        v-for="(room, index) in rooms"
        :key="room.uuid || index"
        :class="['carousel-item', { active: index === 0 }]"
      >
        <RouterLink
          v-if="room.uuid"
          :to="roomLink(room)"
          class="text-decoration-none text-reset room-link"
        >
          <div class="card">
            <img
              v-if="room.images?.length && room.images[0].url"
              :src="room.images[0].url"
              :alt="`${room.name} photo`"
              class="card-img-top object-fit-cover"
              style="height: 180px;"
            />
            <div class="card-body">
              <h5 class="card-title mb-1">{{ room.name }}</h5>
              <small class="text-muted">Type: {{ roomType(room) }} - Capacity: {{ room.capacity }}</small>
              <p class="card-text mt-2" v-if="room.description">{{ room.description }}</p>
              <div class="d-flex align-items-center gap-2 mt-2">
                <span class="badge bg-success">
                  ${{ formatPrice(pricePerNight(room)) }}
                </span>
                <small class="text-muted" v-if="minPrice(room) != null && maxPrice(room) != null">
                  (min: ${{ formatPrice(minPrice(room)) }}, max: ${{ formatPrice(maxPrice(room)) }})
                </small>
              </div>
              <div class="mt-2" v-if="room.amenities?.length">
                <span class="badge bg-secondary me-1" v-for="(a, i) in room.amenities" :key="i">{{ a.name }}</span>
              </div>
            </div>
          </div>
        </RouterLink>
        <div v-else class="card">
          <div class="card-body">
            <h5 class="card-title mb-1">{{ room.name || 'Room' }}</h5>
            <p class="text-muted mb-0">Room is missing an identifier.</p>
          </div>
        </div>
      </div>
    </div>

    <button class="carousel-control-prev" type="button" :data-bs-target="'#' + carouselId" data-bs-slide="prev" v-if="rooms.length > 1">
      <span class="carousel-control-prev-icon" aria-hidden="true"></span>
      <span class="visually-hidden">Previous</span>
    </button>
    <button class="carousel-control-next" type="button" :data-bs-target="'#' + carouselId" data-bs-slide="next" v-if="rooms.length > 1">
      <span class="carousel-control-next-icon" aria-hidden="true"></span>
      <span class="visually-hidden">Next</span>
    </button>
  </div>
  <p v-else class="text-muted m-0">No rooms to display.</p>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { Room } from '@/types/Room'

type SearchParams = {
  checkIn?: string
  checkOut?: string
  guests?: number
}

const props = defineProps<{ rooms: Room[]; id?: string; searchParams?: SearchParams }>()

const carouselId = computed(() => props.id || `rooms-carousel-${Math.random().toString(36).slice(2, 8)}`)

function pick(room: any, camel: string, snake: string) {
  if (!room) return undefined
  const camelValue = room[camel]
  if (camelValue !== undefined && camelValue !== null && camelValue !== '') return camelValue
  const snakeValue = room[snake]
  if (snakeValue !== undefined && snakeValue !== null && snakeValue !== '') return snakeValue
  return undefined
}

function roomType(room: any) {
  return pick(room, 'roomType', 'room_type') || 'Room'
}

function pricePerNight(room: any) {
  return pick(room, 'pricePerNight', 'price_per_night')
}

function minPrice(room: any) {
  return pick(room, 'minPricePerNight', 'min_price_per_night')
}

function maxPrice(room: any) {
  return pick(room, 'maxPricePerNight', 'max_price_per_night')
}

function formatPrice(value: any): string {
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return '--'
  return Number.isInteger(num) ? String(num) : num.toFixed(2)
}

function roomLink(room: any) {
  const propertyUuid = pick(room, 'propertyUuid', 'property_uuid')
  if (!room?.uuid) {
    return '/'
  }
  const query: Record<string, string> = {}
  if (propertyUuid) query.property = String(propertyUuid)
  if (props.searchParams?.checkIn) query.checkIn = props.searchParams.checkIn
  if (props.searchParams?.checkOut) query.checkOut = props.searchParams.checkOut
  if (props.searchParams?.guests) query.guests = String(props.searchParams.guests)
  return { path: `/room/${room.uuid}`, query }
}
</script>

<style scoped>
.room-link {
  display: block;
}
</style>

