<script lang="ts">
  import type { RouteInfo } from '$lib/api';
  export let route: RouteInfo | null = null;
</script>

<section class="card">
  <header>
    <h3>Route</h3>
    {#if route}
      <span class="badge" class:on-device={route.target === 'AutoOD'} class:cloud={route.target === 'AutoClink'}>
        {route.target}
      </span>
    {/if}
  </header>
  {#if route}
    <dl>
      <dt>Reason</dt>
      <dd>{route.reason}</dd>
      <dt>Confidence</dt>
      <dd>{(route.confidence * 100).toFixed(0)}%</dd>
    </dl>
  {:else}
    <p class="empty">No route yet. Run a task to see routing output.</p>
  {/if}
</section>

<style>
  header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.6rem;
  }
  h3 {
    margin: 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }
  .badge {
    font-family: var(--mono);
    font-size: 0.75rem;
    padding: 0.2rem 0.55rem;
    border-radius: 999px;
    border: 1px solid var(--border);
    background: var(--surface-2);
  }
  .badge.on-device {
    color: var(--accent);
    border-color: var(--accent);
    box-shadow: 0 0 12px var(--accent-glow);
  }
  .badge.cloud {
    color: var(--accent-2);
    border-color: var(--accent-2);
    box-shadow: 0 0 12px var(--accent-2-glow);
  }
  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0;
  }
  dt {
    color: var(--text-muted);
    font-size: 0.8rem;
  }
  dd {
    margin: 0;
    font-family: var(--mono);
    font-size: 0.9rem;
  }
  .empty {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0;
  }
</style>
