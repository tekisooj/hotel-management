<template>
  <div class="host-hotel">
    <div class="host-hotel__media">
      <img
        v-if="coverImage"
        :src="coverImage"
        :alt="`${hotel.name} photo`"
      />
      <span v-else>{{ initials }}</span>
    </div>
    <div class="host-hotel__body">
      <div class="host-hotel__header">
        <div>
          <h3 class="host-hotel__title">{{ hotel.name }}</h3>
          <p class="host-hotel__location">{{ locationLabel }}</p>
        </div>
        <span class="host-hotel__rating" v-if="averageRating !== null">
          {{ averageRating.toFixed(1) }} ?
        </span>
      </div>
      <p v-if="hotel.description" class="host-hotel__description">{{ hotel.description }}</p>
      <div class="host-hotel__stats">
        <span>{{ roomCount }} {{ roomCount === 1 ? 'room' : 'rooms' }}</span>
        <span v-if="hotel.stars">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" xmlns="http://www.w3.org/2000/svg">
            <path d="M12 3.5L14.4721 8.5129L20 9.23088L15.8 13.1352L16.9443 18.5L12 15.8129L7.05573 18.5L8.2 13.1352L4 9.23088L9.52786 8.5129L12 3.5Z" fill="#d28d2a"/>
          </svg>
          <span>{{ Number(hotel.stars).toFixed(1) }} stars</span>
        </span>
      </div>
      <div class="host-hotel__actions">
        <slot name="actions" :hotel="hotel"></slot>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { PropertyDetail } from 'types/PropertyDetail'

const props = defineProps<{ hotel: PropertyDetail }>()

const averageRating = computed(() => {
  const raw = (props.hotel as any).averageRating ?? (props.hotel as any).average_rating
  if (raw == null) return null
  const value = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(value) ? value : null
})

const roomCount = computed(() => (Array.isArray(props.hotel.rooms) ? props.hotel.rooms.length : 0))

const locationLabel = computed(() => {
  return [props.hotel.city, props.hotel.state, props.hotel.country].filter(Boolean).join(', ')
})

const coverImage = computed(() => props.hotel.images?.[0]?.url)

const initials = computed(() => {
  const name = props.hotel.name || props.hotel.address || 'P'
  return name.trim().slice(0, 2).toUpperCase()
})
</script>


