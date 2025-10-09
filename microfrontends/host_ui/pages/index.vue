<template>
  <div class="host-page">
    <section class="host-hero">
      <p class="host-hero__eyebrow">Host dashboard</p>
      <h1 class="host-hero__title">Manage your properties</h1>

      <div class="host-hero__actions">
        <button class="host-btn host-btn--primary" @click="addNewProperty">Add new property</button>
        <button class="host-btn host-btn--ghost" @click="viewBookings">View bookings</button>
      </div>
    </section>

    <section class="host-section">
      <header class="host-section__header">
        <h2 class="host-section__title">Your properties</h2>
      </header>
      <div class="host-card host-card--list">
        <template v-if="loading">
          <p class="host-empty">Loading your properties</p>
        </template>
        <template v-else-if="loadError">
          <p class="host-empty">{{ loadError }}</p>
        </template>
        <template v-else-if="!properties.length">
          <p class="host-empty">You don't have any properties yet. Click �Add new property� to get started.</p>
        </template>
        <template v-else>
          <HotelList :hotels="properties" />
        </template>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import HotelList from '@/components/HotelList.vue'
import { useHostBff } from '@/api/hostBff'
import type { PropertyDetail } from '@/types/PropertyDetail'

const router = useRouter()
const { getProperties } = useHostBff()
const properties = ref<PropertyDetail[]>([])
const loading = ref(true)
const loadError = ref<string | null>(null)

onMounted(async () => {
  try {
    const response = await getProperties()
    properties.value = Array.isArray(response) ? response : []
  } catch (error: any) {
    loadError.value = error?.message || 'Unable to load your properties right now.'
  } finally {
    loading.value = false
  }
})

function addNewProperty() {
  router.push({ path: '/add-property' })
}

function viewBookings() {
  router.push({ path: '/bookings' })
}
</script>
