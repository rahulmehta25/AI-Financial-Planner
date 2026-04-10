import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
      // Shim Node.js built-ins that leak into the browser bundle
      buffer: path.resolve(__dirname, './src/polyfills/buffer.js'),
      process: path.resolve(__dirname, './src/polyfills/process.js'),
    },
  },
  define: {
    global: 'globalThis',
    'process.env': {},
  },
  server: {
    port: 5173,
    host: true,
    strictPort: true,
    open: false,
  },
  optimizeDeps: {
    include: ['react', 'react-dom', 'recharts'],
    exclude: ['playwright'],
    esbuildOptions: {
      define: { global: 'globalThis' },
    },
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    // Plotly alone is ~4.8 MB; split builds are expected to be large chunks
    chunkSizeWarningLimit: 5000,
    commonjsOptions: {
      transformMixedEsModules: true,
    },
    rollupOptions: {
      output: {
        // Function-based manualChunks for finer control.
        // Three.js has been removed — these chunks keep optional heavy libs
        // isolated so they only load when lazy-loaded routes are visited.
        manualChunks(id) {
          // Plotly — only loaded by Monte Carlo / ProbabilityChart (lazy)
          if (id.includes('plotly')) return 'vendor-plotly'

          // D3 — only loaded by portfolio optimizer charts (lazy)
          if (id.includes('/node_modules/d3') || id.includes('/node_modules/d3-')) return 'vendor-d3'

          // Supabase
          if (id.includes('@supabase')) return 'vendor-supabase'

          // Radix UI primitives
          if (id.includes('@radix-ui')) return 'vendor-radix'

          // TanStack Query
          if (id.includes('@tanstack')) return 'vendor-query'
        },
      },
    },
  },
})
