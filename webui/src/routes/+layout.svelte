<script lang="ts">
  import { page } from '$app/stores';
  import { theme, toggleTheme } from '$lib/theme';
  import '../app.css';

  const nav = [
    { href: '/autolink', label: 'AutoLink Dashboard' },
    { href: '/dai', label: 'DAI Dashboard' },
    { href: '/maker', label: 'Maker' },
    { href: '/cities2', label: 'Cities2 Tools' }
  ];
</script>

<div class="shell">
  <header class="topbar">
    <div class="brand">
      <span class="dot" aria-hidden="true"></span>
      <h1>Pro-AI Control</h1>
      <span class="sub">AutoLink · DAI</span>
    </div>
    <div class="actions">
      <button class="ghost" on:click={toggleTheme} title="Toggle theme">
        {$theme === 'dark' ? '☾ Dark' : '☀ Light'}
      </button>
    </div>
  </header>

  <aside class="sidebar">
    <nav>
      {#each nav as item}
        <a href={item.href} class:active={$page.url.pathname.startsWith(item.href)}>
          {item.label}
        </a>
      {/each}
    </nav>
    <footer>v0.1.0 · local</footer>
  </aside>

  <main>
    <slot />
  </main>
</div>

<style>
  .shell {
    display: grid;
    grid-template-columns: 240px 1fr;
    grid-template-rows: 56px 1fr;
    grid-template-areas:
      'topbar topbar'
      'sidebar main';
    min-height: 100vh;
  }
  .topbar {
    grid-area: topbar;
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 1.25rem;
    background: var(--surface-1);
    border-bottom: 1px solid var(--border);
    backdrop-filter: saturate(140%) blur(6px);
  }
  .brand {
    display: flex;
    align-items: center;
    gap: 0.75rem;
  }
  .brand h1 {
    font-size: 1rem;
    font-weight: 600;
    letter-spacing: 0.05em;
    margin: 0;
  }
  .brand .sub {
    font-family: var(--mono);
    font-size: 0.75rem;
    color: var(--text-muted);
    padding: 0.1rem 0.5rem;
    border: 1px solid var(--border);
    border-radius: 999px;
  }
  .dot {
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: var(--accent);
    box-shadow: 0 0 14px var(--accent-glow);
  }
  .sidebar {
    grid-area: sidebar;
    background: var(--surface-1);
    border-right: 1px solid var(--border);
    display: flex;
    flex-direction: column;
    justify-content: space-between;
    padding: 1rem 0.75rem;
  }
  .sidebar nav {
    display: flex;
    flex-direction: column;
    gap: 0.25rem;
  }
  .sidebar a {
    color: var(--text);
    text-decoration: none;
    font-size: 0.9rem;
    padding: 0.55rem 0.8rem;
    border-radius: 8px;
    border: 1px solid transparent;
    transition: background 120ms ease, border-color 120ms ease, color 120ms ease;
  }
  .sidebar a:hover {
    background: var(--surface-2);
  }
  .sidebar a.active {
    border-color: var(--accent);
    color: var(--accent);
    background: var(--accent-soft);
    box-shadow: 0 0 10px var(--accent-glow);
  }
  .sidebar footer {
    color: var(--text-muted);
    font-family: var(--mono);
    font-size: 0.7rem;
    padding: 0.5rem 0.8rem;
  }
  main {
    grid-area: main;
    padding: 1.5rem;
    overflow: auto;
  }
  .actions button.ghost {
    background: transparent;
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 8px;
    padding: 0.35rem 0.7rem;
    font-family: var(--mono);
    font-size: 0.8rem;
    cursor: pointer;
  }
  .actions button.ghost:hover {
    border-color: var(--accent);
    color: var(--accent);
  }
</style>
