import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  optimizeDeps: {
    // pixi-live2d-display needs window.PIXI set before it loads,
    // so exclude it from Vite's pre-bundle to allow manual sequencing
    exclude: ['pixi-live2d-display'],
  },
})

