---
name: savestateauto
description: Lightweight state flush — write in-flight hypothesis to slate, remove debug flag, emit compact preserve string.
model: haiku
---

# /savestateauto — Quick state flush (+ compact preserve string)

Called automatically by /ticket, /sprint, /day-close. Also callable directly.

Always emit the preserve string — that way Akien can /compact at any clean
boundary without a separate setup step.

## Steps

### 1. State hypothesis

Always write one sentence naming what's in-flight and why. Use `NONE` when
the session is clean — the slate must say something either way, and silence
is not interpretable.

### 2. Write in-flight to slate

Always append the hypothesis to today's slate so the next session reads it
on /context-load:
```bash
SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
echo "" >> "$SLATE"
echo "## In-flight: <hypothesis from step 1>" >> "$SLATE"
```

### 3. Remove debug flag
```bash
rm -f ~/.TheIgors/Igor-wild-0001/debug_session.flag
```

### 4. Emit compact preserve string

Always emit the preserve block at the end of /savestateauto output, even
when Akien didn't ask for /compact — preserving the option is cheap.

The preserve string is a **pointer, not a copy**. The slate holds all
state on disk; the preserve string tells post-compact CC where to look.

Shape:
```
preserve: State on disk — read ~/.TheIgors/claudecode/YYYYMMDD.slate.txt.
In-flight: <hypothesis or NONE>. Next: <top 1-3 ticket ids>.
```

Build from:
- Slate path: `~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt`
- In-flight hypothesis: step 1
- Next priorities: top 1-3 pending tickets (from queue or today's slate)

Print the block at the end of output, clearly labeled:
```
── COMPACT PRESERVE STRING (copy if you want to /compact now) ──
preserve: ...
───────────────────────────────────────────────────────────────
```

Always keep the preserve string thin. Do NOT include: session ids, commit
lists, done/filed ticket lists, decision counts, or rule text. Every one
of those lives on disk — git log has commits, slate has decisions + done,
the palace has rules. The pointer is enough.

That's it. No compact (Akien triggers that), no DB writes, no session records.
