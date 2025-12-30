import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import { VitePWA } from 'vite-plugin-pwa'
import { themeColors } from './theme.js'

// Custom plugin to inject theme variables into HTML
const htmlThemeTransform = () => {
  return {
    name: 'html-theme-transform',
    transformIndexHtml(html: string) {
      // Replace placeholders with actual values from theme.js
      return html.replace(/%BACKGROUND_COLOR%/g, themeColors.background)
                 .replace(/%THEME_COLOR_HEX%/g, themeColors.backgroundSafeHex)
    }
  }
}

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    react(),
    htmlThemeTransform(),
    VitePWA({
      registerType: 'autoUpdate',
      strategies: 'injectManifest',
      srcDir: 'src',
      filename: 'service-worker.ts',
      includeAssets: ['favicon.ico', 'apple-touch-icon.png'],
      manifest: {
        name: 'BudgetIA Personal Finance',
        short_name: 'BudgetIA',
        description: 'AI-assisted Personal Finance Manager',
        theme_color: themeColors.backgroundSafeHex,
        background_color: themeColors.backgroundSafeHex,
        display: 'standalone',
        orientation: 'portrait',
        icons: [
          {
            src: 'pwa-192x192.png',
            sizes: '192x192',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png'
          },
          {
            src: 'pwa-512x512.png',
            sizes: '512x512',
            type: 'image/png',
            purpose: 'any maskable'
          }
        ],
        scope: '/',
        start_url: '/',

      },
      devOptions: {
        enabled: true,
        type: 'module', // Important for injectManifest strategy with TS
      }
    })
  ],
  server: {
    host: true,
    port: 5173,
    allowedHosts: ['note-luciano', 'NOTE-LUCIANO'],
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8000',
        changeOrigin: true
      }
    }
  }
})
