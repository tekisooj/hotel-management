<template>
  <div v-if="roomsList.length" class="rooms-carousel">
    <div class="rooms-carousel__viewport" role="group" :aria-label="`Room ${currentIndex + 1} of ${roomsList.length}`">
      <div
        class="rooms-carousel__track"
        :style="{ transform: `translateX(-${currentIndex * 100}%)`, width: `${roomsList.length * 100}%` }"
      >
        <RouterLink
          v-for="room in roomsList"
          :key="room.uuid || room.name"
          :to="roomLink(room)"
          class="rooms-carousel__slide"
        >
          <article class="rooms-card">
            <div class="rooms-card__media">
              <img
                v-if="room.images?.length && room.images[0].url"
                :src="room.images[0].url"
                :alt="`${room.name} photo`"
              />
              <div v-else class="rooms-card__media--fallback">{{ roomInitials(room) }}</div>
            </div>
            <div class="rooms-card__body">
              <header class="rooms-card__header">
                <h3 class="rooms-card__title">{{ room.name }}</h3>
                <span class="rooms-card__badge">${{ formatPrice(pricePerNight(room)) }}/night</span>
              </header>
              <p v-if="room.description" class="rooms-card__description">{{ room.description }}</p>
              <dl class="rooms-card__meta">
                <div>
                  <dt>Type</dt>
                  <dd>{{ roomType(room) }}</dd>
                </div>
                <div>
                  <dt>Guests</dt>
                  <dd>{{ room.capacity }}</dd>
                </div>
                <div v-if="minPrice(room) != null && maxPrice(room) != null">
                  <dt>Price range</dt>
                  <dd>${{ formatPrice(minPrice(room)) }} - ${{ formatPrice(maxPrice(room)) }}</dd>
                </div>
              </dl>
              <div v-if="room.amenities?.length" class="rooms-card__amenities">
                <span
                  v-for="(amenity, idx) in room.amenities"
                  :key="idx"
                  class="rooms-card__tag"
                >
                  {{ amenity.name }}
                </span>
              </div>
            </div>
          </article>
        </RouterLink>
      </div>
      <button
        v-if="roomsList.length > 1"
        class="rooms-carousel__nav rooms-carousel__nav--prev"
        type="button"
        aria-label="Previous room"
        @click="prevRoom"
      >
        ‹
      </button>
      <button
        v-if="roomsList.length > 1"
        class="rooms-carousel__nav rooms-carousel__nav--next"
        type="button"
        aria-label="Next room"
        @click="nextRoom"
      >
        ›
      </button>
    </div>

    <div v-if="roomsList.length > 1" class="rooms-carousel__dots" role="tablist">
      <button
        v-for="(room, index) in roomsList"
        :key="room.uuid || `dot-${index}`"
        class="rooms-carousel__dot"
        type="button"
        :aria-label="`Show room ${index + 1}`"
        :aria-current="currentIndex === index ? 'true' : 'false'"
        :class="{ 'rooms-carousel__dot--active': currentIndex === index }"
        @click="goTo(index)"
      ></button>
    </div>
  </div>
  <p v-else class="rooms-carousel__empty">No rooms to display.</p>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Room } from '@/types/Room'

type SearchParams = {
  checkIn?: string
  checkOut?: string
  guests?: number
}

const props = defineProps<{ rooms: Room[]; id?: string; searchParams?: SearchParams }>()

const roomsList = computed(() => props.rooms || [])
const currentIndex = ref(0)

watch(roomsList, (list) => {
  if (!list.length) {
    currentIndex.value = 0
  } else if (currentIndex.value >= list.length) {
    currentIndex.value = 0
  }
})

function goTo(index: number) {
  if (!roomsList.value.length) return
  const length = roomsList.value.length
  currentIndex.value = (index + length) % length
}

function nextRoom() {
  goTo(currentIndex.value + 1)
}

function prevRoom() {
  goTo(currentIndex.value - 1)
}

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

function roomInitials(room: any): string {
  const name = (room.name || 'Room').trim()
  return name.slice(0, 2).toUpperCase()
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
.rooms-carousel {
  position: relative;
  background: rgba(255, 253, 248, 0.95);
  border-radius: 28px;
  padding: 32px 28px 40px;
  box-shadow: 0 22px 44px rgba(39, 24, 11, 0.14);
  border: 1px solid rgba(39, 24, 11, 0.05);
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.rooms-carousel__viewport {
  position: relative;
  overflow: hidden;
  border-radius: 24px;
}

.rooms-carousel__track {
  display: flex;
  transition: transform 0.45s cubic-bezier(0.22, 0.61, 0.36, 1);
  height: 100%;
}

.rooms-carousel__slide {
  flex: 0 0 100%;
  padding: 4px;
  text-decoration: none;
  color: inherit;
}

.rooms-card {
  background: linear-gradient(135deg, rgba(255, 245, 228, 0.85), rgba(255, 237, 215, 0.85));
  border-radius: 24px;
  overflow: hidden;
  display: flex;
  flex-direction: column;
  min-height: 100%;
  border: 1px solid rgba(255, 205, 166, 0.4);
  box-shadow: 0 20px 40px rgba(46, 27, 13, 0.12);
}

.rooms-card__media {
  position: relative;
  height: 220px;
  background: rgba(255, 238, 213, 0.7);
  display: flex;
  align-items: center;
  justify-content: center;
}

.rooms-card__media img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}

.rooms-card__media--fallback {
  font-size: 2rem;
  font-weight: 700;
  color: rgba(65, 40, 18, 0.6);
}

.rooms-card__body {
  padding: 26px 26px 28px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.rooms-card__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
}

.rooms-card__title {
  margin: 0;
  font-size: 1.4rem;
}

.rooms-card__badge {
  background: rgba(29, 15, 5, 0.08);
  color: #2f1a0b;
  border-radius: 999px;
  padding: 6px 14px;
  font-weight: 600;
  font-size: 0.9rem;
}

.rooms-card__description {
  margin: 0;
  color: #6f563c;
  line-height: 1.45;
}

.rooms-card__meta {
  display: flex;
  flex-wrap: wrap;
  gap: 12px 32px;
  margin: 0;
}

.rooms-card__meta dt {
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: rgba(47, 34, 20, 0.6);
  margin-bottom: 4px;
}

.rooms-card__meta dd {
  margin: 0;
  color: #2f261a;
  font-weight: 600;
}

.rooms-card__amenities {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
}

.rooms-card__tag {
  background: rgba(255, 244, 231, 0.9);
  border-radius: 999px;
  padding: 6px 12px;
  font-size: 0.85rem;
  color: #513a20;
}

.rooms-carousel__nav {
  position: absolute;
  top: 50%;
  transform: translateY(-50%);
  width: 42px;
  height: 42px;
  border-radius: 50%;
  border: none;
  background: rgba(255, 251, 245, 0.95);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.12);
  color: #362213;
  font-size: 1.6rem;
  font-weight: 500;
  cursor: pointer;
}

.rooms-carousel__nav:focus-visible {
  outline: 3px solid rgba(222, 124, 50, 0.45);
}

.rooms-carousel__nav--prev {
  left: 16px;
}

.rooms-carousel__nav--next {
  right: 16px;
}

.rooms-carousel__dots {
  display: flex;
  justify-content: center;
  gap: 10px;
  margin-top: 6px;
}

.rooms-carousel__dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  border: none;
  background: rgba(101, 74, 51, 0.25);
  cursor: pointer;
}

.rooms-carousel__dot--active {
  background: #d47b34;
}

.rooms-carousel__empty {
  margin: 0;
  color: #6f563c;
}

@media (max-width: 640px) {
  .rooms-carousel {
    padding: 24px 18px 32px;
  }
  .rooms-card__media {
    height: 200px;
  }
}
</style>
