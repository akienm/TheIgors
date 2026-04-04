# Dockerfile — Igor AI Agent (D235)
# Builds the Igor service container (Python 3.12, wild_igor/).
#
# Build:   docker build -t igor:latest .
# Compose: docker compose -f docker-compose.yml up
#
# Runtime data is mounted at /data (host: ~/.TheIgors).
# Credentials come from docker-compose env_file, not baked into the image.

FROM python:3.12-slim

# ── System packages ───────────────────────────────────────────────────────────
# git          — igor self-edit commits
# libmagic1    — python-magic (file type detection)
# libpq-dev    — psycopg2-binary headers (not needed for binary wheel but keeps psql CLI)
# postgresql-client — psql for manual debugging
# curl         — healthcheck probe
# procps       — ps/kill for crash handler
RUN apt-get update && apt-get install -y --no-install-recommends \
    git \
    libmagic1 \
    postgresql-client \
    curl \
    procps \
    && rm -rf /var/lib/apt/lists/*

# ── Python dependencies ────────────────────────────────────────────────────────
WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Playwright browser install (browser-use requires Chromium)
RUN playwright install chromium \
    && playwright install-deps chromium

# NLTK data
RUN python3 -c "import nltk; [nltk.download(p, quiet=True) for p in ('punkt', 'punkt_tab', 'wordnet', 'averaged_perceptron_tagger')]"

# ── Application code ──────────────────────────────────────────────────────────
COPY wild_igor/ /app/wild_igor/

# ── Runtime config ────────────────────────────────────────────────────────────
# IGOR_RUNTIME_ROOT=/data — all instance data lives in the mounted volume.
# IGOR_INSTANCE_ID    — set in docker-compose or at runtime.
ENV IGOR_RUNTIME_ROOT=/data \
    IGOR_INSTANCE_ID=igor_wild_0001 \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /app/wild_igor

# ── Healthcheck ───────────────────────────────────────────────────────────────
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD curl -sf http://localhost:${IGOR_WEB_PORT:-8080}/api/health || exit 1

ENTRYPOINT ["python", "-m", "igor.main"]
