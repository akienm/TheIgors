---
name: readigor
description: Reads Igor's recent replies from the shared channel. Shows what Igor has been saying. Use when Akien says /readigor, "what did Igor say", "read Igor's replies", or "check Igor's output".
---

# Readigor — Read Igor's Recent Output

Reads the shared channel and shows Igor's recent replies.
Use after a probe, after sending Igor a message, or anytime you want to see what Igor has been up to.

---

## Step 1 — Read recent channel messages

```bash
python3 ~/TheIgors/claudecode/channel.py read 20
```

Filter for `author: igor` entries to see only Igor's output.
The channel shows all participants — look for lines where author is `igor`.

---

## Step 2 — Optionally check the web dashboard

If Igor is running and you want the full session context:
```bash
curl -s http://localhost:8080/api/dashboard | python3 -m json.tool | head -40
```

This shows active sessions, milieu state, and recent activity.

---

## Step 3 — Report

Summarize what Igor said:
- Last N replies, with timestamps
- Any notable patterns (repeated errors, stuck state, unusual responses)
- If Igor is silent: note how long since last message

---

## When to use this

- After `/probe` — to read Igor's actual response to the stimulus
- After `cc_send` — to confirm Igor received and processed the message
- When debugging Igor behavior — to see what he's actually saying
- When another session sent Igor a task — to check the result

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
