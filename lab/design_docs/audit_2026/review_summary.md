# Audit prompts — review summary for Akien

## Pass 1 (Gemini) — `lab/design_docs/audit_2026/pass1_gemini_prompt.md`

- **Length:** 348 lines (16KB)
- **Personas covered:** YES — all 11 personas present with distinct remits:
  1. Senior engineer (correctness, testability, state mgmt)
  2. Architect (coupling, abstractions, boundaries)
  3. Database engineer (SIMPLIFY bias, table/column redundancy)
  4. Systems/performance (threads, leaks, load, observability)
  5. Biomimicry (mechanism vs naming — HIGHEST-VALUE, deeply specified)
  6. Engram neuroscientist (7-criterion checksum against Tonegawa/Josselyn lineage)
  7. Cognitive scientist (priming, spreading activation, TWM competitiveness)
  8. AI safety (goal-drift, habit-misfire, scope_guard robustness)
  9. Systems dynamics (feedback loops, oscillation, second-order effects)
  10. QA/test (failure modes, coverage, flaky tests, self-monitoring)
  11. Docs + CC workflow (coherence + "how to use CC better")
  
- **Biomimicry lens:** YES, extensive and central:
  - Persona 5 (biomimicry engineer) is CROSS-CUTTING with "HIGHEST-VALUE" label
  - Explicit taxonomy: `honest | theatrical | procedural-with-bio-name | n/a`
  - Concrete examples given (hebbian_update counter, habit-as-if/else-branch, milieu propagation, attractor-as-top-K)
  - Verdict requirement for every "procedurally-named" finding
  - Positive outliers section requested separately (validation of real work)
  
- **Skip-rules present:** NO — explicit "Do NOT constrain yourself with 'what to pay attention to'" section (line 251–260). Zero skip rules. Instructions say nitpick everything, over-report rather than under-report, flag mysteriously empty files, unused imports, mismatched names/behavior.
  
- **Full-repo breadth framing:** YES — input payload explicitly includes `wild_igor/ + lab/ + tests/ + CLAUDE.md + memory_palace export + ~/.claude/skills/ + lab/claudecode/ + sample slate + queue.json`. No subsystem pre-filtering.

- **Gaps / suggested edits:** None structural. Minor clarifications for Akien:
  - Line 337–343: "Remaining review questions" asks Akien to confirm 7 engram criteria (drop any not testable) and confirm skip scopes (archive/, fixtures/, __pycache__/, migrations). These are housekeeping for the prompt, not defects.
  - Output format (lines 265–284) specifies per-finding structure with severity/area/personas/biomimicry-verdict — well-shaped.

---

## Pass 2 (Opus subagent) — `lab/design_docs/audit_2026/pass2_opus_subagent_prompt.md`

- **Length:** 239 lines (11KB)
- **Template shape:** YES — template clearly marked with `{{CONCERN_AREA}}`, `{{PASS1_FINDINGS_FOR_THIS_AREA}}`, `{{PASS1_PATTERN_OBSERVATIONS}}` placeholders (line 27). Fixed prompt + substitutable slots.
  
- **Concern-category slots:** YES, 9 orthogonal cuts proposed (lines 200–213):
  1. cognition + reasoning (inference_gateway, reasoners, turn_pipeline, etc.)
  2. memory + cortex (cortex.py, models.py, TWM, consolidation, attractors, heat)
  3. habits + engrams + pe_chain (procedural memory, node_executor, cursor_runtime)
  4. tools + registry + MCP (tool registration, dispatch, misfire tracking)
  5. comms + UC rack (utility_closet, transports, registries)
  6. reading + book_learner (reading_tool, extraction, watch habits)
  7. ops + milieu + boredom + scope_guard (operational loops, experiment_cascade)
  8. infra + db + tests + docs (db_proxy, migrations, test suite, CLAUDE.md coherence)
  9. Claude Code workflow + dev-loop (skills, lab/claudecode scripts, sprint cycle, hooks, inertia enforcement)
  
- **Subagent remit beyond Pass 1 findings:** Clear:
  - Verify/refute per-finding (lines 56–92, verdict taxonomy: CONFIRMED/CONFIRMED_WORSE/CONFIRMED_NARROWER/REFUTED/STALE/NEEDS_RUNTIME)
  - Blast radius analysis (HIGH-inertia files, test coverage, habit references, tool dependencies)
  - Biomimicry check on cited code + honest-mechanism sketches if theatrical
  - Proposed tickets (5-point format: title, size, tags, description 150–400 words, no code)
  - 30% attention on neighbourhood beyond cited lines (lines 96–112)
  - Dead-code cross-check vs habits (lines 108–112)
  - Standing "how could we use CC better?" remit for all subagents (lines 114–124)
  - Per-finding disposal tags: SHIP/DEFER/INVESTIGATE/DISCARD (lines 185–189)
  
- **Output format:** Specified as markdown with sections: per-finding verdicts, Pass 1 gaps, dead-code cross-check, summary (lines 126–171). Summary includes ticket-count rollups and disposal recommendations.

- **Gaps / suggested edits:** None structural. Minor housekeeping at line 229–234:
  - "Remaining review questions": whether 8 concern areas are the right cut (merge/split post-Pass1) and whether 30% neighbourhood attention is right ratio. These are for Akien tuning, not defects.
  - Note (line 199): "8 areas; pick 4–8 at kickoff depending on Pass 1 finding density" — implies dynamic cut-point, which is good (not oversized).

---

## Pass 3 (synthesis)

- **Draft exists:** NO — no `pass3_*` file found in `lab/design_docs/audit_2026/`.
  
- **Action:** Per ticket description, "Pass-3 prompt is trivially different (me synthesizing my own subagents)" — Akien still reviews the synthesis framing. However, ticket notes the prompt may not need a separate file since it's Akien's synthesis work (not external model call). Unclear whether Pass 3 needs a templated prompt file or just Akien's manual synthesis instructions.
  
  **Recommendation:** Flag for Akien — does Pass 3 need a separate prompt file, or is the synthesis framing documented elsewhere (e.g., T-three-pass-audit ticket, or verbal kickoff)?

---

## Recommendation

**READY FOR AKIEN REVIEW.** Pass 1 and Pass 2 prompts are structurally sound:
- Multi-persona depth (11 personas in Pass 1, 9 orthogonal subagent cuts in Pass 2)
- Biomimicry lens is central, not decorative (dedicated persona, explicit taxonomy, honest-vs-theatrical verdicts)
- Zero skip-rules enforced (breadth mandate, over-report bias)
- Template shape is clear and substitution-ready for parallel subagent dispatch
- Both prompts carry housekeeping questions for Akien (confirm skip scopes, concern-area cuts, neighbourhood attention ratio)
- Pass 3 disposition unclear — clarify whether synthesis needs a separate prompt file or is Akien-driven

Akien should review the 11 personas, engram criteria (line 137–175 in Pass 1), and concern-area cuts (line 200–213 in Pass 2) for scope/balance. Prompt quality is high; fixture is ready for approval + kickoff.
