import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

export default defineConfig({
  server: {
    port: 5173,
    open: true,
  },
  plugins: [react()],
  preview: {
    port: 4173,
  },
});
