<template>
  <ul class="host-hotel-list">
    <li
      v-for="hotel in hotels"
      :key="hotel.uuid || hotel.name"
      class="host-hotel-item"
      role="button"
      tabindex="0"
      :aria-disabled="!extractUuid(hotel)"
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

function extractUuid(hotel: PropertyDetail): string | null {
  const raw = hotel.uuid ?? (hotel as any).uuid
  if (!raw) return null
  return typeof raw === 'string' ? raw : String(raw)
}

function openDetails(hotel: PropertyDetail) {
  const uuid = extractUuid(hotel)
  if (!uuid) return
  router.push({ path: `/property/${uuid}` })
}
</script>
