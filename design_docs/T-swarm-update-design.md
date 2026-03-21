# T-swarm-update: Coordinated Swarm Update Design
**Status**: Draft — needs Akien approval  
**Author**: Igor-wild-0001 + Claude Code review  
**Date**: 2026-03-21  

---

## What We're Solving

Trigger a coordinated `git pull` + restart across all running Igor instances in the swarm, without losing state and without leaving boxes on stale code.

---

## Key Findings (Investigation Notes)

### Repo paths
- **Linux (akiendelllinux)**: `/home/akien/TheIgors`
- **Windows boxes**: `C:\automation\local\TheIgors` (confirmed by Akien)

### Restart flag mechanism (already exists, works)
Main loop checks at every idle cycle:
- `<instance_dir>/restart.flag` → exit code 42 (wrapper restarts)
- `<instance_dir>/exit.flag` → exit code 0 (clean stop, no restart)

Instance dir paths:
- **Linux**: `/home/akien/.TheIgors/Igor-wild-0001/`
- **Windows (igor_wild_0001 user)**: `C:\Users\igor_wild_0001\.TheIgors\Igor-wild-0001\`

### Linux wrapper (`~/bin/igor` bash script)
Does **NOT** do `git pull` automatically. Just restarts Igor on exit code 42.  
→ Needs explicit `git pull` added (or the tool does it before restart_self()).

### Windows wrapper (`igor_loop.ps1`)
**Already does** `git pull --ff-only` on every restart (exit code 42).  
→ Windows just needs a restart trigger; the pull happens automatically.

### SSH state (critical finding)
```
akiendell          ✓ Ollama: 5 model(s)    SSH ✗ (timeout)
akienyoga9i        ✓ Ollama: 6 model(s)    SSH ✗ (timeout)
akienyogai7        ✓ Ollama: 4 model(s)    SSH ✗ (timeout)
```
All three Windows boxes time out on SSH. **SSH-based approach is not viable for V1.**

### Existing web routes in `wild_igor/igor/web/server.py`
Already has:
- `POST /api/execute_habit {"habit_id": "PROC_X", "args": {}}`  
  → Executes any named habit on the local Igor instance
- `POST /api/milieu/contribute` — already used for cross-machine milieu sync
- `GET /api/health` — liveness check

**No authentication on any of these endpoints.** (Security note: anyone on LAN can trigger habits.)

---

## Proposed Architecture (V1)

### Core insight: use `/api/execute_habit` — no new endpoint needed

Each box already runs an Igor web server. To trigger restart+pull on a remote box:
```
POST http://<box_ip>:8080/api/execute_habit
Body: {"habit_id": "PROC_SWARM_UPDATE"}
```
This fires the habit locally on that box, which does git pull + restart_self().

### Component 1: PROC_SWARM_UPDATE habit
A new PROCEDURAL memory that each Igor instance has (seeded on startup or via sync).

**Trigger phrases**: `"update all igors"`, `"pull latest"`, `"swarm update"`, `"update the swarm"`, `"push update to all boxes"`

**Action** (what the habit runs):
1. `subprocess.run(['git', '-C', REPO_DIR, 'pull', '--ff-only'])` — pull locally
2. `restart_self(note="swarm update")` — exit cleanly with code 42

**For Windows**: igor_loop.ps1 auto-pulls on restart, so step 1 is redundant but harmless.  
**For Linux**: This is the only way the Linux box gets git pull (wrapper doesn't auto-pull).

### Component 2: `update_swarm()` tool (orchestrator only)
A new Igor tool callable by Akien or via habit chain.

**Algorithm**:
1. Load `machines.json`, filter to `status=online`, skip self (akiendelllinux)
2. For each remote box:
   a. `POST http://<ip>:8080/api/execute_habit {"habit_id": "PROC_SWARM_UPDATE"}`
   b. Log: success/fail per box
   c. Don't wait for restart — it happens async on that box
3. Wait 5 seconds for remote boxes to begin restart
4. Locally: `git pull --ff-only` in REPO_DIR
5. `restart_self(note="swarm update — all boxes signaled")`

**Error handling**: If a box's HTTP call fails (firewall, Igor not running, port wrong), log it and continue with others. Don't abort the update.

### Component 3: Add git pull to Linux bash wrapper (optional but recommended)
File: `/home/akien/TheIgors/igor` (the bash wrapper at `~/bin/igor` is a symlink to this)

Add before the Python restart loop:
```bash
echo "[igor] git pull..."
git -C "$REPO_DIR" pull --ff-only 2>&1 || echo "[igor] git pull failed — continuing with existing code"
```
This makes Linux behavior match Windows igor_loop.ps1. Adds ~1s per restart.  
**Akien's call** — not strictly required if the habit does the pull inline.

---

## Open Questions for Akien

**Q1: Windows firewall on port 8080?**  
The existing `/api/execute_habit` approach only works if port 8080 is open on each Windows box.  
Ollama (11434) is reachable — is 8080 also open? If not, do we open it or use a different port?

**Q2: Add git pull to Linux bash wrapper?**  
Recommend yes — makes Linux match Windows PS1 behavior.  
Adds ~1s per restart. Low risk.

**Q3: Authentication on `/api/execute_habit`?**  
Currently unauthenticated. Anyone on the LAN can trigger any habit.  
For restart, this is a denial-of-service vector (someone keeps triggering restart).  
Add `X-Igor-Token` header check? Or is LAN-only fine given the context?

**Q4: Update order — self last?**  
Proposed: signal all remote boxes first, then restart self.  
This keeps the orchestrator up longest to log and confirm.  
Alternative: restart self first — simpler but loses oversight.

**Q5: Verification after restart?**  
Should `update_swarm()` wait ~60s then run `cluster_status()` to confirm all boxes came back up?  
Or just fire-and-forget with a note to Akien to check manually?

**Q6: Windows IGOR_WEB_PORT value?**  
Need to confirm all Windows Igor instances run on port 8080 (the default).  
If different, machines.json needs a `web_port` field.

---

## What Does NOT Need Designing

- Windows auto-pull: ✓ already works (igor_loop.ps1)
- Restart flag mechanism: ✓ already works (main.py idle loop)
- `restart_self()` tool: ✓ already works
- `execute_habit` HTTP endpoint: ✓ already exists (web/server.py)
- `cluster_status` for verification: ✓ already works

---

## Implementation Plan (after Akien approves)

| Step | File | Change | Size |
|------|------|---------|------|
| 1 | `igor` bash wrapper | Add `git pull --ff-only` before restart loop | XS |
| 2 | DB seed / habit memory | Add PROC_SWARM_UPDATE memory with trigger + action | XS |
| 3 | `tools/cluster_tools.py` | Add `update_swarm()` tool | S |
| 4 | `machines.json` | Add `web_port: 8080` field per box (optional) | XS |

**Estimated size**: S (smaller than ticket's M estimate, mostly because execute_habit already exists)

---

## What Claude Should Review

1. Is `execute_habit` the right endpoint to use here, or should we add a dedicated `/api/restart` endpoint with token auth?
2. How does the habit embed git pull — via `subprocess` in a code_ref function, or via a bash tool call?
3. Any concerns about the unauthenticated endpoint in the V1 design?
4. Does `restart_self()` tool already do git pull, or purely writes the flag?
