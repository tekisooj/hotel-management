<template>
  <ul class="list-group">
    <li
      v-for="hotel in hotels"
      :key="hotel.uuid || hotel.name"
      class="list-group-item list-group-item-action"

    >
      <HotelElement :hotel="hotel">
        <!-- <template #extra>
          <div class="mt-2 d-flex gap-2 flex-wrap">
            <button class="btn btn-sm btn-outline-primary" @click.stop="emit('viewRooms', hotel)">View rooms</button>
            <button class="btn btn-sm btn-outline-secondary" @click.stop="emit('viewReviews', hotel)">Reviews</button>
          </div>
        </template> -->
      </HotelElement>
    </li>
  </ul>
</template>

<script setup lang="ts">
import HotelElement from '@/components/HotelElement.vue'
import { PropertyDetail } from 'types/PropertyDetail';


const props = defineProps<{ hotels: PropertyDetail[] }>()

</script>

