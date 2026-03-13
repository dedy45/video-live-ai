import { defineConfig } from 'vite';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import { svelteTesting } from '@testing-library/svelte/vite';
import { resolve } from 'node:path';

const htmlInputs = {
 index: resolve(__dirname, 'index.html'),
 setup: resolve(__dirname, 'setup.html'),
 aibrain: resolve(__dirname, 'aibrain.html'),
 performer: resolve(__dirname, 'performer.html'),
 monitor: resolve(__dirname, 'monitor.html'),
 stream: resolve(__dirname, 'stream.html'),
 products: resolve(__dirname, 'products.html'),
};

export default defineConfig({
 plugins: [svelte(), svelteTesting()],
 base: '/dashboard/',
 build: {
   outDir: 'dist',
   emptyOutDir: true,
   rollupOptions: {
     input: htmlInputs,
   },
 },
  server: {
   proxy: {
     '/api': 'http://localhost:8001',
   },
  },
 test: {
   environment: 'jsdom',
   globals: true,
   setupFiles: ['./vitest.setup.ts'],
   include: ['src/**/*.test.ts'],
 },
});
