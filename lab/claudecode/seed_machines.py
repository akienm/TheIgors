#!/usr/bin/env python3
"""
seed_machines.py — T-versioned-seed-config.

Reads the machines spec from lab/seed/machines.yaml (source-of-truth, git-versioned)
and upserts it into the infra.machines table. Idempotent — safe to re-run.

Pattern: file → DB (hand-curated; DB is runtime cache).
Restore: python3 lab/claudecode/seed_machines.py
Versioning: git log lab/seed/machines.yaml

Non-goals:
- This does NOT sync DB → file. Live edits to the DB (e.g. a machine going
  online/offline via heartbeat) are ephemeral; if they should persist across
  seeds, they belong in the YAML.
- This does NOT delete machines that are absent from the YAML. Removal is
  explicit: take the row out of machines.yaml + DELETE FROM machines by hand.
  Seed-time deletes are too dangerous.
"""

from __future__ import annotations

import json
import os
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent
_SEED_YAML = _REPO / "lab" / "seed" / "machines.yaml"

_UPSERT_SQL = """
INSERT INTO machines (
    hostname, display_name, ip, os, cpu, ram_gb, gpu, storage, hardware_model,
    network_type, status, ollama_port, ollama_model, ollama_model_batch,
    inference_rank, in_use_hours, in_use_until, roles, aliases,
    ssh_enabled, ssh_user, notes, updated_at
) VALUES (
    %(hostname)s, %(display_name)s, %(ip)s, %(os)s, %(cpu)s, %(ram_gb)s,
    %(gpu)s, %(storage)s, %(hardware_model)s, %(network_type)s, %(status)s,
    %(ollama_port)s, %(ollama_model)s, %(ollama_model_batch)s,
    %(inference_rank)s, %(in_use_hours)s, %(in_use_until)s,
    %(roles)s, %(aliases)s, %(ssh_enabled)s, %(ssh_user)s, %(notes)s,
    %(updated_at)s
)
ON CONFLICT (hostname) DO UPDATE SET
    display_name   = EXCLUDED.display_name,
    ip             = EXCLUDED.ip,
    os             = EXCLUDED.os,
    cpu            = EXCLUDED.cpu,
    ram_gb         = EXCLUDED.ram_gb,
    gpu            = EXCLUDED.gpu,
    storage        = EXCLUDED.storage,
    hardware_model = EXCLUDED.hardware_model,
    network_type   = EXCLUDED.network_type,
    status         = EXCLUDED.status,
    ollama_port    = EXCLUDED.ollama_port,
    ollama_model   = EXCLUDED.ollama_model,
    ollama_model_batch = EXCLUDED.ollama_model_batch,
    inference_rank = EXCLUDED.inference_rank,
    in_use_hours   = EXCLUDED.in_use_hours,
    in_use_until   = EXCLUDED.in_use_until,
    roles          = EXCLUDED.roles,
    aliases        = EXCLUDED.aliases,
    ssh_enabled    = EXCLUDED.ssh_enabled,
    ssh_user       = EXCLUDED.ssh_user,
    notes          = EXCLUDED.notes,
    updated_at     = EXCLUDED.updated_at
"""


def _row_from_yaml(m: dict) -> dict:
    """Normalise a YAML machine dict into params for the SQL upsert."""
    from datetime import datetime, timezone

    return {
        "hostname": m["hostname"],
        "display_name": m.get("display_name"),
        "ip": m.get("ip"),
        "os": m.get("os"),
        "cpu": m.get("cpu"),
        "ram_gb": m.get("ram_gb"),
        "gpu": m.get("gpu"),
        "storage": m.get("storage"),
        "hardware_model": m.get("hardware_model"),
        "network_type": m.get("network_type"),
        "status": m.get("status", "offline"),
        "ollama_port": m.get("ollama_port", 11434),
        "ollama_model": m.get("ollama_model", "qwen2.5:7b"),
        # ollama_model_batch is deprecated (2026-04-18 single-model collapse).
        # Keep the column writable for back-compat; always NULL from YAML.
        "ollama_model_batch": None,
        "inference_rank": m.get("inference_rank"),
        "in_use_hours": json.dumps(m.get("in_use_hours") or []),
        "in_use_until": m.get("in_use_until"),
        "roles": json.dumps(m.get("roles") or []),
        "aliases": json.dumps(m.get("aliases") or []),
        "ssh_enabled": bool(m.get("ssh_enabled", False)),
        "ssh_user": m.get("ssh_user"),
        "notes": m.get("notes"),
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }


def seed_machines(db_url: str) -> dict:
    import psycopg2
    import yaml

    if not _SEED_YAML.exists():
        raise FileNotFoundError(f"Seed file not found: {_SEED_YAML}")

    spec = yaml.safe_load(_SEED_YAML.read_text())
    machines = spec.get("machines", [])
    if not machines:
        return {"inserted_or_updated": 0, "warnings": ["YAML has no machines"]}

    counts = {"inserted_or_updated": 0}
    conn = psycopg2.connect(db_url)
    try:
        with conn:
            with conn.cursor() as cur:
                # Ensure we target the right schema — machines is in infra
                cur.execute("SET search_path TO infra,clan,public")
                for m in machines:
                    cur.execute(_UPSERT_SQL, _row_from_yaml(m))
                    counts["inserted_or_updated"] += 1
    finally:
        conn.close()

    counts["source"] = f"yaml:{_SEED_YAML.name}"
    return counts


def main():
    db_url = os.getenv(
        "IGOR_HOME_DB_URL",
        "postgresql://igor:choose_a_password@127.0.0.1/Igor-wild-0001",
    )
    report = seed_machines(db_url)
    print(
        f"seed_machines: upserted={report['inserted_or_updated']} "
        f"source={report.get('source', '?')}"
    )


if __name__ == "__main__":
    main()
