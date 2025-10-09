<template>
  <div class="host-location-search">
    <input
      v-model="query"
      @input="searchPlaces"
      type="text"
      placeholder="Search for a location"
    />
    <ul v-if="results.length" class="host-location-search__results">
      <li
        v-for="(result, index) in results"
        :key="index"
        @click="selectPlace(result)"
      >
        {{ result.label || result.Label }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useHostBff } from '@/api/hostBff'

const emit = defineEmits<{
  (e: 'selected', value): void
}>()

const query = ref('')
const results = ref<any[]>([])

const { searchPlaces: searchPlacesApi } = useHostBff()

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
</script>

<style scoped>
.host-location-search {
  position: relative;
}

.host-location-search input {
  width: 100%;
}

.host-location-search__results {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  list-style: none;
  margin: 0;
  padding: 8px 0;
  background: #fffdfa;
  border-radius: 16px;
  box-shadow: 0 18px 32px rgba(31, 20, 10, 0.16);
  border: 1px solid rgba(47, 38, 26, 0.08);
  max-height: 240px;
  overflow-y: auto;
  z-index: 10;
}

.host-location-search__results li {
  padding: 10px 16px;
  cursor: pointer;
  color: #4a3a27;
}

.host-location-search__results li:hover {
  background: rgba(255, 236, 215, 0.55);
}
</style>
