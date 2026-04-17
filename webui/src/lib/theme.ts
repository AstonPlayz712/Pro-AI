import { browser } from '$app/environment';
import { writable } from 'svelte/store';

export type Theme = 'dark' | 'light';

const KEY = 'pro-ai-theme';

function initial(): Theme {
  if (!browser) return 'dark';
  const saved = localStorage.getItem(KEY);
  return saved === 'light' ? 'light' : 'dark';
}

export const theme = writable<Theme>(initial());

if (browser) {
  theme.subscribe((value) => {
    document.documentElement.dataset.theme = value;
    localStorage.setItem(KEY, value);
  });
}

export function toggleTheme(): void {
  theme.update((t) => (t === 'dark' ? 'light' : 'dark'));
}
