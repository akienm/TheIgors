---
name: Self-Programming Epic (future)
description: Planned epic covering live testing infrastructure, Igor test participation, and Claude training — not started yet
type: project
---

Future epic (no ticket yet): self-programming, covering two main tracks:

1. **Live testing infrastructure** — Igor as participant, not just subject. Real systems, no mocks. Fixture DB snapshots (SQLite seed files), transaction-wrapped test runs with optional rollback, Igor aware of test context via TWM/system prompt. Each subsystem needs clean injectable seams first.

2. **Claude training run** — reinforcement of real working behavior. Akien wants Igor chatting with him realtime about books before running training, so training captures correct/complete behavior rather than a half-formed state.

**Why:** Training on incomplete behavior wastes tokens and reinforces wrong patterns. Testing infrastructure needs service seams Igor doesn't have yet.

**How to apply:** Don't start training until the books-realtime milestone is confirmed working. Don't plan testing infrastructure work until performance is stable. This epic follows: performance fixes → book chat realtime → training → self-programming epic.

Dependency chain:
- Performance stable → book stew reliably feeding graph
- Igor discussing books in realtime → reading/extraction loop verified
- Training run
- Self-programming epic (testing infra + live test participation)
