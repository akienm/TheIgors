# Palace as Source of Truth — Shape Lock (2026-04-20)

Decision `D-palace-source-of-truth-2026-04-20`. This document locks the architectural shape for the child migration tickets (tickets/decisions/slates/skills → palace). It does NOT implement anything — implementation happens in the child tickets.

## The problem

Today's project state is scattered across:
- `~/.TheIgors/cc_channel/queue.json` — tickets (flat JSON, 694 items)
- `~/TheIgors/lab/design_docs_for_igor/decisions_log.dsb` — decisions (append-only text)
- `~/.TheIgors/claudecode/YYYYMMDD.slate.txt` — daily slates (one file per day)
- `~/.claude/skills/<skill>/SKILL.md` — active skills (user-level)
- `~/TheIgors/lab/claudecode/cc_skills/<skill>/SKILL.md` — skill templates (git-versioned)
- `~/dev/src/ClaudeAndAkien/skills/*.md` — case-study copy (separate repo)
- `~/TheIgors/CLAUDE.md` — rules narrative
- Memory palace `theigors/rules/*` — rules (partial mirror of CLAUDE.md)
- `~/.claude/projects/.../memory/MEMORY.md` — user memory (session-persistent)
- `~/TheIgors/claude_chat_logs/YYYY-MM-DD.md` — chat log echoes

Every workflow change has to update 3-5 of these, by hand. Drift is constant. The /audit rename sprint earlier today hit twelve live references across four subsystems.

## The decision

**Igor's memory palace (table: `memory_palace`) becomes canonical source of truth for project-scoped artifacts.** Everything else becomes a generated echo updated on a well-defined trigger (ticket close).

## Canonical storage choice (two-layer model)

For each artifact class, two things exist in the DB:

1. **Canonical data** — lives in `memories` table as first-class memory rows with `parent_id` forming the subtree. Memory type is chosen from the existing enum (no new types per the "no new memory types, tags only" rule):
   - Tickets: `memory_type=FACTUAL`, metadata.kind='ticket', parent=TICKETS_ROOT
   - Decisions: `memory_type=REFERENCE`, metadata.kind='decision', parent=DECISIONS_ROOT
   - Slates: `memory_type=REFERENCE`, metadata.kind='slate', parent=SLATES_ROOT
   - Skills: `memory_type=PROCEDURAL`, metadata.habit_type='skill', parent=SKILLS_ROOT
   - Rules: (already live as palace rows; keep shape)

2. **Navigable index** — lives in `memory_palace` table as pointer nodes at `theigors/<kind>/<id>`. Each palace row's `pointers` field names the canonical memory id(s). This is the human-navigable tree; canonical data is the graph.

**Roots under PR_IGORS_PROJECT:**
- TICKETS_ROOT (new) — parent=PR_IGORS_PROJECT
- DECISIONS_ROOT (new) — parent=PR_IGORS_PROJECT
- SLATES_ROOT (new) — parent=PR_IGORS_PROJECT
- SKILLS_ROOT (new) — parent=PR_IGORS_PROJECT
- (rules already under `theigors/rules/*` in palace; no new root needed)

PR_IGORS_PROJECT stays as the activation facia — the single node that fires on project-related salience.

## Echo targets + timing

**Timing:** every ticket close triggers echo regeneration. Not day's end. This is T-sync-on-close-not-dayend.

**Targets and their freshness contract:**

| Artifact  | Echo location                                              | Regeneration trigger |
|-----------|------------------------------------------------------------|----------------------|
| Tickets   | `~/.TheIgors/cc_channel/queue.json`                        | ticket close         |
| Decisions | `lab/design_docs_for_igor/decisions_log.dsb` (append mode) | decision close       |
| Slates    | `~/.TheIgors/claudecode/YYYY-MM-DD.slate.txt`              | any ticket close affecting today's slate |
| Skills    | `~/.claude/skills/<skill>/SKILL.md` (active copy)          | skill memory row update |
| Skills    | `lab/claudecode/cc_skills/<skill>/SKILL.md` (git template) | skill memory row update |
| Skills    | `~/dev/src/ClaudeAndAkien/skills/<skill>.md` (case study)  | skill memory row update |
| Rules     | `CLAUDE.md` (thin shim only)                               | rule memory row update |
| GitHub    | issues updated to match ticket state                       | ticket close         |

Each echo is idempotent — re-running generates byte-identical output.

## What writes the echoes

New or extended: `lab/claudecode/palace_sync.py`. Currently syncs the palace repo echo at `lab/theigors/`; extend it with renderers:
- `render_queue_json(tickets_subtree) → queue.json contents`
- `render_slate(slate_memory_row) → markdown`
- `render_skill(skill_memory_row) → SKILL.md (frontmatter + body)`
- `render_decisions_log_line(decision_memory_row) → one-line append`
- `render_rules_shim(rules_subtree) → CLAUDE.md content` (the thin shim that just points at DB)

`cc_queue.py done` (and the future ticket-memory equivalent) invokes palace_sync after the state change.

## Migration paths (one per child ticket)

Each child ticket owns its own migration sub-plan. This shape-lock doc provides the contract each has to honor:

- **T-rules-canonical-db-first** (M) — rules. Palace already has `theigors/rules/*`; audit for gaps vs CLAUDE.md, fill, then shrink CLAUDE.md to a thin shim.
- **T-tickets-into-palace-subtree** (L) — tickets. One-shot migration script reads current queue.json → creates 694 FACTUAL rows → palace pointers → cc_queue.py swaps to read/write graph.
- **T-decisions-into-palace-subtree** (M) — decisions. Ingest decisions_log.dsb → REFERENCE rows. Forward-going writes via /decided into the graph, echo to .dsb.
- **T-slates-into-palace-subtree** (S) — slates. Ingest existing .slate.txt files → REFERENCE rows. slate_manager.py swaps.
- **T-skills-into-palace-subtree** (M) — skills. Ingest ~/.claude/skills/ + lab/claudecode/cc_skills/ into PROCEDURAL rows. Resolve drift by picking the active copy as canonical; on skill update, regenerate all three echo locations.
- **T-sync-on-close-not-dayend** (S) — moves the echo trigger from /day-close to each done action.

## Invariants

- **Palace is write-once per event.** No in-place edits of canonical rows outside of append-only events (ticket close, decision close, etc.). This mirrors the sessions table discipline.
- **Echoes are never read for truth.** They exist for human browsing, git diffs, GitHub UI. If code needs ticket state, code reads the graph.
- **Drift alarm.** If palace and echo disagree on re-render, palace wins and the drift is flagged (logged + slate note). Catches "someone hand-edited queue.json" cases.
- **No new memory types.** Every kind uses existing types + metadata tags.

## What this ticket does NOT do

- Not writing any migration code. Children do that.
- Not changing CLAUDE.md. T-rules-canonical-db-first does that.
- Not touching queue.json. T-tickets-into-palace-subtree does that.

This ticket's deliverable = this document. The epic closes when this document is accepted as the shape-lock, at which point the gated children can start.

## Open questions (resolve during child implementation)

- Exact metadata key names. Pick conventions in T-tickets-into-palace-subtree and follow in the rest.
- Whether `status` should be a scalar metadata field or a separate status-transition-log edge. Bias: scalar, with history preserved via sessions table references.
- Whether ClaudeAndAkien should pull from TheIgors's palace or hold its own copy. Bias: pull from TheIgors; becomes a read-only echo. Defer decision until T-skills-into-palace-subtree.
- Whether GitHub issue sync is bi-directional. Bias: one-way (palace → GitHub). If GitHub issue is hand-edited, next sync overwrites. Defer: might want a read-back for comments.

## Provenance

Akien 2026-04-20 post-/fixit dictation. Bundle with D-workflow-overhaul-2026-04-20 tickets. Day-close planned after full batch ships.
