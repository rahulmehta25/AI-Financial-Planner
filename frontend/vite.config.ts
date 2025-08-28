import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react-swc'
import path from 'path'

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
  server: {
    port: 5173,
    host: true,
    strictPort: true,
    open: false
  },
  optimizeDeps: {
    include: ['react', 'react-dom'],
    exclude: ['playwright', 'three', 'plotly.js', 'react-plotly.js', 'd3']
  },
  build: {
    outDir: 'dist',
    sourcemap: false,
    minify: 'esbuild',
    chunkSizeWarningLimit: 2000,
    commonjsOptions: {
      transformMixedEsModules: true
    },
    rollupOptions: {
      output: {
        manualChunks: {
          'three-js': ['three'],
          'plotly': ['plotly.js', 'react-plotly.js'],
          'd3-charts': ['d3'],
          'ui-radix': [
            '@radix-ui/react-accordion',
            '@radix-ui/react-alert-dialog', 
            '@radix-ui/react-avatar',
            '@radix-ui/react-checkbox',
            '@radix-ui/react-dialog',
            '@radix-ui/react-dropdown-menu'
          ]
        }
      }
    }
  }
})