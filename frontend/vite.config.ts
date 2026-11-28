import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/v3': {
        target: 'https://icicleai.tapis.io',
        changeOrigin: true,
        secure: true,
      },
      '/tapis-proxy': {
        target: 'https://icicleai.tapis.io',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/tapis-proxy/, ''),
        secure: true,
      },
      '/hf-api': {
        target: 'https://huggingface.co',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/hf-api/, '/api'),
        secure: true,
      },
      '/hf-viewer': {
        target: 'https://datasets-server.huggingface.co',
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/hf-viewer/, ''),
        secure: true,
      },
      '/llm': {
        target: 'https://smartcurriculumdesigner.pods.icicleai.tapis.io',
        changeOrigin: true,
        secure: true,
      },
    },
  },
})
