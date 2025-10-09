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
        <div class="card">
          <img
            v-if="room.images?.length && room.images[0]?.url"
            :src="room.images?.[0]?.url"
            :alt="`${room.name} photo`"
            class="card-img-top object-fit-cover"
            style="height: 180px;"
          />
          <div class="card-body">
            <h5 class="card-title mb-1">{{ room.name }}</h5>
            <small class="text-muted">Type: {{ room.room_type }} - Capacity: {{ room.capacity }}</small>
            <p class="card-text mt-2" v-if="room.description">{{ room.description }}</p>
            <div class="d-flex align-items-center gap-2 mt-2">
              <span class="badge bg-success">${{ room.price_per_night }}</span>
              <small class="text-muted" v-if="room.min_price_per_night && room.max_price_per_night">
                (min: ${{ room.min_price_per_night }}, max: ${{ room.max_price_per_night }})
              </small>
            </div>
            <div class="mt-2" v-if="room.amenities?.length">
              <span class="badge bg-secondary me-1" v-for="(a, i) in room.amenities" :key="i">{{ a.name }}</span>
            </div>
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

const props = defineProps<{ rooms: Room[]; id?: string }>()
const carouselId = computed(() => props.id || `rooms-carousel-${Math.random().toString(36).slice(2, 8)}`)
</script>

