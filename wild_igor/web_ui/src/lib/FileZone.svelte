<!-- FileZone: visual drop overlay, rendered when dropping=true -->
<script>
  export let dropping = false
</script>

{#if dropping}
  <div class="drop-overlay">Drop file to send to Igor</div>
{/if}

<style>
  .drop-overlay {
    position: absolute;
    inset: 0;
    z-index: 10;
    background: rgba(74, 74, 138, 0.8);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.5rem;
    color: #fff;
    border: 3px dashed #7ec8e3;
    pointer-events: none;
  }
</style>
