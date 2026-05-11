# D-research-breadth-depth-2026-05-11
**title:** Librarian research API: breadth + depth floats replacing depth string param
**date:** 2026-05-11
**status:** open
**spawned_tickets:** T-research-api-breadth-depth

## Decision narrative
Replace research(query, depth: str) with research(query, breadth: float=0.5, depth: float=0.5) — two independent 0.0-1.0 parameters analogous to model temperature. breadth scales number of sources (0=single, 1=broad multi-source); depth scales processing intensity (0=summary, 1=full synthesis). Canonical use: two-pass research — broad survey first (breadth=0.8, depth=0.2), deep dive second (breadth=0.1, depth=0.9). Backward compat shim converts old depth='shallow'/'deep' string calls. T-librarian-external-doc-fetch is gated on this ticket so external fetch is implemented against the new API.
