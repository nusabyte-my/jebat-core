import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';

export default defineConfig({
  plugins: [react()],
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src'),
    },
  },
  server: {
    port: 3001,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
      '/webhook': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
  // Disable static generation - use SSR
  build: {
    outDir: '../jebat-core/public/dashboard',
    emptyOutDir: true,
  },
  // Disable static generation for all routes
  ssr: {
    noExternal: true,
  },
});