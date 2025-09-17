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

      <div class="col-md-3">
        <label class="form-label">Property Photos</label>
        <input type="file" class="form-control" multiple accept="image/*" @change="handlePropertyFiles" />
        <ul v-if="property.images.length" class="mt-2 list-unstyled">
          <li
            v-for="(image, idx) in property.images"
            :key="`${image.key}-${idx}`"
            class="d-flex align-items-center justify-content-between gap-2"
          >
            <span class="small text-truncate">{{ image.key }}</span>
            <button type="button" class="btn btn-link btn-sm text-danger" @click="removePropertyImage(idx)">
              Remove
            </button>
          </li>
        </ul>
      </div>

      <location-search @selected="handleLocation" />
    </form>

    <div v-if="uploadError" class="alert alert-danger mt-3">{{ uploadError }}</div>
    <p v-if="pendingUploads > 0" class="text-muted mt-2">Uploading images&hellip; please wait.</p>

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
        <div class="col-md-6 mb-3">
          <label class="form-label">Room Photos</label>
          <input type="file" class="form-control" multiple accept="image/*" @change="(event) => handleRoomFiles(index, event)" />
          <ul v-if="room.images?.length" class="mt-2 list-unstyled">
            <li
              v-for="(image, imgIdx) in room.images"
              :key="`${image.key}-${imgIdx}`"
              class="d-flex align-items-center justify-content-between gap-2"
            >
              <span class="small text-truncate">{{ image.key }}</span>
              <button type="button" class="btn btn-link btn-sm text-danger" @click="removeRoomImage(index, imgIdx)">
                Remove
              </button>
            </li>
          </ul>
        </div>
      </div>
    </div>

    <button class="btn btn-primary col-md-3 mb-4" @click="addRoom">+ Add Room</button>
    <hr />
    <button class="btn btn-success col-md-3 mb-4" :disabled="pendingUploads > 0" @click="add">Add Property</button>
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
