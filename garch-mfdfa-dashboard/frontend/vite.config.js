import { defineConfig } from 'vite'
import { svelte } from '@sveltejs/vite-plugin-svelte'

// Public host the browser uses to reach this server (e.g. EC2 public IP/DNS).
// Set VITE_HMR_HOST in the deployment env so the HMR WebSocket connects correctly.
const hmrHost = process.env.VITE_HMR_HOST
// Where the dev server proxies /api to. In Docker this must be the backend
// service name (http://backend:8000); locally it stays 127.0.0.1:8000.
const proxyTarget = process.env.VITE_PROXY_TARGET || 'http://127.0.0.1:8000'

export default defineConfig({
  plugins: [svelte()],
  server: {
    host: '0.0.0.0',
    port: 5173,
    // Allow access via any host (e.g. EC2 public DNS) in Vite 5.
    allowedHosts: true,
    hmr: hmrHost
      ? { host: hmrHost, protocol: 'ws', clientPort: 5173 }
      : true,
    proxy: {
      '/api': {
        target: proxyTarget,
        changeOrigin: true,
        rewrite: (path) => path.replace(/^\/api/, '')
      }
    }
  },
  build: {
    outDir: 'dist',
    sourcemap: false
  }
})
