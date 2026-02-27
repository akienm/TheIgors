<script>
  import Chat from './lib/Chat.svelte'
  import Dashboard from './lib/Dashboard.svelte'
</script>

<main>
  <Chat />
  <Dashboard />
</main>

<style>
  :global(*, *::before, *::after) { box-sizing: border-box; margin: 0; padding: 0; }
  :global(body) {
    font-family: monospace;
    background: #1a1a2e;
    color: #e0e0e0;
    height: 100vh;
    overflow: hidden;
  }
  main {
    display: flex;
    flex-direction: column;
    height: 100vh;
  }
</style>
