"""
consolidate_memories.py — G45: Memory consolidation overnight job.

Three-stage consolidation pass:
  Stage A: Cluster similar EPISODIC memories → merge into INTERPRETIVE/FACTUAL
            (cosine similarity via Ollama nomic-embed-text; threshold configurable)
  Stage B: Prune very low-inertia + long-unaccessed memories (safe to forget)
  Stage C: Reinforce heavily-activated memories (boost last_accessed freshness)

Designed to run overnight (same schedule as retrain_word_graph.py).
Can also be triggered manually or by Igor when machine is idle.

Usage:
  python claudecode/consolidate_memories.py [--dry-run] [--stage A|B|C|all]

Environment:
  IGOR_DB_PATH          — path to live SQLite DB (required)
  IGOR_INSTANCE_ID      — instance id (default: wild-0001)
  CONSOLIDATE_SIM_THRESHOLD  — cosine sim for cluster merge (default: 0.88)
  CONSOLIDATE_PRUNE_INERTIA  — inertia below which to consider pruning (default: 0.12)
  CONSOLIDATE_PRUNE_DAYS     — days since last access before pruning (default: 45)
  CONSOLIDATE_MIN_CLUSTER    — minimum cluster size to merge (default: 3)
"""
import argparse
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
os.environ.setdefault("IGOR_DB_PATH",
    str(Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"))

from wild_igor.igor.memory.models import Memory, MemoryType
from wild_igor.igor.memory.cortex import Cortex

DB_PATH = Path(os.environ["IGOR_DB_PATH"])
INSTANCE_ID = os.getenv("IGOR_INSTANCE_ID", "wild-0001")

SIM_THRESHOLD   = float(os.getenv("CONSOLIDATE_SIM_THRESHOLD",   "0.88"))
PRUNE_INERTIA   = float(os.getenv("CONSOLIDATE_PRUNE_INERTIA",   "0.12"))
PRUNE_DAYS      = int(os.getenv("CONSOLIDATE_PRUNE_DAYS",         "45"))
MIN_CLUSTER     = int(os.getenv("CONSOLIDATE_MIN_CLUSTER",         "3"))


def _embed(text: str) -> list[float] | None:
    """Get embedding from Ollama nomic-embed-text (same as cortex.py)."""
    import urllib.request, json
    try:
        payload = json.dumps({"model": "nomic-embed-text", "prompt": text[:512]}).encode()
        req = urllib.request.Request(
            "http://localhost:11434/api/embeddings",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read())["embedding"]
    except Exception as e:
        print(f"  [embed error] {e}")
        return None


def _cosine(a: list[float], b: list[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = sum(x * x for x in a) ** 0.5
    nb = sum(x * x for x in b) ** 0.5
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def stage_a_cluster_episodics(cortex: Cortex, dry_run: bool) -> int:
    """
    Stage A: Find clusters of similar EPISODIC memories → merge into one FACTUAL memory.
    Returns number of clusters processed.
    """
    print("\n=== Stage A: Cluster + merge similar EPISODIC memories ===")

    # Fetch all EPISODIC memories with at least 2 activations (worth keeping around)
    with cortex._conn() as conn:
        rows = conn.execute(
            "SELECT * FROM memories WHERE memory_type = ? AND activation_count >= 2",
            (MemoryType.EPISODIC.value,)
        ).fetchall()

    episodics = [m for r in rows if (m := cortex._to_memory(r)) is not None]
    print(f"  Found {len(episodics)} EPISODIC memories with activation_count >= 2")

    if len(episodics) < MIN_CLUSTER:
        print(f"  Too few episodics for clustering (need {MIN_CLUSTER}). Skipping.")
        return 0

    print(f"  Embedding {len(episodics)} memories (this may take a while)...")
    embedded = []
    for i, mem in enumerate(episodics):
        emb = _embed(mem.narrative)
        if emb:
            embedded.append((mem, emb))
        if (i + 1) % 20 == 0:
            print(f"    {i+1}/{len(episodics)} embedded...")

    print(f"  Got embeddings for {len(embedded)} memories")
    if len(embedded) < MIN_CLUSTER:
        print("  Not enough embeddings. Skipping Stage A.")
        return 0

    # Greedy clustering: for each unassigned memory, find all similar ones
    assigned: set[str] = set()
    clusters: list[list] = []

    for i, (mem_i, emb_i) in enumerate(embedded):
        if mem_i.id in assigned:
            continue
        cluster = [(mem_i, emb_i)]
        assigned.add(mem_i.id)
        for j, (mem_j, emb_j) in enumerate(embedded):
            if mem_j.id in assigned or i == j:
                continue
            sim = _cosine(emb_i, emb_j)
            if sim >= SIM_THRESHOLD:
                cluster.append((mem_j, emb_j))
                assigned.add(mem_j.id)
        if len(cluster) >= MIN_CLUSTER:
            clusters.append(cluster)

    print(f"  Found {len(clusters)} clusters (size >= {MIN_CLUSTER})")

    processed = 0
    for cluster in clusters:
        mems = [m for m, _ in cluster]
        narratives = " | ".join(m.narrative[:80] for m in mems[:5])
        total_activations = sum(m.activation_count for m in mems)
        avg_valence = sum(m.valence for m in mems) / len(mems)
        avg_arousal = sum(m.arousal for m in mems) / len(mems)

        merged_narrative = (
            f"[CONSOLIDATED from {len(mems)} episodics] "
            f"Recurring experience: {mems[0].narrative[:150]}"
        )

        print(f"\n  Cluster ({len(mems)} memories):")
        print(f"    Sample: {narratives[:120]}")
        print(f"    → Merge into FACTUAL: {merged_narrative[:100]}")

        if dry_run:
            print("    [DRY RUN — skipping write]")
            processed += 1
            continue

        # Create merged FACTUAL memory
        import uuid
        merged = Memory(
            id=f"FACT_{str(uuid.uuid4())[:6].upper()}",
            narrative=merged_narrative,
            memory_type=MemoryType.FACTUAL,
            valence=avg_valence,
            arousal=avg_arousal,
            activation_count=total_activations,
            source="consolidation",
            confidence=0.7,
            context_of_encoding=f"consolidated_from_{len(mems)}_episodics",
            metadata={
                "consolidated_from": [m.id for m in mems],
                "consolidation_date": datetime.now().isoformat(),
            },
        )
        cortex.store(merged)
        # Parent: use first memory's parent, or CP2 (learning from experience)
        parent = mems[0].parent_id or "CP2"
        cortex.add_child(parent, merged.id)

        # Mark source episodics as having been consolidated (don't delete — they may have links)
        with cortex._conn() as conn:
            for m in mems:
                conn.execute(
                    "UPDATE memories SET metadata_json = json_set(metadata_json, '$.consolidated', 1) "
                    "WHERE id = ?",
                    (m.id,)
                )

        print(f"    [MERGED] → {merged.id}")
        processed += 1

    return processed


def stage_b_prune(cortex: Cortex, dry_run: bool) -> int:
    """
    Stage B: Prune very low-inertia + long-unaccessed memories.
    Safety: never prune ROOT, CORE_PATTERN, IDENTITY, ROLE_MODEL, or anything with children.
    Returns number pruned.
    """
    print("\n=== Stage B: Prune low-inertia stale memories ===")

    safe_types = {
        MemoryType.ROOT.value, MemoryType.CORE_PATTERN.value,
        MemoryType.IDENTITY.value, MemoryType.ROLE_MODEL.value,
    }
    cutoff = datetime.now() - timedelta(days=PRUNE_DAYS)

    with cortex._conn() as conn:
        rows = conn.execute(
            """
            SELECT * FROM memories
            WHERE memory_type NOT IN (?, ?, ?, ?)
            AND (last_accessed IS NULL OR last_accessed < ?)
            """,
            (*safe_types, cutoff.isoformat()),
        ).fetchall()

    candidates = [m for r in rows if (m := cortex._to_memory(r)) is not None]
    # Filter by inertia (computed property — not in SQL)
    prune_candidates = [m for m in candidates if m.inertia < PRUNE_INERTIA]
    # Never prune memories with children
    prune_candidates = [m for m in prune_candidates if not m.children_ids]

    print(f"  Candidates: {len(candidates)} stale memories")
    print(f"  After inertia filter (< {PRUNE_INERTIA}): {len(prune_candidates)}")

    if not prune_candidates:
        print("  Nothing to prune.")
        return 0

    pruned = 0
    for m in prune_candidates:
        print(
            f"  {'[DRY]' if dry_run else '[PRUNE]'} {m.id} "
            f"type={m.memory_type.value} inertia={m.inertia:.3f} "
            f"narrative={m.narrative[:60]}"
        )
        if not dry_run:
            with cortex._conn() as conn:
                conn.execute("DELETE FROM memories WHERE id = ?", (m.id,))
        pruned += 1

    if not dry_run:
        print(f"  Pruned {pruned} memories.")
    else:
        print(f"  [DRY RUN] Would prune {pruned} memories.")
    return pruned


def stage_c_reinforce(cortex: Cortex, dry_run: bool) -> int:
    """
    Stage C: Reinforce heavily-activated memories — boost last_accessed freshness.
    Memories activated > 50 times but not accessed recently get a freshness touch.
    Returns count reinforced.
    """
    print("\n=== Stage C: Reinforce heavily-activated memories ===")

    with cortex._conn() as conn:
        rows = conn.execute(
            "SELECT * FROM memories WHERE activation_count > 50 AND last_accessed < ?",
            ((datetime.now() - timedelta(days=7)).isoformat(),),
        ).fetchall()

    memories = [m for r in rows if (m := cortex._to_memory(r)) is not None]
    print(f"  Found {len(memories)} heavily-activated but stale memories")

    reinforced = 0
    now_iso = datetime.now().isoformat()
    for m in memories:
        if dry_run:
            print(f"  [DRY] Would reinforce {m.id} ({m.activation_count} activations)")
        else:
            with cortex._conn() as conn:
                conn.execute(
                    "UPDATE memories SET last_accessed = ? WHERE id = ?",
                    (now_iso, m.id)
                )
            print(f"  [REINFORCE] {m.id} ({m.activation_count} activations) → last_accessed refreshed")
        reinforced += 1

    return reinforced


def main():
    parser = argparse.ArgumentParser(description="Igor memory consolidation job (G45)")
    parser.add_argument("--dry-run", action="store_true", help="Preview without writing")
    parser.add_argument("--stage", default="all", choices=["A", "B", "C", "all"],
                        help="Which stage to run (default: all)")
    args = parser.parse_args()

    print(f"Memory Consolidation — {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"  DB: {DB_PATH}")
    print(f"  Dry run: {args.dry_run}")
    print(f"  Stage: {args.stage}")
    print(f"  Thresholds: sim={SIM_THRESHOLD}  prune_inertia={PRUNE_INERTIA}  "
          f"prune_days={PRUNE_DAYS}  min_cluster={MIN_CLUSTER}")

    cortex = Cortex(DB_PATH, instance_id=INSTANCE_ID)

    total_before = cortex.total_count()
    print(f"\n  Total memories before: {total_before}")

    a_count = b_count = c_count = 0

    if args.stage in ("A", "all"):
        a_count = stage_a_cluster_episodics(cortex, args.dry_run)

    if args.stage in ("B", "all"):
        b_count = stage_b_prune(cortex, args.dry_run)

    if args.stage in ("C", "all"):
        c_count = stage_c_reinforce(cortex, args.dry_run)

    total_after = cortex.total_count()
    print(f"\n{'DRY RUN ' if args.dry_run else ''}Summary:")
    print(f"  Stage A (cluster+merge):  {a_count} clusters processed")
    print(f"  Stage B (prune):          {b_count} memories pruned")
    print(f"  Stage C (reinforce):      {c_count} memories reinforced")
    print(f"  Total memories after:     {total_after} (was {total_before})")
    print("\nConsolidation complete.")


if __name__ == "__main__":
    main()
