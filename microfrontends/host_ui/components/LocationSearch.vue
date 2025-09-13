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
        {{ result.label || result.Label }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRuntimeConfig } from '#imports'
import { useHostBff } from '@/api/hostBff'

const emit = defineEmits<{
  (e: 'selected', value): void
}>()

const query = ref('')
const results = ref<any[]>([])

const config = useRuntimeConfig()
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
