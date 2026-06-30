/// <reference types="vitest/config" />
import { defineConfig, loadEnv } from 'vite'
import react from '@vitejs/plugin-react'

const isVitest = Boolean(process.env.VITEST)

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), '')
  const proxyTarget = env.VITE_DEV_PROXY_TARGET || env.VITE_API_URL

  return {
    logLevel: isVitest ? 'error' : 'info',
    plugins: [react()],
    server: {
      port: 3000,
      proxy: proxyTarget
        ? {
            '/auth': {
              target: proxyTarget,
              changeOrigin: true,
            },
            '/tasks': {
              target: proxyTarget,
              changeOrigin: true,
            },
          }
        : undefined,
    },
    test: {
      environment: 'jsdom',
      globals: true,
      setupFiles: './src/test/setup.ts',
      passWithNoTests: true,
      exclude: ['**/node_modules/**', 'e2e/**'],
    },
  }
})
