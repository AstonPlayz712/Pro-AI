<script lang="ts">
  import type { RunRequest } from '$lib/api';

  export let submitLabel = 'Run task';
  export let loading = false;
  export let onSubmit: (req: RunRequest) => void;

  let intent = 'summarize_doc';
  let payloadText = '{\n  "doc": "hello world"\n}';
  let user_id = 'u1';
  let session_id = 's1';
  let sensitivity: 'low' | 'normal' | 'high' = 'normal';
  let complexity: 'low' | 'normal' | 'high' = 'normal';
  let latency_budget_ms: string = '';
  let parseError = '';

  function submit() {
    parseError = '';
    let payload: Record<string, unknown>;
    try {
      payload = payloadText.trim() ? JSON.parse(payloadText) : {};
    } catch (err) {
      parseError = (err as Error).message;
      return;
    }
    onSubmit({
      intent,
      payload,
      user_id,
      session_id: session_id || null,
      sensitivity,
      complexity,
      latency_budget_ms: latency_budget_ms ? Number(latency_budget_ms) : null
    });
  }
</script>

<form on:submit|preventDefault={submit} class="task-form">
  <label>
    <span>Intent</span>
    <input bind:value={intent} required />
  </label>

  <label>
    <span>Payload (JSON)</span>
    <textarea bind:value={payloadText} rows="6" spellcheck="false" class="mono"></textarea>
    {#if parseError}
      <small class="error">Invalid JSON: {parseError}</small>
    {/if}
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

  <div class="row">
    <label>
      <span>Sensitivity</span>
      <select bind:value={sensitivity}>
        <option value="low">low</option>
        <option value="normal">normal</option>
        <option value="high">high</option>
      </select>
    </label>
    <label>
      <span>Complexity</span>
      <select bind:value={complexity}>
        <option value="low">low</option>
        <option value="normal">normal</option>
        <option value="high">high</option>
      </select>
    </label>
    <label>
      <span>Latency budget (ms)</span>
      <input type="number" min="0" bind:value={latency_budget_ms} placeholder="optional" />
    </label>
  </div>

  <button type="submit" disabled={loading}>
    {loading ? 'Running…' : submitLabel}
  </button>
</form>

<style>
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
  input:focus,
  select:focus,
  textarea:focus {
    outline: none;
    border-color: var(--accent);
    box-shadow: 0 0 0 3px var(--accent-glow);
  }
  textarea.mono {
    font-family: var(--mono);
  }
  .row {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
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
  .error {
    color: var(--danger);
  }
</style>
