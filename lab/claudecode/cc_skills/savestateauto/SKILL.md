---
name: savestateauto
description: Lightweight state flush — write in-flight hypothesis to slate, remove debug flag, emit compact preserve string.
model: haiku
---

# /savestateauto — Quick state flush (+ compact preserve string)

Called automatically by /ticket, /sprint, /day-close. Also callable directly.

The preserve string is always emitted so Akien can /compact at any clean boundary.

## Steps

1. **State hypothesis**: One sentence — what's in-flight and why? NONE if clean.

2. **Write in-flight to slate**:
   ```bash
   SLATE=~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
   echo "" >> "$SLATE"
   echo "## In-flight: <hypothesis from step 1>" >> "$SLATE"
   ```

3. **Remove debug flag**:
   ```bash
   rm -f ~/.TheIgors/Igor-wild-0001/debug_session.flag
   ```

4. **Emit compact preserve string** (always, even if Akien doesn't ask for compact):

   The preserve string is a **pointer, not a copy**. The slate holds all state on disk.

   Shape:
   ```
   preserve: State on disk — read ~/.TheIgors/claudecode/YYYYMMDD.slate.txt.
   In-flight: <hypothesis or NONE>. Next: <top 1-3 ticket ids>.
   ```

   Build from:
   - Slate path: `~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt`
   - In-flight hypothesis: from step 1 above
   - Next priorities: top 1-3 pending tickets from queue or slate

   Print the block at the end of the /savestateauto output, clearly labeled:

   ```
   ── COMPACT PRESERVE STRING (copy if you want to /compact now) ──
   preserve: ...
   ───────────────────────────────────────────────────────────────
   ```

   Do NOT include: session ids, commit lists, done/filed ticket lists, decision counts,
   rule text. All on disk — git log has commits, slate has decisions+done.

That's it. No compact (Akien decides), no DB writes, no session records.
