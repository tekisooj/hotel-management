<template>
  <form class="row g-2 align-items-end" @submit.prevent="submit">
    <location-search @selected="handleLocation">

    </location-search>
    <div class="col-md-2">
      <label class="form-label">Check-in</label>
      <input v-model="checkIn" type="date" class="form-control" />
    </div>
    <div class="col-md-2">
      <label class="form-label">Check-out</label>
      <input v-model="checkOut" type="date" class="form-control" />
    </div>
    <div class="col-12 mt-2">
      <button class="btn btn-primary" @click="submit" :disabled="!canSearch">Search</button>
    </div>
  </form>
</template>

<script setup lang="ts">
import { computed, ref } from 'vue'


const checkIn = ref('')
const checkOut = ref('')
var name = ref('')
var country = ref('')
var state = ref('')
var city = ref('')
var county = ref('')
var address = ref('')
var latitude = ref(undefined)
var longitude = ref(undefined)

const emit = defineEmits<{
  (e: 'search', payload: { country: string; city: string; state?: string; check_in_date: string; check_out_date: string }): void
}>()

const handleLocation = (location) =>
{
  name.value = location.value;
  country.value = location.value;
  state.value = location.value;
  city.value = location.value;
  county.value = location.value;
  address.value = location.value;
  latitude.value = location.value;
  longitude.value = location.value;
}

const canSearch = computed(() => !!country.value && !!city.value && !!checkIn.value && !!checkOut.value)

function submit() {
  if (!canSearch.value) return
  emit('search', {
    country: country.value,
    city: city.value,
    state: state.value || undefined,
    check_in_date: checkIn.value,
    check_out_date: checkOut.value,
  })
}
</script>

