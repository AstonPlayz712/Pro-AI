<script lang="ts">
  import TaskForm from '$lib/components/TaskForm.svelte';
  import RouteView from '$lib/components/RouteView.svelte';
  import ContextView from '$lib/components/ContextView.svelte';
  import ResultView from '$lib/components/ResultView.svelte';
  import { api, type RunRequest, type RunResponse } from '$lib/api';

  let response: RunResponse | null = null;
  let loading = false;
  let error = '';

  async function handleSubmit(req: RunRequest) {
    loading = true;
    error = '';
    try {
      response = await api.autolinkRun(req);
    } catch (err) {
      error = (err as Error).message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="page-title">
  <h2>AutoLink Dashboard</h2>
  <small>Route · Context · Result</small>
</div>

<div class="grid">
  <section class="card form-card">
    <h3>Dispatch task</h3>
    <TaskForm submitLabel="Run through AutoLink" onSubmit={handleSubmit} {loading} />
    {#if error}
      <p class="error">{error}</p>
    {/if}
  </section>

  <div class="panels">
    <RouteView route={response?.route ?? null} />
    <ContextView context={response?.context ?? null} />
    <ResultView result={response?.result ?? null} />
  </div>
</div>

<style>
  .grid {
    display: grid;
    grid-template-columns: minmax(320px, 420px) 1fr;
    gap: 1.25rem;
    align-items: start;
  }
  .form-card h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.9rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }
  .panels {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: auto auto;
    gap: 1rem;
  }
  :global(.panels > section:nth-child(1)) {
    grid-column: 1 / -1;
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
