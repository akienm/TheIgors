---
name: savestateauto
description: Lightweight state flush — update session record, flush to Igor, remove debug flag, AND emit a compact preserve string so Akien can manually /compact at a clean boundary if desired. Does not itself compact.
model: haiku
---

# /savestateauto — Quick state flush (+ compact preserve string)

Called automatically by /ticket, /sprint, /day-close. Also callable directly.

Since 2026-04-20: the final step always emits a compact-ready preserve string. Akien can copy/paste it into `/compact` at any clean boundary. Paired with `/export-chat`, this means unexpected auto-compact is rare — when compact happens, it happens on command, with known preservation instructions.

## Steps

1. **State hypothesis**: One sentence — what's in-flight and why? NONE if clean.

2. **Flush to Igor** (non-fatal):
   ```bash
   python3 ~/TheIgors/lab/claudecode/cc_queue.py flush_session <session_id> "theme: ...; next: ..."
   ```

3. **Append hypothesis to session key_changes** (T-savestate-append-change-gap):
   ```bash
   DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
   IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py append-change "<hypothesis from step 1>"
   ```
   Why: flush_session only posts to the Igor channel; it does not touch infra.sessions.key_changes. Without this step, the session DB record stays empty between /sprint invocations, making "what changed" unrecoverable after compact.

4. **Finalize session record** (if session ending):
   ```bash
   DB=postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001
   IGOR_HOME_DB_URL=$DB python3 ~/TheIgors/lab/claudecode/session_manager.py finalize "YYYY-MM-DDx" \
     "Next: top priorities" "In-flight: hypothesis or NONE"
   ```

5. **Remove debug flag**:
   ```bash
   rm -f ~/.TheIgors/Igor-wild-0001/debug_session.flag
   ```

6. **Emit compact preserve string** (always, even if Akien doesn't ask for compact):

   The preserve string is a **pointer, not a copy**. The slate + session record already hold the detailed state on disk — duplicating that content here just burns tokens and rots fast. Tell post-compact CC *where to look*, plus the one or two things that aren't on disk (in-flight hypothesis, next-move intent).

   Shape:
   ```
   preserve: Session <session-id>. State on disk — read
   ~/.TheIgors/claudecode/YYYYMMDD.slate.txt and run
   `IGOR_HOME_DB_URL=... python3 ~/TheIgors/lab/claudecode/session_manager.py show 1`
   for full context. In-flight: <hypothesis or NONE>. Next: <top 1-3 ticket ids>.
   ```

   Build from:
   - Session id: `cat ~/.TheIgors/cc_channel/current_session.txt`
   - Slate path: `~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt`
   - In-flight hypothesis: from step 1 above
   - Next priorities: top 1-3 from today's slate `## Next up`

   Print the block at the end of the /savestateauto output, clearly labeled:

   ```
   ── COMPACT PRESERVE STRING (copy if you want to /compact now) ──
   preserve: ...
   ───────────────────────────────────────────────────────────────
   ```

   Do NOT include: today's commits, done/filed ticket lists, active decision counts, theme descriptions, rule text. All of that is on disk — the slate has the session's done+filed+decisions, `session_manager show` has theme+key_changes+commits, git has the commit log.

That's it. No compact (Akien decides), no file rewrites, no DSB updates. Just DB + Igor flush + a compact-ready block on standby.
