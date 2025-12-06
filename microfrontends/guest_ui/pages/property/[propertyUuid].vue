<template>
  <div class="property-page">
    <div v-if="loading" class="property-status">Loading property...</div>
    <div v-else-if="error" class="property-status">
      <p>{{ error }}</p>
      <button class="btn btn-outline-primary" @click="retry">Try again</button>
    </div>
    <div v-else-if="property" class="property-content">
      <button class="btn btn-link ps-0" @click="goBack">&larr; Back</button>

      <div v-if="heroImage" class="property-hero">
        <img :src="heroImage" :alt="`${property.name} photo`" />
      </div>

      <header class="property-header">
        <div>
          <h1>{{ property.name }}</h1>
          <p v-if="property.description" class="property-description">{{ property.description }}</p>
          <p class="property-location">
            {{ property.city }}<span v-if="property.state">, {{ property.state }}</span>, {{ property.country }}
          </p>
        </div>
        <div v-if="averageRating != null" class="property-rating">
          <div class="property-rating-score">{{ averageRating.toFixed(1) }}</div>
          <span class="property-rating-label">Guest score</span>
        </div>
      </header>

      <section class="property-info">
        <div class="property-map" v-if="property.latitude != null && property.longitude != null">
          <MiniMap :latitude="property.latitude" :longitude="property.longitude" />
        </div>
        <div class="property-address">
          <h2>Address</h2>
          <p>{{ propertyAddress }}</p>
        </div>
      </section>

      <section class="property-rooms">
        <div class="property-rooms-header">
          <h2>Available rooms</h2>
          <p v-if="!hasRooms" class="text-muted">No rooms match your current search.</p>
        </div>
        <Rooms v-if="hasRooms" :rooms="filteredRooms" :search-params="roomSearchParams" />
      </section>

      <section v-if="reviews.length" class="property-reviews">
        <h2>Recent reviews</h2>
        <ul>
          <li v-for="(review, index) in reviews.slice(0, 3)" :key="review.uuid || index">
            <strong>{{ review.rating }}/5</strong>
            <span v-if="review.comment"> - {{ review.comment }}</span>
          </li>
        </ul>
      </section>
    </div>
    <div v-else class="property-status">Property not found.</div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Rooms from '@/components/Rooms.vue'
import MiniMap from '@/components/MiniMap.vue'
import { useGuestBff } from '@/api/guestBff'
import { useSearchStore } from '@/stores/search'
import type { PropertyDetail } from '@/types/PropertyDetail'

const route = useRoute()
const router = useRouter()
const { getProperty, getPropertyReviews } = useGuestBff()
const store = useSearchStore()

const loading = ref(true)
const error = ref<string | null>(null)
const property = ref<PropertyDetail | null>(null)
const reviews = ref<any[]>([])

const propertyUuid = computed(() => String(route.params.propertyUuid || ''))
const queryCheckIn = computed(() => (route.query.checkIn as string) || (route.query.check_in as string) || '')
const queryCheckOut = computed(() => (route.query.checkOut as string) || (route.query.check_out as string) || '')
const queryGuests = computed(() => {
  const raw = (route.query.guests as string) || (route.query.capacity as string) || ''
  const numeric = Number(raw)
  return Number.isFinite(numeric) && numeric > 0 ? numeric : null
})

const averageRating = computed(() => {
  if (!property.value) return null
  const raw = (property.value as any).averageRating ?? (property.value as any).average_rating
  if (raw == null) return null
  const numeric = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(numeric) ? numeric : null
})

const heroImage = computed(() => property.value?.images?.[0]?.url || null)

const propertyAddress = computed(() => {
  if (!property.value) return ''
  return (
    property.value.fullAddress ||
    [property.value.address, property.value.city, property.value.state, property.value.country]
      .filter(Boolean)
      .join(', ')
  )
})

const roomSearchParams = computed(() => ({
  checkIn: queryCheckIn.value || store.lastSearch?.checkIn,
  checkOut: queryCheckOut.value || store.lastSearch?.checkOut,
  guests: queryGuests.value ?? store.lastSearch?.capacity,
}))

const filteredRooms = computed(() => {
  const rooms = property.value?.rooms || []
  const guests = roomSearchParams.value.guests
  if (guests && guests > 0) {
    return rooms.filter((room) => {
      const capacity = Number((room as any).capacity)
      return Number.isFinite(capacity) ? capacity >= guests : true
    })
  }
  return rooms
})

const hasRooms = computed(() => filteredRooms.value.length > 0)

async function loadProperty() {
  const uuid = propertyUuid.value
  if (!uuid) {
    router.replace('/')
    return
  }
  loading.value = true
  let fetchError: any = null
    try {
      const fromStore = store.getProperty(uuid)
      if (fromStore) {
        property.value = fromStore
      }
      const searchParams = roomSearchParams.value
      const fetched = await getProperty(uuid, {
        checkInDate: searchParams.checkIn,
        checkOutDate: searchParams.checkOut,
        capacity: searchParams.guests ?? undefined,
      })
    if (fetched) {
      store.setProperty(fetched)
      property.value = store.getProperty(uuid) || fetched
    } else if (!property.value) {
      throw new Error('Missing property data')
    }
    try {
      reviews.value = await getPropertyReviews(uuid)
    } catch {
      reviews.value = []
    }
  } catch (err: any) {
    fetchError = err
  } finally {
    loading.value = false
  }
  if (fetchError && !property.value) {
    error.value = fetchError?.message || 'Unable to load this property right now.'
  } else {
    error.value = null
  }
}

function goBack() {
  if (history.length > 1) {
    router.back()
  } else {
    router.push('/')
  }
}

function retry() {
  loadProperty()
}

watch(
  () => propertyUuid.value,
  () => {
    loadProperty()
  },
  { immediate: true }
)
</script>

<style scoped>
.property-page {
  min-height: 100vh;
  background: #f9f5ee;
  padding: 32px 0;
}

.property-status {
  max-width: 960px;
  margin: 0 auto;
  padding: 48px 20px;
  text-align: center;
  color: #3b2a18;
}

.property-content {
  max-width: 960px;
  margin: 0 auto;
  padding: 0 20px 40px;
  color: #2f261a;
}

.property-hero {
  margin: 16px 0 32px;
  border-radius: 20px;
  overflow: hidden;
  box-shadow: 0 18px 40px rgba(40, 24, 10, 0.18);
}

.property-hero img {
  width: 100%;
  height: 320px;
  object-fit: cover;
  display: block;
}

.property-header {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  align-items: flex-start;
}

.property-header h1 {
  margin: 0 0 12px;
  font-size: 2.2rem;
}

.property-description {
  margin: 0 0 12px;
  color: #6f563c;
}

.property-location {
  margin: 0;
  color: #846447;
}

.property-rating {
  text-align: right;
  min-width: 120px;
}

.property-rating-score {
  font-size: 2rem;
  font-weight: 700;
}

.property-rating-label {
  color: #6f563c;
}

.property-info {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 24px;
  margin: 32px 0;
}

.property-map :deep(.mini-map) {
  border-radius: 16px;
  overflow: hidden;
}

.property-address h2,
.property-rooms h2,
.property-reviews h2 {
  font-size: 1.5rem;
  margin-bottom: 12px;
}

.property-rooms {
  margin-top: 12px;
}

.property-reviews ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.property-reviews li {
  background: #fffdf8;
  border-radius: 14px;
  padding: 12px 16px;
  box-shadow: 0 12px 28px rgba(40, 24, 10, 0.12);
}

@media (max-width: 768px) {
  .property-header {
    flex-direction: column;
    align-items: stretch;
  }

  .property-info {
    grid-template-columns: 1fr;
  }
}
</style>
