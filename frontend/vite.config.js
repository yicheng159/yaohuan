import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import path from 'path'

export default defineConfig(({ mode }) => {
  const isProduction = mode === 'production'

  return {
    plugins: [vue()],
    base: isProduction ? '/yaohuan/' : '/',
    build: {
      outDir: isProduction
        ? path.resolve(__dirname, 'dist')
        : path.resolve(__dirname, '../myproject/static/dist'),
      emptyOutDir: true,
    },
    server: {
      proxy: {
        '/api': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/admin': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
        '/static': {
          target: 'http://localhost:8000',
          changeOrigin: true,
        },
      },
    },
  }
})