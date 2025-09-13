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
        {{ result.Place.Label }}
      </li>
    </ul>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import {
  LocationClient,
  SearchPlaceIndexForTextCommand,
  SearchPlaceIndexForTextCommandOutput,
  Place,
} from '@aws-sdk/client-location'
import { fromCognitoIdentityPool } from '@aws-sdk/credential-providers'


const emit = defineEmits<{
  (e: 'selected', value): void
}>()

const region = 'us-east-1'
const placeIndexName = 'MyPlaceIndex'
const identityPoolId = 'us-east-1:xxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx'

const locationClient = new LocationClient({
  region,
  credentials: fromCognitoIdentityPool({
    clientConfig: { region },
    identityPoolId,
  }),
})

const query = ref('')
const results = ref<SearchPlaceIndexForTextCommandOutput['Results']>([])

const searchPlaces = async () => {
  if (query.value.trim().length < 3) {
    results.value = []
    return
  }

  try {
    const command = new SearchPlaceIndexForTextCommand({
      IndexName: placeIndexName,
      Text: query.value,
      MaxResults: 5,
    })

    const response = await locationClient.send(command)
    results.value = response.Results || []
  } catch (error) {
    console.error('Search failed:', error)
  }
}

const selectPlace = (result: { Place: Place }) => {
  const place = result.Place

  const detail = {
    name: place.Label || '',
    country: place.Country || '',
    state: place.Region || '',
    city: place.Municipality || '',
    county: place.SubRegion || '',
    address: place.AddressNumber && place.Street
      ? `${place.AddressNumber} ${place.Street}`
      : place.Street || place.Label || '',
    latitude: place.Geometry?.Point?.[1],
    longitude: place.Geometry?.Point?.[0],
  }

  emit('selected', detail)

  query.value = place.Label || ''
  results.value = []
}
</script>
