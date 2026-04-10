#!/usr/bin/env bash
# utility_closet.sh — TheIgors infrastructure bootstrap + launch (D307)
#
# Single entry point for bringing up Igor's infrastructure:
#   1. Self-install system dependencies (PostgreSQL client, tmux, OpenSSH, curl)
#   2. Run install_igor_linux.sh if .env is missing (first-time setup)
#   3. Validate .env exists and key env vars are present
#   4. Test DB connectivity + bootstrap schema
#   5. Launch tmux session "igor" with Igor running inside
#
# Others can attach to the session with:  tmux attach -t igor
#
# Usage:
#   bash lab/claudecode/utility_closet.sh              — full setup + launch
#   bash lab/claudecode/utility_closet.sh --dry-run    — check only, no changes
#   bash lab/claudecode/utility_closet.sh --no-launch  — setup only, skip tmux

set -uo pipefail

# ── Flags ─────────────────────────────────────────────────────────────────────

DRY_RUN=0
NO_LAUNCH=0
for arg in "${@:-}"; do
    case "$arg" in
        --dry-run)    DRY_RUN=1 ;;
        --no-launch)  NO_LAUNCH=1 ;;
    esac
done

# ── Paths ─────────────────────────────────────────────────────────────────────

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="${IGOR_RUNTIME_ROOT:-$HOME/.TheIgors}"
INSTANCE_ID="${IGOR_INSTANCE_ID:-Igor-wild-0001}"
INSTANCE_DIR="$RUNTIME_ROOT/$INSTANCE_ID"

# Auto-detect .env: the runtime dir may use a different case than INSTANCE_ID
# (e.g. Igor-wild-0001 vs Igor-wild-0001 — see CLAUDE.md instance dir note)
ENV_FILE="$INSTANCE_DIR/.env"
if [[ ! -f "$ENV_FILE" ]]; then
    # Scan for any .env under RUNTIME_ROOT
    _found=$(find "$RUNTIME_ROOT" -maxdepth 2 -name ".env" 2>/dev/null | sort | head -1)
    if [[ -n "$_found" ]]; then
        ENV_FILE="$_found"
        INSTANCE_DIR="$(dirname "$_found")"
    fi
fi
VENV_DIR="$REPO_ROOT/venv"
VENV_PY="$VENV_DIR/bin/python"
TMUX_SESSION="igor"

# ── Logging ───────────────────────────────────────────────────────────────────

green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
step()   { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die()    { red "FATAL: $*"; exit 1; }
dryrun() { yellow "  [dry-run] would: $*"; }

# ── Step 1 — Self-install system dependencies ─────────────────────────────────

step "Step 1 — System dependencies"

_check_install() {
    local cmd="$1"
    local pkg="${2:-$1}"
    if command -v "$cmd" >/dev/null 2>&1; then
        green "  $cmd: OK"
    else
        yellow "  $cmd: missing"
        if [[ $DRY_RUN -eq 1 ]]; then
            dryrun "install $pkg"
        elif command -v apt-get >/dev/null 2>&1; then
            echo "  Installing $pkg via apt..."
            sudo apt-get install -y "$pkg" || yellow "  apt install $pkg failed — install manually"
        elif command -v brew >/dev/null 2>&1; then
            echo "  Installing $pkg via brew..."
            brew install "$pkg" || yellow "  brew install $pkg failed — install manually"
        elif command -v pacman >/dev/null 2>&1; then
            echo "  Installing $pkg via pacman..."
            sudo pacman -S --noconfirm "$pkg" || yellow "  pacman install $pkg failed — install manually"
        else
            yellow "  No known package manager found — install $pkg manually"
        fi
    fi
}

_check_install tmux         tmux
_check_install psql         postgresql-client
_check_install ssh          openssh-client
_check_install curl         curl
_check_install git          git

# Ollama is not in standard package repos — check and guide
if command -v ollama >/dev/null 2>&1; then
    green "  ollama: OK ($(ollama --version 2>/dev/null || echo 'version unknown'))"
else
    yellow "  ollama: missing"
    if [[ $DRY_RUN -eq 1 ]]; then
        dryrun "install ollama via: curl -fsSL https://ollama.com/install.sh | sh"
    else
        yellow "  Install Ollama manually: https://ollama.com/download"
        yellow "  Or run: curl -fsSL https://ollama.com/install.sh | sh"
    fi
fi

# ── Step 2 — First-time install (if .env missing) ─────────────────────────────

step "Step 2 — Igor install check"

INSTALL_SCRIPT="$REPO_ROOT/lab/claudecode/install_igor_linux.sh"

if [[ -f "$ENV_FILE" ]]; then
    green "  .env already exists at $ENV_FILE — skipping full install"
else
    yellow "  .env not found — running install_igor_linux.sh"
    if [[ $DRY_RUN -eq 1 ]]; then
        dryrun "run $INSTALL_SCRIPT"
    else
        [[ -f "$INSTALL_SCRIPT" ]] || die "install_igor_linux.sh not found at $INSTALL_SCRIPT"
        # install_igor_linux.sh needs ANTHROPIC_API_KEY and IGOR_HOME_DB_URL
        if [[ -z "${ANTHROPIC_API_KEY:-}" ]] || [[ -z "${IGOR_HOME_DB_URL:-}" ]]; then
            echo ""
            yellow "  First-time setup — please provide:"
            [[ -z "${ANTHROPIC_API_KEY:-}" ]] && read -r -p "  ANTHROPIC_API_KEY: " ANTHROPIC_API_KEY && export ANTHROPIC_API_KEY
            [[ -z "${IGOR_HOME_DB_URL:-}" ]]  && read -r -p "  IGOR_HOME_DB_URL (e.g. postgresql://igor:pw@localhost/Igor-wild-0001): " IGOR_HOME_DB_URL && export IGOR_HOME_DB_URL
        fi
        bash "$INSTALL_SCRIPT"
    fi
fi

# ── Step 3 — Validate .env ────────────────────────────────────────────────────

step "Step 3 — Validate environment"

if [[ ! -f "$ENV_FILE" ]]; then
    [[ $DRY_RUN -eq 1 ]] && dryrun "create $ENV_FILE" || die ".env still missing at $ENV_FILE — run install_igor_linux.sh first"
else
    # Load .env into current shell for validation
    set -a
    # shellcheck source=/dev/null
    source "$ENV_FILE"
    set +a

    REQUIRED_VARS=(IGOR_HOME_DB_URL OPENROUTER_API_KEY)
    missing_vars=0
    for var in "${REQUIRED_VARS[@]}"; do
        if [[ -n "${!var:-}" ]]; then
            green "  $var: set"
        else
            yellow "  $var: NOT SET"
            missing_vars=$((missing_vars + 1))
        fi
    done

    if [[ $missing_vars -gt 0 ]]; then
        yellow "  $missing_vars required var(s) missing — edit $ENV_FILE"
    fi
fi

# ── Step 4 — DB connectivity + schema bootstrap ───────────────────────────────

step "Step 4 — DB connectivity + schema bootstrap"

if [[ ! -f "$VENV_PY" ]]; then
    yellow "  venv not found at $VENV_DIR — run install_igor_linux.sh first"
elif [[ $DRY_RUN -eq 1 ]]; then
    dryrun "test DB + bootstrap schema via Cortex"
else
    REPO_ROOT="$REPO_ROOT" IGOR_HOME_DB_URL="${IGOR_HOME_DB_URL:-}" "$VENV_PY" - <<'PYEOF'
import os, sys

repo_root = os.environ.get("REPO_ROOT", "")
sys.path.insert(0, os.path.join(repo_root, "wild_igor"))

db_url = os.environ.get("IGOR_HOME_DB_URL", "")
if not db_url:
    print("  IGOR_HOME_DB_URL not set — skipping DB check", file=sys.stderr)
    sys.exit(0)

try:
    from igor.memory.cortex import Cortex
    cortex = Cortex(None)
    with cortex._conn() as conn:
        row = conn.execute("SELECT COUNT(*) FROM memories").fetchone()
    print(f"  DB OK — {row[0]} memories (schema bootstrapped)")
except Exception as e:
    print(f"  DB FAILED: {e}", file=sys.stderr)
    sys.exit(1)
PYEOF
fi

# ── Step 5 — Launch tmux session ──────────────────────────────────────────────

step "Step 5 — tmux session"

if [[ $NO_LAUNCH -eq 1 ]] || [[ $DRY_RUN -eq 1 ]]; then
    [[ $DRY_RUN -eq 1 ]] && dryrun "create tmux session '$TMUX_SESSION' with Igor"
    [[ $NO_LAUNCH -eq 1 ]] && yellow "  --no-launch: skipping tmux"
else
    if tmux has-session -t "$TMUX_SESSION" 2>/dev/null; then
        green "  tmux session '$TMUX_SESSION' already running"
    else
        if [[ ! -f "$VENV_PY" ]]; then
            yellow "  venv missing — cannot launch Igor, starting empty tmux session"
            tmux new-session -d -s "$TMUX_SESSION"
        else
            # Window 0: Igor main process
            IGOR_CMD="source $VENV_DIR/bin/activate && cd $REPO_ROOT/wild_igor && while true; do python -m igor.main; EC=\$?; [ \$EC -eq 42 ] && continue; break; done"
            tmux new-session -d -s "$TMUX_SESSION" -n "igor" bash -c "$IGOR_CMD"
            # Window 1: shell for inspection/attachment
            tmux new-window -t "$TMUX_SESSION" -n "shell"
            tmux send-keys -t "$TMUX_SESSION:shell" "cd $REPO_ROOT && source $VENV_DIR/bin/activate" Enter
            green "  tmux session '$TMUX_SESSION' launched"
        fi
    fi

    echo ""
    green "  Attach with:  tmux attach -t $TMUX_SESSION"
    green "  List windows: tmux list-windows -t $TMUX_SESSION"
fi

# ── Done ──────────────────────────────────────────────────────────────────────

echo ""
green "Utility closet complete."
[[ $DRY_RUN -eq 1 ]] && yellow "(dry-run: no changes made)" || true
