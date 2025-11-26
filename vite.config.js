import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true, // Нужно, чтобы Vite был доступен снаружи контейнера
    port: 5173,
    proxy: {
      // 1. ИНТЕРВЬЮ (порт 8082)
      '/v1/hr/interviews': {
        // Внутри Docker вместо localhost используем host.docker.internal
        target: 'http://host.docker.internal:8082', 
        changeOrigin: true,
        secure: false,
      },

      // 2. АВТОРИЗАЦИЯ (порт 8081)
      '/v1': {
        // Внутри Docker вместо localhost используем host.docker.internal
        target: 'http://host.docker.internal:8081',
        changeOrigin: true,
        secure: false,
      }
    }
  }
})