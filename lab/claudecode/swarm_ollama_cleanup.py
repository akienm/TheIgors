#!/usr/bin/env python3
"""
swarm_ollama_cleanup.py — T-ollama-model-cleanup

Audits Ollama installs across every online machine in the fleet and removes
models outside the keep-list. Uses Ollama's HTTP API (GET /api/tags,
DELETE /api/delete) — SSH not required, works over the tailnet/LAN.

## Usage

    # Dry-run (default): shows what WOULD be removed per box, no action
    python3 lab/claudecode/swarm_ollama_cleanup.py

    # Actually delete
    python3 lab/claudecode/swarm_ollama_cleanup.py --confirm

## Keep list (2026-04-19)

- qwen2.5:7b — the single local workhorse
- nomic-embed-text:latest — embeddings model

Everything else on each box is proposed for removal.

## Relationship to T-swarm-model-sync (done)

That ticket shipped the PUSH direction: sync configured models to every
online box. This is the inverse: prune unused models from every box.

## Provenance

Akien 2026-04-19: 'yes, the swarm manager would be the entity responsible
for reaching thru the ssh to each of the boxes to drop uneeded models.'
CC impl note: used HTTP API rather than SSH because CC lacks SSH keys to
the fleet from akiendelllinux — same result, different transport.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

_REPO = Path(__file__).resolve().parent.parent.parent

# Models we keep everywhere. Everything else on each box gets proposed for
# removal. Per-box exceptions can be added here if specific machines need
# specific niche models (e.g. an embedding box that needs a different
# embedder).
KEEP_EVERYWHERE = {
    "qwen2.5:7b",
    "nomic-embed-text:latest",
}


def _load_machines() -> list[dict]:
    """Load machines from lab/seed/machines.yaml (source of truth)."""
    import yaml

    spec = yaml.safe_load((_REPO / "lab" / "seed" / "machines.yaml").read_text())
    return [m for m in spec.get("machines", []) if m.get("status") == "online"]


def _list_models(host: str, port: int, timeout: int = 10) -> list[dict] | None:
    """GET /api/tags on a remote Ollama. Returns list of {name, size} or None."""
    try:
        url = f"http://{host}:{port}/api/tags"
        with urllib.request.urlopen(url, timeout=timeout) as resp:
            data = json.loads(resp.read())
        return data.get("models", [])
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
        print(f"  [{host}] unreachable or bad response: {e}", file=sys.stderr)
        return None


def _delete_model(host: str, port: int, model_name: str, timeout: int = 30) -> bool:
    """DELETE /api/delete on a remote Ollama. Returns True on 200."""
    try:
        url = f"http://{host}:{port}/api/delete"
        body = json.dumps({"name": model_name}).encode()
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json"},
            method="DELETE",
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status in (200, 204)
    except urllib.error.HTTPError as e:
        print(f"  [{host}] DELETE {model_name} HTTP {e.code}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"  [{host}] DELETE {model_name} failed: {e}", file=sys.stderr)
        return False


def plan_cleanup() -> list[dict]:
    """Return a per-box plan of {host, hostname, keep, remove}.

    remove entries are tuples of (name, size_mb).
    """
    plan: list[dict] = []
    for m in _load_machines():
        host = m.get("ip")
        hostname = m.get("hostname")
        port = m.get("ollama_port", 11434)
        if not host:
            print(f"  [{hostname}] no ip — skipping", file=sys.stderr)
            continue
        models = _list_models(host, port)
        if models is None:
            plan.append(
                {
                    "host": host,
                    "hostname": hostname,
                    "port": port,
                    "status": "unreachable",
                    "keep": [],
                    "remove": [],
                }
            )
            continue
        keep = []
        remove = []
        for mdl in models:
            name = mdl.get("name", "")
            size_mb = mdl.get("size", 0) // 1024 // 1024
            if name in KEEP_EVERYWHERE:
                keep.append((name, size_mb))
            else:
                remove.append((name, size_mb))
        plan.append(
            {
                "host": host,
                "hostname": hostname,
                "port": port,
                "status": "ok",
                "keep": keep,
                "remove": remove,
            }
        )
    return plan


def print_plan(plan: list[dict], header: str = "PLAN") -> None:
    print(f"\n── {header} ─────────────────────────────────────")
    total_reclaim_mb = 0
    for box in plan:
        marker = "✓" if box["status"] == "ok" else "?"
        print(f"\n{marker} {box['hostname']} ({box['host']}:{box['port']})")
        if box["status"] == "unreachable":
            print("    unreachable — skipping")
            continue
        for name, sz in box["keep"]:
            print(f"    KEEP    {name:50} {sz} MB")
        for name, sz in box["remove"]:
            print(f"    REMOVE  {name:50} {sz} MB")
            total_reclaim_mb += sz
    print(
        f"\n── total would reclaim: {total_reclaim_mb} MB ({total_reclaim_mb/1024:.1f} GB) ──\n"
    )


def execute_plan(plan: list[dict]) -> dict:
    """Remove each model in the plan. Returns per-box results."""
    results: dict = {}
    for box in plan:
        if box["status"] != "ok":
            results[box["hostname"]] = {"skipped": "unreachable"}
            continue
        removed = []
        failed = []
        for name, sz in box["remove"]:
            ok = _delete_model(box["host"], box["port"], name)
            if ok:
                removed.append(name)
                print(f"  [{box['hostname']}] ✓ removed {name} ({sz} MB)")
            else:
                failed.append(name)
                print(f"  [{box['hostname']}] ✗ failed to remove {name}")
        results[box["hostname"]] = {"removed": removed, "failed": failed}
    return results


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--confirm",
        action="store_true",
        help="Actually delete the models. Without this, the script only shows the plan.",
    )
    args = parser.parse_args()

    plan = plan_cleanup()
    print_plan(plan, header="AUDIT")

    if not args.confirm:
        print("DRY-RUN: re-run with --confirm to execute deletions.")
        return 0

    print("── EXECUTING ─────────────────────────────────────")
    results = execute_plan(plan)
    print(f"\nResults: {json.dumps(results, indent=2)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
