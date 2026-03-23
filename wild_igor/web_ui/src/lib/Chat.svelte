<script>
  import { onMount } from 'svelte'
  import FileZone from './FileZone.svelte'

  let messages = []
  let inputText = ''
  let chatEl
  let ws
  let dropping = false
  let dragDepth = 0

  function connect() {
    ws = new WebSocket(`${location.protocol === 'https:' ? 'wss' : 'ws'}://${location.host}/ws`)
    ws.onopen  = () => addMsg('system', '', 'Connected to Igor.')
    ws.onclose = () => {
      addMsg('system', '', 'Disconnected. Retrying…')
      setTimeout(connect, 2000)
    }
    ws.onmessage = (e) => {
      const m = JSON.parse(e.data)
      if (m.type === 'message')
        addMsg(m.author === 'igor' ? 'igor' : 'user',
               m.author === 'igor' ? 'Igor' : 'You',
               m.content)
      else if (m.type === 'file_dropped')
        addMsg('system', '', `📎 ${m.filename} received in inbox`)
    }
  }

  function addMsg(cls, author, content) {
    messages = [...messages, { cls, author, content }]
    setTimeout(() => { if (chatEl) chatEl.scrollTop = chatEl.scrollHeight }, 0)
  }

  function send() {
    const text = inputText.trim()
    if (!text || !ws || ws.readyState !== WebSocket.OPEN) return
    ws.send(JSON.stringify({ type: 'message', content: text }))
    inputText = ''
  }

  function onKey(e) { if (e.key === 'Enter') send() }

  async function uploadFile(file) {
    const fd = new FormData()
    fd.append('file', file)
    const r = await fetch('/api/upload', { method: 'POST', body: fd })
    const j = await r.json()
    addMsg('system', '', `📎 ${j.filename} uploaded to inbox`)
  }

  /* Global drag-and-drop handlers */
  function onDragEnter(e) {
    if (e.dataTransfer.types.includes('Files')) { dragDepth++; dropping = true }
  }
  function onDragLeave() {
    if (--dragDepth <= 0) { dragDepth = 0; dropping = false }
  }
  function onDragOver(e) { e.preventDefault() }
  function onDrop(e) {
    e.preventDefault()
    dragDepth = 0; dropping = false
    const file = e.dataTransfer.files[0]
    if (file) uploadFile(file)
  }

  onMount(connect)
</script>

<svelte:window
  on:dragenter={onDragEnter}
  on:dragleave={onDragLeave}
  on:dragover={onDragOver}
  on:drop={onDrop}
/>

<div class="chat-wrap">
  <div class="messages" bind:this={chatEl}>
    {#each messages as m}
      <div class="msg msg-{m.cls}">
        {#if m.author}<span class="author">{m.author}:</span>{/if}
        <span class="content">{m.content}</span>
      </div>
    {/each}
  </div>

  <FileZone {dropping} />

  <div class="input-row">
    <input
      bind:value={inputText}
      on:keydown={onKey}
      placeholder="Message Igor..."
      autocomplete="off"
    />
    <button on:click={send}>Send</button>
    <button on:click={() => document.getElementById('file-pick').click()}>📎</button>
    <input
      id="file-pick"
      type="file"
      style="display:none"
      on:change={e => { const f = e.target.files[0]; if (f) { uploadFile(f); e.target.value = '' } }}
    />
  </div>
</div>

<style>
  .chat-wrap {
    flex: 1;
    display: flex;
    flex-direction: column;
    overflow: hidden;
    position: relative;
  }
  .messages {
    flex: 1;
    overflow-y: auto;
    padding: 1rem;
    display: flex;
    flex-direction: column;
    gap: 0.4rem;
  }
  .msg { font-size: 0.95rem; line-height: 1.4; }
  .msg-igor   .author { color: #90ee90; font-weight: bold; }
  .msg-user   .author { color: #7ec8e3; font-weight: bold; }
  .msg-system { color: #888; font-style: italic; }
  .author { margin-right: 0.4rem; }
  .input-row {
    display: flex;
    gap: 0.5rem;
    padding: 0.5rem;
    border-top: 1px solid #333;
  }
  input {
    flex: 1;
    background: #2a2a3e;
    color: #e0e0e0;
    border: 1px solid #555;
    padding: 0.5rem;
    font-family: monospace;
    font-size: 1rem;
  }
  button {
    background: #4a4a8a;
    color: #fff;
    border: none;
    padding: 0.5rem 1rem;
    cursor: pointer;
    font-family: monospace;
  }
  button:hover { background: #6a6aaa; }
</style>
