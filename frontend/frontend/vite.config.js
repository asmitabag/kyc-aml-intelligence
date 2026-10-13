import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// Port 3000 matches the backend's existing CORS allowlist
// (http://localhost:3000 and http://127.0.0.1:3000).
// strictPort makes Vite fail loudly instead of silently moving to another
// port that the backend would reject with a CORS error.
export default defineConfig({
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks: {
          react: ['react', 'react-dom', 'react-router-dom'],
          charts: ['recharts'],
        },
      },
    },
  },
  server: { port: 3000, strictPort: true, host: 'localhost' },
  preview: { port: 3000, strictPort: true, host: 'localhost' },
});
