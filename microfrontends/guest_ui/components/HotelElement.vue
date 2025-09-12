<template>
  <div class="d-flex w-100 justify-content-between align-items-start">
    <div>
      <h5 class="mb-1">{{ hotel.name }}</h5>
      <small class="text-muted">
        {{ hotel.city }}<span v-if="hotel.state">, {{ hotel.state }}</span>, {{ hotel.country }}
      </small>
      <p class="mb-1 mt-2" v-if="hotel.description">{{ hotel.description }}</p>
      <slot name="extra"></slot>
    </div>
    <span class="badge bg-primary rounded-pill align-self-start" v-if="hotel.average_rating != null">
      {{ Number(hotel.average_rating).toFixed(1) }} ★
    </span>
    <Rooms :rooms="hotel.rooms">
    </Rooms>
  </div>
</template>

<script setup lang="ts">
import { PropertyDetail } from 'types/PropertyDetail';

defineProps<{ hotel: PropertyDetail }>()
</script>

