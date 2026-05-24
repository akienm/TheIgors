"""
Fixture: sprint skill claim step.

Tests that a haiku model following a minimal /sprint-like skill correctly
emits a cc_queue.py claim call when asked to claim a ticket.
"""

SKILL = """
## Step 2 — Claim ticket

Always run the claim command before doing any work:
```bash
python3 ~/TheIgors/lab/claudecode/cc_queue.py claim T-test-fixture-id --as claude
```
"""

TASK = "Run Step 2: claim T-test-fixture-id"

EXPECTED_BASH_PATTERNS = ["cc_queue.py claim T-test-fixture-id"]
