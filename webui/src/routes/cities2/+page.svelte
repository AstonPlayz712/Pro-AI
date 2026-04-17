<script lang="ts">
  const features = [
    {
      title: 'Screenshot analysis',
      body: 'Drop a Cities: Skylines II screenshot and get a labelled breakdown of what the camera sees.'
    },
    {
      title: 'Traffic diagnosis',
      body: 'Pinpoint intersection-level bottlenecks, weave conflicts, and broken turning rules.'
    },
    {
      title: 'Interchange generator',
      body: 'Describe a corridor; AutoLink drafts interchange candidates and ranks them by throughput.'
    }
  ];
</script>

<div class="page-title">
  <h2>Cities2 Traffic Lab</h2>
  <small>Placeholder · coming soon</small>
</div>

<section class="card hero">
  <h3>Built on AutoLink + DAI</h3>
  <p>
    A purpose-built suite for Cities: Skylines II simulation work. The same
    AutoLink routing substrate and DAI orchestration powering this Control
    app will drive every tool below.
  </p>
</section>

<div class="feature-grid">
  {#each features as f}
    <section class="card">
      <h4>{f.title}</h4>
      <p>{f.body}</p>
      <span class="pill">planned</span>
    </section>
  {/each}
</div>

<style>
  .hero h3 {
    margin-top: 0;
  }
  .feature-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
    gap: 1rem;
    margin-top: 1rem;
  }
  .feature-grid h4 {
    margin: 0 0 0.4rem 0;
  }
  .feature-grid p {
    color: var(--text-muted);
    font-size: 0.9rem;
  }
  .pill {
    display: inline-block;
    font-family: var(--mono);
    font-size: 0.7rem;
    padding: 0.15rem 0.5rem;
    border-radius: 999px;
    border: 1px solid var(--accent-2);
    color: var(--accent-2);
    margin-top: 0.5rem;
  }
</style>
