# Startup Shim — D232

Cross-platform startup launchers for Igor and Claude Code with restart loops, crash logging, and pause/resume capability.

## Overview

The startup shim provides unified launcher scripts for Linux, macOS, and Windows that handle:

- **Restart loop** — Exit code 42 triggers automatic restart (re-reads .env on each restart)
- **Pause/resume semaphore** — `~/.TheIgors/pause.wait` file gates restarts
- **Crash logging** — Non-zero exits logged to `~/.TheIgors/alerts.txt` (shown pre-dashboard)
- **Config validation** — Ensures ANTHROPIC_API_KEY is set before launching
- **Fresh-install wizard** — Creates .env template on first run
- **Pull and restart** — Git pull happens before each restart

## Files

### Linux/Mac (bash)

- **`~/bin/_igor_common.sh`** — Shared functions (public)
  - `check_requirements()` — verify python3, git, repo dir
  - `require_config()` — ensure ANTHROPIC_API_KEY set
  - `activate_venv()` — source venv/bin/activate
  - `log_crash()` — append to ~/.TheIgors/alerts.txt
  - `restart_loop()` — handle exit 42, pull, pause.wait

- **`~/bin/igor`** — Igor launcher (symlink to ~/TheIgors/igor)
  - Calls venv python to run `wild_igor.main`
  - Restart loop on exit 42
  - Logs crashes to alerts file

- **`~/TheIgors/superclaude`** — Claude Code launcher
  - Fresh-install wizard if ANTHROPIC_API_KEY not set
  - Creates .env template with instructions
  - Launches `claude --dangerously-skip-permissions`

### Windows (PowerShell)

- **`~/bin/_igor_common.ps1`** — Shared functions
  - Same functionality as bash version
  - Handles Windows paths and elevated context

- **`~/bin/igor.ps1`** — Igor launcher for Windows
  - Should be copied/symlinked to `%LOCALAPPDATA%\Microsoft\WindowsApps\igor.ps1`
  - May require elevated privileges for service management

- **`~/bin/superclaude.ps1`** — Claude Code launcher for Windows
  - Should be copied/symlinked to `%LOCALAPPDATA%\Microsoft\WindowsApps\superclaude.ps1`
  - Same first-run wizard as bash version

## Usage

### Linux/Mac

```bash
# Start Igor (uses restart loop)
igor

# Start Igor with specific instance
igor --id wild-0002

# Start Claude Code
superclaude

# Pause Igor (create semaphore)
touch ~/.TheIgors/pause.wait

# Resume Igor (remove semaphore)
rm ~/.TheIgors/pause.wait

# Force savestate on restart
touch ~/.TheIgors/igor_wild_0001/force_savestate.flag
kill -USR1 <igor-pid>  # Signal Igor to exit, triggering restart
```

### Windows

```powershell
# Start Igor
igor

# Start Claude Code
superclaude

# Pause Igor
New-Item -Path "$HOME\.TheIgors\pause.wait" -ItemType File

# Resume Igor
Remove-Item "$HOME\.TheIgors\pause.wait"
```

## Configuration

All configuration lives in `~/.TheIgors/{INSTANCE_ID}/.env`:

```bash
# REQUIRED: Anthropic API key for Claude Code
ANTHROPIC_API_KEY="sk-..."

# OPTIONAL: OpenRouter fallback
OPENROUTER_API_KEY="sk-or-..."

# OPTIONAL: Local inference
KOBOLDCPP_HOST="localhost"
KOBOLDCPP_PORT="5001"

# OPTIONAL: Remote database
IGOR_SWARM_DB_URL="postgresql://..."

# OPTIONAL: Instance ID (default: igor_wild_0001)
IGOR_INSTANCE_ID="igor_wild_0001"
```

## First Run

Both launchers detect missing configuration on first run:

### Igor first run

The Igor launcher has a built-in first-start wizard (`igor.first_start` module) that:
1. Creates the instance directory
2. Asks for instance ID
3. Creates .env template
4. Instructs user to add API keys

### Claude Code first run

The `superclaude` launcher checks for `ANTHROPIC_API_KEY`:
1. If missing, runs setup wizard
2. Creates .env template
3. Shows path and instructions
4. Exits (user edits .env and re-runs)

## Crash Alerts

When Igor or Claude Code exits with non-zero code (other than 42):

1. Exit code is logged to `~/.TheIgors/alerts.txt`
2. Alert includes:
   - Timestamp
   - Exit code
   - Instance ID
   - Hostname and user
   - Last 20 lines of logs (if available)
3. Alert is shown in dashboard (before main view)
4. Alert can be snoozed (deferred implementation)

## Restart Behavior

Exit code 42 is special: it triggers a restart sequence:

1. Check `~/.TheIgors/pause.wait` — if exists, wait until removed
2. `git pull --ff-only` in repo root
3. Re-read `.env`
4. Restart the process
5. Loop until non-42 exit

This allows:
- Code updates via git pull
- .env changes to take effect
- Clean signal for "restart me" from Igor itself

## Installation

### Linux/Mac (automatic)

The scripts are already installed at:
- `~/bin/igor` (symlink)
- `~/bin/superclaude`
- `~/bin/_igor_common.sh`

Just ensure `~/bin` is in your PATH:
```bash
echo $PATH | grep -q "${HOME}/bin" || echo 'export PATH="${HOME}/bin:$PATH"' >> ~/.bashrc
```

### Windows (manual)

1. Copy the PowerShell scripts to your Windows App directory:
   ```powershell
   copy "$HOME\bin\igor.ps1" "$env:LOCALAPPDATA\Microsoft\WindowsApps\igor.ps1"
   copy "$HOME\bin\superclaude.ps1" "$env:LOCALAPPDATA\Microsoft\WindowsApps\superclaude.ps1"
   copy "$HOME\bin\_igor_common.ps1" "$env:LOCALAPPDATA\Microsoft\WindowsApps\_igor_common.ps1"
   ```

2. Ensure the directory is in your PATH:
   ```powershell
   $env:PATH -split ';' | ? { $_ -eq "$env:LOCALAPPDATA\Microsoft\WindowsApps" }
   ```

3. Make scripts executable (may require admin):
   ```powershell
   Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
   ```

## Architecture

### Common Functions (_igor_common.sh / _igor_common.ps1)

Both versions provide:
- `check_requirements()` — validates dependencies
- `require_config()` — ensures API key set
- `activate_venv()` — sources virtual environment
- `log_crash()` — appends to alerts file
- `restart_loop()` — main restart logic
- `is_paused()` / `wait_for_resume()` — semaphore handling
- `pull_and_restart()` — git operations

### Igor Launcher

1. Source common functions
2. Check requirements
3. Require config (show error if missing)
4. Activate venv
5. Loop:
   - Check pause.wait
   - Run `python3 -m wild_igor.main`
   - If exit 42: git pull + loop
   - Else: log crash (if non-zero) + exit

### superclaude Launcher

1. Source common functions (if available)
2. Check if ANTHROPIC_API_KEY set
3. If not:
   - Show setup wizard
   - Create .env template
   - Show instructions
   - Exit 1
4. Otherwise: exec claude

## Design Notes

- Restart loop is in the shell launcher, not Python, to handle ungraceful crashes
- pause.wait is a file (not a database lock) for simplicity and visibility
- Alerts are appended to a single file (not rotated) — user should rotate manually
- Exit code 42 is chosen to be unlikely to occur naturally (unlike 1 or 2)
- Commands are sourced from shared _igor_common.sh to avoid duplication
- Windows uses PowerShell (not batch) for better portability and readability

## Related Decisions

- **D232**: Startup shim design (this file)
- **D088**: Anthropic→OR failover (superclaude origin)
- **D020**: Portable identity (SOUL.md/IDENTITY.md)
