import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api/marquez': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/marquez/, '/api/v1'),
      },
      '/api/prefect': {
        target: process.env.VITE_PREFECT_API_URL || 'http://localhost:4200',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api\/prefect/, '/api'),
      },
    },
  },
})
