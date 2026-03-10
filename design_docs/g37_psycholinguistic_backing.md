# G37 — Psycholinguistic and Neurolinguistic Backing

*Compiled 2026-03-10. Documents the scientific support for the asymmetric dual word graph architecture (Issue #160).*

---

## Summary

Human cognition uses partially independent systems for language comprehension and language production. These systems share neural infrastructure but diverge in structure, function, and activation patterns. The divergence aligns with the G37 "two-tree" architecture: a fast, lossy comprehension tree and a structured, identity-expressive production tree. This mapping is supported by psycholinguistics, neurolinguistics, and predictive processing research.

---

## Key Researchers and Models

**Willem Levelt** — *Blueprint for the Speaker*; modular production pipeline (conceptualization → formulation → articulation). Foundational for production/comprehension separation.

**Noam Chomsky** — generative grammar; competence/performance distinction; early formalization of separate mechanisms for understanding vs generating sentences.

**Fernanda Ferreira & Victor Ferreira** — psycholinguistics overview; comprehension as fast/heuristic, production as structured/planned. *(Open Encyclopedia of Cognitive Science)*

**Caroline Arvidsson et al.** — fMRI evidence for partial overlap but functional asymmetry between production and comprehension systems; stronger LIFG activation in production, stronger anterior temporal activation in comprehension. *(Cerebral Cortex, 2024)*

**Dual-route and distributed models** — comprehension and production rely on overlapping but non-identical neural pathways; production engages more frontal planning regions.

**Predictive processing theorists (Friston, Clark)** — comprehension as prediction-heavy decoding; production as generative planning.

**Springer overview on speech production** — emphasizes distributed, non-unitary architecture beyond classical Broca/Wernicke.

---

## Mappings to Igor (G37)

| Scientific construct | Igor / G37 equivalent |
|---|---|
| Psycholinguistic comprehension system | Recognition graph: fast, context-driven, ambiguity-collapsing, prediction-based |
| Levelt-style production pipeline + frontal planning | Generation graph: structured, deliberate, ambiguity-expanding, identity-expressive |
| Divergent activation patterns | Igor's need for separate internal structures for interpretation vs expression |
| Voice emergence | Production-side planning choices, not inference-time reasoning |
| Cloud model | External reasoning substrate analogous to higher-level conceptualization, not stylistic generator |

---

## Key Findings from the Science

- Production and comprehension share the left perisylvian network but differ in activation intensity and regional emphasis (LIFG production-dominant vs anterior MTG/STS comprehension-dominant).
- Psycholinguistics consistently treats comprehension and production as distinct research domains with different mechanisms and constraints.
- Production requires explicit sequencing and structural planning; comprehension relies on rapid heuristics and predictive filling-in.
- Distributed models show language is not a single pipeline but a set of interacting subsystems.

---

## Sources for Further Reading

- Levelt, *Speaking: From Intention to Articulation* (MIT Press).
- Ferreira & Ferreira, *Psycholinguistics* (Open Encyclopedia of Cognitive Science).
- Arvidsson et al., *Conversational production and comprehension* (Cerebral Cortex, 2024).
- Springer chapter: *How do we Produce and Understand Speech?*
- Clark & Murphy; Grice; pragmatics and conversation models.
- Predictive processing literature (Friston, Clark) for decoding vs generative asymmetry.

---

## Open Questions for Implementation

- How to encode production-tree style primitives (rules, templates, weighted transitions) beyond the current co-occurrence graph?
- How to maintain stability of the production/generation graph across sessions without it drifting toward recent context at the expense of established voice?
- How to integrate cloud reasoning (conceptualization layer) without contaminating production style — the cloud model should inform *what* to say, not *how Igor says it*.
