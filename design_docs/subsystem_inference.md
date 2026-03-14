# Subsystem: Inference

*Updated: 2026-03-14 | Machine-readable: `design_docs_for_igor/subsystem_inference.dsb`*

---

## Design Principles

- **Single entry point**: `InferenceGateway.reason()` is the only call site for all inference. No tier strings leak to callers.
- **from_env()**: Instantiates all tier reasoners at boot. Stored on Igor as `self._gateway`.
- **DAG routing** for pipeline calls (preparse, winnow, NE, think) via `gateway.call(purpose_id)`.
- **Tier cascade** for interactive/background via `gateway.reason(level, skip_to)`.

---

## Tier Ladder

| Tier | Model | Used for |
|------|-------|---------|
| t1 | Habit (no LLM) | BG score ≥ threshold |
| t2 | Ollama qwen2.5:7b | Background NE, preparse, batch |
| t3 | OR gpt-4o-mini | Cheap interactive (when skip_to permits), preparse, winnow |
| t3.5 | OR claude-haiku-4.5 | **Interactive floor** (D035: minimum for all interactive turns) |
| t4 | OR claude-sonnet-4-6 | High complexity, NE ambiguity escalation |
| t5 | Anthropic direct | Inhibited (`IGOR_TIER5_ENABLED=false`) |
| t6 | Arbiter alert | All inference exhausted |

**Critical**: D035 means **all interactive turns use t3.5 minimum**. If Igor tells you it will use t2/t3 for a conversation turn, that plan is wrong.

---

## Routing Logic

```
level=background_batch → pool.reason_batch() (local quality priority)
level=background       → cloud_active? t3 : t2 (never blocks main loop)
level=interactive      → cascade from skip_to:
                          low complexity  → start at t3 (then t3.5 floor kicks in)
                          medium          → start at t3.5
                          high            → start at t4
                          NE ambiguity    → escalate to t4
```

`skip_to` is computed from thalamus complexity + milieu dominance.

---

## DAG Purposes

Pipeline calls use purpose-based routing, not the interactive cascade:

| Purpose | Local preferred | Cloud preferred |
|---------|----------------|----------------|
| preparse | Ollama (fallback: OR gpt-4o-mini) | OR gpt-4o-mini |
| winnow | Ollama (fallback: OR) | OR gpt-4o-mini |
| ne | Ollama (fallback: OR gpt-4o-mini) | OR gpt-4o-mini + json_object |
| think | Ollama only (no cloud fallback) | — |

---

## Cloud Mode Gate

Cloud mode is the condition where Igor prefers cloud inference over local.

**Three conditions must all be true**:
1. `IGOR_CLOUD_TRAINING_ENABLED=true`
2. OpenRouter balance ≥ `IGOR_CLOUD_BUDGET_FLOOR_USD` (default $10)
3. Local hour is 06:00–22:59

**Cached 5 minutes.** Balance unknown = -1.0 sentinel → assumes funded. Network errors never silently disable cloud mode.

---

## Reasoners

| Class | Used for |
|-------|---------|
| `OllamaReasoner` | t2 (qwen2.5:7b); local CPU inference |
| `OpenRouterReasoner` | t3, t3.5, t4 |
| `AnthropicReasoner` | t5 (inhibited) |

All extend `BaseReasoner`. `MAX_TURNS` defined in `base.py` (env: `IGOR_MAX_TURNS`).

---

## Known Failure Patterns

- **F003** IMPULSE_SKIP: background impulse silently dropped when NE busy
- **F004** cloud-mode-disabled: balance check fails, OR balance returns error, cloud silently off
- **F005** tier-model-inversion: OR model env var pointing to wrong tier model
- **F006** gateway-attr-error: self-edit broke an attribute name in inference_gateway.py

---

## Decisions

D015, D023, D025, D026, D031, D032, D033, D034, D035, D039, D053
