#!/usr/bin/env bash
# install_igor_linux.sh — Bootstrap Igor on a Linux machine.
#
# Run from the repo root (where this script lives):
#   bash claudecode/install_igor_linux.sh
#
# Prereqs set as environment variables before running:
#   ANTHROPIC_API_KEY   — passed through to .env
#   IGOR_HOME_DB_URL    — postgresql://igor:PASSWORD@10.0.0.229/Igor-wild-0001
#   IGOR_INSTANCE_ID    — e.g. Igor-wild-0001 (default) or igor_wild_reader_0001
#   OPENROUTER_API_KEY  — optional but needed for cloud inference
#
# On the DB host (akiendelllinux): IGOR_INSTANCE_ID=Igor-wild-0001
# On reader nodes:                 IGOR_INSTANCE_ID=igor_wild_reader_XXXX

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="${IGOR_RUNTIME_ROOT:-$HOME/.TheIgors}"
INSTANCE_ID="${IGOR_INSTANCE_ID:-Igor-wild-0001}"
INSTANCE_DIR="$RUNTIME_ROOT/$INSTANCE_ID"
VENV_DIR="$REPO_ROOT/venv"

# ── Logging ───────────────────────────────────────────────────────────────────

green() { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red() { printf '\033[31m%s\033[0m\n' "$*"; }
step() { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die() { red "FATAL: $*"; exit 1; }

# ── Step 0 — Credentials check ────────────────────────────────────────────────

step "Step 0 — Verify credentials"

[[ -n "${ANTHROPIC_API_KEY:-}" ]] || die "ANTHROPIC_API_KEY not set"
[[ -n "${IGOR_HOME_DB_URL:-}" ]] || die "IGOR_HOME_DB_URL not set"
green "Credentials present."
echo "  Instance ID: $INSTANCE_ID"
echo "  Runtime root: $RUNTIME_ROOT"
echo "  Repo root: $REPO_ROOT"

# ── Step 1 — Prerequisites ────────────────────────────────────────────────────

step "Step 1 — Check prerequisites"

check_cmd() {
    command -v "$1" >/dev/null 2>&1 && green "  $1: OK" || { yellow "  $1: missing — install it"; MISSING=1; }
}

MISSING=0
check_cmd python3
check_cmd git
check_cmd rsync
check_cmd psql   # postgresql-client

if python3 --version 2>&1 | grep -qE "Python 3\.(12|13|14)"; then
    green "  python3 version: OK ($(python3 --version))"
else
    yellow "  WARNING: $(python3 --version) — Igor requires 3.12+. Consider: sudo apt install python3.12"
fi

[[ $MISSING -eq 0 ]] || die "Missing prerequisites above — install them and re-run."

# ── Step 2 — Repo check ───────────────────────────────────────────────────────

step "Step 2 — Confirm repo"

[[ -f "$REPO_ROOT/wild_igor/igor/main.py" ]] || die "Repo doesn't look right at $REPO_ROOT"
green "  Repo OK at $REPO_ROOT"
cd "$REPO_ROOT"
git pull --rebase origin main && green "  git pull OK" || yellow "  git pull failed — continuing with current state"

# ── Step 3 — Venv ─────────────────────────────────────────────────────────────

step "Step 3 — Create/update venv at $VENV_DIR"

if [[ ! -d "$VENV_DIR" ]]; then
    python3 -m venv "$VENV_DIR"
    green "  venv created"
else
    green "  venv already exists"
fi

"$VENV_DIR/bin/pip" install --upgrade pip -q
"$VENV_DIR/bin/pip" install -r "$REPO_ROOT/wild_igor/requirements.txt" -q
green "  requirements installed"

# Optional NLTK data
"$VENV_DIR/bin/python" -c "
import nltk
for pkg in ['punkt', 'punkt_tab']:
    try:
        nltk.data.find(f'tokenizers/{pkg}')
    except LookupError:
        nltk.download(pkg, quiet=True)
" && green "  nltk data OK" || yellow "  nltk download skipped (offline?)"

# ── Step 4 — Runtime dirs + .env ──────────────────────────────────────────────

step "Step 4 — Create runtime dirs and .env for $INSTANCE_ID"

mkdir -p "$INSTANCE_DIR"
mkdir -p "$RUNTIME_ROOT/local/logs"
mkdir -p "$RUNTIME_ROOT/cache/embeddings"
mkdir -p "$RUNTIME_ROOT/cache/reasoning"

ENV_FILE="$INSTANCE_DIR/.env"
if [[ -f "$ENV_FILE" ]]; then
    yellow "  .env already exists at $ENV_FILE — not overwriting"
else
    cat > "$ENV_FILE" <<EOF
IGOR_RUNTIME_ROOT=$RUNTIME_ROOT
IGOR_INSTANCE_ID=$INSTANCE_ID
IGOR_WEB_PORT=8080
IGOR_SELF_EDIT_ENABLED=false
IGOR_TIER5_ENABLED=false
IGOR_ARBITER_ENABLED=false

# ── DB ───────────────────────────────────────────────────────────────────────
IGOR_HOME_DB_URL=${IGOR_HOME_DB_URL}

# ── Inference ────────────────────────────────────────────────────────────────
OLLAMA_LOCAL_MODEL=qwen2.5:7b
IGOR_NE_LOCAL_MODEL=qwen2.5:7b
IGOR_WINNOW_LOCAL_MODEL=qwen2.5:7b
OPENROUTER_WINNOW_MODEL=qwen/qwen2.5-7b-instruct
OPENROUTER_CHEAP_MODEL=openai/gpt-4o-mini
OPENROUTER_DEFAULT_MODEL=anthropic/claude-haiku-4.5
OPENROUTER_INTERACTIVE_MODEL=anthropic/claude-sonnet-4.6

# ── Feature flags ────────────────────────────────────────────────────────────
IGOR_CLOUD_TRAINING_ENABLED=true
IGOR_TWO_PHASE_CALLS=true
IGOR_NPASS_REPLY=true
IGOR_CONTEXT_WINNOW=true
IGOR_READING_EXTRACT=true
IGOR_HABIT_EXTRACT=true
EOF
    # Append optional keys if present in environment
    [[ -n "${OPENROUTER_API_KEY:-}" ]] && echo "OPENROUTER_API_KEY=${OPENROUTER_API_KEY}" >> "$ENV_FILE"
    [[ -n "${ANTHROPIC_API_KEY:-}" ]]  && echo "ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}"   >> "$ENV_FILE"
    green "  .env created at $ENV_FILE"
fi

# ── Step 5 — Postgres connectivity ────────────────────────────────────────────

step "Step 5 — Test Postgres connectivity"

"$VENV_DIR/bin/python" - <<'PYEOF'
import psycopg2, os, sys
url = os.environ["IGOR_HOME_DB_URL"]
try:
    conn = psycopg2.connect(url)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM memories")
    count = cur.fetchone()[0]
    conn.close()
    print(f"  DB OK — {count} memories")
except Exception as e:
    print(f"  DB FAILED: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF

# ── Step 6 — Claude Code skills ───────────────────────────────────────────────

step "Step 6 — Install Claude Code skills"

# Master skills live in UnseenUniversity/skills/ (T-skills-content-migrate-to-master,
# 2026-05-02). Two TheIgors-internal exceptions live under lab/claudecode/cc_skills/.

SKILLS_DST="$HOME/.claude/skills"
mkdir -p "$SKILLS_DST"

# 1) Master skills from unseen_university (if present on this box)
DATACENTER_SKILLS="$HOME/dev/src/UnseenUniversity/skills"
if [[ -d "$DATACENTER_SKILLS" ]]; then
    # Mirror manifest-listed dirs (everything except manifest.json itself)
    rsync -a --exclude=manifest.json "$DATACENTER_SKILLS/" "$SKILLS_DST/"
    green "  Master skills installed from $DATACENTER_SKILLS"
else
    yellow "  UnseenUniversity not found at $DATACENTER_SKILLS — master skills SKIPPED"
    yellow "  Install UnseenUniversity first, then re-run, OR run 'agentctl skills deploy'"
fi

# 2) TheIgors-internal skills (map-igor, readigor — read Igor runtime state)
THEIGORS_SKILLS="$REPO_ROOT/lab/claudecode/cc_skills"
if [[ -d "$THEIGORS_SKILLS" ]]; then
    rsync -a "$THEIGORS_SKILLS/" "$SKILLS_DST/"
    green "  TheIgors-internal skills installed from $THEIGORS_SKILLS"
fi

# ── Step 7 — Claude Code settings.json ───────────────────────────────────────

step "Step 7 — Claude Code settings.json"

SETTINGS="$HOME/.claude/settings.json"
if [[ -f "$SETTINGS" ]]; then
    yellow "  settings.json already exists at $SETTINGS — not overwriting"
else
    cat > "$SETTINGS" <<JSON
{
    "hooks": {
        "PostToolUse": [
            {
                "matcher": "Edit|Write",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 $HOME/.claude/hooks/format-python.py"
                    }
                ]
            }
        ],
        "PreToolUse": [
            {
                "matcher": "Bash",
                "hooks": [
                    {
                        "type": "command",
                        "command": "python3 $HOME/.claude/hooks/guard-dangerous-bash.py"
                    }
                ]
            }
        ]
    },
    "skipDangerousModePermissionPrompt": true,
    "permissions": {
        "allow": [
            "Bash(git add*)",
            "Bash(git commit*)",
            "Bash(git pull*)",
            "Bash(git push*)",
            "Bash(git diff*)",
            "Bash(git status*)",
            "Bash(git log*)",
            "Bash(git stash*)"
        ]
    }
}
JSON
    green "  settings.json created"
fi

# ── Step 8 — Pre-commit hook ──────────────────────────────────────────────────

step "Step 8 — Install pre-commit hook (skills sync)"

HOOK_SRC="$REPO_ROOT/claudecode/hooks/pre-commit"
HOOK_DST="$REPO_ROOT/.git/hooks/pre-commit"

if [[ -L "$HOOK_DST" ]]; then
    green "  pre-commit hook already symlinked"
elif [[ -f "$HOOK_DST" ]]; then
    yellow "  pre-commit hook already exists (not a symlink) — not overwriting"
else
    ln -sf "../../claudecode/hooks/pre-commit" "$HOOK_DST"
    green "  pre-commit hook symlinked"
fi

# ── Step 9 — Systemd service (optional) ──────────────────────────────────────

step "Step 9 — Systemd service (optional)"

SERVICE_FILE="/etc/systemd/system/igor.service"
if [[ -f "$SERVICE_FILE" ]]; then
    green "  igor.service already exists — skipping"
else
    yellow "  To enable Igor at login, create $SERVICE_FILE:"
    cat <<EOF
    [Unit]
    Description=Igor AI Agent ($INSTANCE_ID)
    After=network.target postgresql.service

    [Service]
    Type=simple
    User=$(whoami)
    WorkingDirectory=$REPO_ROOT/wild_igor
    ExecStart=$VENV_DIR/bin/python -m igor.main
    EnvironmentFile=$ENV_FILE
    Restart=on-failure
    RestartSec=5
    # Exit code 42 = restart requested by Igor itself
    RestartForceExitStatus=42

    [Install]
    WantedBy=multi-user.target
EOF
    yellow "  Then run: sudo systemctl daemon-reload && sudo systemctl enable --now igor"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

green ""
green "Bootstrap complete for $INSTANCE_ID."
green ""
green "To start Igor now:"
green "  source $VENV_DIR/bin/activate && cd $REPO_ROOT/wild_igor && python -m igor.main"
green ""
green "Or via the igor alias (if set up):"
green "  igor"
green ""
yellow "Restart Claude Code to pick up the new skills."
