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

  const style = {
    version: 8,
    sources: {
      'osm-tiles': {
        type: 'raster',
        tiles: [
          'https://a.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://b.tile.openstreetmap.org/{z}/{x}/{y}.png',
          'https://c.tile.openstreetmap.org/{z}/{x}/{y}.png',
        ],
        tileSize: 256,
        attribution: '© OpenStreetMap contributors',
      },
    },
    layers: [
      {
        id: 'osm-tiles',
        type: 'raster',
        source: 'osm-tiles',
        minzoom: 0,
        maxzoom: 19,
      },
    ],
  }

  const map = new maplibre.Map({
    container: container.value,
    style,
    center: [props.longitude, props.latitude],
    zoom: props.zoom ?? 12,
    interactive: false,
  })

  map.addControl(new maplibre.AttributionControl({ compact: true }))
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
