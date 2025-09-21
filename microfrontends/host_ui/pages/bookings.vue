<template>
  <div class="bookings-page">
    <div class="container py-4">
      <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-4">
        <div>
          <h1 class="page-title">Bookings for <span class="highlight">{{ selectedProperty?.name || 'N/A' }}</span></h1>
          <p v-if="selectedProperty?.address" class="property-address">{{ selectedProperty.address }}</p>
        </div>
        <div class="property-picker">
          <label class="form-label text-muted mb-1">Property</label>
          <select
            class="form-select"
            v-model="selectedPropertyUuid"
            :disabled="propertiesLoading || !properties.length"
          >
            <option value="" disabled>Select a property</option>
            <option v-for="property in properties" :key="property.uuid" :value="property.uuid">
              {{ property.name }}
            </option>
          </select>
        </div>
      </div>

      <div class="d-flex flex-wrap justify-content-between align-items-center gap-3 mb-3">
        <div class="d-flex align-items-center gap-2">
          <button class="btn btn-outline-secondary btn-sm" @click="goToPreviousMonth" :disabled="loadingBookings">
            &lt;
          </button>
          <span class="month-range">{{ monthRangeLabel }}</span>
          <button class="btn btn-outline-secondary btn-sm" @click="goToNextMonth" :disabled="loadingBookings">
            &gt;
          </button>
        </div>
        <div class="legend d-flex align-items-center gap-2">
          <span class="legend-box"></span>
          <small class="text-muted">Booked</small>
        </div>
      </div>

      <div v-if="bookingsError" class="alert alert-warning">{{ bookingsError }}</div>

      <div v-if="loadingBookings" class="text-center py-5">
        <div class="spinner-border text-secondary" role="status">
          <span class="visually-hidden">Loading...</span>
        </div>
      </div>

      <div v-else-if="!roomAvailabilities.length" class="empty-state">
        <h2>No bookings yet</h2>
        <p>Select another month or property to see upcoming reservations.</p>
      </div>

      <div v-else class="d-flex flex-column gap-4">
        <div
          v-for="availability in roomAvailabilities"
          :key="availability.uuid"
          class="card room-card shadow-sm"
        >
          <div class="card-body">
            <div class="d-flex flex-wrap justify-content-between align-items-start gap-3 mb-3">
              <div>
                <h3 class="room-title">{{ availability.name }}</h3>
                <div class="text-muted small">
                  Max. {{ availability.capacity }} {{ availability.capacity === 1 ? 'Guest' : 'Guests' }} |
                  ${{ availability.price_per_night }}/night
                </div>
              </div>
              <div v-if="availability.property?.name" class="text-muted small text-end">
                {{ availability.property.name }}
              </div>
            </div>
            <div class="row g-3">
              <div
                v-for="month in visibleMonths"
                :key="`${availability.uuid}-${month.year}-${month.month}`"
                class="col-12 col-md-6"
              >
                <BookingCalendar
                  :month="month.month"
                  :year="month.year"
                  :bookings="calendarBookings[availability.uuid] || []"
                />
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue'
import BookingCalendar from '@/components/BookingCalendar.vue'
import { useHostBff } from '@/api/hostBff'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { RoomAvailability, CalendarBooking, AvailabilityBooking } from '@/types/Availability'

const { getProperties, getBookings } = useHostBff()

const properties = ref<PropertyDetail[]>([])
const propertiesLoading = ref(true)
const selectedPropertyUuid = ref<string>('')

const roomAvailabilities = ref<RoomAvailability[]>([])
const loadingBookings = ref(false)
const bookingsError = ref<string | null>(null)

const currentMonth = ref(startOfMonth(new Date()))

const propertiesReady = computed(() => properties.value.length > 0)
const selectedProperty = computed(() =>
  properties.value.find((item) => item.uuid === selectedPropertyUuid.value)
)

const rangeStart = computed(() => startOfMonth(currentMonth.value))
const rangeEnd = computed(() => {
  const end = new Date(rangeStart.value)
  end.setMonth(end.getMonth() + 2)
  return end
})

const visibleMonths = computed(() => {
  const first = rangeStart.value
  const second = new Date(first.getFullYear(), first.getMonth() + 1, 1)
  return [
    { month: first.getMonth() + 1, year: first.getFullYear() },
    { month: second.getMonth() + 1, year: second.getFullYear() },
  ]
})

const monthRangeLabel = computed(() => {
  const [first, second] = visibleMonths.value
  return `${formatMonth(first)} - ${formatMonth(second)}`
})

const calendarBookings = computed<Record<string, CalendarBooking[]>>(() => {
  const record: Record<string, CalendarBooking[]> = {}
  roomAvailabilities.value.forEach((availability) => {
    record[availability.uuid] = (availability.bookings || []).map((booking) => ({
      uuid: booking.uuid,
      checkIn: new Date(booking.check_in),
      checkOut: new Date(booking.check_out),
      label: buildGuestLabel(booking),
      status: booking.status,
      guestName: booking.guest_name ?? undefined,
      guestEmail: booking.guest_email ?? undefined,
    }))
  })
  return record
})

onMounted(async () => {
  try {
    const fetched = await getProperties()
    properties.value = Array.isArray(fetched) ? fetched : []
    if (properties.value.length) {
      selectedPropertyUuid.value = properties.value[0].uuid || ''
    }
  } catch (error) {
    bookingsError.value = 'Unable to load properties right now.'
    properties.value = []
  } finally {
    propertiesLoading.value = false
  }
})

watch(
  () => selectedPropertyUuid.value,
  async (value, oldValue) => {
    if (!propertiesReady.value) {
      return
    }
    if (!value) {
      roomAvailabilities.value = []
      return
    }
    if (value !== oldValue) {
      await fetchBookings()
    }
  }
)

watch(
  () => `${rangeStart.value.getTime()}-${rangeEnd.value.getTime()}`,
  async () => {
    if (!selectedPropertyUuid.value) {
      return
    }
    await fetchBookings()
  }
)

async function fetchBookings() {
  if (!selectedPropertyUuid.value) {
    roomAvailabilities.value = []
    return
  }
  loadingBookings.value = true
  bookingsError.value = null
  try {
    const availabilities = await getBookings(selectedPropertyUuid.value, rangeStart.value, rangeEnd.value)
    roomAvailabilities.value = Array.isArray(availabilities) ? availabilities : []
  } catch (error) {
    bookingsError.value = 'Unable to load bookings for this property.'
    roomAvailabilities.value = []
  } finally {
    loadingBookings.value = false
  }
}

function goToPreviousMonth() {
  const previous = new Date(rangeStart.value)
  previous.setMonth(previous.getMonth() - 1)
  currentMonth.value = previous
}

function goToNextMonth() {
  const next = new Date(rangeStart.value)
  next.setMonth(next.getMonth() + 1)
  currentMonth.value = next
}

function formatMonth(month: { month: number; year: number }) {
  return new Date(month.year, month.month - 1, 1).toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })
}

function buildGuestLabel(booking: AvailabilityBooking): string {
  const fullName = (booking.guest_name || '').trim()
  if (fullName) {
    return fullName.split(/\s+/)[0]
  }
  const email = (booking.guest_email || '').trim()
  if (email) {
    return email.split('@')[0]
  }
  return formatBookingLabel(booking.status)
}

function formatBookingLabel(status: string) {
  switch (status) {
    case 'pending':
      return 'Pending'
    case 'cancelled':
      return 'Cancelled'
    case 'completed':
      return 'Completed'
    default:
      return 'Booked'
  }
}

function startOfMonth(date: Date) {
  const copy = new Date(date)
  copy.setDate(1)
  copy.setHours(0, 0, 0, 0)
  return copy
}
</script>

<style scoped>
.bookings-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #f7f1e8 0%, #fdfbf7 100%);
}

.page-title {
  font-size: 1.75rem;
  margin-bottom: 0.25rem;
}

.highlight {
  color: #805b2c;
}

.property-address {
  margin: 0;
  color: #8c8273;
}

.property-picker {
  min-width: 220px;
}

.month-range {
  font-weight: 600;
  font-size: 1rem;
}

.legend-box {
  width: 16px;
  height: 16px;
  border-radius: 4px;
  background: #d7e9cf;
  border: 1px solid rgba(0, 0, 0, 0.1);
}

.empty-state {
  background: #fff;
  border-radius: 16px;
  padding: 48px 32px;
  text-align: center;
  border: 1px dashed rgba(0, 0, 0, 0.1);
}

.empty-state h2 {
  margin-bottom: 8px;
  font-size: 1.4rem;
}

.room-card {
  border: none;
  border-radius: 18px;
}

.room-title {
  margin-bottom: 4px;
}
</style>

