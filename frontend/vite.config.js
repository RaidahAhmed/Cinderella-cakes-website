import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  build: {
    // Inline small assets to reduce HTTP requests
    assetsInlineLimit: 4096,
    // Target modern browsers for smaller bundles
    target: 'es2020',
  },
})
