#!/usr/bin/env python3
"""
book_learner.py — Bulk graph-node extraction from books via LLM.

Reads a book in chunks, sends each chunk to an LLM with an extraction prompt,
deposits resulting nodes (FACTUAL, INTERPRETIVE, PROCEDURAL) into Igor's graph.
Trains the word graph from each chunk as a side effect.

This is the "bootstrap loader" for self-programming: give Igor a book on
neuroscience, epistemology, or any domain and it becomes part of his graph.

Usage:
  python3 claudecode/book_learner.py --book "Descartes Error"     # dry run
  python3 claudecode/book_learner.py --book "Descartes Error" --run
  python3 claudecode/book_learner.py --calibre-id 3023 --run
  python3 claudecode/book_learner.py --calibre-id 3023 --run --resume
  python3 claudecode/book_learner.py --calibre-id 3023 --run --limit 10

Options:
  --book STR         Book title (fuzzy search in Calibre library)
  --calibre-id INT   Exact Calibre book ID (faster)
  --chunk INT        Sentences per chunk (default 15)
  --delay FLOAT      Seconds between API calls (default 1.5)
  --model STR        LLM model (default: openai/gpt-4o-mini via OpenRouter)
  --run              Actually call API and deposit nodes (default: dry run)
  --resume           Skip chunks already processed in a previous run
  --limit INT        Stop after N chunks (for testing)
  --start INT        Start at sentence position (skip to chapter)

Cost estimate (gpt-4o-mini):
  ~15 sentences ≈ 200 words ≈ 280 tokens input
  System prompt ≈ 400 tokens (constant)
  Output ≈ 200 tokens
  Per chunk ≈ $0.0001  ·  A 300-page book ≈ 200 chunks ≈ $0.02 total
"""

import argparse
import hashlib
import json
import os
import sys
import time
import uuid
from pathlib import Path

# ── Path setup ────────────────────────────────────────────────────────────────
REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))
sys.path.insert(0, str(REPO / "wild_igor"))

env_path = Path.home() / ".TheIgors" / "igor_wild_0001" / ".env"
if env_path.exists():
    for line in env_path.read_text().splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, _, v = line.partition("=")
            os.environ.setdefault(k.strip(), v.strip())

from igor.memory.cortex import Cortex

_CLOUD_OK_OVERRIDE_FILE = Path.home() / ".TheIgors" / "cloud_ok_override.json"


def _should_use_local(explicit_local: bool = False) -> bool:
    """
    Decide whether to use local Ollama for this inference call (D071).
    - If --local flag passed explicitly: always local.
    - If cloud_ok_override file exists and is active: use cloud.
    - Otherwise: default to local (background = economical, no surprise spend).
    Called per-chunk so mode can change mid-book without restart.
    """
    if explicit_local:
        return True
    try:
        if not _CLOUD_OK_OVERRIDE_FILE.exists():
            return True  # no override = local
        data = json.loads(_CLOUD_OK_OVERRIDE_FILE.read_text())
        if not data.get("active", False):
            return True
        expires = data.get("expires")
        if expires:
            from datetime import datetime as _dt

            if _dt.now() > _dt.fromisoformat(expires):
                return True  # expired = back to local
        return False  # override active = cloud OK
    except Exception:
        return True  # on any error, default to local


from igor.memory.models import Memory, MemoryType
from igor.tools.ebook_reader import open_book, read_chunk

DB_PATH = Path(
    os.environ.get(
        "IGOR_DB_PATH", Path.home() / ".TheIgors" / "igor_wild_0001" / "wild-0001.db"
    )
)
PROGRESS_DIR = Path.home() / ".TheIgors" / "book_learner_progress"
OPENROUTER_BASE = "https://openrouter.ai/api/v1"
OPENROUTER_REFERER = "https://github.com/akienm/TheIgors"

# ── Extraction system prompt ───────────────────────────────────────────────────
_EXTRACT_PROMPT = """\
You are a graph-node extractor for a cognitive AI. Given a passage from a book,
extract knowledge worth storing as permanent nodes in a semantic memory graph.

Extract ONLY nodes that are:
- Generalizable principles or concepts (not summaries of just this passage)
- Conceptual connections that reduce future reasoning (A implies B, X is a form of Y)
- Empirical facts about how minds, bodies, or systems work
- Action patterns (procedural nodes) only if the passage implies a clear "when X, do Y"

NODE TYPES:
  factual      — a concept, definition, or empirical fact
  interpretive — a connection: "when X, it means/implies Y"
  procedural   — an action pattern with a clear trigger (rare in prose)

PARENT_CP MAPPING (use the best fit):
  CP1 — learning, growth, capability
  CP2 — helping others, social connection
  CP3 — curiosity, exploration, creativity
  CP4 — integrity, commitment, honoring agreements
  CP5 — kindness, empathy, care
  CP6 — safety, survival, homeostasis

RESPONSE FORMAT — output ONLY valid JSON, no markdown, no extra text:
{
  "nodes": [
    {
      "type": "factual|interpretive|procedural",
      "narrative": "1-2 sentences: the generalizable knowledge, present tense",
      "confidence": 0.0-1.0,
      "parent_cp": "CP1-CP6 or empty string",
      "trigger": "2-8 words that fire this habit (procedural only, else empty string)"
    }
  ],
  "summary": "1 sentence: what this passage is about (for progress logging)"
}

Rules:
- 0-4 nodes max per chunk. Quality over quantity.
- Minimum confidence 0.65 to include a node.
- Skip: plot summaries, obvious truisms, author biography, hedged speculation.
- For neuroscience/Damasio: prioritize somatic markers, homeostasis, emotion-cognition
  integration, consciousness layers, body-mind continuity.
- Narratives must be self-contained — no "in this chapter" or "the author says".
"""


# ── Checkpoint management ──────────────────────────────────────────────────────


def _progress_path(book_key: str) -> Path:
    PROGRESS_DIR.mkdir(parents=True, exist_ok=True)
    safe = hashlib.md5(book_key.encode()).hexdigest()[:12]
    return PROGRESS_DIR / f"{safe}.json"


def _load_progress(book_key: str) -> dict:
    p = _progress_path(book_key)
    if p.exists():
        try:
            return json.loads(p.read_text())
        except Exception:
            pass
    return {"book_key": book_key, "processed_positions": [], "total_deposited": 0}


def _save_progress(book_key: str, state: dict) -> None:
    _progress_path(book_key).write_text(json.dumps(state, indent=2))


# ── LLM extraction ────────────────────────────────────────────────────────────


def _clean_json(raw: str) -> str:
    """Strip markdown code fences if the model wraps its JSON output."""
    raw = raw.strip()
    if raw.startswith("```"):
        raw = raw.split("```")[1]
        if raw.startswith("json"):
            raw = raw[4:]
    return raw.strip()


def _extract_nodes_local(chunk_text: str, chapter_title: str = "") -> dict:
    """
    Extract nodes using local Ollama — zero API cost.
    Uses OLLAMA_LOCAL_MODEL (default qwen2.5:7b) at OLLAMA_HOST.
    """
    import urllib.request

    model = os.getenv("OLLAMA_LOCAL_MODEL", "qwen2.5:7b").split("#")[0].strip()
    host = os.getenv("OLLAMA_HOST", "http://localhost:11434")

    user_content = "BOOK PASSAGE"
    if chapter_title:
        user_content += f" (from chapter: {chapter_title})"
    user_content += f":\n\n{chunk_text}"

    payload = json.dumps(
        {
            "model": model,
            "messages": [
                {"role": "system", "content": _EXTRACT_PROMPT},
                {"role": "user", "content": user_content},
            ],
            "stream": False,
            "options": {"temperature": 0.2},
        }
    ).encode()

    req = urllib.request.Request(
        f"{host}/api/chat",
        data=payload,
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=300) as resp:
            data = json.loads(resp.read())
        raw = data.get("message", {}).get("content", "").strip()
        return json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        return {
            "nodes": [],
            "summary": f"local parse error: {raw[:100] if 'raw' in dir() else '?'}",
        }
    except Exception as e:
        return {"nodes": [], "summary": f"local inference error: {e}"}


def _extract_nodes(
    chunk_text: str, model: str, chapter_title: str = "", local: bool = False
) -> dict:
    """
    Send one chunk to the LLM. Returns parsed JSON dict or error dict.
    If local=True, uses Ollama directly (free, no API key needed).
    """
    if local:
        return _extract_nodes_local(chunk_text, chapter_title)

    import urllib.request

    api_key = os.getenv("OPENROUTER_API_KEY", "")
    if not api_key:
        return {"nodes": [], "summary": "ERROR: OPENROUTER_API_KEY not set"}

    user_content = "BOOK PASSAGE"
    if chapter_title:
        user_content += f" (from chapter: {chapter_title})"
    user_content += f":\n\n{chunk_text}"

    # Prompt caching: system prompt is identical across all chunks of a book.
    # OR supports cache_control for Claude models — cache once, free for ~200 chunks.
    _use_cache = "claude" in model.lower() or "anthropic" in model.lower()
    _sys_msg = {"role": "system", "content": _EXTRACT_PROMPT}
    if _use_cache:
        _sys_msg["cache_control"] = {"type": "ephemeral"}

    payload = json.dumps(
        {
            "model": model,
            "messages": [_sys_msg, {"role": "user", "content": user_content}],
            "temperature": 0.2,
            "max_tokens": 500,
        }
    ).encode()

    req = urllib.request.Request(
        f"{OPENROUTER_BASE}/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": OPENROUTER_REFERER,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read())
        raw = data["choices"][0]["message"]["content"].strip()
        return json.loads(_clean_json(raw))
    except json.JSONDecodeError:
        return {
            "nodes": [],
            "summary": f"parse error: {raw[:100] if 'raw' in dir() else '?'}",
        }
    except Exception as e:
        return {"nodes": [], "summary": f"API error: {e}"}


# ── Node deposit ──────────────────────────────────────────────────────────────


def _deposit_nodes(nodes: list, cortex: Cortex, book_title: str, chunk_pos: int) -> int:
    """Deposit extracted nodes. Returns count successfully deposited."""
    deposited = 0
    for node in nodes:
        try:
            ntype = node.get("type", "factual").strip().lower()
            narrative = node.get("narrative", "").strip()
            confidence = float(node.get("confidence", 0.6))
            parent_cp = node.get("parent_cp", "").strip()
            trigger = node.get("trigger", "").strip()

            if not narrative or confidence < 0.60:
                continue

            mt = {
                "procedural": MemoryType.PROCEDURAL,
                "factual": MemoryType.FACTUAL,
                "interpretive": MemoryType.INTERPRETIVE,
            }.get(ntype, MemoryType.FACTUAL)

            uid = f"BL_{str(uuid.uuid4())[:8].upper()}"
            meta = {
                "source": "book_learner",
                "book": book_title[:60],
                "chunk_position": chunk_pos,
            }
            if trigger:
                meta["trigger"] = trigger

            mem = Memory(
                id=uid,
                narrative=narrative,
                memory_type=mt,
                source="book_learner",
                confidence=confidence,
                context_of_encoding=f"book_learner|{ntype}|{book_title[:40]}",
                metadata=meta,
            )
            cortex.store(mem)

            if parent_cp and parent_cp.startswith("CP"):
                try:
                    cortex.add_child(parent_cp, uid)
                except Exception:
                    pass

            deposited += 1
        except Exception as e:
            print(f"    [deposit error] {e}")
    return deposited


# ── Word graph training ────────────────────────────────────────────────────────


def _train_word_graph(chunk_text: str) -> None:
    """Train the word graph from this chunk. Silently skips if unavailable."""
    try:
        wg_db = Path.home() / ".TheIgors" / "word_graph.db"
        if not wg_db.exists():
            return
        from igor.cognition.word_graph import WordGraph

        wg = WordGraph(str(wg_db))
        wg.train(chunk_text)
    except Exception:
        pass


# ── Main loop ─────────────────────────────────────────────────────────────────


def run(args) -> None:
    cortex = Cortex(DB_PATH)

    # ── Open book ─────────────────────────────────────────────────────────
    print(f"Opening book...")
    if args.url:
        from igor.tools.ebook_reader import open_book_url

        handle = open_book_url(args.url, title=args.title or args.url)
    elif args.calibre_id:
        handle = open_book(calibre_id=args.calibre_id, resume=False)
    else:
        handle = open_book(title=args.book, resume=False)

    if isinstance(handle, str):
        print(f"ERROR: {handle}")
        sys.exit(1)

    # open_book returns a serializable dict; the BookHandle lives in _HANDLE_CACHE
    book_title = handle["title"]
    book_key = f"{book_title}|{handle.get('calibre_id') or args.calibre_id or ''}"
    total_sentences = handle["total_sentences"]
    # hold onto the handle_key for read_chunk calls
    handle_key = handle["_handle_key"]

    print(f"Book: {book_title}")
    print(f"Author: {handle['author']}")
    print(f"Sentences: {total_sentences}")
    print(f"Chunk size: {args.chunk} sentences")
    print(
        f"Model: {'local Ollama (' + os.getenv('OLLAMA_LOCAL_MODEL','qwen2.5:7b') + ')' if args.local else args.model}"
    )
    print(f"Mode: {'DRY RUN' if not args.run else 'LIVE'}")

    # ── Checkpoint ────────────────────────────────────────────────────────
    progress = _load_progress(book_key)
    processed_positions = set(progress.get("processed_positions", []))
    total_deposited = progress.get("total_deposited", 0)

    # ── Console note: new book vs resume ───────────────────────────────────
    if processed_positions and args.resume:
        print(
            f'▶ Resuming absorption: "{book_title}" '
            f"({len(processed_positions)} chunks done, {total_deposited} nodes deposited)"
        )
    else:
        print(
            f"★ New book — starting absorption: \"{book_title}\" by {handle['author']}"
        )

    # ── Seek to start position ─────────────────────────────────────────────
    # Access the live BookHandle from cache for position management
    from igor.tools.ebook_reader import _HANDLE_CACHE

    live_handle = _HANDLE_CACHE.get(handle_key)
    if live_handle is None:
        print("ERROR: BookHandle not found in cache after open_book")
        sys.exit(1)

    if args.start:
        live_handle.position = args.start
        print(f"Starting at sentence {args.start}")
    print("─" * 60)

    chunks_done = 0
    chunks_skipped = 0
    errors = 0

    while True:
        pos = live_handle.position
        if pos >= total_sentences:
            break
        if args.limit and chunks_done >= args.limit:
            break

        # Read a chunk
        result = read_chunk(handle_key=handle_key, n=args.chunk)
        if result.get("error"):
            print(f"Read error: {result['error']}")
            break

        sentences = result["sentences"]
        new_pos = result["position"]
        chapter = result["chapter"]
        chapter_title = result.get("chapter_title", "")
        percent = result["percent"]
        at_end = result["at_end"]
        chunk_text = " ".join(sentences)

        chunk_label = (
            f"[{chunks_done+1:03d}] ch.{chapter} pos={pos}-{new_pos} ({percent:.0f}%)"
        )

        # Resume: skip if already processed
        if args.resume and pos in processed_positions:
            print(f"{chunk_label} SKIP (already processed)")
            chunks_skipped += 1
            if at_end:
                break
            continue

        if args.run:
            # Extract nodes — check cloud_ok override per chunk (D071: mode can change mid-book)
            use_local = _should_use_local(args.local)
            extraction = _extract_nodes(
                chunk_text, args.model, chapter_title, local=use_local
            )
            nodes = extraction.get("nodes", [])
            summary = extraction.get("summary", "")

            if "ERROR" in summary or "error" in summary.lower():
                print(f"{chunk_label} ERROR: {summary}")
                errors += 1
            else:
                n_dep = _deposit_nodes(nodes, cortex, book_title, pos)
                total_deposited += n_dep
                _train_word_graph(chunk_text)

                status = f"→ {n_dep} node(s)" if n_dep else "→ no nodes"
                print(f"{chunk_label} {status}  {summary[:60]}")

                # Save progress
                processed_positions.add(pos)
                progress["processed_positions"] = list(processed_positions)
                progress["total_deposited"] = total_deposited
                _save_progress(book_key, progress)

            if args.delay > 0:
                time.sleep(args.delay)
        else:
            # Dry run: just show what would happen
            print(f"{chunk_label} {chunk_text[:80].replace(chr(10), ' ')}...")

        chunks_done += 1
        if at_end:
            break

    # G-RL3: mark reading_list completed if we reached the end of the book
    _reached_end = (live_handle.position >= total_sentences) and not args.limit
    if args.run and _reached_end and args.calibre_id:
        try:
            import sqlite3 as _sqlite3

            _conn = _sqlite3.connect(str(DB_PATH))
            _conn.execute(
                "UPDATE reading_list SET status='completed', completed_at=datetime('now')"
                " WHERE source=? AND status IN ('in_progress','queued')",
                (f"calibre://{args.calibre_id}",),
            )
            _conn.commit()
            _conn.close()
            print(f"reading_list: calibre://{args.calibre_id} → completed")
        except Exception as _rl_e:
            print(f"reading_list update failed: {_rl_e}")

    print("─" * 60)
    if args.run:
        print(
            f"Done. {chunks_done} chunks processed. {total_deposited} total nodes deposited. {errors} errors."
        )
        print(f"Progress saved: {_progress_path(book_key)}")
    else:
        print(f"Dry run: {chunks_done} chunks would be processed.")
        print("Add --run to execute.")


def main():
    parser = argparse.ArgumentParser(
        description="Book learner — extract graph nodes from a book"
    )
    parser.add_argument("--book", default="", help="Book title (fuzzy search)")
    parser.add_argument(
        "--calibre-id", type=int, default=None, help="Exact Calibre book ID"
    )
    parser.add_argument("--url", default="", help="URL to fetch and learn (web source)")
    parser.add_argument("--title", default="", help="Title override for URL sources")
    parser.add_argument(
        "--chunk", type=int, default=15, help="Sentences per chunk (default 15)"
    )
    parser.add_argument(
        "--delay",
        type=float,
        default=1.5,
        help="Seconds between API calls (default 1.5)",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("BOOK_LEARNER_MODEL", "openai/gpt-4o-mini"),
        help="LLM model (default: BOOK_LEARNER_MODEL env or gpt-4o-mini)",
    )
    parser.add_argument(
        "--local",
        action="store_true",
        help="Use local Ollama instead of OpenRouter (free, no API cost)",
    )
    parser.add_argument(
        "--run",
        action="store_true",
        help="Actually call API and deposit (default: dry run)",
    )
    parser.add_argument(
        "--resume", action="store_true", help="Skip chunks already processed"
    )
    parser.add_argument(
        "--limit", type=int, default=0, help="Max chunks to process (0=all)"
    )
    parser.add_argument(
        "--start", type=int, default=0, help="Start at sentence position"
    )
    args = parser.parse_args()

    if not args.book and not args.calibre_id and not args.url:
        parser.error("Provide --book, --calibre-id, or --url")

    run(args)


if __name__ == "__main__":
    main()
