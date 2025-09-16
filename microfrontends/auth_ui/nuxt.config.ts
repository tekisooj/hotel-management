// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  ssr: false, // build as SPA (good for S3/CloudFront)
  devtools: { enabled: false },
  modules: [
    '@pinia/nuxt',
  ],
  app: {
    head: {
      title: 'Auth UI',
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
      awsRegion: process.env.VITE_AWS_REGION || '',
      cognitoApiDomain: process.env.COGNITO_API_DOMAIN || '',
      congitoUserPoolID: process.env.COGNITO_USER_POOL_ID || '',
      cognitoAppClientId: process.env.COGNITO_APP_CLIENT_ID || ''
    },
  },
})
