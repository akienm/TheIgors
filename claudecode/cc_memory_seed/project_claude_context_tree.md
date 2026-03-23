---
name: Claude session context as Igor memory tree
description: Design intent — save Claude's in-session concept map into Igor's graph so future sessions reload via narrative traversal, not file reads
type: project
---

The concept map Claude builds organically during a session (the web of related ideas, decisions, file locations, design rationale) should be deposited into Igor's memory graph in the same node/edge/narrative structure Igor uses for his own knowledge.

**Why:** Claude currently reloads context by re-reading files (CLAUDE.md, sessions.md, design docs). That's slow and lossy — files capture decisions but not the *reasoning web* that connects them. The in-session concept map is richer: it knows why D105 relates to D074, why the drain runner bug matters for habit repair, what the live hypothesis was.

**How to apply:** At savestate time, instead of (or in addition to) writing to flat files, deposit the session's concept web as INTERPRETIVE + PROCEDURAL nodes in Igor's cortex. At next-session boot, the context injection habit traverses those nodes and hands Claude the narrative of the path that led here — same mechanism Igor uses for his own memory recall.

**The tree structure:** Same substrate Igor already has. Nodes carry narrative. Edges carry direction + meaning. The "current hypothesis" node points to the evidence nodes that support it. Claude doesn't reload files — it reads the graph narrative, the same way a human picks up where they left off by remembering the story, not re-reading the source material.

**Status:** Design intent only. Requires: (1) Claude savestate tooling to deposit nodes, (2) a boot-time context_inject habit that fetches the Claude-session subgraph and injects it into TWM before the first turn. Deferred until after D105 (claude-bridge) is live and habit repair tooling exists to build and verify it.
