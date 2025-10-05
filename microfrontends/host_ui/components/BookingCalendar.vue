<template>
  <div class="booking-calendar">
    <div class="calendar-title">{{ monthLabel }}</div>
    <div class="calendar-grid">
      <div v-for="dayName in weekdays" :key="dayName" class="weekday">{{ dayName }}</div>
      <div
        v-for="day in days"
        :key="day.key"
        :class="['calendar-day', { outside: !day.inMonth, booked: day.isBooked }]"
      >
        <span class="date">{{ day.date.getDate() }}</span>
        <span v-if="day.isStart" class="booking-label">{{ day.bookingLabel }}</span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import type { CalendarBooking } from '@/types/Availability'

const props = defineProps<{
  month: number
  year: number
  bookings: CalendarBooking[]
}>()

const weekdays = ['S', 'M', 'T', 'W', 'T', 'F', 'S']

function stripTime(date: Date) {
  const d = new Date(date)
  d.setHours(0, 0, 0, 0)
  return d
}

const normalizedBookings = computed(() =>
  props.bookings.map((booking) => ({
    ...booking,
    checkIn: stripTime(booking.checkIn),
    checkOut: stripTime(booking.checkOut),
  }))
)

const firstDayOfMonth = computed(() => new Date(props.year, props.month - 1, 1))

const days = computed(() => {
  const result: Array<{
    key: string
    date: Date
    inMonth: boolean
    isBooked: boolean
    isStart: boolean
    bookingLabel: string
  }> = []
  const start = new Date(firstDayOfMonth.value)
  const startDay = start.getDay()
  start.setDate(start.getDate() - startDay)

  for (let i = 0; i < 42; i += 1) {
    const current = new Date(start)
    current.setDate(start.getDate() + i)

    const booking = normalizedBookings.value.find(
      (entry) => current >= entry.checkIn && current < entry.checkOut
    )

    result.push({
      key: current.toISOString().slice(0, 10),
      date: current,
      inMonth: current.getMonth() === firstDayOfMonth.value.getMonth(),
      isBooked: Boolean(booking),
      isStart: Boolean(booking && current.getTime() === booking.checkIn.getTime()),
      bookingLabel: booking?.label ?? '',
    })
  }

  return result
})

const monthLabel = computed(() =>
  firstDayOfMonth.value.toLocaleDateString(undefined, { month: 'long', year: 'numeric' })
)
</script>

<style scoped>
.booking-calendar {
  background: #fff;
  border: 1px solid rgba(0, 0, 0, 0.05);
  border-radius: 12px;
  padding: 16px;
  height: 100%;
}

.calendar-title {
  font-weight: 600;
  margin-bottom: 12px;
}

.calendar-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 4px;
  font-size: 0.85rem;
}

.weekday {
  text-align: center;
  font-weight: 600;
  color: #8a8a8a;
  padding-bottom: 4px;
}

.calendar-day {
  position: relative;
  min-height: 56px;
  border-radius: 8px;
  padding: 6px;
  color: #3a3a3a;
  background: transparent;
  transition: background-color 0.2s ease-in-out;
}

.calendar-day .date {
  font-size: 0.9rem;
  font-weight: 500;
}

.calendar-day.booked {
  background: #d7e9cf;
}

.calendar-day.booked .date {
  font-weight: 600;
}

.calendar-day.outside {
  color: #c0c0c0;
}

.booking-label {
  display: block;
  font-size: 0.7rem;
  margin-top: 6px;
  font-weight: 600;
  color: #4f6b45;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
</style>
