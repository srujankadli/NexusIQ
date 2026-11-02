import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'

// https://vite.dev/config/
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const backendPort = process.env.BACKEND_PORT || env.BACKEND_PORT || env.VITE_BACKEND_PORT || '8001'
  const backendUrl = process.env.BACKEND_URL || env.BACKEND_URL || env.VITE_API_BASE_URL || `http://127.0.0.1:${backendPort}`
  const frontendPort = Number(process.env.PORT || env.PORT || 3000)

  return {
    plugins: [
      react(),
      tailwindcss(),
    ],
    server: {
      port: frontendPort,
      proxy: {
        '/api': {
          target: backendUrl,
          changeOrigin: true,
        },
      },
    },
  }
})
