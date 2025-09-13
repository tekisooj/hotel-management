<template>
  <form class="row g-2 align-items-end" @submit.prevent="submit">
    <div class="col-md-3">
      <label class="form-label">Country</label>
      <input v-model="country" type="text" class="form-control" placeholder="Country" />
    </div>
    <div class="col-md-3">
      <label class="form-label">City</label>
      <input v-model="city" type="text" class="form-control" placeholder="City" />
    </div>
    <div class="col-md-2">
      <label class="form-label">State (optional)</label>
      <input v-model="state" type="text" class="form-control" placeholder="State" />
    </div>
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
const country = ref('')
const city = ref('')
const state = ref('')
const checkIn = ref('')
const checkOut = ref('')

const emit = defineEmits<{
  (e: 'search', payload: { country: string; city: string; state?: string; check_in_date: string; check_out_date: string }): void
}>()

const canSearch = computed(() => !!country.value && !!city.value && !!checkIn.value && !!checkOut.value)

function submit() {
    console.log("LOGGG")
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

