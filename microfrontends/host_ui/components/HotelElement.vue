<template>
  <div class="d-flex w-100 justify-content-between align-items-start gap-3">
    <div class="d-flex flex-column flex-grow-1 gap-2">
      <div class="d-flex align-items-start gap-3">
        <img
          v-if="hotel.images?.length && hotel.images[0].url"
          :src="hotel.images[0].url"
          :alt="`${hotel.name} photo`"
          class="rounded object-fit-cover"
          style="width: 120px; height: 90px;"
        />
        <div>
          <h5 class="mb-1">{{ hotel.name }}</h5>
          <small class="text-muted">
            {{ hotel.city }}<span v-if="hotel.state">, {{ hotel.state }}</span>, {{ hotel.country }}
          </small>
          <p class="mb-1 mt-2" v-if="hotel.description">{{ hotel.description }}</p>
        </div>
      </div>
      <slot name="extra"></slot>
    </div>
    <span class="badge bg-primary rounded-pill align-self-start" v-if="hotel.average_rating != null">
      {{ Number(hotel.average_rating).toFixed(1) }} ?
    </span>
    <Rooms :rooms="hotel.rooms" />
  </div>
</template>

<script setup lang="ts">
import { PropertyDetail } from 'types/PropertyDetail';

defineProps<{ hotel: PropertyDetail }>()
</script>
