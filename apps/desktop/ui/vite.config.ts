import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import path from 'path'

export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:18234',
        changeOrigin: true,
      },
      '/ws': {
        target: 'ws://localhost:18234',
        ws: true,
      },
      '/healthz': {
        target: 'http://localhost:18234',
        changeOrigin: true,
      },
    },
  },
})
