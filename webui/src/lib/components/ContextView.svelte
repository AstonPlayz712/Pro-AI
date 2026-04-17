<script lang="ts">
  import type { ContextInfo } from '$lib/api';
  export let context: ContextInfo | null = null;
</script>

<section class="card">
  <header>
    <h3>Context</h3>
    {#if context}
      <span class="badge">memory: {context.memory_size}</span>
    {/if}
  </header>
  {#if context}
    <div class="block">
      <span class="label">system_state</span>
      <pre class="mono">{JSON.stringify(context.system_state, null, 2)}</pre>
    </div>
    <div class="block">
      <span class="label">notes</span>
      <ul>
        {#each context.notes as note}
          <li>{note}</li>
        {/each}
      </ul>
    </div>
  {:else}
    <p class="empty">No context yet.</p>
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
  .block {
    margin-top: 0.75rem;
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
    font-family: var(--mono);
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
