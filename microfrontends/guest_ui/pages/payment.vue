<template>
  <div class="payment-page">
    <div class="container">
      <div v-if="loading" class="payment-card placeholder">
        <p>Preparing your payment session...</p>
      </div>
      <div v-else-if="error" class="payment-card placeholder">
        <p>{{ error }}</p>
        <button class="btn btn-outline-primary" @click="returnToRoom">Back to room</button>
      </div>
      <div v-else-if="!room" class="payment-card placeholder">
        <p>Room details are unavailable. Please start the booking again.</p>
        <button class="btn btn-outline-primary" @click="goHome">Go home</button>
      </div>
      <div v-else class="payment-card card">
        <header class="payment-header">
          <div>
            <h1>Confirm your stay</h1>
            <p class="subtitle">{{ room.name }}, {{ property?.name || room.propertyUuid }}</p>
          </div>
          <div class="payment-amount" v-if="displayAmount">
            <span class="label">Total</span>
            <span class="value">${{ displayAmount }}</span>
          </div>
        </header>

        <section class="payment-summary">
          <div class="summary-row">
            <span class="summary-label">Check-in</span>
            <span class="summary-value">{{ formattedCheckIn }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Check-out</span>
            <span class="summary-value">{{ formattedCheckOut }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Guests</span>
            <span class="summary-value">{{ guests }}</span>
          </div>
          <div class="summary-row">
            <span class="summary-label">Nights</span>
            <span class="summary-value">{{ nights }}</span>
          </div>
          <div class="summary-row" v-if="pricePerNight">
            <span class="summary-label">Rate per night</span>
            <span class="summary-value">${{ formatPrice(pricePerNight) }}</span>
          </div>
        </section>

        <section class="payment-actions">
          <div id="paypal-button-container" class="paypal-container"></div>
          <p v-if="paymentError" class="payment-message error">{{ paymentError }}</p>
          <p v-if="paymentSuccess" class="payment-message success">
            Payment completed! Booking reference {{ bookingUuid }}.
          </p>
        </section>

        <footer class="payment-footer" v-if="propertyAddress">
          <p class="footer-title">Property address</p>
          <p class="footer-text">{{ propertyAddress }}</p>
        </footer>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useRuntimeConfig } from 'nuxt/app'
import { useGuestBff } from '@/api/guestBff'
import { useSearchStore } from '@/stores/search'
import type { Room } from '@/types/Room'
import type { PropertyDetail } from '@/types/PropertyDetail'

const route = useRoute()
const router = useRouter()
const config = useRuntimeConfig()
const { getRoom, getProperty, createPaymentOrder, capturePayment } = useGuestBff()
const store = useSearchStore()

const loading = ref(true)
const error = ref<string | null>(null)
const room = ref<Room | null>(null)
const property = ref<PropertyDetail | null>(null)
const orderId = ref<string | null>(null)
const orderAmount = ref<{ currency_code: string; value: string } | null>(null)
const paymentError = ref<string | null>(null)
const paymentSuccess = ref(false)
const bookingUuid = ref<string | null>(null)
const paypalButtonsRendered = ref(false)

const roomUuid = computed(() => (route.query.room as string) || (route.query.roomUuid as string) || '')
const checkIn = ref((route.query.checkIn as string) || (route.query.check_in as string) || '')
const checkOut = ref((route.query.checkOut as string) || (route.query.check_out as string) || '')
const guests = ref(Number(route.query.guests || route.query.capacity || store.lastSearch?.capacity || 1) || 1)

const pricePerNight = computed(() => {
  const raw = pick(room.value, 'pricePerNight', 'price_per_night')
  const numeric = typeof raw === 'number' ? raw : Number(raw)
  return Number.isFinite(numeric) ? numeric : 0
})

const nights = computed(() => {
  if (!checkIn.value || !checkOut.value) return 0
  const start = new Date(checkIn.value)
  const end = new Date(checkOut.value)
  const diff = (end.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)
  return diff > 0 ? Math.floor(diff) : 0
})

const totalPrice = computed(() => pricePerNight.value * nights.value)

const displayAmount = computed(() => {
  if (orderAmount.value?.value) return orderAmount.value.value
  if (!nights.value || !pricePerNight.value) return null
  return formatPrice(totalPrice.value)
})

const formattedCheckIn = computed(() => formatDate(checkIn.value))
const formattedCheckOut = computed(() => formatDate(checkOut.value))

const propertyAddress = computed(() => {
  if (!property.value) return ''
  return (
    property.value.fullAddress ||
    [property.value.address, property.value.city, property.value.state, property.value.country]
      .filter(Boolean)
      .join(', ')
  )
})

const paypalClientIdFromConfig = computed(() => (config.public.paypalClientId as string || '').trim())
const activePaypalClientId = ref<string | null>(paypalClientIdFromConfig.value || null)
let paypalSdkClientId: string | null = null
let paypalSdkLoading: Promise<void> | null = null
let initializeOrderPromise: Promise<void> | null = null

onMounted(async () => {
  if (!roomUuid.value || !checkIn.value || !checkOut.value) {
    error.value = 'Missing booking details. Please start again.'
    loading.value = false
    return
  }
  try {
    await hydrateRoom()
    await initializePaymentOrder(false)
    orderId.value = null
    await renderPayPalButtons()
  } catch (err: any) {
    error.value = parseError(err, 'Unable to prepare the payment page.')
  } finally {
    loading.value = false
  }
})

async function hydrateRoom() {
  let currentRoom = store.getRoom(roomUuid.value)
  if (!currentRoom) {
    const fetchedRoom = await getRoom(roomUuid.value)
    if (fetchedRoom) {
      store.setRoom(fetchedRoom)
      currentRoom = store.getRoom(roomUuid.value)
    }
  }
  if (!currentRoom) {
    throw new Error('Room not available for booking.')
  }
  room.value = currentRoom

  const propertyUuid =
    (route.query.property as string) ||
    pick(currentRoom, 'propertyUuid', 'property_uuid') ||
    undefined

  if (propertyUuid) {
    let existing = store.getProperty(propertyUuid)
    if (!existing) {
      const fetched = await getProperty(propertyUuid)
      if (fetched) {
        store.setProperty(fetched)
        existing = store.getProperty(propertyUuid) || fetched
      }
    }
    property.value = existing || null
  }
}

async function initializePaymentOrder(force = false) {
  if (!force && orderId.value) {
    return
  }
  if (initializeOrderPromise) {
    await initializeOrderPromise
    return
  }
  initializeOrderPromise = (async () => {
    const response = await createPaymentOrder({
      room_uuid: roomUuid.value,
      check_in: checkIn.value,
      check_out: checkOut.value,
      guests: guests.value,
    })
    orderId.value = response.order_id
    orderAmount.value = response.amount

    const responseClientId =
      typeof response.paypal_client_id === 'string' ? response.paypal_client_id.trim() : ''
    const fallbackClientId = paypalClientIdFromConfig.value || null
    const nextClientId = responseClientId || fallbackClientId

    if (!nextClientId) {
      throw new Error('PayPal client ID is not configured.')
    }

    const clientIdChanged = activePaypalClientId.value !== nextClientId
    activePaypalClientId.value = nextClientId
    if (clientIdChanged) {
      paypalButtonsRendered.value = false
    }

    await ensurePayPalSdk(nextClientId)
  })()

  try {
    await initializeOrderPromise
  } finally {
    initializeOrderPromise = null
  }
}

async function ensurePayPalSdk(clientId: string) {
  if (typeof window === 'undefined') return
  if (!clientId) {
    throw new Error('PayPal client ID is not configured.')
  }

  if (paypalSdkClientId === clientId && (window as any).paypal?.Buttons) {
    return
  }

  if (paypalSdkLoading) {
    try {
      await paypalSdkLoading
      if (paypalSdkClientId === clientId && (window as any).paypal?.Buttons) {
        return
      }
    } catch {
      // fall through to reload
    }
  }

  const existingScript = document.getElementById('paypal-sdk') as HTMLScriptElement | null
  if (existingScript) {
    const existingId =
      existingScript.getAttribute('data-client-id') ||
      (existingScript.src ? new URL(existingScript.src, window.location.origin).searchParams.get('client-id') : '')
    if (existingId === clientId && (window as any).paypal?.Buttons) {
      paypalSdkClientId = clientId
      return
    }
    existingScript.remove()
    paypalButtonsRendered.value = false
  }

  delete (window as any).paypal
  paypalButtonsRendered.value = false
  paypalSdkClientId = clientId

  paypalSdkLoading = new Promise<void>((resolve, reject) => {
    const script = document.createElement('script')
    script.id = 'paypal-sdk'
    script.src = `https://www.paypal.com/sdk/js?client-id=${encodeURIComponent(clientId)}&currency=USD&intent=CAPTURE&components=buttons`
    script.setAttribute('data-client-id', clientId)
    script.onload = () => resolve()
    script.onerror = () => reject(new Error('Unable to load PayPal SDK.'))
    document.head.appendChild(script)
  })

  try {
    await paypalSdkLoading
  } finally {
    paypalSdkLoading = null
  }
}

async function renderPayPalButtons(forceReload = false) {
  if (typeof window === 'undefined') return

  let clientId = activePaypalClientId.value || paypalClientIdFromConfig.value || null
  if (!clientId) {
    await initializePaymentOrder(true)
    clientId = activePaypalClientId.value || paypalClientIdFromConfig.value || null
  }

  if (!clientId) {
    throw new Error('PayPal client ID is not configured.')
  }

  await ensurePayPalSdk(clientId)

  const paypal = (window as any).paypal
  if (!paypal?.Buttons) {
    throw new Error('PayPal Buttons are not available.')
  }

  if (paypalButtonsRendered.value && !forceReload) {
    return
  }

  const container = document.getElementById('paypal-button-container') as HTMLElement | null
  if (!container) {
    throw new Error('PayPal button container is not available.')
  }

  container.innerHTML = ''

  try {
    paypalButtonsRendered.value = true
    await paypal.Buttons({
      style: {
        layout: 'vertical',
        shape: 'rect',
        label: 'pay',
      },
      createOrder: async () => {
        paymentError.value = null
        paymentSuccess.value = false
        bookingUuid.value = null
        try {
          await initializePaymentOrder(true)
          if (!orderId.value) {
            throw new Error('Unable to create PayPal order.')
          }
          return orderId.value
        } catch (err) {
          paymentError.value = parseError(err, 'Unable to create the PayPal order.')
          throw err
        }
      },
      onApprove: async (data: any) => {
        paymentError.value = null
        try {
          const result = await capturePayment({
            order_id: data.orderID,
            room_uuid: roomUuid.value,
            check_in: checkIn.value,
            check_out: checkOut.value,
            guests: guests.value,
          })
          bookingUuid.value = String(result.booking_uuid)
          orderAmount.value = result.amount
          paymentSuccess.value = true
          orderId.value = null
        } catch (err: any) {
          paymentError.value = parseError(err, 'Something went wrong while processing the payment.')
        }
      },
      onCancel: () => {
        paymentError.value = 'Payment was cancelled. You can try again when ready.'
        orderId.value = null
      },
      onError: (err: any) => {
        paymentError.value = parseError(err, 'Something went wrong while processing the payment.')
        orderId.value = null
      },
    }).render(container)
  } catch (err) {
    paypalButtonsRendered.value = false
    throw err
  }
}

function formatPrice(value: number) {
  return value.toFixed(2)
}

function formatDate(value: string) {
  if (!value) return ''
  try {
    return new Date(value).toLocaleDateString(undefined, {
      year: 'numeric',
      month: 'short',
      day: 'numeric',
    })
  } catch (err) {
    return value
  }
}

function pick(source: any, camel: string, snake: string) {
  if (!source) return undefined
  if (source[camel] !== undefined && source[camel] !== null) return source[camel]
  return source[snake]
}

function parseError(err: any, fallback: string): string {
  return (
    err?.response?.data?.detail ||
    err?.data?.detail ||
    err?.message ||
    fallback
  )
}

function goHome() {
  router.push('/')
}

function returnToRoom() {
  const targetUuid = room.value?.uuid || roomUuid.value
  if (targetUuid) {
    router.push({
      path: `/room/${targetUuid}`,
      query: {
        checkIn: checkIn.value,
        checkOut: checkOut.value,
        guests: String(guests.value),
      },
    })
  } else {
    goHome()
  }
}
</script>

<style scoped>
.payment-page {
  min-height: 100vh;
  padding: 32px 0;
  background: #f9f5ee;
  color: #2f261a;
}

.container {
  max-width: 720px;
  margin: 0 auto;
  padding: 0 20px;
}

.payment-card {
  border-radius: 24px;
  background: #fffdf8;
  box-shadow: 0 18px 38px rgba(33, 20, 6, 0.1);
  padding: 28px 26px;
  display: flex;
  flex-direction: column;
  gap: 24px;
}

.payment-card.placeholder {
  text-align: center;
}

.payment-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
}

.payment-header h1 {
  margin: 0 0 6px;
  font-size: 1.9rem;
}

.payment-header .subtitle {
  margin: 0;
  color: #6f563c;
}

.payment-amount {
  text-align: right;
}

.payment-amount .label {
  display: block;
  color: #6f563c;
  font-size: 0.85rem;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.payment-amount .value {
  font-size: 1.8rem;
  font-weight: 700;
}

.payment-summary {
  background: #fef7eb;
  border-radius: 18px;
  padding: 18px 20px;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.summary-row {
  display: flex;
  justify-content: space-between;
  font-size: 0.98rem;
}

.summary-label {
  color: #6f563c;
}

.summary-value {
  font-weight: 600;
}

.payment-actions {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.paypal-container {
  min-height: 45px;
}

.payment-message {
  margin: 0;
  font-weight: 600;
}

.payment-message.error {
  color: #b03a2e;
}

.payment-message.success {
  color: #2e7d32;
}

.payment-footer {
  border-top: 1px solid rgba(47, 38, 26, 0.08);
  padding-top: 18px;
}

.footer-title {
  margin: 0 0 4px;
  font-size: 0.9rem;
  text-transform: uppercase;
  letter-spacing: 0.06em;
  color: #6f563c;
}

.footer-text {
  margin: 0;
}

@media (max-width: 640px) {
  .payment-header {
    flex-direction: column;
    align-items: stretch;
  }

  .payment-amount {
    text-align: left;
  }
}
</style>

