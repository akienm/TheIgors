#!/usr/bin/env python3
"""
Igor Model Benchmarking Framework (#138)

Runs a standardised question set against one or more Ollama models and writes
structured results. Uses a Shakespeare corpus (Macbeth) fetched from Project
Gutenberg — a well-known, copyright-free text covering factual retrieval,
comprehension, instruction-following, and reasoning task classes.

Two test regimes:
  fast      — 8 questions, ~1-3 min/model  — interactive latency focus
  overnight — 25 questions, ~10-20 min/model — quality/depth focus

The 14B model (qwen2.5:14b) is treated as the quality reference baseline.
When it is included in a run its median latency anchors the relative speed table.

NOTE: The original benchmark example on akienyoga9i was built around a 17B model.
That machine is the reference point for "what quality looks like" — 14B (qwen2.5:14b)
is our available proxy. Adapt REFERENCE_MODEL once the 17B baseline is recovered.

Usage:
    python benchmarks/benchmark.py
    python benchmarks/benchmark.py --models llama3.2:1b qwen2.5:14b
    python benchmarks/benchmark.py --regime overnight --host localhost:11434
    python benchmarks/benchmark.py --list-models
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

# ── Configuration ─────────────────────────────────────────────────────────────

_GUTENBERG_MACBETH = "https://www.gutenberg.org/cache/epub/1533/pg1533.txt"
CORPUS_CACHE  = Path(__file__).parent / "corpus" / "macbeth.txt"
RESULTS_DIR   = Path(__file__).parent / "results"
REFERENCE_MODEL = "qwen2.5:14b"    # 14B = quality reference baseline

# ── Context excerpts (short passages injected for comprehension questions) ─────

_EXCERPTS: dict[str, str] = {
    "witches_opening": (
        "Thunder and lightning. Enter three Witches.\n"
        "First Witch: When shall we three meet again?\n"
        "In thunder, lightning, or in rain?\n"
        "Second Witch: When the hurlyburly's done,\n"
        "When the battle's lost and won.\n"
        "Third Witch: That will be ere the set of sun.\n"
        "First Witch: Where the place? Second Witch: Upon the heath.\n"
        "Third Witch: There to meet with Macbeth.\n"
        "All: Fair is foul, and foul is fair:\n"
        "Hover through the fog and filthy air."
    ),
    "dagger_soliloquy": (
        "Is this a dagger which I see before me,\n"
        "The handle toward my hand? Come, let me clutch thee.\n"
        "I have thee not, and yet I see thee still.\n"
        "Art thou not, fatal vision, sensible\n"
        "To feeling as to sight? Or art thou but\n"
        "A dagger of the mind, a false creation,\n"
        "Proceeding from the heat-oppressed brain?\n"
        "I see thee yet, in form as palpable\n"
        "As this which now I draw.\n"
        "Thou marshall'st me the way that I was going;\n"
        "And such an instrument I was to use."
    ),
    "banquet_scene": (
        "Macbeth: Which of you have done this?\n"
        "Lords: What, my good lord?\n"
        "Macbeth: Thou canst not say I did it: never shake\n"
        "Thy gory locks at me.\n"
        "Ross: Gentlemen, rise: his highness is not well.\n"
        "Lady Macbeth: Sit, worthy friends: my lord is often thus,\n"
        "And hath been from his youth: pray you, keep seat;\n"
        "The fit is momentary; upon a thought\n"
        "He will again be well: if much you note him,\n"
        "You shall offend him and extend his passion:\n"
        "Feed, and regard him not."
    ),
    "sleepwalking": (
        "Enter Lady Macbeth, with a taper.\n"
        "Lady Macbeth: Out, damned spot! out, I say!\n"
        "One: two: why, then 'tis time to do't.\n"
        "Hell is murky! Fie, my lord, fie! a soldier, and afeard?\n"
        "What need we fear who knows it, when none can call our power to account?\n"
        "Yet who would have thought the old man to have had so much blood in him.\n"
        "The Thane of Fife had a wife: where is she now?\n"
        "What, will these hands ne'er be clean?\n"
        "No more o' that, my lord, no more o' that:\n"
        "you mar all with this starting."
    ),
}

# ── Question sets ─────────────────────────────────────────────────────────────
# Each question: id, type, text, and optionally context_tag (→ excerpt injected)
# Types: factual | comprehension | instruction | reasoning | speed

_Q_FAST: list[dict] = [
    # Factual — tests training knowledge, no context supplied
    {"id": "f1", "type": "factual",
     "text": "Who is the king of Scotland at the start of Macbeth? Answer in one sentence."},
    {"id": "f2", "type": "factual",
     "text": "What do the three witches say to Macbeth when they first meet? Summarize in one sentence."},
    {"id": "f3", "type": "factual",
     "text": "How does Lady Macbeth die? One sentence."},
    # Comprehension — excerpt supplied inline
    {"id": "c1", "type": "comprehension", "context_tag": "witches_opening",
     "text": "Based only on the passage above: what atmosphere does it establish? Two sentences."},
    {"id": "c2", "type": "comprehension", "context_tag": "dagger_soliloquy",
     "text": "Based only on the passage above: what is Macbeth experiencing and why is it significant? Two sentences."},
    # Instruction-following
    {"id": "i1", "type": "instruction",
     "text": "List exactly three themes in Macbeth as a numbered list. No other text."},
    {"id": "i2", "type": "instruction",
     "text": "Write a one-sentence plot summary of Macbeth suitable for a 10-year-old."},
    # Reasoning
    {"id": "r1", "type": "reasoning",
     "text": "Who bears more moral responsibility for Duncan's murder — Macbeth or Lady Macbeth? Give a two-sentence argument."},
]

_Q_OVERNIGHT: list[dict] = _Q_FAST + [
    {"id": "f4", "type": "factual",
     "text": "What is the 'Tomorrow and tomorrow and tomorrow' speech about? One paragraph."},
    {"id": "f5", "type": "factual",
     "text": "Name all of Macbeth's victims in order. Numbered list only."},
    {"id": "f6", "type": "factual",
     "text": "What is the significance of Birnam Wood coming to Dunsinane? Two sentences."},
    {"id": "c3", "type": "comprehension", "context_tag": "banquet_scene",
     "text": "Based only on the passage above: what does Macbeth's behaviour reveal about his mental state? Two sentences."},
    {"id": "c4", "type": "comprehension", "context_tag": "sleepwalking",
     "text": "Based only on the passage above: what guilt is Lady Macbeth revealing? Two sentences."},
    {"id": "i3", "type": "instruction",
     "text": "Write a haiku about ambition using imagery from Macbeth."},
    {"id": "i4", "type": "instruction",
     "text": "Translate to modern English: 'Is this a dagger which I see before me, the handle toward my hand?' One sentence."},
    {"id": "r2", "type": "reasoning",
     "text": "How does appearance vs reality manifest in Macbeth? Give three specific examples as bullet points."},
    {"id": "r3", "type": "reasoning",
     "text": "What does Macbeth suggest about the relationship between power and morality? One paragraph."},
    {"id": "r4", "type": "reasoning",
     "text": "Compare Macbeth's arc to a cautionary tale about ambition. Two sentences."},
    # Speed tests — minimal expected output, maximise latency signal
    {"id": "s1", "type": "speed", "text": "Who wrote Macbeth? One word."},
    {"id": "s2", "type": "speed", "text": "In what century was Macbeth first performed? One word."},
    {"id": "s3", "type": "speed", "text": "Name one witch from Macbeth. One word."},
    {"id": "s4", "type": "speed", "text": "What is Macbeth's title at the start of the play? Two words max."},
    {"id": "s5", "type": "speed",
     "text": "Complete this quote with one word: 'Double, double toil and ___'"},
]

_REGIMES: dict[str, list[dict]] = {
    "fast":      _Q_FAST,
    "overnight": _Q_OVERNIGHT,
}

# ── OpenRouter client ─────────────────────────────────────────────────────────

def or_generate(model: str, prompt: str, api_key: str,
                timeout: int = 60) -> dict[str, Any]:
    """Call OpenRouter /chat/completions. Returns timing + response."""
    payload = json.dumps({
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "temperature": 0.0,
        "max_tokens": 512,
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions",
        data=payload,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    wall_ms = int((time.time() - t0) * 1000)
    text = data["choices"][0]["message"]["content"].strip()
    usage = data.get("usage", {})
    return {
        "response":    text,
        "eval_count":  usage.get("completion_tokens", 0),
        "eval_ms":     wall_ms,
        "wall_ms":     wall_ms,
        "tok_per_sec": round(usage.get("completion_tokens", 0) / (wall_ms / 1000), 1) if wall_ms > 0 else 0.0,
        "done":        True,
    }


def run_or_model(model: str, api_key: str, questions: list[dict],
                 timeout: int = 60) -> dict:
    """Run all questions against one OpenRouter model."""
    print(f"\n  ── {model} (cloud) ──")
    results = []
    for q in questions:
        sys.stdout.write(f"    [{q['id']:3s}] {q['type'][:6]:6s}  ")
        sys.stdout.flush()
        try:
            r = or_generate(model, build_prompt(q), api_key, timeout=timeout)
            results.append({
                "question_id": q["id"],
                "type":        q["type"],
                "question":    q["text"][:120],
                "response":    r["response"][:600],
                "wall_ms":     r["wall_ms"],
                "eval_ms":     r["eval_ms"],
                "eval_count":  r["eval_count"],
                "tok_per_sec": r["tok_per_sec"],
                "error":       None,
            })
            print(f"{r['wall_ms']:>6}ms  {r['tok_per_sec']:>6.1f} tok/s  "
                  f"{r['response'][:60].replace(chr(10),' ')}")
        except Exception as exc:
            results.append({
                "question_id": q["id"], "type": q["type"],
                "question": q["text"][:120], "response": "",
                "wall_ms": None, "eval_ms": None, "eval_count": 0,
                "tok_per_sec": 0.0, "error": str(exc),
            })
            print(f"  ERROR: {exc}")

    latencies = sorted(r["wall_ms"] for r in results if r["wall_ms"] is not None)
    tok_rates  = [r["tok_per_sec"] for r in results if r["tok_per_sec"]]
    summary = {
        "questions_run":   len(results),
        "errors":          sum(1 for r in results if r["error"]),
        "median_wall_ms":  _percentile(latencies, 50),
        "p95_wall_ms":     _percentile(latencies, 95),
        "min_wall_ms":     latencies[0]  if latencies else None,
        "max_wall_ms":     latencies[-1] if latencies else None,
        "avg_tok_per_sec": round(sum(tok_rates) / len(tok_rates), 1) if tok_rates else 0.0,
    }
    return {"model": model, "host": "openrouter", "results": results, "summary": summary}


# ── Ollama client ─────────────────────────────────────────────────────────────

def ollama_generate(host: str, model: str, prompt: str,
                    timeout: int = 120) -> dict[str, Any]:
    """Call Ollama /api/generate (non-streaming). Returns timing + response."""
    url = f"http://{host}/api/generate"
    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.0, "seed": 42},   # deterministic
    }).encode()
    req = urllib.request.Request(
        url, data=payload, headers={"Content-Type": "application/json"}
    )
    t0 = time.time()
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = json.loads(resp.read())
    wall_ms = int((time.time() - t0) * 1000)
    # Ollama reports eval_duration in nanoseconds
    eval_ms    = data.get("eval_duration", 0) // 1_000_000
    eval_count = data.get("eval_count", 0)
    tok_per_sec = round(eval_count / (eval_ms / 1000), 1) if eval_ms > 0 else 0.0
    return {
        "response":     data.get("response", "").strip(),
        "eval_count":   eval_count,
        "eval_ms":      eval_ms,
        "wall_ms":      wall_ms,
        "tok_per_sec":  tok_per_sec,
        "done":         data.get("done", False),
    }


def ollama_list_models(host: str) -> list[str]:
    """Return model tags available on an Ollama host."""
    try:
        with urllib.request.urlopen(f"http://{host}/api/tags", timeout=10) as r:
            return [m["name"] for m in json.loads(r.read()).get("models", [])]
    except Exception:
        return []

# ── Corpus ────────────────────────────────────────────────────────────────────

def fetch_corpus(url: str, cache: Path, skip_fetch: bool = False) -> str:
    """Return corpus text, fetching from URL if not already cached locally."""
    if cache.exists():
        return cache.read_text(encoding="utf-8", errors="replace")
    if skip_fetch:
        return ""
    print(f"  Fetching corpus ... ", end="", flush=True)
    cache.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(url, timeout=30) as resp:
        text = resp.read().decode("utf-8", errors="replace")
    cache.write_text(text, encoding="utf-8")
    print(f"{len(text) // 1024} KB cached to {cache}")
    return text

# ── Prompt builder ────────────────────────────────────────────────────────────

def build_prompt(q: dict) -> str:
    ctx_tag = q.get("context_tag")
    if ctx_tag:
        excerpt = _EXCERPTS.get(ctx_tag, "")
        return f"Read the following passage from Macbeth:\n\n{excerpt}\n\n{q['text']}"
    return q["text"]

# ── Per-model runner ──────────────────────────────────────────────────────────

def _percentile(sorted_vals: list[float], p: int) -> float | None:
    if not sorted_vals:
        return None
    idx = max(0, min(int(len(sorted_vals) * p / 100), len(sorted_vals) - 1))
    return sorted_vals[idx]


def run_model(host: str, model: str, questions: list[dict],
              timeout: int = 120) -> dict:
    """Run all questions against one model. Returns structured result dict."""
    print(f"\n  ── {model} ──")
    results = []
    for q in questions:
        sys.stdout.write(f"    [{q['id']:3s}] {q['type'][:6]:6s}  ")
        sys.stdout.flush()
        try:
            r = ollama_generate(host, model, build_prompt(q), timeout=timeout)
            results.append({
                "question_id": q["id"],
                "type":        q["type"],
                "question":    q["text"][:120],
                "response":    r["response"][:600],
                "wall_ms":     r["wall_ms"],
                "eval_ms":     r["eval_ms"],
                "eval_count":  r["eval_count"],
                "tok_per_sec": r["tok_per_sec"],
                "error":       None,
            })
            print(f"{r['wall_ms']:>6}ms  {r['tok_per_sec']:>6.1f} tok/s  "
                  f"{r['response'][:60].replace(chr(10),' ')}")
        except Exception as exc:
            results.append({
                "question_id": q["id"],
                "type":        q["type"],
                "question":    q["text"][:120],
                "response":    "",
                "wall_ms":     None,
                "eval_ms":     None,
                "eval_count":  0,
                "tok_per_sec": 0.0,
                "error":       str(exc),
            })
            print(f"  ERROR: {exc}")

    latencies = sorted(r["wall_ms"] for r in results if r["wall_ms"] is not None)
    tok_rates = [r["tok_per_sec"] for r in results if r["tok_per_sec"]]
    errors    = sum(1 for r in results if r["error"])

    summary = {
        "questions_run":  len(results),
        "errors":         errors,
        "median_wall_ms": _percentile(latencies, 50),
        "p95_wall_ms":    _percentile(latencies, 95),
        "min_wall_ms":    latencies[0]  if latencies else None,
        "max_wall_ms":    latencies[-1] if latencies else None,
        "avg_tok_per_sec": round(sum(tok_rates) / len(tok_rates), 1) if tok_rates else 0.0,
    }
    return {"model": model, "host": host, "results": results, "summary": summary}

# ── Reporter ──────────────────────────────────────────────────────────────────

def save_results(run: dict, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    ts   = run["run_id"].replace(":", "-").replace("T", "_")
    path = output_dir / f"bench_{ts}.json"
    path.write_text(json.dumps(run, indent=2), encoding="utf-8")
    return path


def print_summary(run: dict):
    models = run["models"]
    if not models:
        return
    print(f"\n{'─'*80}")
    print(f"Benchmark: {run['corpus']}  regime={run['regime']}  "
          f"questions={run['question_count']}  host={run['host']}")
    print(f"{'─'*80}")
    hdr = f"  {'Model':<32} {'Median':>8} {'P95':>8} {'Min':>7} {'Max':>7} {'tok/s':>7}  Errors"
    print(hdr)
    print(f"  {'─'*32} {'─'*8} {'─'*8} {'─'*7} {'─'*7} {'─'*7}  {'─'*6}")

    ref_ms = None
    for m in models:
        s  = m["summary"]
        is_ref = REFERENCE_MODEL in m["model"]
        marker = " ★" if is_ref else ""
        if is_ref and s["median_wall_ms"]:
            ref_ms = s["median_wall_ms"]

        def _fmt(v):
            return f"{v}ms" if v is not None else "n/a"

        print(f"  {m['model'][:32]:<32} "
              f"{_fmt(s['median_wall_ms']):>8} "
              f"{_fmt(s['p95_wall_ms']):>8} "
              f"{_fmt(s['min_wall_ms']):>7} "
              f"{_fmt(s['max_wall_ms']):>7} "
              f"{s['avg_tok_per_sec']:>7.1f}  "
              f"{s['errors']}{marker}")

    if ref_ms and len(models) > 1:
        print(f"\n  Relative latency (★ = {REFERENCE_MODEL}, {ref_ms}ms baseline):")
        for m in models:
            if m["summary"]["median_wall_ms"]:
                ratio = m["summary"]["median_wall_ms"] / ref_ms
                bar   = "█" * min(int(ratio * 10), 40)
                print(f"    {m['model'][:28]:<28}  {ratio:.2f}x  {bar}")
    print()

# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--models", nargs="+", default=None,
                    help="Ollama model tags (default: auto-discover from host)")
    ap.add_argument("--regime", choices=list(_REGIMES), default="fast",
                    help="Question set: fast (8q) or overnight (25q)")
    ap.add_argument("--host", default="localhost:11434",
                    help="Ollama host:port")
    ap.add_argument("--output", type=Path, default=RESULTS_DIR,
                    help="Output directory for results JSON")
    ap.add_argument("--corpus", type=Path, default=None,
                    help="Use this local corpus file instead of auto-fetch")
    ap.add_argument("--no-fetch", action="store_true",
                    help="Skip Gutenberg fetch; use cached corpus only")
    ap.add_argument("--timeout", type=int, default=120,
                    help="Per-question timeout seconds (default 120)")
    ap.add_argument("--list-models", action="store_true",
                    help="Print available models on --host and exit")
    ap.add_argument("--or-models", nargs="+", default=None,
                    metavar="MODEL",
                    help="OpenRouter model IDs to include (uses OPENROUTER_API_KEY env var)")
    args = ap.parse_args()

    if args.list_models:
        available = ollama_list_models(args.host)
        if not available:
            print(f"No models found on {args.host} (is Ollama running?)")
            sys.exit(1)
        print(f"Models on {args.host}:")
        for m in available:
            note = "  ★ reference baseline" if REFERENCE_MODEL in m else ""
            print(f"  {m}{note}")
        return

    # Resolve model list
    models = args.models
    if not models:
        models = ollama_list_models(args.host)
        if not models:
            print(f"ERROR: no models found on {args.host}. Use --models or check Ollama.")
            sys.exit(1)
        print(f"Auto-discovered {len(models)} model(s): {', '.join(models)}")

    # Fetch corpus (used for context excerpts; also cached for inspection)
    corpus_path = args.corpus or CORPUS_CACHE
    fetch_corpus(_GUTENBERG_MACBETH, corpus_path, skip_fetch=args.no_fetch)
    corpus_label = corpus_path.stem if corpus_path else "macbeth"

    questions = _REGIMES[args.regime]
    print(f"\nStarting benchmark: regime={args.regime} ({len(questions)} questions), "
          f"host={args.host}, models={len(models)}")

    run: dict = {
        "run_id":         datetime.now().isoformat(timespec="seconds"),
        "corpus":         corpus_label,
        "regime":         args.regime,
        "question_count": len(questions),
        "host":           args.host,
        "models":         [],
    }

    for model in models:
        run["models"].append(run_model(args.host, model, questions, args.timeout))

    # Cloud models via OpenRouter
    if args.or_models:
        import os as _os
        or_key = _os.getenv("OPENROUTER_API_KEY", "")
        if not or_key:
            print("WARNING: --or-models specified but OPENROUTER_API_KEY not set — skipping cloud.")
        else:
            for model in args.or_models:
                run["models"].append(run_or_model(model, or_key, questions, args.timeout))

    out_path = save_results(run, args.output)
    print(f"\nResults saved → {out_path}")
    print_summary(run)


if __name__ == "__main__":
    main()
