<template>
  <div class="host-property" v-if="!loadError && property">
    <header class="host-property__header">
      <div>
        <p class="host-property__eyebrow">Property overview</p>
        <h1 class="host-property__title">{{ property.name }}</h1>
        <p class="host-property__location">{{ locationLabel }}</p>
      </div>
      <div class="host-property__summary" v-if="averageRating !== null">
        <span class="host-property__score">{{ averageRating.toFixed(1) }}</span>
        <span class="host-property__score-label">Guest score</span>
      </div>
    </header>

    <section class="host-property__details">
      <div class="host-property__gallery" v-if="images.length">
        <img
          v-for="(image, index) in images"
          :key="index"
          :src="image.url"
          :alt="`${property.name} image ${index + 1}`"
        />
      </div>
      <div class="host-property__gallery host-property__gallery--empty" v-else>
        <span>{{ initials }}</span>
      </div>

      <article class="host-property__card">
        <h2>Property overview</h2>
        <p v-if="property.description">{{ property.description }}</p>
        <p v-else>This property does not have a description yet.</p>

        <ul class="host-property__facts">
          <li>
            <strong>Rooms:</strong>
            <span>{{ roomCount }}</span>
          </li>
          <li v-if="property.stars">
            <strong>Rating:</strong>
            <span>{{ Number(property.stars).toFixed(1) }} stars</span>
          </li>
          <li v-if="averageRating !== null">
            <strong>Guest reviews:</strong>
            <span>{{ averageRating.toFixed(1) }} average score</span>
          </li>
          <li v-if="property.phone">
            <strong>Phone:</strong>
            <span>{{ property.phone }}</span>
          </li>
          <li v-if="property.email">
            <strong>Email:</strong>
            <span>{{ property.email }}</span>
          </li>
        </ul>
      </article>
    </section>

    <section class="host-property__rooms">
      <header>
        <h2>Rooms</h2>
        <p v-if="!rooms.length">No rooms created for this property yet.</p>
      </header>
      <ul v-if="rooms.length" class="host-property__room-list">
        <li v-for="room in rooms" :key="room.uuid || room.name">
          <h3>{{ room.name }}</h3>
          <p class="host-property__room-meta">{{ room.capacity }} guests - ${{ formatPrice(room.price_per_night) }} per night</p>
          <p v-if="room.description">{{ room.description }}</p>
        </li>
      </ul>
    </section>
  </div>
  <p v-else-if="loadError" class="host-property__empty">{{ loadError }}</p>
  <p v-else class="host-property__empty">Loading property details...</p>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { useHostBff } from '@/api/hostBff'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { Room } from '@/types/Room'

definePageMeta({
  layout: 'default',
})

const route = useRoute()
const { getProperty } = useHostBff()

const property = ref<PropertyDetail | null>(null)
const rooms = ref<Room[]>([])
const loadError = ref<string | null>(null)

const averageRating = computed(() => {
  const raw = (property.value as any)?.averageRating ?? (property.value as any)?.average_rating
  if (raw == null) return null
  const value = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(value) ? value : null
})

const roomCount = computed(() => rooms.value.length)

const locationLabel = computed(() => {
  if (!property.value) return ''
  return [property.value.city, property.value.state, property.value.country].filter(Boolean).join(', ')
})

const images = computed(() => property.value?.images ?? [])

const initials = computed(() => {
  const name = property.value?.name || property.value?.address || 'P'
  return name ? name.trim().slice(0, 2).toUpperCase() : 'P'
})

function formatPrice(raw: number | string | null | undefined) {
  if (raw == null) return '0.00'
  const value = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(value) ? value.toFixed(2) : '0.00'
}

async function loadProperty(uuid: string) {
  const normalized = uuid.trim()
  if (!normalized) {
    loadError.value = 'Missing property identifier.'
    property.value = null
    rooms.value = []
    return
  }
  loadError.value = null
  property.value = null
  rooms.value = []
  try {
    const detail = await getProperty(normalized)
    property.value = detail
    rooms.value = Array.isArray(detail?.rooms) ? detail.rooms : []
  } catch (error: any) {
    const detailMessage =
      error?.response?.data?.detail ??
      error?.data?.detail ??
      error?.message ??
      ''
    loadError.value = detailMessage && typeof detailMessage === 'string'
      ? detailMessage
      : 'Unable to load property details.'
  }
}

onMounted(() => {
  const current = typeof route.params.id === 'string' ? route.params.id : ''
  loadProperty(current)
})

watch(
  () => route.params.id,
  (next) => {
    if (typeof next === 'string') {
      loadProperty(next)
    }
  },
)
</script>

<style scoped>
.host-property {
  min-height: 100vh;
  padding: 40px 32px 80px;
  max-width: 1180px;
  margin: 0 auto;
}

.host-property__header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 32px;
}

.host-property__eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.18em;
  font-size: 0.72rem;
  color: #b48a56;
  margin-bottom: 8px;
}

.host-property__title {
  font-size: 2.5rem;
  font-weight: 700;
  margin: 0;
  color: #2d1f12;
}

.host-property__location {
  color: #775c3b;
  margin-top: 8px;
}

.host-property__summary {
  display: flex;
  flex-direction: column;
  align-items: center;
  background: rgba(255, 248, 236, 0.94);
  padding: 18px 22px;
  border-radius: 18px;
  box-shadow: 0 12px 32px rgba(44, 30, 16, 0.12);
}

.host-property__score {
  font-size: 2rem;
  font-weight: 700;
  color: #e18734;
}

.host-property__score-label {
  font-size: 0.85rem;
  color: #6d5134;
}

.host-property__details {
  display: grid;
  grid-template-columns: minmax(0, 2fr) minmax(320px, 1fr);
  gap: 32px;
}

.host-property__gallery {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(240px, 1fr));
  gap: 18px;
}

.host-property__gallery img {
  width: 100%;
  height: 180px;
  object-fit: cover;
  border-radius: 18px;
  box-shadow: 0 12px 24px rgba(36, 25, 14, 0.18);
}

.host-property__gallery--empty {
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 240px;
  background: rgba(255, 249, 240, 0.9);
  border-radius: 18px;
  font-size: 3rem;
  color: #c58a45;
}

.host-property__card {
  background: #fffaf3;
  border-radius: 20px;
  padding: 28px;
  box-shadow: 0 16px 40px rgba(38, 26, 15, 0.12);
}

.host-property__card h2 {
  margin-top: 0;
  margin-bottom: 16px;
}

.host-property__facts {
  list-style: none;
  padding: 0;
  margin: 0;
  display: grid;
  gap: 12px;
}

.host-property__facts li {
  display: flex;
  gap: 8px;
}

.host-property__facts strong {
  color: #5d442a;
}

.host-property__rooms {
  margin-top: 48px;
}

.host-property__room-list {
  list-style: none;
  margin: 0;
  padding: 0;
  display: grid;
  gap: 24px;
}

.host-property__room-list li {
  padding: 24px;
  border-radius: 20px;
  background: rgba(255, 252, 246, 0.96);
  box-shadow: 0 12px 32px rgba(31, 20, 10, 0.1);
}

.host-property__room-meta {
  margin: 6px 0 12px;
  color: #86653f;
}

.host-property__empty {
  text-align: center;
  padding: 60px 20px;
  color: #856742;
}

@media (max-width: 960px) {
  .host-property__details {
    grid-template-columns: 1fr;
  }

  .host-property__header {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>