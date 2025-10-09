<template>
  <NuxtLayout>
    <NuxtPage />
  </NuxtLayout>
</template>

<script setup lang="ts">
import { useHead } from 'nuxt/app'

useHead({
  bodyAttrs: {
    class: 'host-body'
  }
})
</script>

