<template>
  <div class="page">
    <section class="search">
      <div class="search_overlay"></div>
      <div class="search_content">
        <div class="search_intro">
          <p class="search_text">Plan your next stay</p>
          <h1 class="search_title">Find your perfect hotel</h1>
        </div>
        <div class="search_card">
          <h3 class="search_card-title">Search</h3>
          <form class="search_form" @submit.prevent="submit">
            <location-search @selected="handleLocation" />

            <div class="search_row">
              <div class="search_field">
                <label class="search_label" for="check-in">Check-in</label>
                <input id="check-in" v-model="checkIn" type="date" class="search_input" />
              </div>
              <div class="search_field">
                <label class="search_label" for="check-out">Check-out</label>
                <input id="check-out" v-model="checkOut" type="date" class="search_input" />
              </div>
            </div>

            <div class="search_row">
              <div class="search_field">
                <label class="search_label" for="capacity">Guests</label>
                <input id="capacity" v-model="capacity" type="number" min="0" class="search_input" placeholder="2 adults" />
              </div>
              <div class="search_field">
                <label class="search_label" for="max-price">Max price</label>
                <input id="max-price" v-model="maxPrice" type="number" min="0" class="search_input" placeholder="$200" />
              </div>
            </div>

            <button class="search_submit" type="submit" :disabled="!canSearch">Find hotels</button>
          </form>
        </div>
      </div>
    </section>

    <section ref="resultsRef" class="results">
      <header class="results_header">
        <h2 class="results_title">Featured stays</h2>
        <p class="results_subtitle">
          Discover curated properties matched to your travel plans.
        </p>
      </header>
      <HotelList v-if="propertyDetails.length" :hotels="propertyDetails" />
      <p v-else class="results_empty">Start by setting your destination and dates to see available hotels.</p>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'
import { useGuestBff } from '@/api/guestBff'
import HotelList from '@/components/HotelList.vue'
import { useSearchStore } from '@/stores/search'

const { searchRooms } = useGuestBff()
const store = useSearchStore()
const country = ref('')
const city = ref('')
const state = ref('')
const checkIn = ref('')
const checkOut = ref('')
const capacity = ref(0)
const maxPrice = ref<number | undefined>(undefined)
const latitude = ref<number | null>(null)
const longitude = ref<number | null>(null)
const DEFAULT_SEARCH_RADIUS_KM = 50

const propertyDetails = ref<any[]>([])
const resultsRef = ref<HTMLElement | null>(null)

const hasCity = computed(() => city.value.trim().length > 0)
const hasCoordinates = computed(() => latitude.value !== null && longitude.value !== null)

const canSearch = computed(() => (hasCity.value || hasCoordinates.value) && !!checkIn.value && !!checkOut.value)


const handleLocation = (location: any) => {
  country.value = location.country || ''
  state.value = location.state || ''
  city.value = location.city || ''
  latitude.value = typeof location.latitude === 'number' ? location.latitude : null
  longitude.value = typeof location.longitude === 'number' ? location.longitude : null
};


async function submit() {
  if (!canSearch.value) return
  try {
    const capacityValue = Number(capacity.value)
    const hasCapacity = Number.isFinite(capacityValue) && capacityValue > 0
    const maxPriceValue = Number(maxPrice.value)
    const hasMaxPrice = Number.isFinite(maxPriceValue) && maxPriceValue > 0

    const res = await searchRooms({
      ...(country.value ? { country: country.value } : {}),
      ...(city.value ? { city: city.value } : {}),
      ...(state.value ? { state: state.value } : {}),
      ...(latitude.value !== null && longitude.value !== null
        ? {
            latitude: latitude.value,
            longitude: longitude.value,
            radius_km: DEFAULT_SEARCH_RADIUS_KM,
          }
        : {}),
      check_in_date: checkIn.value,
      check_out_date: checkOut.value,
      ...(hasCapacity ? { capacity: capacityValue } : {}),
      ...(hasMaxPrice ? { max_price: maxPriceValue } : {}),
    })
    store.setLastSearch({
      country: country.value || undefined,
      city: city.value || undefined,
      state: state.value || undefined,
      checkIn: checkIn.value || undefined,
      checkOut: checkOut.value || undefined,
      capacity: hasCapacity ? capacityValue : undefined,
      maxPrice: hasMaxPrice ? maxPriceValue : undefined,
      latitude: latitude.value ?? undefined,
      longitude: longitude.value ?? undefined,
      radiusKm: latitude.value !== null && longitude.value !== null ? DEFAULT_SEARCH_RADIUS_KM : undefined,
    })
    propertyDetails.value = Array.isArray(res) ? res : []

    if (Array.isArray(propertyDetails.value)) {
      store.ingestSearch(propertyDetails.value)
    }
    if (propertyDetails.value.length) {
      requestAnimationFrame(() => {
        resultsRef.value?.scrollIntoView({ behavior: 'smooth', block: 'start' })
      })
    }
  } catch {
    propertyDetails.value = []
  }
}

</script>

<style scoped>
.page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fef9f1 0%, #f9f1e7 45%, #f6efe6 100%);
  color: #2f261a;
}

.search {
  position: relative;
  min-height: 480px;
  display: flex;
  align-items: stretch;
  background-image: linear-gradient(120deg, rgba(20, 12, 4, 0.6), rgba(20, 12, 4, 0.35)),
    url('https://images.unsplash.com/photo-1582719478250-c89cae4dc85b?auto=format&fit=crop&w=1600&q=80');
  background-size: cover;
  background-position: center;
  border-bottom-left-radius: 48px;
  border-bottom-right-radius: 48px;
  overflow: hidden;
  margin-bottom: 80px;
}

.search_overlay {
  position: absolute;
  inset: 0;
  background: linear-gradient(110deg, rgba(19, 10, 2, 0.75) 0%, rgba(19, 10, 2, 0.2) 55%, rgba(19, 10, 2, 0.05) 100%);
}

.search_content {
  position: relative;
  z-index: 1;
  width: 100%;
  max-width: 1180px;
  margin: 0 auto;
  padding: 80px 32px 96px;
  display: flex;
  justify-content: space-between;
  gap: 48px;
  align-items: flex-start;
}

.search_intro {
  max-width: 520px;
  display: flex;
  flex-direction: column;
  gap: 20px;
  color: #fff7eb;
}

.search_text {
  text-transform: uppercase;
  letter-spacing: 0.32rem;
  font-size: 0.85rem;
  font-weight: 600;
  color: rgba(255, 251, 242, 0.8);
}

.search_title {
  font-size: clamp(2.4rem, 5vw, 3.8rem);
  font-weight: 700;
  line-height: 1.1;
  text-transform: uppercase;
}

.search_copy {
  max-width: 440px;
  font-size: 1.05rem;
  line-height: 1.6;
  color: rgba(255, 250, 244, 0.9);
}

.search_cta {
  align-self: flex-start;
  padding: 14px 28px;
  border-radius: 999px;
  border: none;
  background: linear-gradient(135deg, #ffb16f, #e2732d);
  color: #1f140a;
  font-weight: 700;
  letter-spacing: 0.04em;
  text-transform: uppercase;
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

.search_cta:hover {
  transform: translateY(-2px);
  box-shadow: 0 16px 30px rgba(0, 0, 0, 0.25);
}

.search_card {
  width: 360px;
  padding: 32px 28px;
  border-radius: 28px;
  background: rgba(255, 252, 246, 0.98);
  color: #2d2013;
  box-shadow: 0 30px 60px rgba(26, 11, 1, 0.35);
  backdrop-filter: blur(6px);
}

.search_card-title {
  font-size: 1.45rem;
  font-weight: 700;
  margin-bottom: 18px;
}

.search_form {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.search_label {
  font-size: 0.85rem;
  font-weight: 600;
  color: #7a5c3a;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.search_input {
  width: 80%;
  padding: 12px 14px;
  border-radius: 14px;
  border: 1px solid rgba(125, 102, 71, 0.25);
  background: rgba(255, 253, 248, 0.9);
  color: #271c11;
  transition: border 0.2s ease, box-shadow 0.2s ease;
}

.search_input:focus {
  outline: none;
  border-color: #e6a56d;
  box-shadow: 0 0 0 3px rgba(230, 165, 109, 0.35);
}

.search_row {
  display: flex;
  gap: 12px;
}

.search_field {
  flex: 1 1 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.search_submit {
  margin-top: 6px;
  padding: 14px 20px;
  border-radius: 18px;
  border: none;
  font-weight: 700;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #fff9f0;
  background: linear-gradient(135deg, #1f140a 0%, #3a2414 100%);
  cursor: pointer;
  transition: transform 0.2s ease, box-shadow 0.2s ease, opacity 0.2s ease;
}

.search_submit:disabled {
  opacity: 0.55;
  cursor: not-allowed;
}

.search_submit:not(:disabled):hover {
  transform: translateY(-1px);
  box-shadow: 0 12px 24px rgba(31, 20, 10, 0.35);
}

.results {
  position: relative;
  z-index: 2;
  max-width: 1180px;
  margin: -60px auto 80px;
  padding: 0 32px 32px;
}

.results_header {
  display: flex;
  flex-direction: column;
  gap: 8px;
  margin-bottom: 28px;
}

.results_title {
  font-size: 2rem;
  font-weight: 700;
  color: #3c2b1b;
}

.results_subtitle {
  color: #7a5e44;
  font-size: 1rem;
}

.results_empty {
  padding: 32px;
  border-radius: 20px;
  background: rgba(255, 253, 248, 0.95);
  box-shadow: 0 12px 30px rgba(44, 28, 13, 0.08);
  color: #6d5134;
}

:deep(.list-group) {
  display: flex;
  flex-direction: column;
  gap: 24px;
  border: none;
  background: transparent;
  padding: 0;
  margin: 0;
}

:deep(.list-group-item) {
  border: none;
  border-radius: 28px;
  padding: 26px 32px;
  background: rgba(255, 253, 246, 0.96);
  box-shadow: 0 16px 38px rgba(33, 20, 6, 0.08);
  transition: transform 0.2s ease, box-shadow 0.2s ease;
}

:deep(.list-group-item:hover) {
  transform: translateY(-4px);
  box-shadow: 0 22px 44px rgba(33, 20, 6, 0.16);
}

:deep(.list-group-item .d-flex img) {
  width: 185px;
  height: 140px;
  border-radius: 20px;
  object-fit: cover;
  box-shadow: 0 10px 18px rgba(18, 10, 3, 0.18);
}

:deep(.badge.bg-primary) {
  background: linear-gradient(135deg, #ffb16f, #e2732d) !important;
  color: #201309 !important;
  font-weight: 700;
  padding: 6px 10px;
}

@media (max-width: 1100px) {
  .search_content {
    flex-direction: column;
    align-items: stretch;
    gap: 36px;
  }

  .search_card {
    width: 100%;
    max-width: 420px;
  }

  .search_intro {
    max-width: none;
  }

  .search_row {
    flex-direction: column;
  }
}

@media (max-width: 640px) {
  .hero {
    border-bottom-left-radius: 24px;
    border-bottom-right-radius: 24px;
    margin-bottom: 10px;
  }

  .search_content {
    padding: 60px 20px;
  }

  .search_card {
    padding: 26px 22px;
    border-radius: 22px;
  }

  .results {
    margin: -30px auto 60px;
    padding: 0 20px 20px;
  }

  :deep(.list-group-item) {
    padding: 22px;
    border-radius: 22px;
  }

  :deep(.list-group-item .d-flex img) {
    width: 140px;
    height: 110px;
  }
}
</style>
