// https://nuxt.com/docs/api/configuration/nuxt-config
export default defineNuxtConfig({
  compatibilityDate: '2024-04-03',
  srcDir: 'app',
  devtools: { enabled: true },
  app: {
    head: {
      title: 'PriceTrack Notifier',
      link: [
        { rel: 'apple-touch-icon', href: '/pwa-512x512.png' }
      ],
      meta: [
        { name: 'apple-mobile-web-app-title', content: 'PriceTrack' },
        { name: 'apple-mobile-web-app-capable', content: 'yes' },
        { name: 'apple-mobile-web-app-status-bar-style', content: 'black-translucent' }
      ]
    }
  },
  modules: ['@vite-pwa/nuxt'],
  css: ['~/assets/css/main.css'],
  pwa: {
    manifest: {
      name: 'PriceTrack Notifier',
      short_name: 'PriceTrack',
      description: 'Smart E-Commerce Price Tracking & Notifications',
      theme_color: '#0ea5e9',
      background_color: '#0f172a',
      icons: [
        {
          src: '/pwa-192x192.png',
          sizes: '192x192',
          type: 'image/png',
          purpose: 'any maskable'
        },
        {
          src: '/pwa-512x512.png',
          sizes: '512x512',
          type: 'image/png',
          purpose: 'any maskable'
        }
      ]
    },
    workbox: {
      navigateFallback: '/'
    },
    devOptions: {
      enabled: true,
      type: 'module'
    }
  },
  routeRules: {
    '/api/**': { proxy: 'http://134.98.130.247:8000/**' }
  },
  runtimeConfig: {
    public: {
      apiBase: '/api'
    }
  }
})
