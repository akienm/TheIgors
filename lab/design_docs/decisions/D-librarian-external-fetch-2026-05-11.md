# D-librarian-external-fetch-2026-05-11
**title:** Wire external doc fetch into librarian _research_deep
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-librarian-external-doc-fetch

## Decision narrative
librarian/research.py _research_deep() has an explicit stub (`sources=[]  # populated when external search is wired`). Context 7 MCP is what general CC users use for live doc lookup — the librarian IS our equivalent. Wire the stub with a curated source index (Anthropic docs, psycopg2, Python stdlib, ADC/TheIgors) + urllib fetch + synthesis grounding. Non-blocking on fetch failure.
