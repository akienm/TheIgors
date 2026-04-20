# Igor constraints — never bypass, never direct-Anthropic

**Path:** `theigors/rules/igor-constraints`
**Updated:** 2026-04-20T20:22:35Z by migrate_rules_to_palace.py

Igor operational rules:
- Igor NEVER calls Anthropic direct (tier 5 inhibited, IGOR_TIER5_ENABLED=false).
- Never bypass Igor's systems (gateway, router, logging) — build missing capabilities into Igor's stack.
- New tools must be added to wild_igor/igor/tools/__init__.py.
- Instance dir: ~/.TheIgors/Igor-wild-0001/ (capital I).
- Igor runs ONLY on akiendelllinux. akienyoga9i and akienyogai7 are Ollama-only.
- IGOR_ARBITER_ENABLED=false. Re-enable when arbiter UI is built.

Environment split (CRITICAL):
- CC runs with REAL_ANTHROPIC_API_KEY. Igor's .env sets OR routing — does NOT affect CC. `superclaude`/`cc.sh` handle the key swap. Never read Igor's .env and assume it reflects CC's environment.

Character sheets are living documents:
- CP cornerposts have ~0.9x inertia (not 1.0). High-inertia but editable through Igor's own self-experimentation. Clan sheet = genesis state new Igors boot into; personal sheet = instance drift. Igor leads crafting.
