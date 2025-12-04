<template>
  <div class="host-page host-page--bookings">
    <section class="host-section">
      <header class="host-section__header">
        <p class="host-hero__eyebrow">Calendar</p>
        <h1 class="host-section__title">Booking overview</h1>
        <p class="host-section__subtitle">
          Track upcoming stays and availability for each of your properties across the next two months.
        </p>
      </header>
      <div class="host-card host-card--bookings">
        <div class="host-bookings-header">
          <div>
            <h2 class="host-subsection-title">
              Bookings for <span class="highlight">{{ selectedProperty?.name || 'Select a property' }}</span>
            </h2>
            <p v-if="selectedProperty?.address" class="host-subtext">{{ selectedProperty.address }}</p>
          </div>
          <div class="host-property-picker">
            <label class="host-label" for="property-select">Property</label>
            <select
              id="property-select"
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

        <div class="host-bookings-toolbar">
          <div class="host-month-nav">
            <button class="host-btn host-btn--ghost" type="button" @click="goToPreviousMonth" :disabled="loadingBookings">
              ‹
            </button>
            <span class="host-month-label">{{ monthRangeLabel }}</span>
            <button class="host-btn host-btn--ghost" type="button" @click="goToNextMonth" :disabled="loadingBookings">
              ›
            </button>
          </div>
          <div class="host-legend">
            <span class="host-legend-box"></span>
            <small>Booked</small>
          </div>
        </div>

        <p v-if="bookingsError" class="host-alert">{{ bookingsError }}</p>

        <div v-if="loadingBookings" class="host-empty">Loading bookings…</div>

        <div v-else-if="!roomAvailabilities.length" class="host-empty-card">
          <h2>No bookings yet</h2>
          <p>Select another month or property to see upcoming reservations.</p>
        </div>

        <div v-else class="host-calendar-grid">
          <div
            v-for="availability in roomAvailabilities"
            :key="availability.uuid"
            class="host-calendar-card"
          >
            <div class="host-calendar-card__header">
              <div>
                <h3 class="host-calendar-card__title">{{ availability.name }}</h3>
                <p class="host-calendar-card__meta">
                  Max. {{ availability.capacity }} {{ availability.capacity === 1 ? 'guest' : 'guests' }} · ${{ availability.price_per_night }}/night
                </p>
              </div>
              <span v-if="availability.property?.name" class="host-calendar-card__property">
                {{ availability.property.name }}
              </span>
            </div>
            <div class="host-calendar-grid">
              <div
                v-for="month in visibleMonths"
                :key="`${availability.uuid}-${month.year}-${month.month}`"
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
    </section>
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

const calendarBookings = computed<Record<string, CalendarBooking[]>>(() => {
  const record: Record<string, CalendarBooking[]> = {}
  for (const availability of roomAvailabilities.value) {
    record[availability.uuid] = buildCalendarBookings(availability.bookings || [])
  }
  return record
})

const monthRangeLabel = computed(() => {
  const labels = visibleMonths.value.map(formatMonth)
  return labels.join(' · ')
})

onMounted(async () => {
  await fetchProperties()
})

watch(selectedPropertyUuid, () => {
  if (selectedPropertyUuid.value) {
    fetchBookings()
  }
})

watch(rangeStart, () => {
  if (selectedPropertyUuid.value) {
    fetchBookings()
  }
})

async function fetchProperties() {
  propertiesLoading.value = true
  try {
    const response = await getProperties()
    properties.value = Array.isArray(response) ? response : []
    if (properties.value.length && !selectedPropertyUuid.value) {
      selectedPropertyUuid.value = properties.value[0].uuid || ''
    }
  } finally {
    propertiesLoading.value = false
  }
}

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
  } catch {
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

function buildCalendarBookings(bookings: AvailabilityBooking[]): CalendarBooking[] {
  return bookings.map((booking) => ({
    uuid: booking.uuid,
    checkIn: new Date(booking.check_in),
    checkOut: new Date(booking.check_out),
    label: buildGuestLabel(booking),
    status: booking.status,
    guestName: booking.guest_name,
    guestEmail: booking.guest_email,
  }))
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
    return fullName.split(/\\s+/)[0]
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


