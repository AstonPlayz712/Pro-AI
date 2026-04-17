// SPA mode — the app is statically built and served from either Vite (web)
// or Tauri (desktop); all data comes from FastAPI at runtime.
export const ssr = false;
export const prerender = false;
export const trailingSlash = 'always';
