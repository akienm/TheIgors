# Igor constraints — inference in-stack, environment CC-owned

**Path:** `theigors/rules/igor-constraints`
**Updated:** 2026-04-21 by T-audit-cc-rules-approach-frame

Igor's inference runs through his own stack: gateway, router, logging. Direct-Anthropic is gated OFF (`IGOR_TIER5_ENABLED=false`) and arbiter is gated OFF (`IGOR_ARBITER_ENABLED=false`) pending the arbiter UI. Flipping either gate needs explicit Akien go-ahead.

Extend Igor's stack to fill capability gaps — new tools in `wild_igor/igor/tools/__init__.py`, new channels in the existing `network/channels/` framework, etc. Target: Igor has every capability he needs through his own infrastructure.

Instance layout: `wild_igor/igor/` = code, `~/.TheIgors/Igor-wild-0001/` = runtime (capital I). Igor runs on akiendelllinux; yoga9i and yogai7 are Ollama-only.

Environment split (CRITICAL): CC uses Claude Max auth — no API key required; Igor's .env sets OR routing separately. Use CC's env for CC decisions — Igor's .env does not reflect CC's environment.

Character sheets are living documents: CP cornerposts have ~0.9x inertia (not 1.0). High-inertia but editable through Igor's own self-experimentation. Clan sheet = genesis state new Igors boot into; personal sheet = instance drift. Igor leads the crafting.

revision: 2026-04-21 — reframed to approach-target (T-audit-cc-rules-approach-frame)

