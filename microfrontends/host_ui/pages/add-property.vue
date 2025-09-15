<template>
  <div class="container mt-4">
    <form id="property-form" class="row g-2 align-items-end">
      <div class="col-md-3">
        <label class="form-label">Name</label>
        <input v-model="property.hotelName" type="text" class="form-control" placeholder="Name" />
      </div>
      <div class="col-md-3">
        <label class="form-label">Description</label>
        <input v-model="property.description" type="text" class="form-control" placeholder="Description" />
      </div>
      <div class="col-md-3">
        <label class="form-label">Stars</label>
        <input v-model="property.stars" type="number" class="form-control" placeholder="Stars" />
      </div>

      <location-search @selected="handleLocation" />
    </form>

    <div
      v-for="(room, index) in rooms"
      :key="index"
      class="mb-4 p-3 border rounded bg-light"
    >
      <div class="row">
        <div class="col-md-6 mb-3">
          <label class="form-label">Name</label>
          <input type="text" class="form-control" v-model="room.name" required />
        </div>
        <div class="col-md-3 mb-3">
          <label class="form-label">Description</label>
          <input type="text" class="form-control" v-model="room.description" required />
        </div>
        <div class="col-md-3 mb-3">
          <label class="form-label">Max Guests</label>
          <input type="number" class="form-control" v-model="room.capacity" required />
        </div>

        <div class="col-md-3 mb-3">
          <label class="form-label">Room Type</label>
          <select class="form-select" v-model="room.roomType" required>
            <option disabled value="">Select a room type</option>
            <option v-for="type in roomTypes" :key="type" :value="type">
              {{ type.charAt(0).toUpperCase() + type.slice(1) }}
            </option>
          </select>
        </div>

        <div class="col-md-3 mb-3">
          <label class="form-label">Price Per Night</label>
          <input type="number" class="form-control" v-model="room.pricePerNight" required />
        </div>
        <div class="col-md-3 mb-3">
          <label class="form-label">Min Price Per Night</label>
          <input type="number" class="form-control" v-model="room.minPricePerNight" required />
        </div>
        <div class="col-md-3 mb-3">
          <label class="form-label">Max Price Per Night</label>
          <input type="number" class="form-control" v-model="room.maxPricePerNight" required />
        </div>
        <div class="col-md-3 mb-3">
          <label class="form-label">Amenities (comma separated)</label>
          <input type="text" class="form-control" v-model="room.amenitiesInput" />
        </div>
      </div>
    </div>

    <button class="btn btn-primary col-md-3 mb-4" @click="addRoom">+ Add Room</button>
    <hr></hr>
    <button class="btn btn-success col-md-3 mb-4" @click="add">Add Property</button>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue';
import { useRuntimeConfig } from 'nuxt/app'
import { useUserStore } from '@/stores/user'
import { RoomType } from '@/types/RoomType';
import { Room } from '@/types/Room';
import { Amenity } from '@/types/Amenity';
import { PropertyDetail } from '@/types/PropertyDetail';
import { useHostBff } from '@/api/hostBff';

const { addProperty } = useHostBff();
const config = useRuntimeConfig()
const user = useUserStore()

// Room types for select
const roomTypes: RoomType[] = ['single', 'double', 'suite', 'family', 'deluxe', 'studio'];

// Property form data
const property = reactive({
  hotelName: '',
  address: '',
  city: '',
  country: '',
  state: '',
  county: '',
  description: '',
  stars: 3,
  latitude: undefined,
  longitude: undefined,
  placeId: undefined
});

// Rooms (with amenitiesInput string for now)
const rooms = reactive<Array<Partial<Room> & { amenitiesInput?: string }>>([
  {
    name: '',
    description: '',
    capacity: 1,
    roomType: '' as RoomType,
    pricePerNight: undefined,
    minPricePerNight: undefined,
    maxPricePerNight: undefined,
    amenitiesInput: ''
  }
]);

function addRoom() {
  rooms.push({
    name: '',
    description: '',
    capacity: 1,
    roomType: '' as RoomType,
    pricePerNight: undefined,
    minPricePerNight: undefined,
    maxPricePerNight: undefined,
    amenitiesInput: ''
  });
}

const handleLocation = (location: any) => {
  property.country = location.country;
  property.state = location.state;
  property.city = location.city;
  property.county = location.county;
  property.address = location.address;
  property.latitude = location.latitude;
  property.longitude = location.longitude;
  property.placeId = location.placeId;
};

async function add() {
  const convertedRooms: Room[] = rooms.map((room) => ({
    name: room.name!,
    description: room.description!,
    capacity: room.capacity!,
    room_type: room.roomType!,
    price_per_night: room.pricePerNight!,
    min_price_per_night: room.minPricePerNight!,
    max_price_per_night: room.maxPricePerNight!,
    amenities: room.amenitiesInput
      ? room.amenitiesInput.split(',').map((name) => ({ name: name.trim() }))
      : []
  }));

  const propDetail: PropertyDetail = {
    userUuid: user.uuid || (config.public as any).devUserId,
    name: property.hotelName,
    country: property.country,
    state: property.state,
    city: property.city,
    county: property.county,
    address: property.address,
    latitude: Number(property.latitude),
    longitude: Number(property.longitude),
    placeId: property.placeId,
    stars: property.stars,
    rooms: convertedRooms
  };

  addProperty(propDetail);
}
</script>
