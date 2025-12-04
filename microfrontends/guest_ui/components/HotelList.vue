<template>
  <ul class="list-group">
    <li
      v-for="hotel in hotels"
      :key="hotel.uuid || hotel.name"
      class="list-group-item list-group-item-action hotel-item"
      role="button"
      tabindex="0"
      :aria-disabled="!hotel.uuid"
      @click="openDetails(hotel)"
      @keyup.enter="openDetails(hotel)"
      @keyup.space.prevent="openDetails(hotel)"
    >
      <HotelElement :hotel="hotel">
        <template #extra>
          <slot name="extra" :hotel="hotel"></slot>
        </template>
      </HotelElement>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import HotelElement from '@/components/HotelElement.vue'
import type { PropertyDetail } from 'types/PropertyDetail'
import { useSearchStore } from '@/stores/search'

defineProps<{ hotels: PropertyDetail[] }>()
const router = useRouter()
const store = useSearchStore()

function openDetails(hotel: PropertyDetail) {
  const uuid = hotel.uuid || (hotel as any).uuid
  if (!uuid) return
  const qs: Record<string, string> = {}
  const last = store.lastSearch
  if (last?.checkIn) qs.checkIn = last.checkIn
  if (last?.checkOut) qs.checkOut = last.checkOut
  if (last?.capacity) qs.guests = String(last.capacity)
  router.push({ path: `/property/${uuid}`, query: qs })
}
</script>

<style scoped>
.hotel-item:focus-visible {
  outline: 2px solid #ff8b4d;
  outline-offset: 2px;
}

.hotel-item[aria-disabled='true'] {
  cursor: default;
  opacity: 0.75;
}
</style>



