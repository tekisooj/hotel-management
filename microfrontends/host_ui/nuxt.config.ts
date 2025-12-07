import { defineNuxtConfig } from 'nuxt/config'
// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  css: ['~/assets/styles/host-theme.css'],
  ssr: false, // build as SPA (good for S3/CloudFront)
  devtools: { enabled: false },
  modules: [
    '@pinia/nuxt',
  ],
  app: {
    head: {
      title: 'Host UI',
      meta: [
        { name: 'viewport', content: 'width=device-width, initial-scale=1' },
      ],
      link: [
        {
          rel: 'stylesheet',
          href: 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/css/bootstrap.min.css',
          integrity: 'sha384-QWTKZyjpPEjISv5WaRU9OFeRpok6YctnYmDr5pNlyT2bRjXh0JMhjY6hW+ALEwIH',
          crossorigin: 'anonymous'
        },
        { rel: 'stylesheet', href: 'https://unpkg.com/maplibre-gl@3.x/dist/maplibre-gl.css' }
      ],
      script: [
        {
          src: 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.3/dist/js/bootstrap.bundle.min.js',
          integrity: 'sha384-YvpcrYf0tY3lHB60NNkmXc5s9fDVZLESaAA55NDzOxhy9GkcIdslK1eN7N6jIeHz',
          crossorigin: 'anonymous'
        },
        { src: 'https://unpkg.com/maplibre-gl@3.x/dist/maplibre-gl.js' }
      ]
    },
  },
  runtimeConfig: {
    public: {
      apiBase: process.env.HOST_API_BASE || process.env.HOST_API_DOMAIN || '',
      awsRegion: process.env.AWS_REGION || '',
      awsPlaceIndex: process.env.VITE_AWS_PLACE_INDEX || '',
      awsLocationApiKey: process.env.VITE_AWS_LOCATION_API_KEY || '',
      devUserId: process.env.DEV_USER_ID || '',
      authUiUrl: process.env.AUTH_UI_URL || '',
      hostUiUrl: process.env.HOST_UI_URL || '',
      guestUiUrl: process.env.GUEST_UI_URL || '',
    },
  },
})


