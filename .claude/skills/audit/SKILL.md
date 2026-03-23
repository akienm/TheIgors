---
name: audit
description: Automated code + system audit for TheIgors. Runs tests, file placement check, code smell scan, registry coherence, inertia check, thread hygiene, log sizes, OR burn rate, DB schema spot-check. Then evaluate findings: fix small issues now, ticket anything bigger. Use when Akien says /audit, "run the audit", "audit the code", or before /day-close.
---

# Audit — Automated Health Check

Produces a findings report. Then evaluate: fix small issues now (missing log call, bare except),
ticket anything bigger. After fixes, run /commit, then /day-close.

---

## Step 1 — Tests

```bash
cd ~/TheIgors && source venv/bin/activate && python -m pytest tests/ -x -q 2>&1 | tail -20
```

If tests fail: **STOP**. Fix before proceeding. Offer to run `/test-fix`.

---

## Step 2 — File placement

```bash
/validate-files
```

Note any misplaced files. Small fixes now; large restructures → ticket.

---

## Step 3 — Code smell scan

```bash
cd ~/TheIgors && source venv/bin/activate && python3 - << 'EOF'
import ast, pathlib, sys

issues = []
src = pathlib.Path("wild_igor/igor")
for f in sorted(src.rglob("*.py")):
    try:
        tree = ast.parse(f.read_text())
    except SyntaxError as e:
        issues.append(f"SYNTAX_ERROR|{f}|{e}")
        continue
    for node in ast.walk(tree):
        # bare except: pass
        if isinstance(node, ast.ExceptHandler):
            if node.type is None and len(node.body) == 1 and isinstance(node.body[0], ast.Pass):
                issues.append(f"BARE_EXCEPT_PASS|{f}:{node.lineno}")
        # except block with only Pass (typed)
        if isinstance(node, ast.ExceptHandler):
            if all(isinstance(s, ast.Pass) for s in node.body):
                issues.append(f"SILENT_EXCEPT|{f}:{node.lineno}")

for i in issues:
    print(i)
print(f"\n{len(issues)} smell(s) found")
EOF
```

For each finding: is there a log call in the except block? If not → add one now (small fix).

---

## Step 4 — Registry coherence

```bash
cd ~/TheIgors && source venv/bin/activate && python3 - << 'EOF'
import sys, os
os.environ.setdefault("IGOR_HOME_DB_URL", "postgresql://igor:choose_a_password@127.0.0.1/igor_wild_0001")
os.environ.setdefault("IGOR_DB_PATH", os.path.expanduser("~/.TheIgors/igor_wild_0001/wild-0001.db"))
sys.path.insert(0, ".")
from wild_igor.igor.tools.registry import registry
import wild_igor.igor.tools  # noqa — triggers all registrations

tools = registry.list()
print(f"Registered tools: {len(tools)}")
for t in sorted(tools, key=lambda x: x.name):
    print(f"  {t.name}")
EOF
```

Check: are there tools registered whose `fn` references a function that no longer exists?
Check: are there tool functions in tool files that are NOT registered?

---

## Step 5 — Inertia check

```bash
cd ~/TheIgors && git log --oneline --name-only $(git log --format=%H --grep='audit' -1 2>/dev/null || git rev-list --max-parents=0 HEAD)..HEAD \
  | grep -E "brainstem/|memory/models\.py|cognition/reasoners/base\.py" | sort -u
```

If HIGH-inertia files appear: verify a corresponding Dxxx decision exists in decisions_log.dsb.
If no decision exists → add to findings report as a gap.

---

## Step 6 — Thread hygiene

```bash
cd ~/TheIgors && source venv/bin/activate && python3 - << 'EOF'
import subprocess, re
# Check for ThreadPoolExecutor usage that might not use daemon threads
result = subprocess.run(
    ["grep", "-rn", "ThreadPoolExecutor", "wild_igor/igor/"],
    capture_output=True, text=True
)
if result.stdout.strip():
    print("ThreadPoolExecutor usages (verify daemon=True or queue pattern):")
    print(result.stdout)
else:
    print("No ThreadPoolExecutor usages found — OK")
EOF
```

---

## Step 7 — Log file sizes

```bash
du -sh ~/.TheIgors/logs/*.log 2>/dev/null | sort -rh | head -10
```

Any file > 10MB → rotate or truncate. Note in findings.

---

## Step 8 — OR burn rate

```bash
cd ~/TheIgors && source venv/bin/activate && python3 - << 'EOF'
import os
os.environ.setdefault("IGOR_DB_PATH", os.path.expanduser("~/.TheIgors/igor_wild_0001/wild-0001.db"))
sys.path.insert(0, ".")
import sys
from wild_igor.igor.tools.budget import _tool_balance_trajectory
print(_tool_balance_trajectory(window_hours=48))
EOF
```

If trend is `burning_fast` (>$20/day) or days_remaining < 3 → add to findings, surface to Akien.

---

## Step 9 — DB schema spot-check

```bash
cd ~/TheIgors && source venv/bin/activate && python3 - << 'EOF'
import os, sqlite3
db = os.path.expanduser("~/.TheIgors/igor_wild_0001/wild-0001.db")
conn = sqlite3.connect(db)
tables = {r[0] for r in conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
required = {"memories", "ring_memory", "twm_observations", "interpretive_edges"}
missing = required - tables
if missing:
    print(f"MISSING TABLES: {missing}")
else:
    print(f"Schema OK — {len(tables)} tables present")
    # Check balance_history in budget DB
    budget_db = os.path.expanduser("~/.TheIgors/igor_wild_0001/claude_budget.db")
    if os.path.exists(budget_db):
        bc = sqlite3.connect(budget_db)
        bt = {r[0] for r in bc.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()}
        print(f"Budget DB tables: {bt}")
    else:
        print("Budget DB not found")
EOF
```

---

## Step 10 — Evaluate findings + fix

Review all findings from Steps 1–9. For each:

- **Small fix** (missing log call, silent except, typo, wrong import): fix now, note what changed
- **Medium/large** (architecture issue, missing test, inertia violation): add to top of next slate as a ticket

After fixes: run `/commit` with message `fix: post-audit small fixes — <date>`.

---

## Findings report format

```
AUDIT — YYYY-MM-DD
Tests:        PASS (30/30) | FAIL (<details>)
Files:        OK | <N> misplaced
Code smells:  <N> silent excepts, <N> bare excepts
Registry:     <N> tools registered, <N> unregistered functions
Inertia:      OK | HIGH files changed without decision: <list>
Threads:      OK | <N> ThreadPoolExecutor usages to verify
Logs:         OK | <file> over 10MB
Burn rate:    $X/day (<trend>) — <N>d remaining
Schema:       OK | MISSING: <tables>

Fixed now: <list of small fixes>
Ticketed:  <list of new tickets>
```

---

## Hard rules

- Never delete files during audit — candidates list only, discuss with Akien
- Never fix medium/large issues inline — ticket them
- Never skip Step 1 (tests) — a failing test blocks everything else
- Run /commit after fixes before /day-close
