export interface AvailabilityBooking {
  uuid: string
  user_uuid: string
  room_uuid: string
  check_in: string
  check_out: string
  total_price: number
  status: string
  created_at: string
  updated_at: string
  guest_name?: string
  guest_email?: string
}

export interface AvailabilityRoom {
  uuid: string
  property_uuid?: string
  name: string
  description?: string
  capacity: number
  room_type: string
  price_per_night: number
  min_price_per_night: number
  max_price_per_night: number
}

export interface RoomAvailability extends AvailabilityRoom {
  property?: {
    uuid?: string
    name: string
    address: string
  }
  bookings: AvailabilityBooking[]
}

export interface CalendarBooking {
  uuid: string
  checkIn: Date
  checkOut: Date
  label: string
  status: string
  guestName?: string
  guestEmail?: string
}
