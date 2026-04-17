import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    port: 5173,
    strictPort: true,
    proxy: {
      // Same-origin calls to FastAPI during dev; prod (Tauri) uses the env URL.
      '/autolink': 'http://127.0.0.1:8000',
      '/dai': 'http://127.0.0.1:8000'
    }
  }
});
