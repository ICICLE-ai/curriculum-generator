import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/tapis-proxy': {
        target: 'https://icicleai.tapis.io',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tapis-proxy/, ''),
        secure: true,
      },
    },
  },
})
