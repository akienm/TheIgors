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
python --version
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

## Step 2 — Clone the repo

```powershell
cd $env:USERPROFILE
git clone https://github.com/akienm/TheIgors.git TheIgors
cd TheIgors
```

If the repo already exists, pull latest:
```powershell
cd $env:USERPROFILE\TheIgors
git pull
```

---

## Step 3 — Create the virtual environment

```powershell
cd $env:USERPROFILE\TheIgors
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r wild_igor/requirements.txt
```

If requirements.txt doesn't exist at that path, find it:
```powershell
Get-ChildItem -Recurse -Name "requirements.txt"
```
Use whichever path contains the main Igor dependencies (uvicorn, anthropic, psycopg2, etc.).

---

## Step 4 — Create the instance directory and .env

```powershell
$instanceDir = "$env:APPDATA\TheIgors\igor_wild_windows_001"
New-Item -ItemType Directory -Force -Path $instanceDir

$envContent = @"
IGOR_RUNTIME_ROOT=$env:APPDATA\TheIgors
IGOR_INSTANCE_ID=igor_wild_windows_001
IGOR_WEB_PORT=8080
IGOR_SELF_EDIT_ENABLED=false
IGOR_TIER5_ENABLED=false
IGOR_ARBITER_ENABLED=false
"@

$envContent | Out-File -FilePath "$instanceDir\.env" -Encoding UTF8
```

Substitute the real values from the **Your .env** section above before writing.

---

## Step 5 — Verify Postgres connectivity

```powershell
python -c "
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

If this fails:
- Check akiendelllinux is reachable: `ping` the host from `$env:IGOR_DB_URL`
- Check Postgres is listening on 5432: the service layer should be running on akiendelllinux
- Check firewall on akiendelllinux allows port 5432 from this machine's IP
- Check `pg_hba.conf` on akiendelllinux allows remote connections from this subnet

Do not proceed until DB connectivity is confirmed.

---

## Step 6 — Start Igor

```powershell
$env:IGOR_INSTANCE_ID = "igor_wild_windows_001"
$env:IGOR_RUNTIME_ROOT = "$env:APPDATA\TheIgors"
cd $env:USERPROFILE\TheIgors
.\venv\Scripts\Activate.ps1
python -m wild_igor.igor.main
```

If the module path fails, try:
```powershell
cd $env:USERPROFILE\TheIgors\wild_igor\igor
python main.py
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

Send via CC bridge:
```powershell
$body = '{"content": "Please register this Windows machine in the environment tree. Instance ID: igor_wild_windows_001. Platform: Windows. Role: attention_center. Store as a FACTUAL memory node under the environment subtree."}'
Invoke-RestMethod -Uri "http://localhost:8080/api/cc_send" -Method POST -ContentType "application/json" -Body $body
```

---

## Step 9 — Set Igor to start on login (optional)

```powershell
$action = New-ScheduledTaskAction -Execute "powershell.exe" `
    -Argument "-WindowStyle Hidden -Command `"cd $env:USERPROFILE\TheIgors; .\venv\Scripts\Activate.ps1; python -m wild_igor.igor.main`""
$trigger = New-ScheduledTaskTrigger -AtLogOn
$settings = New-ScheduledTaskSettingsSet -ExecutionTimeLimit (New-TimeSpan -Hours 0) -RestartCount 3 -RestartInterval (New-TimeSpan -Minutes 1)
Register-ScheduledTask -TaskName "IgorStartup" -Action $action -Trigger $trigger -Settings $settings -RunLevel Highest
```

---

## What you are NOT doing

- Do not copy or migrate any data — the DB already has everything
- Do not modify brainstem/ or memory/models.py
- Do not commit credentials to git

---

## If anything goes wrong

Check logs at `$env:APPDATA\TheIgors\logs\` once Igor has started at least once.
Triage order: `errors.log` → `startup.log` → `pipeline_trace.YYYYMMDD.log`

Common failure modes:
1. **Postgres unreachable** — firewall, pg_hba.conf, or akiendelllinux is down
2. **Module not found** — venv not activated, or wrong working directory
3. **Port 8080 in use** — another process has it; change `IGOR_WEB_PORT` in .env
4. **Missing dependency** — `pip install <package>` while venv is active, then add to requirements.txt
