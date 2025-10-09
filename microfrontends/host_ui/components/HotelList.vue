<template>
  <ul class="host-hotel-list">
    <li
      v-for="hotel in hotels"
      :key="hotel.uuid || hotel.name"
      class="host-hotel-item"
      role="button"
      tabindex="0"
      :aria-disabled="!hotel.uuid"
      @click="openDetails(hotel)"
      @keyup.enter="openDetails(hotel)"
      @keyup.space.prevent="openDetails(hotel)"
    >
      <HotelElement :hotel="hotel">
        <template #actions>
          <slot name="actions" :hotel="hotel"></slot>
        </template>
      </HotelElement>
    </li>
  </ul>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import HotelElement from '@/components/HotelElement.vue'
import type { PropertyDetail } from 'types/PropertyDetail'

defineProps<{ hotels: PropertyDetail[] }>()

const router = useRouter()

function openDetails(hotel: PropertyDetail) {
  const uuid = hotel.uuid || (hotel as any).uuid
  if (!uuid) return
  router.push({ path: /property/ })
}
</script>
