# voice_ab — A/B framework for voice production (graph vs LLM)

**Path:** `theigors/subsystem_index/voice_ab`
**Updated:** 2026-04-27 by cap-map-followups

Final stage of Igor's output-side pipeline. By the time a DecisionBlob lands here, input-side trees have already decided WHAT Igor wants to say (selected_action). voice_ab decides HOW he says it — in whose voice. Two voice actors compete:

  - GraphVoiceActor — Igor's own voice, grown from his generation word graph (G37). Currently primitive token extension; gets better as the graph trains.
  - LLMVoiceActor — calls gateway.reason with voice_context() to produce character-coherent text. Current production path.

The A/B comparison is the graduation mechanism: the LLM voice actor retires when the graph voice consistently scores higher.

Primary file: wild_igor/igor/cognition/voice_ab.py — read its top-of-file docstring for the canonical explanation.

Also see: wild_igor/igor/cognition/decision_blob.py, wild_igor/igor/cognition/prompt_contexts.py (voice_context).

Originating ticket: T-voice-actor-ab-framework (#439).

CP grounding: CP1 (both outputs logged with provenance), CP3 (per-turn comparison + winner in JSONL), CP6 (framework produces candidates; existing VoiceProducer selects).
