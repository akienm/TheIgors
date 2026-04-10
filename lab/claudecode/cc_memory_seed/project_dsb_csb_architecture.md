---
name: DSB/CSB architecture — role of compressed doc formats
description: Clarification of .md vs .dsb/.csb vs DB roles for design docs
type: project
---

DSB/CSB files are for Claude (and Igor) to absorb with fewest tokens — they are the compressed representation of the human-readable .md files.

Pipeline:
- `.md` files in `design_docs/` = human-readable source, maintained by Claude (not Akien); updated when we get around to it, not on every session
- `.dsb`/`.csb` files in `design_docs_for_igor/` = compressed/token-efficient form for Claude/Igor
- DB = eventual runtime store; change detection on .md files triggers reload into DB in compressed form

**Why:** In the DB, content should be stored in whichever form Claude and Igor can absorb with fewest tokens. The .md files are the only English-language form needed in the repo. Eventually Igor will maintain them himself without external inference.

**How to apply:** Never delete the .md files as "superseded by .dsb" — they are the source. The .dsb files are derived artifacts. Claude updates the .md files; Igor will eventually take this over.
