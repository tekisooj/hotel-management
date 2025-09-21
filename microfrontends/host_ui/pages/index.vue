<template>
  <div class="page">
    <div class="d-flex gap-2 mb-3 flex-wrap">
      <button class="btn btn-outline-secondary" @click="viewBookings">View bookings</button>
      <button class="btn btn-primary" @click="addNewProperty">Add new Property</button>
    </div>

    <div class="hotels">
      <HotelList :hotels="propertyDetails" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { useHostBff } from '@/api/hostBff'
import HotelList from '@/components/HotelList.vue'
import { onMounted } from 'vue'
import { ref, computed } from 'vue'

const { getProperties } = useHostBff()
const router = useRouter()
const country = ref('')
const city = ref('')
const state = ref('')
const checkIn = ref('')
const checkOut = ref('')
const capacity = ref(0)
const maxPrice = ref(undefined)

const propertyDetails = ref<any[]>([])

onMounted(async () => {
  try {
    const res = await getProperties()
    propertyDetails.value = Array.isArray(res) ? res : []
  } catch (e) {
    propertyDetails.value = []
  }
})

async function addNewProperty() {
  await router.push({ path: '/add-property' })
}

async function viewBookings() {
  await router.push({ path: '/bookings' })
}

async function submit() {
  if (!canSearch.value) return
  try {
    const res = await searchRooms({
      country: country.value,
      city: city.value,
      state: state.value || undefined,
      check_in_date: checkIn.value,
      check_out_date: checkOut.value,
      capacity: capacity.value || undefined,
      max_price: maxPrice.value || undefined,
    })
    propertyDetails.value = Array.isArray(res) ? res : []
  } catch (e) {
    // optional: surface error
    propertyDetails.value = []
  }
}
</script>

<style scoped>
.page { padding: 24px; }
.actions { margin-top: 16px; }
button { padding: 8px 12px; }
</style>
