<template>
  <div ref="container" class="mini-map"></div>
</template>

<script setup lang="ts">
const props = defineProps<{ latitude?: number; longitude?: number; zoom?: number }>()
const container = ref<HTMLDivElement | null>(null)

onMounted(() => {
  if (!container.value || props.latitude == null || props.longitude == null) return
  // @ts-ignore maplibregl is loaded via CDN in app head
  const map = new maplibregl.Map({
    container: container.value,
    style: `https://demotiles.maplibre.org/style.json`,
    center: [props.longitude, props.latitude],
    zoom: props.zoom ?? 12,
    interactive: false,
  })
  // @ts-ignore
  new maplibregl.Marker().setLngLat([props.longitude, props.latitude]).addTo(map)
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

