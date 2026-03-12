import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

// Determine backend URL for Vite proxy based on environment
// VITE_BACKEND_URL is used only for the proxy configuration (server-side)
// VITE_API_BASE_URL (if set) is used by the browser client
// In TLS mode: proxy uses https://backend:8000, browser uses relative URLs via proxy
// In non-TLS mode: proxy uses http://backend:8000, browser uses relative URLs via proxy
const backendUrl = process.env.VITE_BACKEND_URL || 'http://backend:8000'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3000,
    host: true,
    proxy: {
      '/api': {
        target: backendUrl,
        changeOrigin: true,
        secure: false, // Accept self-signed certificates in TLS mode
        configure: (proxy, _options) => {
          proxy.on('error', (err, _req, _res) => {
            console.log('proxy error', err);
          });
          proxy.on('proxyReq', (proxyReq, req, _res) => {
            console.log('Sending Request to the Target:', req.method, req.url);
          });
          proxy.on('proxyRes', (proxyRes, req, _res) => {
            console.log('Received Response from the Target:', proxyRes.statusCode, req.url);
          });
        },
      },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: true,
  },
})

// Made with Bob
