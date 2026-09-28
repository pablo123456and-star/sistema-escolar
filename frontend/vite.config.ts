import path from 'node:path'
import tailwindcss from '@tailwindcss/vite'
import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// El frontend llama a "/api/..." y Vite lo reenvía al backend (uvicorn en el puerto 8000).
// Así funciona igual en esta PC y desde otros equipos de la red (npm run dev -- --host):
// solo se abre el puerto 5173 y no hay problemas de CORS.
const proxyApi = { '/api': { target: 'http://localhost:8000', changeOrigin: true } }

// https://vite.dev/config/
export default defineConfig({
  plugins: [react(), tailwindcss()],
  resolve: {
    alias: {
      // "@/..." apunta a src/ (ej. import { Button } from '@/componentes/ui/button')
      '@': path.resolve(import.meta.dirname, './src'),
    },
  },
  server: { proxy: proxyApi },
  // "npm run preview" sirve la versión compilada y puede publicarse con un túnel
  // (playit.gg, ngrok...): se acepta cualquier nombre de dominio del túnel.
  preview: { proxy: proxyApi, allowedHosts: true },
})
