---
name: Today's plan and big topics (2026-03-18)
description: Three-round work plan + Claude organization initiative + figure-it-out meta-process
type: project
---

## Three-Round Plan (in order)

1. **Cleaning round** — audit_report_20260317.md findings; fix misplaced files, hardcoded paths, source tree leakage
2. **Push-code-into-data round** — move logic from Python into Igor's DB (habits, skills, procedures)
3. **Performance optimization round** — after the substrate is clean

Also: bug reports starting to come in from Windows instance (Igor internal).

## Claude Organization Initiative

Goal: bootstrap anyone (new hire, collaborator) with Akien's process — not a "working with Claude" doc but a transferable methodology.

End state:
- DB of patterns/habits
- Skills file (composable units)
- Minimal CLAUDE.md (just wiring, not process)
- Methodology for pushing process to DB or OR minions
- For TheIgors specifically: push more and more into Igor

### Skill aliases to build (trigger words → Igor skills)
- `commit` → full git cycle skill
- `decided` → record decision skill
- `scan debug logs` → log triage skill
- `prepare a sprint/discussion` → sprint prep skill
- More will emerge from use

**Why:** By the time we're done, the process IS the data. Claude.md becomes minimal scaffolding; the rest lives in Igor or OR minions.

## Figure-It-Out Meta-Process (ticket created, deferred post-Windows)

Akien's insight: his habits don't have fixed code — the steps ARE habits linked together. He remembers how to *figure out* the process each time, not the process itself. That's how processes improve.

Igor should learn to derive procedures via graph traversal, not recall fixed lists. A PROCEDURAL node should be a traversal path, not a stored sequence.

**GitHub issue created 2026-03-18. Do after cleaning + code-into-data rounds.**
