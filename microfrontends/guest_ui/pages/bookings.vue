<template>
  <div class="bookings-page">
    <section class="bookings-hero">
      <div class="bookings-hero__content">
        <div>
          <p class="eyebrow">Your stays</p>
          <h1>My bookings</h1>
          <p class="lead">
            Review upcoming trips, keep track of past stays, and jump back to any property or room with full details.
          </p>
          <div class="bookings-hero__actions">
            <button class="cta" type="button" @click="goToSearch">Book another stay</button>
            <button class="ghost" type="button" :disabled="refreshing" @click="refresh">
              {{ refreshing ? 'Refreshing…' : 'Refresh' }}
            </button>
          </div>
          <div class="bookings-stats">
            <div class="stat">
              <p class="stat__label">Upcoming</p>
              <p class="stat__value">{{ upcomingCount }}</p>
            </div>
            <div class="stat">
              <p class="stat__label">Completed</p>
              <p class="stat__value">{{ pastCount }}</p>
            </div>
          </div>
        </div>
        <div class="bookings-hero__badge">
          <span>Reservations</span>
        </div>
      </div>
    </section>

    <section class="bookings-content">
      <div v-if="loading" class="state-card">Loading your bookings…</div>

      <div v-else-if="error" class="state-card">
        <p>{{ error }}</p>
        <button class="ghost" type="button" @click="refresh">Try again</button>
      </div>

      <div v-else-if="!bookingCards.length" class="state-card empty">
        <h2>No bookings yet</h2>
        <p>Ready for your next trip? Find a property to get started.</p>
        <button class="cta" type="button" @click="goToSearch">Start exploring</button>
      </div>

      <div v-else class="booking-list">
        <div
          v-for="item in bookingCards"
          :key="item.booking.uuid"
          class="booking-card"
        >
          <HotelElement :hotel="propertyForCard(item)">
            <template #extra>
              <div class="booking-meta">
                <div class="booking-dates">
                  <div class="booking-dates__row">
                    <span class="label">Check-in</span>
                    <span class="value">{{ formatDate(item.booking.checkIn) }}</span>
                  </div>
                  <div class="booking-dates__row">
                    <span class="label">Check-out</span>
                    <span class="value">{{ formatDate(item.booking.checkOut) }}</span>
                  </div>
                  <div class="booking-dates__row">
                    <span class="label">Nights</span>
                    <span class="value">{{ bookingNights(item.booking) }}</span>
                  </div>
                </div>
                <div class="booking-room">
                  <p class="label">Room</p>
                  <p class="value">{{ item.room?.name || 'Room details unavailable' }}</p>
                  <p v-if="item.room?.capacity" class="muted">
                    Fits {{ item.room.capacity }} {{ item.room.capacity === 1 ? 'guest' : 'guests' }}
                  </p>
                </div>
                <div class="booking-status">
                  <span class="status-pill" :class="statusTone(item.booking.status)">
                    {{ formatStatus(item.booking.status) }}
                  </span>
                  <p class="muted">Booked on {{ formatDate(item.booking.createdAt) }}</p>
                  <div class="booking-actions">
                    <button
                      class="ghost"
                      type="button"
                      @click="viewProperty(item)"
                      :disabled="!propertyForCard(item)?.uuid"
                    >
                      View property
                    </button>
                    <button
                      class="ghost"
                      type="button"
                      @click="viewRoom(item)"
                      :disabled="!item.room?.uuid"
                    >
                      View room
                    </button>
                    <button
                      v-if="canCancel(item.booking)"
                      class="danger"
                      type="button"
                      :disabled="cancelling[item.booking.uuid]"
                      @click="cancel(item.booking.uuid)"
                    >
                      {{ cancelling[item.booking.uuid] ? 'Cancelling…' : 'Cancel booking' }}
                    </button>
                  </div>
                </div>
              </div>
            </template>
          </HotelElement>
        </div>
      </div>
    </section>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import HotelElement from '@/components/HotelElement.vue'
import { useGuestBff } from '@/api/guestBff'
import { useSearchStore } from '@/stores/search'
import type { Booking } from '@/types/Booking'
import type { PropertyDetail } from '@/types/PropertyDetail'
import type { Room } from '@/types/Room'
import type { BookingStatus } from '@/types/BookingStatus'

type BookingCard = {
  booking: Booking
  room: Room | null
  property: PropertyDetail | null
}

const { getMyBookings, cancelMyBooking, getRoom, getProperty } = useGuestBff()
const store = useSearchStore()
const router = useRouter()

const loading = ref(true)
const refreshing = ref(false)
const error = ref<string | null>(null)
const bookingCards = ref<BookingCard[]>([])
const cancelling = ref<Record<string, boolean>>({})

const upcomingCount = computed(() =>
  bookingCards.value.filter((item) => isUpcoming(item.booking)).length
)
const pastCount = computed(() =>
  bookingCards.value.filter((item) => !isUpcoming(item.booking)).length
)

onMounted(() => {
  refresh()
})

async function refresh() {
  if (refreshing.value) return
  refreshing.value = true
  error.value = null
  if (!bookingCards.value.length) {
    loading.value = true
  }
  try {
    const res = await getMyBookings()
    const sorted = (Array.isArray(res) ? res : []).sort(
      (a, b) => b.checkIn.getTime() - a.checkIn.getTime()
    )
    bookingCards.value = await enrichBookings(sorted)
  } catch (err: any) {
    error.value = parseError(err, 'Unable to load your bookings right now.')
    bookingCards.value = []
  } finally {
    loading.value = false
    refreshing.value = false
  }
}

async function enrichBookings(items: Booking[]): Promise<BookingCard[]> {
  const roomIds = Array.from(new Set(items.map((b) => b.roomUuid).filter(Boolean)))
  const roomEntries = await Promise.all(
    roomIds.map(async (uuid) => {
      try {
        const room = await getRoom(uuid)
        if (room) {
          store.setRoom(room)
          return [uuid, room as Room] as const
        }
      } catch (err) {
        console.error('Failed to load room', uuid, err)
      }
      return [uuid, null] as const
    })
  )
  const roomMap = Object.fromEntries(roomEntries) as Record<string, Room | null>

  const propertyIds = Array.from(
    new Set(
      roomEntries
        .map(([, room]) => pick(room, 'propertyUuid', 'property_uuid'))
        .filter(Boolean) as string[]
    )
  )

  const propertyEntries = await Promise.all(
    propertyIds.map(async (uuid) => {
      try {
        const property = await getProperty(uuid)
        if (property) {
          store.setProperty(property)
          return [uuid, property as PropertyDetail] as const
        }
      } catch (err) {
        console.error('Failed to load property', uuid, err)
      }
      return [uuid, null] as const
    })
  )
  const propertyMap = Object.fromEntries(propertyEntries) as Record<string, PropertyDetail | null>

  return items.map((booking) => {
    const room = roomMap[booking.roomUuid] || store.getRoom(booking.roomUuid) || null
    const propertyUuid = pick(room, 'propertyUuid', 'property_uuid')
    const property =
      (propertyUuid && (propertyMap[propertyUuid] || store.getProperty(propertyUuid))) || null
    return { booking, room, property }
  })
}

function propertyForCard(item: BookingCard): PropertyDetail {
  if (item.property) return item.property
  const fallbackName = item.room?.name ? `Room ${item.room.name}` : 'Property details unavailable'
  return {
    uuid: pick(item.room, 'propertyUuid', 'property_uuid'),
    userUuid: '',
    name: fallbackName,
    description: item.room?.description,
    country: '—',
    city: '—',
    address: '—',
    stars: 0,
    rooms: item.room ? [item.room] : [],
  }
}

function viewProperty(item: BookingCard) {
  const propertyUuid = propertyForCard(item)?.uuid
  if (!propertyUuid) return
  router.push({
    path: `/property/${propertyUuid}`,
    query: {
      checkIn: formatInputDate(item.booking.checkIn),
      checkOut: formatInputDate(item.booking.checkOut),
    },
  })
}

function viewRoom(item: BookingCard) {
  if (!item.room?.uuid) return
  const propertyUuid = propertyForCard(item)?.uuid
  const query: Record<string, string> = {
    checkIn: formatInputDate(item.booking.checkIn),
    checkOut: formatInputDate(item.booking.checkOut),
  }
  if (propertyUuid) {
    query.property = String(propertyUuid)
  }
  router.push({ path: `/room/${item.room.uuid}`, query })
}

async function cancel(bookingUuid: string) {
  if (cancelling.value[bookingUuid]) return
  cancelling.value = { ...cancelling.value, [bookingUuid]: true }
  try {
    await cancelMyBooking(bookingUuid)
    bookingCards.value = bookingCards.value.filter((item) => item.booking.uuid !== bookingUuid)
  } catch (err: any) {
    error.value = parseError(err, 'Unable to cancel this booking right now.')
  } finally {
    cancelling.value = { ...cancelling.value, [bookingUuid]: false }
  }
}

function canCancel(booking: Booking) {
  const status = (booking.status || '').toString().toLowerCase() as BookingStatus
  const hasStarted = new Date(booking.checkIn).getTime() <= Date.now()
  return status !== 'cancelled' && status !== 'completed' && !hasStarted
}

function bookingNights(booking: Booking) {
  const diff =
    new Date(booking.checkOut).getTime() - new Date(booking.checkIn).getTime()
  const nights = Math.floor(diff / (1000 * 60 * 60 * 24))
  return nights > 0 ? nights : 0
}

function isUpcoming(booking: Booking) {
  return new Date(booking.checkOut).getTime() >= Date.now()
}

function formatStatus(status: BookingStatus | string) {
  const normalized = (status || '').toString().toLowerCase()
  switch (normalized) {
    case 'confirmed':
      return 'Confirmed'
    case 'completed':
      return 'Completed'
    case 'cancelled':
      return 'Cancelled'
    default:
      return 'Pending'
  }
}

function statusTone(status: BookingStatus | string) {
  const normalized = (status || '').toString().toLowerCase()
  switch (normalized) {
    case 'confirmed':
      return 'status-pill--success'
    case 'completed':
      return 'status-pill--muted'
    case 'cancelled':
      return 'status-pill--danger'
    default:
      return 'status-pill--warning'
  }
}

function formatDate(value: Date | string | undefined) {
  if (!value) return '—'
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return '—'
  return date.toLocaleDateString(undefined, {
    weekday: 'short',
    month: 'short',
    day: 'numeric',
    year: 'numeric',
  })
}

function formatInputDate(value: Date | string | undefined) {
  if (!value) return ''
  const date = value instanceof Date ? value : new Date(value)
  if (Number.isNaN(date.getTime())) return ''
  return date.toISOString().slice(0, 10)
}

function parseError(err: any, fallback: string) {
  return (
    err?.response?.data?.detail ||
    err?.data?.detail ||
    err?.message ||
    fallback
  )
}

function pick(source: any, camel: string, snake: string) {
  if (!source) return undefined
  if (source[camel] !== undefined && source[camel] !== null) return source[camel]
  return source[snake]
}

function goToSearch() {
  router.push('/')
}
</script>

<style scoped>
.bookings-page {
  min-height: 100vh;
  background: linear-gradient(180deg, #fef9f1 0%, #f7efe4 45%, #f4ede4 100%);
  color: #2f261a;
}

.bookings-hero {
  background: linear-gradient(120deg, rgba(39, 24, 10, 0.85), rgba(39, 24, 10, 0.55)),
    url('https://images.unsplash.com/photo-1522708323590-d24dbb6b0267?auto=format&fit=crop&w=1400&q=80')
      center/cover no-repeat;
  padding: 48px 20px 64px;
  border-bottom-left-radius: 44px;
  border-bottom-right-radius: 44px;
  box-shadow: 0 24px 60px rgba(17, 10, 4, 0.35);
}

.bookings-hero__content {
  max-width: 1100px;
  margin: 0 auto;
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 24px;
  color: #fff6ea;
}

.bookings-hero h1 {
  margin: 6px 0 12px;
  font-size: clamp(2.2rem, 4vw, 3rem);
}

.bookings-hero .lead {
  max-width: 700px;
  color: rgba(255, 247, 234, 0.9);
}

.bookings-hero__actions {
  margin: 20px 0;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.bookings-hero__badge {
  align-self: flex-start;
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.25);
  padding: 12px 16px;
  border-radius: 14px;
  font-weight: 700;
  letter-spacing: 0.05em;
}

.bookings-stats {
  display: flex;
  gap: 16px;
  margin-top: 12px;
}

.stat {
  background: rgba(255, 255, 255, 0.12);
  border: 1px solid rgba(255, 255, 255, 0.24);
  border-radius: 14px;
  padding: 12px 16px;
  min-width: 110px;
}

.stat__label {
  margin: 0;
  font-size: 0.9rem;
  color: rgba(255, 247, 234, 0.85);
}

.stat__value {
  margin: 6px 0 0;
  font-size: 1.6rem;
  font-weight: 700;
}

.bookings-content {
  max-width: 1100px;
  margin: -40px auto 80px;
  padding: 0 20px 20px;
}

.state-card {
  background: #fffdf8;
  border-radius: 24px;
  padding: 28px 24px;
  box-shadow: 0 18px 40px rgba(33, 20, 6, 0.12);
  text-align: center;
}

.state-card.empty h2 {
  margin-top: 0;
}

.booking-list {
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.booking-card {
  background: #fffdf8;
  border-radius: 24px;
  padding: 22px 20px;
  box-shadow: 0 18px 40px rgba(33, 20, 6, 0.12);
  border: 1px solid rgba(41, 24, 9, 0.06);
}

.booking-meta {
  display: grid;
  grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
  gap: 14px;
  padding: 10px 12px;
  background: #f9f1e5;
  border-radius: 16px;
}

.booking-dates__row,
.booking-room,
.booking-status {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.label {
  font-size: 0.85rem;
  letter-spacing: 0.06em;
  text-transform: uppercase;
  color: #7a5e44;
}

.value {
  font-weight: 700;
}

.muted {
  margin: 0;
  color: #6f563c;
}

.booking-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 8px;
}

.cta,
.ghost,
.danger {
  border: none;
  border-radius: 12px;
  padding: 10px 16px;
  font-weight: 700;
  cursor: pointer;
}

.cta {
  background: linear-gradient(135deg, #ffb16f, #e2732d);
  color: #1f140a;
}

.ghost {
  background: rgba(255, 252, 246, 0.7);
  border: 1px solid rgba(125, 102, 71, 0.3);
  color: #3b2b19;
}

.danger {
  background: #b03a2e;
  color: #fffaf4;
}

.cta:disabled,
.ghost:disabled,
.danger:disabled {
  opacity: 0.65;
  cursor: not-allowed;
}

.status-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  border-radius: 999px;
  font-weight: 700;
  font-size: 0.9rem;
}

.status-pill--success {
  background: rgba(53, 129, 89, 0.16);
  color: #2e7d51;
}

.status-pill--warning {
  background: rgba(223, 151, 65, 0.16);
  color: #b2691c;
}

.status-pill--danger {
  background: rgba(176, 58, 46, 0.16);
  color: #9c2f23;
}

.status-pill--muted {
  background: rgba(64, 55, 44, 0.14);
  color: #3f3327;
}

.eyebrow {
  text-transform: uppercase;
  letter-spacing: 0.28rem;
  font-size: 0.85rem;
  color: rgba(255, 247, 234, 0.75);
  margin: 0;
}

@media (max-width: 768px) {
  .bookings-hero {
    border-bottom-left-radius: 28px;
    border-bottom-right-radius: 28px;
  }

  .bookings-hero__content {
    flex-direction: column;
  }

  .booking-meta {
    grid-template-columns: 1fr;
  }
}
</style>
