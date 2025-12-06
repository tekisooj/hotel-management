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
              &lt;
            </button>
            <span class="host-month-label">{{ monthRangeLabel }}</span>
            <button class="host-btn host-btn--ghost" type="button" @click="goToNextMonth" :disabled="loadingBookings">
              &gt;
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
            <div v-if="availability.bookings?.length" class="host-booking-contacts">
              <p class="host-booking-contacts__title">Guest details</p>
              <ul class="host-booking-contacts__list">
                <li
                  v-for="booking in availability.bookings"
                  :key="booking.uuid"
                  class="host-booking-contacts__item"
                >
                  <div class="host-booking-contacts__name">
                    <strong>{{ guestFullName(booking) }}</strong>
                    <span class="host-booking-contacts__dates">
                      {{ new Date(booking.check_in).toLocaleDateString() }}
                      - {{ new Date(booking.check_out).toLocaleDateString() }}
                    </span>
                  </div>
                  <div class="host-booking-contacts__contact">
                    <span v-if="booking.guest_email">Email: {{ booking.guest_email }}</span>
                    <span v-if="booking.guest_phone">Phone: {{ booking.guest_phone }}</span>
                    <button
                      class="host-btn host-btn--ghost"
                      type="button"
                      :disabled="cancelling[booking.uuid]"
                      @click="onCancel(booking.uuid)"
                    >
                      {{ cancelling[booking.uuid] ? 'Cancelling…' : 'Cancel booking' }}
                    </button>
                  </div>
                </li>
              </ul>
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

const { getProperties, getBookings, cancelBooking } = useHostBff()

const properties = ref<PropertyDetail[]>([])
const propertiesLoading = ref(true)
const selectedPropertyUuid = ref<string>('')

const roomAvailabilities = ref<RoomAvailability[]>([])
const loadingBookings = ref(false)
const bookingsError = ref<string | null>(null)
const cancelling = ref<Record<string, boolean>>({})

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
    guestLastName: booking.guest_last_name,
    guestEmail: booking.guest_email,
    guestPhone: booking.guest_phone,
  }))
}

function formatMonth(month: { month: number; year: number }) {
  return new Date(month.year, month.month - 1, 1).toLocaleDateString(undefined, {
    month: 'long',
    year: 'numeric',
  })
}

function buildGuestLabel(booking: AvailabilityBooking): string {
  const first = (booking.guest_name || '').trim()
  const last = (booking.guest_last_name || '').trim()
  const fullName = [first, last].filter(Boolean).join(' ').trim()
  if (fullName) {
    return fullName.split(/\s+/)[0]
  }
  const email = (booking.guest_email || '').trim()
  if (email) {
    return email.split('@')[0]
  }
  return formatBookingLabel(booking.status)
}

function guestFullName(booking: AvailabilityBooking): string {
  const first = (booking.guest_name || '').trim()
  const last = (booking.guest_last_name || '').trim()
  const full = [first, last].filter(Boolean).join(' ').trim()
  if (full) return full
  if (booking.guest_email) return booking.guest_email
  return 'Guest'
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

async function onCancel(bookingUuid: string) {
  if (cancelling.value[bookingUuid]) return
  cancelling.value = { ...cancelling.value, [bookingUuid]: true }
  try {
    await cancelBooking(bookingUuid)
    roomAvailabilities.value = roomAvailabilities.value.map((availability) => ({
      ...availability,
      bookings: (availability.bookings || []).filter((b) => b.uuid !== bookingUuid),
    }))
  } catch {
    bookingsError.value = 'Unable to cancel this booking right now.'
  } finally {
    cancelling.value = { ...cancelling.value, [bookingUuid]: false }
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
.host-booking-contacts {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid rgba(0, 0, 0, 0.06);
  border-radius: 12px;
  background: #faf7f2;
}

.host-booking-contacts__title {
  margin: 0 0 8px;
  font-weight: 700;
  color: #2f261a;
}

.host-booking-contacts__list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.host-booking-contacts__item {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  padding: 10px 12px;
  border-radius: 10px;
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.03);
}

.host-booking-contacts__name {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.host-booking-contacts__dates {
  font-size: 0.9rem;
  color: #6a5b45;
}

.host-booking-contacts__contact {
  display: flex;
  flex-direction: column;
  gap: 6px;
  align-items: flex-end;
  color: #3a3124;
  font-size: 0.95rem;
}

@media (max-width: 640px) {
  .host-booking-contacts__item {
    flex-direction: column;
    align-items: flex-start;
  }

  .host-booking-contacts__contact {
    align-items: flex-start;
  }
}
</style>
