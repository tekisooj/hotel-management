<template>
  <div class="w-full max-w-md mx-auto mt-8">
    <input
      v-model="query"
      @input="searchPlaces"
      type="text"
      placeholder="Search for a location..."
      class="w-full border border-gray-300 rounded px-4 py-2"
    />

    <ul v-if="results.length" class="border rounded-b shadow bg-white mt-1">
      <li
        v-for="(result, index) in results"
        :key="index"
        @click="selectPlace(result)"
        class="px-4 py-2 cursor-pointer hover:bg-gray-100"
      >
        {{ result.label || result.Place?.Label }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useGuestBff } from '@/api/guestBff'
const emit = defineEmits<{
  (e: 'selected', value): void
}>()

const query = ref('')
const results = ref<any[]>([])
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
  // place already simplified by BFF
  const detail = {
    name: place.label || '',
    country: place.country || '',
    state: place.state || '',
    city: place.city || '',
    county: place.county || '',
    address: place.address || place.label || '',
    latitude: place.latitude,
    longitude: place.longitude,
  }

  emit('selected', detail)

  query.value = detail.name
  results.value = []
}
</script>
