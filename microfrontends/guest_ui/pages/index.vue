<template>
  <div class="page">
    <div class="search">
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
        <div class="col-md-3">
          <label class="form-label">Capacity</label>
          <input v-model="capacity" type="number" class="form-control" />
        </div>
        <div class="col-md-3">
          <label class="form-label">Max price</label>
          <input v-model="maxPrice" type="number" class="form-control"/>
        </div>
        <div class="col-12 mt-2">
          <button class="btn btn-primary" @click="submit" :disabled="!canSearch">Search</button>
        </div>
      </form>
    </div>

    <div class="hotels">
      <HotelList :hotels="propertyDetails" />
    </div>



  </div>
</template>

<script setup lang="ts">
import { useGuestBff } from 'api/guestBff'
import axios from 'axios'
import HotelList from 'components/HotelList.vue'
import { useRuntimeConfig } from 'nuxt/app'
import { onMounted, ref, watch } from 'vue'

const {searchRooms, addReview, addBooking, getPropertyReviews} = useGuestBff()
const config = useRuntimeConfig()
const message = ref('')
const country = ref('')
const city = ref('')
const state = ref('')
const checkIn = ref('')
const checkOut = ref('')
const capacity = ref(0)
const maxPrice = ref(undefined)

const propertyDetails = ref([])


const canSearch = computed(() => !!country.value && !!city.value && !!checkIn.value && !!checkOut.value)

function submit() {
  if (!canSearch.value) return

  propertyDetails = searchRooms(country, city, state, checkIn, checkOut, capacity, maxPrice)
}



</script>

<style scoped>
.page { padding: 24px; }
.actions { margin-top: 16px; }
button { padding: 8px 12px; }
</style>

