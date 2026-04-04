#!/usr/bin/env bash
# igor-docker.sh — Docker Compose launcher for Igor (D235)
#
# Usage:
#   deploy/igor-docker.sh [up|down|logs|rebuild|pull-model <model>]
#
# Requires: docker (with compose plugin), git, ~/.TheIgors/igor_wild_0001/.env
#
# First run:
#   1. Install Docker: https://docs.docker.com/engine/install/
#   2. clone the repo, cd into it
#   3. Run: deploy/igor-docker.sh up

set -euo pipefail

REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RUNTIME_ROOT="${IGOR_RUNTIME_ROOT:-$HOME/.TheIgors}"
INSTANCE_ID="${IGOR_INSTANCE_ID:-igor_wild_0001}"
ENV_SRC="$RUNTIME_ROOT/$INSTANCE_ID/.env"
ENV_DST="$REPO_ROOT/.env.igor"

# ── Helpers ───────────────────────────────────────────────────────────────────
green()  { printf '\033[32m%s\033[0m\n' "$*"; }
yellow() { printf '\033[33m%s\033[0m\n' "$*"; }
red()    { printf '\033[31m%s\033[0m\n' "$*"; }
step()   { printf '\n\033[1;36m==> %s\033[0m\n' "$*"; }
die()    { red "FATAL: $*"; exit 1; }

# ── Checks ────────────────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || die "Docker not found. Install from https://docs.docker.com/engine/install/"
docker compose version >/dev/null 2>&1 || die "Docker Compose plugin not found. Update Docker or install the compose plugin."

cd "$REPO_ROOT"

# ── Commands ──────────────────────────────────────────────────────────────────
CMD="${1:-up}"

case "$CMD" in

up)
    step "Syncing .env.igor from instance dir"
    if [ -f "$ENV_SRC" ]; then
        # Strip lines that docker-compose overrides (DB URL, runtime root)
        grep -v "^IGOR_HOME_DB_URL=\|^IGOR_RUNTIME_ROOT=" "$ENV_SRC" > "$ENV_DST"
        green "  .env.igor written from $ENV_SRC"
    else
        yellow "  No instance .env found at $ENV_SRC — .env.igor must exist manually"
        [ -f "$ENV_DST" ] || die ".env.igor not found. Copy ~/.TheIgors/$INSTANCE_ID/.env to .env.igor"
    fi

    step "Pulling latest repo"
    git pull --rebase origin main && green "  git pull OK" || yellow "  git pull failed — continuing"

    step "Building Igor image"
    docker compose build igor

    step "Starting stack"
    docker compose up -d

    step "Waiting for Igor healthcheck"
    _port="${IGOR_WEB_PORT:-8080}"
    for i in $(seq 1 24); do
        if curl -sf "http://localhost:$_port/api/health" >/dev/null 2>&1; then
            green "  Igor is healthy at http://localhost:$_port"
            break
        fi
        echo "  Waiting... ($i/24)"
        sleep 5
    done
    ;;

down)
    step "Stopping stack"
    docker compose down
    green "Done."
    ;;

logs)
    docker compose logs -f igor
    ;;

rebuild)
    step "Rebuilding Igor image (no-cache)"
    docker compose build --no-cache igor
    step "Restarting Igor service"
    docker compose up -d igor
    ;;

pull-model)
    MODEL="${2:-qwen2.5:7b}"
    step "Pulling Ollama model: $MODEL"
    docker compose exec ollama ollama pull "$MODEL"
    green "Model $MODEL ready."
    ;;

status)
    docker compose ps
    ;;

*)
    echo "Usage: $0 [up|down|logs|rebuild|pull-model <model>|status]"
    exit 1
    ;;
esac
