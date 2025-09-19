<template>
  <div class="location-search" ref="root">
    <label class="location-search_label" for="location-input">Location</label>
    <div class="location-search_field">
      <svg class="location-search_icon" viewBox="0 0 24 24" aria-hidden="true">
        <path
          d="M15.5 14h-.79l-.28-.27a6.471 6.471 0 0 0 1.57-4.23A6.5 6.5 0 0 0 9.5 3a6.5 6.5 0 0 0-6.49 6.5A6.5 6.5 0 0 0 9.5 16c1.61 0 3.09-.59 4.23-1.57l.27.28v.79l4.99 5L21 19l-5-4.99Zm-6 0A4.5 4.5 0 0 1 5 9.5 4.5 4.5 0 0 1 9.5 5a4.5 4.5 0 0 1 4.5 4.5A4.5 4.5 0 0 1 9.5 14Z"
        />
      </svg>
      <input
        id="location-input"
        v-model="query"
        @input="searchPlaces"
        type="text"
        placeholder="Where are you headed?"
        class="location-search_input"
      />
    </div>

    <transition name="location-search_fade">
      <ul v-if="results.length" class="location-search_dropdown" role="listbox">
        <li
          v-for="(result, index) in results"
          :key="index"
          @click="selectPlace(result)"
          class="location-search_option"
          role="option"
        >
          <span class="location-search_option-title">{{ result.label || result.Label }}</span>
          <span class="location-search_option-sub">
            {{ formatLocation(result) }}
          </span>
        </li>
      </ul>
    </transition>
  </div>
</template>

<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { useGuestBff } from '@/api/guestBff'

const emit = defineEmits<{ (e: 'selected', value: any): void }>()

const query = ref('')
const results = ref<any[]>([])
const root = ref<HTMLElement | null>(null)

const { searchPlaces: searchPlacesApi } = useGuestBff()

const searchPlaces = async () => {
  if (query.value.trim().length < 3) {
    results.value = []
    return
  }

  try {
    const data = await searchPlacesApi(query.value)
    results.value = Array.isArray(data) ? data : []
  } catch (error) {
    console.error('Search failed:', error)
  }
}

const selectPlace = (place: any) => {
  const detail = {
    name: place.label || '',
    country: place.country || '',
    state: place.state || '',
    city: place.city || '',
    county: place.county || '',
    address: place.address || place.label || '',
    latitude: place.latitude,
    longitude: place.longitude,
    placeId: place.place_id,
  }

  emit('selected', detail)
  query.value = detail.name
  results.value = []
}

function formatLocation(place: any): string {
  const parts = [place.city, place.state, place.country].filter(Boolean)
  return parts.join(', ')
}

function handleClickOutside(event: MouseEvent) {
  if (root.value && !root.value.contains(event.target as Node)) {
    results.value = []
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onBeforeUnmount(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<style scoped>
.location-search {
  width: 100%;
  max-width: 420px;
  display: flex;
  flex-direction: column;
  gap: 10px;
  position: relative;
}

.location-search_label {
  font-size: 0.85rem;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.08em;
  color: #7a5c3a;
}

.location-search_field {
  position: relative;
  border-radius: 18px;
  border: 1px solid rgba(125, 102, 71, 0.2);
  background: rgba(255, 253, 246, 0.96);
  box-shadow: 0 10px 28px rgba(33, 20, 6, 0.12);
  overflow: hidden;
  transition: box-shadow 0.2s ease, border-color 0.2s ease;
}

.location-search_field:focus-within {
  border-color: #e6a56d;
  box-shadow: 0 16px 36px rgba(230, 165, 109, 0.28);
}

.location-search_icon {
  position: absolute;
  left: 16px;
  top: 50%;
  transform: translateY(-50%);
  width: 20px;
  height: 20px;
  fill: rgba(122, 92, 58, 0.75);
  pointer-events: none;
}

.location-search_input {
  width: 100%;
  padding: 14px 18px 14px 48px;
  border: none;
  background: transparent;
  color: #2d2013;
  font-size: 1rem;
}

.location-search_input::placeholder {
  color: rgba(122, 92, 58, 0.55);
}

.location-search_input:focus {
  outline: none;
}

.location-search_dropdown {
  position: absolute;
  top: 100%;
  left: 0;
  right: 0;
  margin-top: 10px;
  border-radius: 18px;
  background: rgba(255, 252, 245, 0.98);
  box-shadow: 0 24px 48px rgba(25, 14, 4, 0.22);
  list-style: none;
  padding: 8px 0;
  max-height: 280px;
  overflow-y: auto;
  border: 1px solid rgba(125, 102, 71, 0.15);
  backdrop-filter: blur(4px);
  z-index: 20;
}

.location-search_option {
  display: flex;
  flex-direction: column;
  gap: 4px;
  padding: 12px 20px;
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.location-search_option:hover {
  background: rgba(230, 165, 109, 0.15);
}

.location-search_option-title {
  font-weight: 600;
  color: #3c2b1b;
}

.location-search_option-sub {
  font-size: 0.85rem;
  color: rgba(60, 43, 27, 0.65);
}

.location-search_fade-enter-active,
.location-search_fade-leave-active {
  transition: opacity 0.18s ease, transform 0.18s ease;
}

.location-search_fade-enter-from,
.location-search_fade-leave-to {
  opacity: 0;
  transform: translateY(-4px);
}
</style>
