---
name: ADCHelp
description: Workflow reference — outputs organized skill/command cheat-sheet to console or a file. Args: optional output path (e.g. /ADCHelp ~/tmp/ref.md).
model: haiku
---

# /ADCHelp — Workflow reference

Prints the skill cheat-sheet to the console. When given a file path as an argument, writes there instead.

## Steps

### 1. Determine output target

If an argument was given (e.g. `/ADCHelp ~/tmp/workflow_reference.md`), expand it:
```bash
OUTPUT="${ARGS:-}"
if [ -n "$OUTPUT" ]; then
  OUTPUT="${OUTPUT/#\~/$HOME}"
  mkdir -p "$(dirname "$OUTPUT")"
fi
```

### 2. Generate the reference

Always generate the full reference as shown in the template below. Write it to `$OUTPUT` when set, otherwise print to stdout.

```bash
SKILLS_DIR=~/.claude/skills

# Gather descriptions from frontmatter
describe_skill() {
  local skill="$1"
  local f="$SKILLS_DIR/$skill/SKILL.md"
  [ -f "$f" ] && grep "^description:" "$f" | head -1 | sed 's/description: //' || echo "(no description)"
}
```

### 3. Output template

Always output exactly this structure (fill `<desc>` from the skill's `description:` frontmatter):

```
╔══════════════════════════════════════════════════════════════╗
║                  ADC WORKFLOW REFERENCE                      ║
╚══════════════════════════════════════════════════════════════╝
Generated: <YYYY-MM-DD HH:MM>

━━ SESSION ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/context-load          Start of session — slate + rules + palace briefing
/savestate             Flush in-flight state to slate (mid-session or close)
/autocompact           Block-end — release debug flag + /compact
/day-close [date]      End-of-day ritual — audit + docs + GitHub sync
/note <text>           Log milestone/insight to notes.log + slate

━━ TICKETS & DESIGN ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/ticket [last|desc]    Create or update a ticket
/design                Mark start of a design block (optional bracket)
/sorted [summary]      Close design block → batch file tickets with audit
/fixit                 Reactive shortcut: /sorted + /sprint-batch inline

━━ SPRINTING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/sprint [id]           Claim → work → commit → close one ticket
/sprint-ticket T-xxx   Atomic unit: capability check → build → test → commit
/sprint-batch <sel>    Multi-ticket sprint with shared setup
  Selectors:
    today-slate        every pending ticket on today's slate
    slate:planned      ## Planned section only
    slate:ad-hoc       ## Ad hoc section only
    decision:D-...     all tickets from one decision
    tag:<tag>          all tickets with this tag
    T-x T-y T-z        explicit list

━━ AUDITS (called automatically — manual invocation for spot-checks) ━
/audit-ticket          Filing-time quality gate — runs inside /sorted
/audit-design          Decision coherence audit — runs inside /sorted
/audit-precode         Pre-edit audit — runs inside /sprint-ticket
/audit-smell           Post-code pre-test audit — runs inside /sprint-ticket
/audit-debris          Post-test pre-commit cleanup — runs inside /sprint-ticket
/day-close-audit       Mandatory day-close hygiene (tests + smells + registry)
/audit-day             Extended day-close audit — includes cross-day patterns
/audit-expert          Expert-lens audit — 11 specialists, weekly/monthly cadence
/audit-audits          Meta-audit — analyzes telemetry across all audit layers
/test-fix              Bounded test-run-fix loop (up to 3 retries)

━━ DEBUGGING ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/cognition-debug       Step through Igor's cognition cycle (replay or realtime)
/debug-pe-chain T-xxx  Step through Igor's pe_chain for a blocked ticket
/map-igor              Full Igor state snapshot → JSON + summary

━━ IGOR COMMS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/readigor [machine]    Read Igor's recent channel replies
/readinbox             Read CC inbox (notifications from Igor subsystems)

━━ REPO / MISC ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
/commit                Thin commit: test → stage → commit → push
/skills-sync           Sync skills local↔repo
/export-chat           Dump session transcript to ~/TheIgors/claude_chat_logs/

━━ KEY FLOWS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

  Standard sprint:
    /context-load → work → /sprint-batch today-slate → /autocompact

  Design + sprint:
    /design → discuss → /sorted → /sprint-batch decision:D-... → /autocompact

  Reactive fix:
    describe problem → /fixit → done

  Day start:
    /context-load  (creates slate, checks rules, palace briefing)

  Day end:
    /day-close [YYYY-MM-DD]  (savestate → audit → docs → GitHub → compact)

━━ TICKET STATUS ICONS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⏳ pending   🔵 in_progress   🔍 triage   ✅ done
  ⏸ hold      🔗 dependency    👤 akien     ⬜ sprint

━━ KEY PATHS ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Slate today:     ~/.TheIgors/claudecode/$(date +%Y%m%d).slate.txt
  Queue:           $CC_WORKFLOW_TOOLS/cc_queue.py
  Skills:          ~/.claude/skills/
  Igor logs:       ~/.agent_datacenter/logs/Igor-wild-0001/
  ADC logs:        ~/dev/src/agent_datacenter/datacenter_logs/
  Palace DB:       psql postgresql://igor:...@127.0.0.1/Igor-wild-0001
    → tables: clan.memories, instance.ring_memory, adc.palace
```

### 4. When writing to file

After writing, always print:
```
ADCHelp written to: <expanded path>
```

And show a 5-line preview (head -5).

### 5. After output

No savestate, no ticket filing — this skill is read-only reference output.
