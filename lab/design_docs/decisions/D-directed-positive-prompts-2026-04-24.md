# D-directed-positive-prompts-2026-04-24

**title:** Directed positive framing + binding imperatives + MCP-first tool naming — prompt-rewrite pass across skills and rules
**date:** 2026-04-24
**status:** open
**spawned_tickets:** T-directed-positive-prompts-pass-1

## Decision narrative

High-friction skills and CLAUDE.md rules state rules as negations, making the right behavior a constraint rather than a path. Rewrite mandatory-step lines using the paired shape: binding imperative (Always/Shall/Must/First) + directed workflow (spell the path) + named MCP tool where one exists. All three layers required; any two-layer combination is weaker. Rationale: today's session showed repeated ad-hoc psql patterns where MCP tools exist but aren't prescribed; binding imperatives + workflow spelling is the scaffold that makes them the default path. Akien's principle: "we make it easier for you to follow the rules by spelling them out where relevant" — the 'Always' imperative functions like 'shall' in requirements writing.
