<script lang="ts">
  import { api, type MakeRequest, type MakeResponse, type MakerMode } from '$lib/api';

  let goal = '';
  let mode: MakerMode = 'plan';
  let user_id = 'u1';
  let session_id = 's1';

  let response: MakeResponse | null = null;
  let loading = false;
  let error = '';

  const modes: MakerMode[] = ['idea', 'plan', 'spec', 'code_stub'];

  async function submit() {
    error = '';
    if (!goal.trim()) {
      error = 'Please describe what you want to make.';
      return;
    }
    loading = true;
    try {
      const req: MakeRequest = {
        goal: goal.trim(),
        mode,
        user_id,
        session_id: session_id || null
      };
      response = await api.daiMake(req);
    } catch (err) {
      error = (err as Error).message;
    } finally {
      loading = false;
    }
  }
</script>

<div class="page-title">
  <h2>Maker</h2>
  <small>DAI · make_something</small>
</div>

<div class="grid">
  <section class="card form-card">
    <h3>Describe it</h3>
    <form on:submit|preventDefault={submit} class="task-form">
      <label>
        <span>What do you want to make?</span>
        <textarea
          bind:value={goal}
          rows="5"
          placeholder="e.g. design a small tool that tracks habits"
          spellcheck="false"
        ></textarea>
      </label>

      <label>
        <span>Mode</span>
        <select bind:value={mode}>
          {#each modes as m}
            <option value={m}>{m}</option>
          {/each}
        </select>
      </label>

      <div class="row">
        <label>
          <span>user_id</span>
          <input bind:value={user_id} required />
        </label>
        <label>
          <span>session_id</span>
          <input bind:value={session_id} />
        </label>
      </div>

      <button type="submit" disabled={loading}>
        {loading ? 'Making…' : 'Make'}
      </button>

      {#if error}
        <p class="error">{error}</p>
      {/if}
    </form>
  </section>

  <section class="card output-card">
    <header>
      <h3>Maker Plan / Output</h3>
      {#if response?.result?.engine}
        <span class="badge">{response.result.engine}</span>
      {/if}
    </header>

    {#if response?.maker}
      <dl class="summary">
        <dt>goal</dt>
        <dd>{response.maker.goal}</dd>
        <dt>mode</dt>
        <dd class="mono">{response.maker.mode}</dd>
      </dl>
    {/if}

    {#if response}
      <span class="label">Full response</span>
      <pre class="mono">{JSON.stringify(response, null, 2)}</pre>
    {:else}
      <p class="empty">No output yet. Describe something and hit Make.</p>
    {/if}
  </section>
</div>

<style>
  .grid {
    display: grid;
    grid-template-columns: minmax(320px, 420px) 1fr;
    gap: 1.25rem;
    align-items: start;
  }
  .form-card h3,
  .output-card h3 {
    margin: 0 0 0.75rem 0;
    font-size: 0.85rem;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-muted);
  }
  .task-form {
    display: flex;
    flex-direction: column;
    gap: 0.9rem;
  }
  label {
    display: flex;
    flex-direction: column;
    gap: 0.3rem;
    font-size: 0.85rem;
    color: var(--text-muted);
  }
  label > span {
    letter-spacing: 0.04em;
    text-transform: uppercase;
  }
  input,
  select,
  textarea {
    background: var(--surface-2);
    color: var(--text);
    border: 1px solid var(--border);
    border-radius: 6px;
    padding: 0.55rem 0.7rem;
    font: inherit;
    transition: border-color 120ms ease, box-shadow 120ms ease;
  }
  textarea {
    font-family: var(--mono);
    resize: vertical;
  }
  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  .row {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.75rem;
  }
  button {
    align-self: flex-start;
    background: linear-gradient(135deg, var(--accent), var(--accent-2));
    color: #0b0d12;
    border: none;
    border-radius: 8px;
    padding: 0.6rem 1.1rem;
    font-weight: 600;
    letter-spacing: 0.03em;
    cursor: pointer;
    box-shadow: 0 6px 18px var(--accent-glow);
  }
  button:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }
  .output-card header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 0.75rem;
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
  .summary {
    display: grid;
    grid-template-columns: max-content 1fr;
    gap: 0.4rem 1rem;
    margin: 0 0 0.75rem 0;
  }
  .summary dt {
    color: var(--text-muted);
    font-size: 0.8rem;
  }
  .summary dd {
    margin: 0;
    font-size: 0.9rem;
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
    max-height: 520px;
  }
  .mono {
    font-family: var(--mono);
  }
  .empty {
    color: var(--text-muted);
    font-size: 0.85rem;
    margin: 0;
  }
  .error {
    color: var(--danger);
    font-size: 0.85rem;
    margin: 0;
  }
  @media (max-width: 1100px) {
    .grid {
      grid-template-columns: 1fr;
    }
  }
</style>
