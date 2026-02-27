<script>
  import { onMount } from 'svelte'

  let stats = {}

  async function poll() {
    try {
      const r = await fetch('/api/dashboard')
      stats = await r.json()
    } catch(e) {}
  }

  onMount(() => {
    poll()
    const id = setInterval(poll, 5000)
    return () => clearInterval(id)
  })

  function fmt(v, decimals = 2) { return Number(v).toFixed(decimals) }
  function sign(v) { return v >= 0 ? '+' : '' }
</script>

<div class="dash">
  {#if stats.memory_count !== undefined}
    <span>mem:{stats.memory_count}</span>
  {/if}
  {#if stats.session_cost !== undefined}
    <span>cost:${fmt(stats.session_cost, 4)}</span>
  {/if}
  {#if stats.last_valence !== undefined}
    <span>val:{sign(stats.last_valence)}{fmt(stats.last_valence)}</span>
  {/if}
  {#if stats.last_friction !== undefined}
    <span>f:{fmt(stats.last_friction)}</span>
  {/if}
  {#if !stats.memory_count && !stats.session_cost}
    <span>Igor online</span>
  {/if}
</div>

<style>
  .dash {
    padding: 0.3rem 1rem;
    background: #0f0f1e;
    font-size: 0.8rem;
    color: #888;
    border-top: 1px solid #222;
    display: flex;
    gap: 1rem;
    flex-shrink: 0;
  }
</style>
