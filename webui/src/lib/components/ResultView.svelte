<script lang="ts">
  import type { EngineResult } from '$lib/api';
  export let result: EngineResult | null = null;
</script>

<section class="card">
  <header>
    <h3>Result</h3>
    {#if result}
      <span class="badge">{result.engine}</span>
    {/if}
  </header>
  {#if result}
    <dl>
      <dt>task_id</dt>
      <dd class="mono">{result.task_id}</dd>
      <dt>intent</dt>
      <dd class="mono">{result.intent}</dd>
    </dl>
    <div class="block">
      <span class="label">payload</span>
      <pre class="mono">{JSON.stringify(result.payload, null, 2)}</pre>
    </div>
    <div class="block">
      <span class="label">context_notes</span>
      <ul>
        {#each result.context_notes as note}
          <li>{note}</li>
        {/each}
      </ul>
    </div>
  {:else}
    <p class="empty">No result yet.</p>
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
    border: 1px solid var(--accent-2);
    color: var(--accent-2);
    box-shadow: 0 0 12px var(--accent-2-glow);
  }
  dl {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0 0 0.75rem 0;
  }
  dt {
    color: var(--text-muted);
    font-size: 0.8rem;
  }
  dd {
    margin: 0;
    font-size: 0.85rem;
  }
  .mono {
    font-family: var(--mono);
  }
  .block {
    margin-top: 0.6rem;
  }
  .label {
    display: block;
    font-size: 0.75rem;
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.08em;
    margin-bottom: 0.3rem;
  }
  pre.mono {
    margin: 0;
    padding: 0.7rem;
    background: var(--surface-2);
    border: 1px solid var(--border);
    border-radius: 6px;
    font-size: 0.8rem;
    overflow-x: auto;
  }
  ul {
    margin: 0;
    padding-left: 1.1rem;
    font-size: 0.85rem;
  }
  .empty {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0;
  }
</style>
