import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  clearScreen: false,
  cacheDir: '.vite-cache',
  server: { port: 1420, strictPort: true },
})
