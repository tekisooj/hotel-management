<template>
  <div class="host-property" v-if="!loadError && property">
    <header class="host-property__header">
      <div>
        <p class="host-property__eyebrow">Property overview</p>
        <h1 class="host-property__title">{{ property.name }}</h1>
        <p class="host-property__location">{{ locationLabel }}</p>
      </div>
      <div class="host-property__summary" v-if="averageRating !== null">
        <span class="host-property__score">{{ averageRating.toFixed(1) }}</span>
        <span class="host-property__score-label">Guest score</span>
      </div>
      <div class="host-property__actions">
        <button
          v-if="!isEditingProperty"
          class="host-btn host-btn--ghost"
          type="button"
          @click="beginEditProperty"
        >
          Edit property
        </button>
        <button
          v-if="isEditingProperty"
          class="host-btn host-btn--ghost"
          type="button"
          @click="cancelEditProperty"
        >
          Cancel
        </button>
        <button
          v-if="isEditingProperty"
          class="host-btn host-btn--primary"
          type="button"
          :disabled="savingProperty || propertyUploadCount > 0"
          @click="submitEditProperty"
        >
          Save changes
        </button>
        <button
          class="host-btn host-btn--danger"
          type="button"
          @click="confirmPropertyRemoval"
        >
          Delete property
        </button>
      </div>
    </header>

    <section v-if="propertyEditError" class="host-property__message host-property__message--error">
      {{ propertyEditError }}
    </section>
    <p v-if="propertyUploadCount > 0" class="host-property__note">Uploading property images...</p>

    <section v-if="isEditingProperty" class="host-property__card host-property__edit-card">
      <div class="host-form-grid">
        <div class="host-form-field">
          <label class="host-label">Name</label>
          <input v-model="editPropertyForm.name" type="text" placeholder="Property name" />
        </div>
        <div class="host-form-field">
          <label class="host-label">Description</label>
          <input v-model="editPropertyForm.description" type="text" placeholder="Short description" />
        </div>
        <div class="host-form-field">
          <label class="host-label">Stars</label>
          <input v-model="editPropertyForm.stars" type="number" min="0" max="5" step="0.5" />
        </div>
        <div class="host-form-field">
          <label class="host-label">Country</label>
          <input v-model="editPropertyForm.country" type="text" placeholder="Country" />
        </div>
        <div class="host-form-field">
          <label class="host-label">State</label>
          <input v-model="editPropertyForm.state" type="text" placeholder="State" />
        </div>
        <div class="host-form-field">
          <label class="host-label">City</label>
          <input v-model="editPropertyForm.city" type="text" placeholder="City" />
        </div>
        <div class="host-form-field">
          <label class="host-label">County</label>
          <input v-model="editPropertyForm.county" type="text" placeholder="County" />
        </div>
        <div class="host-form-field host-form-field--full">
          <label class="host-label">Address</label>
          <input v-model="editPropertyForm.address" type="text" placeholder="Street and number" />
        </div>
        <div class="host-form-field">
          <label class="host-label">Latitude</label>
          <input v-model="editPropertyForm.latitude" type="number" step="0.000001" />
        </div>
        <div class="host-form-field">
          <label class="host-label">Longitude</label>
          <input v-model="editPropertyForm.longitude" type="number" step="0.000001" />
        </div>
        <div class="host-form-field host-form-field--full">
          <label class="host-label">Search &amp; replace location</label>
          <LocationSearch @selected="applyLocation" />
          <p class="host-form-note">Selecting a new place will update location related fields above.</p>
        </div>
        <div class="host-form-field host-form-field--full">
          <label class="host-label">Property images</label>
          <input type="file" multiple accept="image/*" @change="handlePropertyImageUpload" />
          <ul v-if="editPropertyForm.images.length" class="host-uploader-list">
            <li v-for="(image, index) in editPropertyForm.images" :key="image.key || index" class="host-uploader-item">
              <span class="text-truncate">{{ image.key }}</span>
              <button type="button" class="host-link host-link--danger" @click="removePropertyImage(index)">Remove</button>
            </li>
          </ul>
        </div>
      </div>
    </section>

    <section class="host-property__details">
      <div class="host-property__gallery" v-if="images.length">
        <img
          v-for="(image, index) in images"
          :key="image.key || index"
          :src="image.url"
          :alt="`${property.name} image ${index + 1}`"
        />
      </div>
      <div class="host-property__gallery host-property__gallery--empty" v-else>
        <span>{{ initials }}</span>
      </div>

      <article class="host-property__card">
        <h2>Property overview</h2>
        <p v-if="property.description">{{ property.description }}</p>
        <p v-else>This property does not have a description yet.</p>

        <ul class="host-property__facts">
          <li>
            <strong>Rooms:</strong>
            <span>{{ roomCount }}</span>
          </li>
          <li v-if="property.stars">
            <strong>Rating:</strong>
            <span>{{ Number(property.stars).toFixed(1) }} stars</span>
          </li>
          <li v-if="averageRating !== null">
            <strong>Guest reviews:</strong>
            <span>{{ averageRating.toFixed(1) }} average score</span>
          </li>
          <li v-if="property.phone">
            <strong>Phone:</strong>
            <span>{{ property.phone }}</span>
          </li>
          <li v-if="property.email">
            <strong>Email:</strong>
            <span>{{ property.email }}</span>
          </li>
        </ul>
      </article>
    </section>

    <section class="host-property__rooms">
      <header>
        <h2>Rooms</h2>
        <p v-if="!rooms.length">No rooms created for this property yet.</p>
      </header>

      <section v-if="roomEditError" class="host-property__message host-property__message--error">
        {{ roomEditError }}
      </section>
      <p v-if="roomUploadCount > 0" class="host-property__note">Uploading room images...</p>

      <ul v-if="rooms.length" class="host-property__room-list">
        <li v-for="room in rooms" :key="room.uuid || room.name">
          <h3>{{ room.name }}</h3>
          <p class="host-property__room-meta">
            {{ room.capacity }} guests • ${{ Number(room.price_per_night ?? room.pricePerNight ?? 0).toFixed(2) }} per night
          </p>
          <p v-if="room.description">{{ room.description }}</p>
          <div class="host-room-images" v-if="room.images?.length">
            <img
              v-for="(image, idx) in room.images"
              :key="image.key || idx"
              v-if="image.url"
              :src="image.url"
              :alt="`${room.name} image ${idx + 1}`"
            />
          </div>
          <div class="host-room-actions">
            <button type="button" class="host-link" @click="startRoomEdit(room)">Edit room</button>
            <button type="button" class="host-link host-link--danger" @click="removeRoom(room)">Delete room</button>
          </div>

          <div v-if="editingRoomId === (room.uuid || room.name)" class="host-room-edit host-form-grid">
            <div class="host-form-field">
              <label class="host-label">Name</label>
              <input v-model="editRoomForm.name" type="text" placeholder="Room name" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Description</label>
              <input v-model="editRoomForm.description" type="text" placeholder="Short description" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Capacity</label>
              <input v-model="editRoomForm.capacity" type="number" min="1" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Room type</label>
              <select v-model="editRoomForm.roomType">
                <option disabled value="">Select type</option>
                <option v-for="type in roomTypes" :key="type" :value="type">
                  {{ type.charAt(0).toUpperCase() + type.slice(1) }}
                </option>
              </select>
            </div>
            <div class="host-form-field">
              <label class="host-label">Price / night</label>
              <input v-model="editRoomForm.pricePerNight" type="number" min="0" step="0.01" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Min price</label>
              <input v-model="editRoomForm.minPricePerNight" type="number" min="0" step="0.01" />
            </div>
            <div class="host-form-field">
              <label class="host-label">Max price</label>
              <input v-model="editRoomForm.maxPricePerNight" type="number" min="0" step="0.01" />
            </div>
            <div class="host-form-field host-form-field--full">
              <label class="host-label">Amenities (comma separated)</label>
              <input v-model="editRoomForm.amenitiesInput" type="text" placeholder="Wi-Fi, Parking" />
            </div>
            <div class="host-form-field host-form-field--full">
              <label class="host-label">Room images</label>
              <input type="file" multiple accept="image/*" @change="handleRoomImageUpload" />
              <ul v-if="editRoomForm.images.length" class="host-uploader-list">
                <li
                  v-for="(image, idx) in editRoomForm.images"
                  :key="image.key || idx"
                  class="host-uploader-item"
                >
                  <span class="text-truncate">{{ image.key }}</span>
                  <button type="button" class="host-link host-link--danger" @click="removeRoomImage(idx)">Remove</button>
                </li>
              </ul>
            </div>
            <div class="host-room-edit__actions host-form-field host-form-field--full">
              <button
                type="button"
                class="host-btn host-btn--primary"
                :disabled="roomUploadCount > 0"
                @click="submitRoomEdit"
              >
                Save room
              </button>
              <button type="button" class="host-btn host-btn--ghost" @click="cancelRoomEdit">Cancel</button>
            </div>
          </div>
        </li>
      </ul>
    </section>

    <section v-if="showDeletePrompt" class="host-property__message host-property__message--warning">
      <p>Deleting this property will remove all associated rooms. This action cannot be undone.</p>
      <div class="host-property__message-actions">
        <button class="host-btn host-btn--danger" type="button" @click="deletePropertyAndRedirect">Confirm delete</button>
        <button class="host-btn host-btn--ghost" type="button" @click="showDeletePrompt = false">Cancel</button>
      </div>
    </section>
  </div>

  <p v-else-if="loadError" class="host-property__empty">{{ loadError }}</p>
  <p v-else class="host-property__empty">Loading property details...</p>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import LocationSearch from '@/components/LocationSearch.vue'
import { useHostBff } from '@/api/hostBff'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { Room } from '@/types/Room'
import type { Amenity } from '@/types/Amenity'
import { RoomType } from '@/types/RoomType'

const route = useRoute()
const router = useRouter()
const {
  getProperty,
  updateProperty,
  deleteProperty,
  updateRoom,
  deleteRoom,
  createAssetUploadUrl,
} = useHostBff()

const property = ref<any | null>(null)
const rooms = ref<any[]>([])
const loadError = ref<string | null>(null)

const isEditingProperty = ref(false)
const savingProperty = ref(false)
const propertyUploadCount = ref(0)
const propertyEditError = ref<string | null>(null)
const showDeletePrompt = ref(false)

const roomUploadCount = ref(0)
const roomEditError = ref<string | null>(null)
const editingRoomId = ref<string | null>(null)

const editPropertyForm = reactive({
  name: '',
  description: '',
  stars: '' as string | number,
  country: '',
  state: '',
  city: '',
  county: '',
  address: '',
  latitude: '' as string | number,
  longitude: '' as string | number,
  placeId: '',
  images: [] as Array<{ key: string; url?: string }>,
})

const editRoomForm = reactive({
  uuid: '',
  propertyUuid: '',
  name: '',
  description: '',
  capacity: '' as number | string,
  roomType: '',
  pricePerNight: '' as number | string,
  minPricePerNight: '' as number | string,
  maxPricePerNight: '' as number | string,
  amenitiesInput: '',
  images: [] as Array<{ key: string; url?: string }>,
})

const roomTypes = Object.values(RoomType)

const images = computed(() => property.value?.images ?? [])
const roomCount = computed(() => rooms.value.length)
const locationLabel = computed(() => {
  if (!property.value) return ''
  const city = property.value.city ?? ''
  const state = property.value.state ?? ''
  const country = property.value.country ?? ''
  return [city, state, country].filter(Boolean).join(', ')
})
const initials = computed(() => {
  const name = property.value?.name || property.value?.address || 'P'
  return name.trim().slice(0, 2).toUpperCase()
})
const averageRating = computed(() => {
  const raw = property.value?.average_rating ?? property.value?.averageRating
  if (raw == null) return null
  const value = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(value) ? value : null
})

function parseNumber(value: string | number): number | undefined {
  if (value === '' || value === null || value === undefined) return undefined
  const num = typeof value === 'number' ? value : parseFloat(value)
  return Number.isFinite(num) ? num : undefined
}

async function loadPropertyDetail() {
  const param = route.params.id
  if (typeof param !== 'string' || !param) {
    loadError.value = 'Missing property identifier.'
    return
  }
  try {
    loadError.value = null
    const detail = await getProperty(param)
    property.value = detail
    rooms.value = Array.isArray(detail?.rooms) ? detail.rooms : []
    if (isEditingProperty.value) {
      hydrateEditProperty()
    }
    if (editingRoomId.value) {
      const match = rooms.value.find((room) => String(room.uuid || room.name || '') === editingRoomId.value)
      if (match) {
        hydrateEditRoom(match)
      } else {
        editingRoomId.value = null
      }
    }
  } catch (error: any) {
    loadError.value = error?.message || 'Unable to load property details.'
    property.value = null
    rooms.value = []
  }
}

function hydrateEditProperty() {
  if (!property.value) return
  editPropertyForm.name = property.value.name ?? ''
  editPropertyForm.description = property.value.description ?? ''
  editPropertyForm.stars = property.value.stars ?? ''
  editPropertyForm.country = property.value.country ?? ''
  editPropertyForm.state = property.value.state ?? ''
  editPropertyForm.city = property.value.city ?? ''
  editPropertyForm.county = property.value.county ?? ''
  editPropertyForm.address = property.value.address ?? ''
  editPropertyForm.latitude = property.value.latitude ?? ''
  editPropertyForm.longitude = property.value.longitude ?? ''
  editPropertyForm.placeId = property.value.place_id ?? (property.value as any).placeId ?? ''
  editPropertyForm.images = Array.isArray(property.value.images)
    ? property.value.images.map((image: any) => ({ key: image.key, url: image.url }))
    : []
}

function beginEditProperty() {
  if (!property.value) return
  propertyEditError.value = null
  isEditingProperty.value = true
  hydrateEditProperty()
}

function cancelEditProperty() {
  isEditingProperty.value = false
  propertyEditError.value = null
  propertyUploadCount.value = 0
}

function applyLocation(location: any) {
  if (!location) return
  editPropertyForm.country = location.country || editPropertyForm.country
  editPropertyForm.state = location.state || ''
  editPropertyForm.city = location.city || ''
  editPropertyForm.county = location.county || ''
  editPropertyForm.address = location.address || editPropertyForm.address
  if (location.latitude != null) {
    editPropertyForm.latitude = location.latitude
  }
  if (location.longitude != null) {
    editPropertyForm.longitude = location.longitude
  }
  if (location.placeId) {
    editPropertyForm.placeId = location.placeId
  }
}

async function submitEditProperty() {
  if (!property.value) return
  if (propertyUploadCount.value > 0) {
    propertyEditError.value = 'Please wait for image uploads to finish before saving.'
    return
  }
  propertyEditError.value = null
  savingProperty.value = true
  try {
    const payload: PropertyDetail = {
      uuid: property.value.uuid,
      userUuid: property.value.user_uuid ?? property.value.userUuid ?? undefined,
      name: String(editPropertyForm.name || '').trim(),
      description: editPropertyForm.description || '',
      country: editPropertyForm.country || '',
      state: editPropertyForm.state || undefined,
      city: editPropertyForm.city || '',
      county: editPropertyForm.county || undefined,
      address: editPropertyForm.address || '',
      fullAddress: property.value.full_address ?? property.value.fullAddress ?? undefined,
      latitude: parseNumber(editPropertyForm.latitude),
      longitude: parseNumber(editPropertyForm.longitude),
      stars: parseNumber(editPropertyForm.stars),
      placeId: editPropertyForm.placeId || undefined,
      images: editPropertyForm.images.map((image) => ({ key: image.key })),
      rooms: undefined,
    }
    await updateProperty(String(property.value.uuid), payload)
    isEditingProperty.value = false
    await loadPropertyDetail()
  } catch (error: any) {
    propertyEditError.value = error?.data?.detail || error?.message || 'Unable to update property.'
  } finally {
    savingProperty.value = false
  }
}

function removePropertyImage(index: number) {
  editPropertyForm.images.splice(index, 1)
}

async function handlePropertyImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || !files.length) return
  propertyEditError.value = null
  for (const file of Array.from(files)) {
    try {
      const key = await uploadFile('properties', file, propertyUploadCount)
      editPropertyForm.images.push({ key })
    } catch (error: any) {
      propertyEditError.value = error?.message || 'Unable to upload property image.'
      break
    }
  }
  input.value = ''
}

function hydrateEditRoom(room: any) {
  editingRoomId.value = String(room.uuid || room.name || '')
  editRoomForm.uuid = String(room.uuid || '')
  editRoomForm.propertyUuid = String(room.property_uuid || room.propertyUuid || property.value?.uuid || '')
  editRoomForm.name = room.name || ''
  editRoomForm.description = room.description || ''
  editRoomForm.capacity = room.capacity ?? ''
  editRoomForm.roomType = room.room_type || room.roomType || ''
  editRoomForm.pricePerNight = room.price_per_night ?? room.pricePerNight ?? ''
  editRoomForm.minPricePerNight = room.min_price_per_night ?? room.minPricePerNight ?? ''
  editRoomForm.maxPricePerNight = room.max_price_per_night ?? room.maxPricePerNight ?? ''
  editRoomForm.amenitiesInput = Array.isArray(room.amenities)
    ? room.amenities.map((amenity: Amenity) => amenity.name).filter(Boolean).join(', ')
    : ''
  editRoomForm.images = Array.isArray(room.images)
    ? room.images.map((image: any) => ({ key: image.key, url: image.url }))
    : []
}

function startRoomEdit(room: any) {
  roomEditError.value = null
  roomUploadCount.value = 0
  hydrateEditRoom(room)
}

function cancelRoomEdit() {
  editingRoomId.value = null
  roomEditError.value = null
  roomUploadCount.value = 0
}

function removeRoomImage(index: number) {
  editRoomForm.images.splice(index, 1)
}

async function handleRoomImageUpload(event: Event) {
  const input = event.target as HTMLInputElement
  const files = input.files
  if (!files || !files.length) return
  roomEditError.value = null
  for (const file of Array.from(files)) {
    try {
      const key = await uploadFile('rooms', file, roomUploadCount)
      editRoomForm.images.push({ key })
    } catch (error: any) {
      roomEditError.value = error?.message || 'Unable to upload room image.'
      break
    }
  }
  input.value = ''
}

function toAmenities(input: string): Amenity[] {
  if (!input) return []
  return input
    .split(',')
    .map((name) => name.trim())
    .filter((name) => name.length)
    .map((name) => ({ name }))
}

async function submitRoomEdit() {
  if (!editingRoomId.value) return
  if (roomUploadCount.value > 0) {
    roomEditError.value = 'Please wait for image uploads to finish before saving.'
    return
  }
  roomEditError.value = null
  try {
    const payload: Room = {
      uuid: editRoomForm.uuid,
      propertyUuid: editRoomForm.propertyUuid,
      name: editRoomForm.name,
      description: editRoomForm.description,
      capacity: Number(editRoomForm.capacity) || 0,
      roomType: editRoomForm.roomType as Room['roomType'],
      pricePerNight: Number(editRoomForm.pricePerNight) || 0,
      minPricePerNight: Number(editRoomForm.minPricePerNight) || 0,
      maxPricePerNight: Number(editRoomForm.maxPricePerNight) || 0,
      amenities: toAmenities(editRoomForm.amenitiesInput),
      images: editRoomForm.images.map((image) => ({ key: image.key })),
    }
    await updateRoom(editRoomForm.uuid, payload)
    editingRoomId.value = null
    await loadPropertyDetail()
  } catch (error: any) {
    roomEditError.value = error?.data?.detail || error?.message || 'Unable to update room.'
  }
}

async function removeRoom(room: any) {
  const roomUuid = room.uuid ?? null
  if (!roomUuid) return
  if (!window.confirm('Delete this room?')) return
  try {
    await deleteRoom(String(roomUuid))
    await loadPropertyDetail()
  } catch (error: any) {
    roomEditError.value = error?.data?.detail || error?.message || 'Unable to delete room.'
  }
}

function confirmPropertyRemoval() {
  showDeletePrompt.value = true
  propertyEditError.value = null
}

async function deletePropertyAndRedirect() {
  if (!property.value) return
  try {
    await deleteProperty(String(property.value.uuid))
    showDeletePrompt.value = false
    router.push('/')
  } catch (error: any) {
    propertyEditError.value = error?.data?.detail || error?.message || 'Unable to delete property.'
  }
}

async function uploadFile(prefix: string, file: File, counter: { value: number }): Promise<string> {
  counter.value += 1
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
    counter.value = Math.max(counter.value - 1, 0)
  }
}

onMounted(() => {
  const param = route.params.id
  if (typeof param === 'string' && param.length) {
    loadPropertyDetail()
  }
})

watch(
  () => route.params.id,
  (next) => {
    if (typeof next === 'string' && next.length) {
      isEditingProperty.value = false
      editingRoomId.value = null
      loadPropertyDetail()
    }
  },
)
</script>

<style scoped>
.host-property__actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  align-items: center;
  margin-left: auto;
}

.host-property__note {
  margin: 8px 0 16px;
  color: #8a7358;
  font-size: 0.9rem;
}

.host-property__message {
  margin: 16px 0;
  padding: 16px 18px;
  border-radius: 16px;
  font-size: 0.96rem;
  line-height: 1.4;
}

.host-property__message--error {
  background: rgba(225, 93, 69, 0.14);
  color: #7f3122;
}

.host-property__message--warning {
  background: rgba(254, 209, 120, 0.22);
  color: #7a4f02;
}

.host-property__message-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin-top: 12px;
}

.host-property__edit-card {
  margin-bottom: 32px;
}

.host-room-images {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  margin: 18px 0;
}

.host-room-images img {
  width: 110px;
  height: 90px;
  object-fit: cover;
  border-radius: 12px;
  box-shadow: 0 10px 22px rgba(41, 26, 14, 0.18);
}

.host-room-actions {
  display: flex;
  gap: 16px;
  margin-top: 12px;
}

.host-room-edit {
  margin-top: 18px;
  padding: 20px;
  border-radius: 18px;
  border: 1px dashed rgba(210, 160, 110, 0.6);
  background: rgba(255, 248, 236, 0.6);
}

.host-room-edit__actions {
  display: flex;
  gap: 12px;
  align-items: center;
}

.host-form-note {
  font-size: 0.85rem;
  color: #8a7358;
}

@media (max-width: 768px) {
  .host-property__actions {
    justify-content: flex-start;
    margin-top: 16px;
  }
}
</style>


