import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      // Все запросы на /v1 будут улетать на бэкенд 8081
      '/v1': {
        target: 'http://host.docker.internal:8081', // Если запускаете в Docker
        // target: 'http://localhost:8081', // Если запускаете просто локально без Docker
        changeOrigin: true,
        secure: false,
      }
    }
  }
})