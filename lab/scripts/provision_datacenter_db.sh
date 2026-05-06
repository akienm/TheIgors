#!/bin/bash
# Provision agent-datacenter-0001 Postgres database
# Run as: sudo -u postgres bash provision_datacenter_db.sh
# Or interactively: bash provision_datacenter_db.sh (will prompt for postgres password if needed)

set -e

DBNAME="agent-datacenter-0001"
ROLE="datacenter"
PASS="${DATACENTER_DB_PASSWORD:-choose_a_password}"

echo "==> Creating role $ROLE..."
psql postgres -c "
  DO \$\$
  BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = '$ROLE') THEN
      CREATE ROLE $ROLE LOGIN PASSWORD '$PASS';
      RAISE NOTICE 'Role $ROLE created';
    ELSE
      RAISE NOTICE 'Role $ROLE already exists — skipping';
    END IF;
  END\$\$;
"

echo "==> Creating database $DBNAME..."
psql postgres -tc "SELECT 1 FROM pg_database WHERE datname = '$DBNAME'" | grep -q 1 \
  && echo "Database $DBNAME already exists — skipping" \
  || psql postgres -c "CREATE DATABASE \"$DBNAME\" OWNER $ROLE"

echo "==> Creating schema in $DBNAME..."
psql "$DBNAME" -c "
  CREATE TABLE IF NOT EXISTS memory_palace (
      id          SERIAL PRIMARY KEY,
      path        TEXT NOT NULL UNIQUE,
      parent_path TEXT,
      title       TEXT,
      content     TEXT,
      pointers    JSONB DEFAULT '{}',
      updated_at  TEXT,
      updated_by  TEXT
  );

  CREATE TABLE IF NOT EXISTS memories (
      id                   TEXT PRIMARY KEY,
      narrative            TEXT,
      memory_type          TEXT,
      parent_id            TEXT,
      children_ids         TEXT DEFAULT '[]',
      link_ids             TEXT DEFAULT '[]',
      valence              REAL DEFAULT 0.0,
      arousal              REAL DEFAULT 0.0,
      dominance            REAL DEFAULT 0.0,
      activation_count     INTEGER DEFAULT 0,
      friction_history     TEXT DEFAULT '[]',
      timestamp            TEXT,
      metadata             JSONB DEFAULT '{}',
      portable             INTEGER DEFAULT 1,
      links_weighted       TEXT DEFAULT '{}',
      last_accessed        TEXT,
      source               TEXT DEFAULT '',
      confidence           REAL DEFAULT 1.0,
      context_of_encoding  TEXT DEFAULT '',
      updated_at           TEXT,
      scope                TEXT DEFAULT 'class',
      payload              TEXT
  );

  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO $ROLE;
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO $ROLE;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO $ROLE;
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO $ROLE;
"

echo "==> Done. Connection string:"
echo "    postgresql://$ROLE:$PASS@127.0.0.1/$DBNAME"
echo ""
echo "Add to agent_datacenter .env:"
echo "    AGENT_DATACENTER_DB_URL=postgresql://$ROLE:$PASS@127.0.0.1/$DBNAME"
