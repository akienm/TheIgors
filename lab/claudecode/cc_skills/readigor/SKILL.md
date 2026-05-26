---
name: readigor
description: Reads Igor's recent replies from the shared channel. Shows what Igor has been saying. Use when Akien says /readigor, "what did Igor say", "read Igor's replies", or "check Igor's output". Accepts optional machine argument (akiendell, yoga9i, yogai7, local).
model: haiku
---

# Readigor — Read Igor's Recent Output

Reads the channel and shows Igor's recent replies for the specified machine.
Use after a probe, after cc_send, or anytime you want to see what Igor has been up to.

**Argument**: optional machine name — `akiendell`, `yoga9i`, `yogai7`, `local` (default if omitted)

---

## Machine routing table

| Argument | MCP channel_read tool | Dashboard URL |
|---|---|---|
| (none) / `local` | `mcp__igor__channel_read` | `http://localhost:8080/api/dashboard` |
| `akiendell` | `mcp__igor_akiendell__channel_read` | `http://10.0.0.99:8080/api/dashboard` |
| `yoga9i` | `mcp__igor_yoga9i__channel_read` | `http://10.0.0.90:8080/api/dashboard` |
| `yogai7` | `mcp__igor_yogai7__channel_read` | `http://10.0.0.71:8080/api/dashboard` |

---

## Step 1 — Read recent channel messages

Call the MCP `channel_read` tool for the target machine (see table above) with `limit: 20`.

If no MCP tool is available for the target machine, fall back to:
```bash
python3 ${CC_WORKFLOW_TOOLS}/channel.py read 20
```
(shared Postgres channel — shows all machines)

Filter for `author: igor` entries to see only Igor's output.

---

## Step 2 — Optionally check the web dashboard

Use the dashboard URL from the table above:
```bash
curl -s http://<ip>:8080/api/dashboard | python3 -m json.tool | head -40
```

This shows active sessions, milieu state, and recent activity for that Igor instance.

---

## Step 3 — Report

Summarize what Igor said:
- Last N replies, with timestamps
- Any notable patterns (repeated errors, stuck state, unusual responses)
- If Igor is silent: note how long since last message and whether the bridge is up

---

## When to use this

- After `/probe` — to read Igor's actual response to the stimulus
- After `cc_send` — to confirm Igor received and processed the message
- When debugging Igor behavior — to see what he's actually saying
- When another session sent Igor a task — to check the result
- When checking a remote machine — pass the machine name as argument

---

## Fallback (if channel.py unavailable)

```bash
tail -20 ~/.TheIgors/cc_channel/messages.jsonl | \
  python3 -c "
import sys, json
for line in sys.stdin:
    line = line.strip()
    if not line: continue
    try:
        m = json.loads(line)
        if m.get('author') == 'igor':
            print(f\"[{m.get('ts','?')}] {m.get('content','')}\")
    except Exception:
        pass
"
```
