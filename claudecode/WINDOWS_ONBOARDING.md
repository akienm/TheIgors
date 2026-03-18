# Igor Windows Bootstrap — Autonomous Onboarding Prompt

**Read this file at the start of a new Claude Code session on a fresh Windows machine.**
You are Claude Code running in an elevated PowerShell with `--dangerously-skip-permissions`.
Complete the entire bootstrap autonomously. Do not wait for Akien. Do not ask for confirmation.
If a step fails, diagnose and fix it before moving on.

---

## Credentials

`ANTHROPIC_API_KEY` and `IGOR_DB_URL` are set as Windows system environment variables on this machine — do not write them to any file. Verify they are present before proceeding:

```powershell
echo $env:ANTHROPIC_API_KEY
echo $env:IGOR_DB_URL
```

Both must be non-empty. If either is missing, stop and ask Akien.

---

## Confirmed working environment (akienwindows, 2026-03-17)

- Python 3.12 required — 3.11 is installed by default on Akien's machines but will NOT work (some packages require 3.12)
- Repo is synced via OneDrive — do NOT git clone; it's already at `C:\Users\akien\OneDrive\AkiensWorkshop\dev\src\TheIgors`
- `requirements.txt` is at the **repo root**, not in `wild_igor/`
- Venv lives at `C:\Users\akien\.TheIgors\venv` — kept outside OneDrive to avoid syncing gigabytes of packages
- Runtime root is `C:\Users\akien\.TheIgors` (not `%APPDATA%\TheIgors`)
- Instance ID convention: `igor_wild_windows_XXXX` with **four** zeros (e.g. `igor_wild_windows_0001`)
- akiendelllinux IP: `10.0.0.229` — Postgres port 5432 must be open in firewall AND `listen_addresses = '*'` in postgresql.conf AND subnet allowed in pg_hba.conf
- `start_igor_windows.ps1` in repo root — use this to launch Igor; it loads `.env` automatically
- `sign_igor_script.bat` in repo root — run this (elevated) after any edit to `start_igor_windows.ps1`

---

## Goal

Bootstrap Igor on this Windows machine so that:
1. Igor starts and connects to the shared Postgres DB on akiendelllinux
2. Igor responds correctly to a test message via the CC bridge
3. The instance is registered in the environment tree in the DB

This machine is an attention center — a cognitive node that shares the same memory and habits as all other Igor instances. It does NOT have its own isolated DB.

---

## Step 1 — Verify prerequisites

Check Python 3.12+ is installed:
```powershell
py -3.12 --version
```
If missing or below 3.12:
```powershell
winget install Python.Python.3.12
# Then close and reopen elevated PowerShell to refresh PATH
```

Check git is installed:
```powershell
git --version
```
If missing:
```powershell
winget install Git.Git
```

---

## Step 2 — Confirm repo is present (OneDrive sync)

The repo is synced via OneDrive — do NOT clone it again.
```powershell
ls "$env:USERPROFILE\OneDrive\AkiensWorkshop\dev\src\TheIgors"
```
If missing, OneDrive hasn't synced yet — wait, or sign in to OneDrive first. Do not clone.

If OneDrive is not available on this machine (rare), then clone:
```powershell
cd $env:USERPROFILE
git clone https://github.com/akienm/TheIgors.git "OneDrive\AkiensWorkshop\dev\src\TheIgors"
```

---

## Step 3 — Create the virtual environment

Venv goes in `~\.TheIgors\venv` — NOT in the repo (keeps packages out of OneDrive sync).
```powershell
$repoRoot = "$env:USERPROFILE\OneDrive\AkiensWorkshop\dev\src\TheIgors"
py -3.12 -m venv "$env:USERPROFILE\.TheIgors\venv"
& "$env:USERPROFILE\.TheIgors\venv\Scripts\python.exe" -m pip install --upgrade pip
& "$env:USERPROFILE\.TheIgors\venv\Scripts\python.exe" -m pip install -r "$repoRoot\requirements.txt"
```

Note: `requirements.txt` is at the repo root (not `wild_igor/`).

---

## Step 4 — Create the instance directory and .env

Choose a unique instance ID following the `igor_wild_windows_XXXX` convention (four zeros).
`ANTHROPIC_API_KEY` and `IGOR_DB_URL` are inherited from system environment variables — do not put them in `.env`.

```powershell
$instanceId = "igor_wild_windows_0001"   # increment for each new machine
$instanceDir = "$env:USERPROFILE\.TheIgors\$instanceId"
New-Item -ItemType Directory -Force -Path $instanceDir

$envContent = @"
IGOR_RUNTIME_ROOT=$env:USERPROFILE\.TheIgors
IGOR_INSTANCE_ID=$instanceId
IGOR_WEB_PORT=8080
IGOR_SELF_EDIT_ENABLED=false
IGOR_TIER5_ENABLED=false
IGOR_ARBITER_ENABLED=false
"@

$envContent | Out-File -FilePath "$instanceDir\.env" -Encoding UTF8
```

---

## Step 5 — Verify Postgres connectivity

Postgres on akiendelllinux must be reachable before proceeding. Common issues on first run:
- `listen_addresses` in `postgresql.conf` must be `'*'` (not `'localhost'`)
- `pg_hba.conf` must allow the subnet: `host igor igor 10.0.0.0/24 md5`
- Linux firewall must allow port 5432: `sudo ufw allow 5432` or equivalent iptables rule
- Restart Postgres after config changes: `sudo systemctl restart postgresql`

Test from Windows:
```powershell
# Quick TCP test first
Test-NetConnection -ComputerName 10.0.0.229 -Port 5432

# Then Python test (reads IGOR_DB_URL from system env)
& "$env:USERPROFILE\.TheIgors\venv\Scripts\python.exe" -c "
import psycopg2, os
url = os.environ['IGOR_DB_URL']
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute('SELECT COUNT(*) FROM memories')
    count = cur.fetchone()[0]
    print(f'DB OK — {count} memories')
    conn.close()
except Exception as e:
    print(f'DB FAILED: {e}')
"
```

Do not proceed until DB connectivity is confirmed and memory count is non-zero.

---

## Step 6 — Start Igor

Use the launch script in the repo root — it loads `.env` automatically:
```powershell
& "$env:USERPROFILE\OneDrive\AkiensWorkshop\dev\src\TheIgors\start_igor_windows.ps1"
```

Igor should print startup logs showing DB connection, habit cache load, and web server starting on port 8080.

---

## Step 7 — Validate via CC bridge

In a second elevated PowerShell (keep Igor running in the first):
```powershell
$body = '{"content": "Hello Igor, this is the Windows bootstrap validation. Confirm you are running and connected to the shared database."}'
Invoke-RestMethod -Uri "http://localhost:8080/api/cc_send" -Method POST -ContentType "application/json" -Body $body
```

Expected: `{"status":"ok"}`

Then check Igor's response in the first window. It should acknowledge the message and reference memory content from the shared DB (not zero — confirming shared Postgres, not an empty local DB).

---

## Step 8 — Register this machine in the environment tree

Replace `igor_wild_windows_0001` with the actual instance ID for this machine:
```powershell
$instanceId = "igor_wild_windows_0001"
$body = "{`"content`": `"Please register this Windows machine in the environment tree. Instance ID: $instanceId. Platform: Windows. Role: attention_center. Store as a FACTUAL memory node under the environment subtree.`"}"
Invoke-RestMethod -Uri "http://localhost:8080/api/cc_send" -Method POST -ContentType "application/json" -Body $body
```

---

## Step 9 — Set Igor to start on login

The repo contains `sign_igor_script.bat` — run it (elevated, double-click) to create a self-signed cert and sign `start_igor_windows.ps1`. This only needs to be done once per machine (and again after any edit to the script).

Then register the scheduled task:
```powershell
$scriptPath = "$env:USERPROFILE\OneDrive\AkiensWorkshop\dev\src\TheIgors\start_igor_windows.ps1"
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Normal -ExecutionPolicy Bypass -File `"$scriptPath`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "IgorStartup" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest -Force
```

---

## What you are NOT doing

- Do not create a local SQLite DB — this instance uses shared Postgres only
- Do not copy or migrate any data — the DB already has everything
- Do not git clone if OneDrive is already synced
- Do not put the venv inside the repo or OneDrive path
- Do not write credentials to `.env` — they live in system environment variables
- Do not modify brainstem/ or memory/models.py
- Do not commit credentials to git

---

## If anything goes wrong

Check logs at `$env:USERPROFILE\.TheIgors\logs\` once Igor has started at least once.
Triage order: `errors.log` → `startup.log` → `pipeline_trace.YYYYMMDD.log`

Common failure modes:
1. **Postgres unreachable (TCP refused)** — firewall on akiendelllinux blocking 5432, or `listen_addresses = 'localhost'` in postgresql.conf
2. **Postgres auth failure** — wrong password or missing pg_hba.conf entry for this subnet
3. **Module not found** — wrong working directory, or ran with system Python instead of venv
4. **Port 8080 in use** — another process has it; change `IGOR_WEB_PORT` in .env
5. **Missing dependency** — `pip install <package>` while venv is active, then add to requirements.txt
6. **Script signing prompt** — run `sign_igor_script.bat` elevated to sign `start_igor_windows.ps1`
