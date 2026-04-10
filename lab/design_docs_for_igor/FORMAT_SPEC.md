# DSB Format Specification
# Distilled Structured Block — token-minimal machine-readable docs

## Rules

1. Every file starts with a one-line header: `DOC|name|version|updated=YYYY-MM-DD`
2. Sections use `SECTION_NAME|` on its own line, content indented 2 spaces beneath
3. Key:value pairs use `KEY|value` — no spaces around pipe
4. Multi-value: `KEY|v1,v2,v3`
5. Sub-keys: `KEY|field=value|field2=value2`
6. Lists: one item per line, 2-space indent, no bullet markers
7. No markdown: no #, ##, *, -, ---, or decorative lines
8. No blank lines except between top-level sections
9. No prose where structure will do
10. No redundant context — the file name IS the context
11. Abbreviations encouraged for repeated terms (defined in glossary.dsb)
12. Comments: `//` prefix, used sparingly, only where meaning is non-obvious

## Common abbreviations
CP    = Core Pattern (CP1-CP6)
ID    = Identity memory
PROC  = Procedural memory
TWM   = Temporal Working Memory
NE    = Narrative Engine
BG    = Basal Ganglia
OR    = OpenRouter
t2/t3/t35/t4/t5 = tier.2 through tier.5

## Example

DOC|subsystem_thalamus|v1|updated=2026-03-13

META|inertia=MEDIUM|parent=architecture_root.dsb|ticket=#42

PURPOSE|
  Classify user intent into 13-category taxonomy
  Drive tier skip_to based on complexity signal

INPUTS|user_text,ring_memory_summary,milieu_state
OUTPUTS|intent=str,complexity=low|medium|high,skip_to=tier.3|tier.3.5|tier.4

DESIGN_POINTS|
  DP1|13-intent taxonomy incl creative_request
  DP2|complexity drives skip_to — low skips preparse, high skips to t4
  DP3|milieu dominance escalates skip_to by one tier

DECISIONS|
  D014|why thalamus not inline in main — separation of routing from response
  D019|why 13 intents not fewer — empirically derived from session logs

GAPS|
  G44p1|open|thalamus confidence score not yet wired to BG threshold
