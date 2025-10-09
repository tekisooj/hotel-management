<template>
  <div class="host-page host-page--form">
    <header class="host-form-header">
      <p class="host-hero__eyebrow">New listing</p>
      <h1>List a new property</h1>
      <p>Add essential details, images, and rooms to make your property bookable in minutes.</p>
    </header>

    <div class="host-card host-card--form">
      <form id="property-form" class="host-form-grid" @submit.prevent>
        <div class="host-form-field">
          <label class="host-label" for="property-name">Name</label>
          <input id="property-name" v-model="property.hotelName" type="text" placeholder="Sunset Villas" />
        </div>
        <div class="host-form-field">
          <label class="host-label" for="property-description">Description</label>
          <input id="property-description" v-model="property.description" type="text" placeholder="Short description" />
        </div>
        <div class="host-form-field">
          <label class="host-label" for="property-stars">Stars</label>
          <input id="property-stars" v-model="property.stars" type="number" min="0" max="5" step="0.5" placeholder="4.5" />
        </div>
        <div class="host-form-field host-form-field--full">
          <label class="host-label" for="property-images">Property photos</label>
          <input id="property-images" type="file" multiple accept="image/*" @change="handlePropertyFiles" />
          <ul v-if="property.images.length" class="host-uploader-list">
            <li
              v-for="(image, idx) in property.images"
              :key="`${image.key}-${idx}`"
              class="host-uploader-item"
            >
              <span class="text-truncate">{{ image.key }}</span>
              <button type="button" class="host-link host-link--danger" @click="removePropertyImage(idx)">
                Remove
              </button>
            </li>
          </ul>
        </div>
        <div class="host-form-field host-form-field--full">
          <label class="host-label">Location</label>
          <location-search @selected="handleLocation" />
        </div>
      </form>

      <div v-if="uploadError" class="host-alert">{{ uploadError }}</div>
      <p v-if="pendingUploads > 0" class="host-subtext">Uploading images… please wait.</p>

      <section class="host-section">
        <header class="host-section__header">
          <h2 class="host-subsection-title">Rooms</h2>
          <p class="host-subtext">Add one room entry for each layout or rate plan you offer.</p>
        </header>

        <div
          v-for="(room, index) in rooms"
          :key="index"
          class="host-room-card"
        >
          <div class="host-form-grid">
            <div class="host-form-field">
              <label class="host-label">Name</label>
              <input type="text" v-model="room.name" placeholder="Deluxe King" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Description</label>
              <input type="text" v-model="room.description" placeholder="Spacious room with city view" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Max guests</label>
              <input type="number" v-model="room.capacity" min="1" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Room type</label>
              <select v-model="room.roomType">
                <option disabled value="">Select a room type</option>
                <option v-for="type in roomTypes" :key="type" :value="type">
                  {{ type.charAt(0).toUpperCase() + type.slice(1) }}
                </option>
              </select>
            </div>
            <div class="host-form-field">
              <label class="host-label">Price / night</label>
              <input type="number" v-model="room.pricePerNight" min="0" step="0.01" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Minimum price</label>
              <input type="number" v-model="room.minPricePerNight" min="0" step="0.01" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Maximum price</label>
              <input type="number" v-model="room.maxPricePerNight" min="0" step="0.01" />
            </div>
            <div class="host-form-field host-form-field--full">
              <label class="host-label">Amenities (comma separated)</label>
              <input type="text" v-model="room.amenitiesInput" placeholder="Wi-Fi, Parking, Pool" />
            </div>
            <div class="host-form-field host-form-field--full">
              <label class="host-label">Room photos</label>
              <input type="file" multiple accept="image/*" @change="(event) => handleRoomFiles(index, event)" />
              <ul v-if="room.images?.length" class="host-uploader-list">
                <li
                  v-for="(image, imgIdx) in room.images"
                  :key="`${image.key}-${imgIdx}`"
                  class="host-uploader-item"
                >
                  <span class="text-truncate">{{ image.key }}</span>
                  <button type="button" class="host-link host-link--danger" @click="removeRoomImage(index, imgIdx)">
                    Remove
                  </button>
                </li>
              </ul>
            </div>
          </div>
        </div>
      </section>

      <div class="host-form-actions">
        <button type="button" class="host-btn host-btn--ghost" @click="addRoom">+ Add room</button>
        <button type="button" class="host-btn host-btn--primary" :disabled="pendingUploads > 0" @click="add">
          Publish property
        </button>
      </div>
    </div>
  </div>
</template>


<script setup lang="ts">
import { reactive, ref } from 'vue';
import { useRuntimeConfig } from 'nuxt/app'
import { useUserStore } from '@/stores/user'
import { RoomType } from '@/types/RoomType';
import { Room } from '@/types/Room';
import { Amenity } from '@/types/Amenity';
import { PropertyDetail } from '@/types/PropertyDetail';
import { Image } from '@/types/Image';
import { useHostBff } from '@/api/hostBff';

const { addProperty, createAssetUploadUrl } = useHostBff();
const config = useRuntimeConfig()
const user = useUserStore()

const roomTypes: RoomType[] = ['single', 'double', 'suite', 'family', 'deluxe', 'studio'];

const pendingUploads = ref(0)
const uploadError = ref<string | null>(null)

const property = reactive({
  hotelName: '',
  address: '',
  city: '',
  country: '',
  state: '',
  county: '',
  description: '',
  stars: 3,
  latitude: undefined as number | undefined,
  longitude: undefined as number | undefined,
  placeId: undefined as string | undefined,
  images: [] as Image[],
})

function createEmptyRoom(): Partial<Room> & { amenitiesInput?: string; images: Image[] } {
  return {
    name: '',
    description: '',
    capacity: 1,
    roomType: '' as RoomType,
    pricePerNight: undefined,
    minPricePerNight: undefined,
    maxPricePerNight: undefined,
    amenitiesInput: '',
    images: [],
  }
}

const rooms = reactive<Array<Partial<Room> & { amenitiesInput?: string; images: Image[] }>>([
  createEmptyRoom(),
])

function addRoom() {
  rooms.push(createEmptyRoom());
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

async function uploadFile(prefix: string, file: File): Promise<string> {
  pendingUploads.value += 1
  try {
    const extension = file.name.includes('.') ? file.name.split('.').pop() : undefined
    const { key, uploadUrl, fields } = await createAssetUploadUrl(prefix, file.type || 'application/octet-stream', extension)
    const formData = new FormData()
    Object.entries(fields).forEach(([formKey, value]) => formData.append(formKey, value))
    formData.append('file', file)
    const response = await fetch(uploadUrl, {
      method: 'POST',
      body: formData,
    })
    if (!response.ok) {
      throw new Error(`Upload failed with status ${response.status}`)
    }
    return key
  } finally {
    pendingUploads.value = Math.max(pendingUploads.value - 1, 0)
  }
}

async function handlePropertyFiles(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) {
    return
  }
  uploadError.value = null
  for (const file of Array.from(files)) {
    try {
      const key = await uploadFile('properties', file)
      property.images.push({ key })
    } catch (error: any) {
      uploadError.value = error?.message || 'Unable to upload property image.'
      break
    }
  }
  input.value = ''
}

async function handleRoomFiles(index: number, event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || files.length === 0) {
    return
  }
  uploadError.value = null
  const room = rooms[index]
  if (!room) {
    return
  }
  room.images = room.images || []
  for (const file of Array.from(files)) {
    try {
      const key = await uploadFile('rooms', file)
      room.images.push({ key })
    } catch (error: any) {
      uploadError.value = error?.message || 'Unable to upload room image.'
      break
    }
  }
  input.value = ''
}

function removePropertyImage(index: number) {
  property.images.splice(index, 1)
}

function removeRoomImage(roomIndex: number, imageIndex: number) {
  const room = rooms[roomIndex]
  if (!room?.images) {
    return
  }
  room.images.splice(imageIndex, 1)
}

async function add() {
  if (pendingUploads.value > 0) {
    uploadError.value = 'Please wait for uploads to finish before submitting.'
    return
  }

  const convertedRooms: Room[] = rooms.map((room) => ({
    name: room.name || '',
    description: room.description || '',
    capacity: room.capacity || 0,
    roomType: room.roomType as RoomType,
    pricePerNight: Number(room.pricePerNight) || 0,
    minPricePerNight: Number(room.minPricePerNight) || 0,
    maxPricePerNight: Number(room.maxPricePerNight) || 0,
    amenities: room.amenitiesInput
      ? room.amenitiesInput.split(',').map((name) => ({ name: name.trim() })).filter((amenity: Amenity) => amenity.name.length)
      : [],
    images: room.images || [],
  }))

  const propDetail: PropertyDetail = {
    userUuid: user.uuid || (config.public as any).devUserId,
    name: property.hotelName,
    country: property.country,
    state: property.state,
    city: property.city,
    county: property.county,
    address: property.address,
    latitude: property.latitude ? Number(property.latitude) : undefined,
    longitude: property.longitude ? Number(property.longitude) : undefined,
    placeId: property.placeId as any,
    stars: property.stars,
    rooms: convertedRooms,
    images: property.images,
    description: property.description,
  }

  try {
    await addProperty(propDetail);
  } catch (error: any) {
    uploadError.value = error?.data?.message || error?.message || 'Unable to create property.'
  }
}
</script>
