<script lang="ts">
  import { onMount } from 'svelte';
  import TaskForm from '$lib/components/TaskForm.svelte';
  import RouteView from '$lib/components/RouteView.svelte';
  import ContextView from '$lib/components/ContextView.svelte';
  import ResultView from '$lib/components/ResultView.svelte';
  import { api, type RunRequest, type RunResponse } from '$lib/api';

  let response: RunResponse | null = null;
  let systemMap: unknown = null;
  let evolutionLog: unknown = null;
  let loading = false;
  let error = '';

  async function handleSubmit(req: RunRequest) {
    loading = true;
    error = '';
    try {
      response = await api.daiRun(req);
    } catch (err) {
      error = (err as Error).message;
    } finally {
      loading = false;
    }
  }

  onMount(async () => {
    try {
      systemMap = await api.daiSystemMap();
      evolutionLog = await api.daiEvolutionLog();
    } catch (err) {
      // non-fatal; stubs may not be available
      console.warn('DAI stubs unreachable:', err);
    }
  });
</script>

<div class="page-title">
  <h2>DAI Dashboard</h2>
  <small>Director AI · inside AutoLink</small>
</div>

<div class="grid">
  <section class="card form-card">
    <h3>DAI console</h3>
    <TaskForm submitLabel="Run through DAI" onSubmit={handleSubmit} {loading} />
    {#if error}
      <p class="error">{error}</p>
    {/if}
  </section>

  <div class="panels">
    <RouteView route={response?.route ?? null} />
    <ContextView context={response?.context ?? null} />
    <ResultView result={response?.result ?? null} />

    <section class="card">
      <h3>System map</h3>
      <pre class="mono">{systemMap ? JSON.stringify(systemMap, null, 2) : '— loading —'}</pre>
    </section>

    <section class="card">
      <h3>Evolution log</h3>
      <pre class="mono">{evolutionLog ? JSON.stringify(evolutionLog, null, 2) : '— loading —'}</pre>
    </section>
  </div>
</div>

<style>
  .grid {
    display: grid;
    grid-template-columns: minmax(320px, 420px) 1fr;
    gap: 1.25rem;
    align-items: start;
  }
  .form-card h3,
  .card h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }
  .panels {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1rem;
  }
  :global(.panels > section:nth-child(1)) {
    grid-column: 1 / -1;
  }
  pre.mono {
    margin: 0;
    padding: 0.7rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-family: var(--mono);
    font-size: 0.8rem;
    overflow-x: auto;
    max-height: 260px;
  }
  .error {
    color: var(--danger);
    font-size: 0.85rem;
  }
  @media (max-width: 1100px) {
    .grid {
      grid-template-columns: 1fr;
    }
    .panels {
      grid-template-columns: 1fr;
    }
  }
</style>
