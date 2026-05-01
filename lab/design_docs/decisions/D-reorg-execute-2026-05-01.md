# D-reorg-execute-2026-05-01
**title:** Execute reorg per § 4 unclear cases (per-bucket Akien decisions 2026-05-01)
**date:** 2026-05-01
**status:** open
**spawned_tickets:** T-sqlite-out-wild-0001-db, T-sqlite-out-word-graph-db, T-sqlite-out-claude-budget-db, T-reorg-bucket-archive-moves, T-closed-tickets-path-normalize

## Decision narrative
Akien reviewed the 12 unclear cases in lab/design_docs/reorg-plan-2026-05-01-opus-pass.md § 4 and ratified per-bucket decisions:

- **#1 (live .db files)** — REMOVE (CLAUDE.md "always protect" pre-dates Postgres migration). Migrate-first, debug-ready. Three sqlite-out tickets filed.
- **#2 seed_*.py** — MOVE → TheIgorsProject/seed_archive/ (palace migration absorbed)
- **#5 migrate_*.py** — MOVE → TheIgorsProject/migrations_archive/ (one-shot scripts)
- **#6 cc_memory_seed/** — MOVE → TheIgorsProject/20260427.Cleanup/auto_memory_archive/ (predecessor of live auto-memory)
- **#7 papers/history/_archive/** — MOVE → TheIgorsProject (loose .csb.txt files stay)
- **#11 closed_tickets.txt** — NORMALIZE path (~/.TheIgors/lab/claudecode/ → ~/.TheIgors/claudecode/)
- **#3 cc_skills/** — folds into D-claudeandakien-folded-2026-05-01 (workshop dead → datacenter)
- **#4 TheIgorsProject/skills/** — DELETE (executed inline; predecessors, git preserves)
- **#8 utility_closet/** — coordinated under T-capability-extraction-from-igor (already filed)
- **#9 TheIgorsProject root** — STAY (dump bucket pattern intentional)
- **#10 imap_stub_spike.py** — MOVE → agent_datacenter/lab/spikes/ (executed inline)
- **#12 hosted_igor.txt** — MOVE → TheIgorsProject (executed inline)

#4, #10, #12 executed inline (3 simple moves, no cross-tree code deps); the bucket archive moves and .db migrations are tracked through the spawned tickets.
