<template>
  <div ref="container" class="mini-map"></div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

const props = defineProps<{ latitude?: number; longitude?: number; zoom?: number }>()
const container = ref<HTMLDivElement | null>(null)

onMounted(() => {
  if (!container.value || props.latitude == null || props.longitude == null) return
  if (typeof window === 'undefined') return
  const maplibre = (window as any).maplibregl
  if (!maplibre?.Map) return

  const map = new maplibre.Map({
    container: container.value,
    style: 'https://demotiles.maplibre.org/style.json',
    center: [props.longitude, props.latitude],
    zoom: props.zoom ?? 12,
    interactive: false,
  })

  new maplibre.Marker().setLngLat([props.longitude, props.latitude]).addTo(map)
})
</script>

<style scoped>
.mini-map {
  width: 220px;
  height: 160px;
  border-radius: 8px;
  overflow: hidden;
}
</style>
