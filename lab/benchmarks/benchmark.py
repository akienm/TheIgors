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

# ── Preparse benchmark (#191) ──────────────────────────────────────────────────
# Ground truth derived from thalamus._classify_intent() + _assess_complexity() rules.
# Intent taxonomy (13): greeting | meta_question | explanation_request | factual_question |
#   memory_instruction | action_request | code_task | analysis_task |
#   complaint | conversation | command | creative_request | general
# Complexity: low (≤6 words or greeting/command) | high (≥2 high signals) | medium (default)

_PREPARSE_INTENTS = (
    "greeting", "meta_question", "explanation_request", "factual_question",
    "memory_instruction", "action_request", "code_task", "analysis_task",
    "complaint", "conversation", "command", "creative_request", "general",
)

_Q_PREPARSE: list[dict] = [
    {"id": "p01",  "input": "hello there",
     "intent": "greeting",            "complexity": "low"},
    {"id": "p02",  "input": "how do you work?",
     "intent": "meta_question",       "complexity": "low"},
    {"id": "p03",  "input": "remember that I prefer concise replies",
     "intent": "memory_instruction",  "complexity": "low"},
    {"id": "p04",  "input": "write code to sort a list",
     "intent": "code_task",           "complexity": "low"},
    {"id": "p05",  "input": "explain how neural networks work",
     "intent": "explanation_request", "complexity": "low"},
    {"id": "p06",  "input": "what is the capital of France?",
     "intent": "factual_question",    "complexity": "medium"},
    {"id": "p07",  "input": "analyze the patterns in my recent conversations",
     "intent": "analysis_task",       "complexity": "medium"},
    {"id": "p08",  "input": "run the benchmark now",
     "intent": "action_request",      "complexity": "low"},
    {"id": "p09",  "input": "this code is not working correctly",
     "intent": "complaint",           "complexity": "low"},
    {"id": "p10",  "input": "what do you think about consciousness?",
     "intent": "conversation",        "complexity": "low"},
    {"id": "p11",  "input": "/help",
     "intent": "command",             "complexity": "low"},
    {"id": "p12",  "input": "tell me a story about a magical forest",
     "intent": "creative_request",    "complexity": "medium"},
    {"id": "p13",  "input": "what is the best way to learn Python?",
     "intent": "factual_question",    "complexity": "medium"},
    {"id": "p14",  "input": "compare themes in three Shakespeare plays, first identify key motifs then explain their modern relevance",
     "intent": "analysis_task",       "complexity": "high"},
    {"id": "p15",  "input": "debug this function and implement a complete fix, step by step",
     "intent": "code_task",           "complexity": "high"},
    {"id": "p16",  "input": "good morning",
     "intent": "greeting",            "complexity": "low"},
    {"id": "p17",  "input": "search for the latest AI news",
     "intent": "action_request",      "complexity": "low"},
    {"id": "p18",  "input": "things seem wrong and the output looks broken",
     "intent": "complaint",           "complexity": "medium"},
    {"id": "p19",  "input": "summarize the meeting notes and identify action items",
     "intent": "analysis_task",       "complexity": "medium"},
    {"id": "p20",  "input": "yes please",
     "intent": "general",             "complexity": "low"},
]

_PREPARSE_PROMPT_TPL = """\
You are an intent classifier for an AI assistant. Classify the user message below.

Valid intents: greeting | meta_question | explanation_request | factual_question | \
memory_instruction | action_request | code_task | analysis_task | \
complaint | conversation | command | creative_request | general

Complexity rules:
  low    — 6 words or fewer, greeting, or a single slash command
  high   — multi-step instruction, analytical depth keywords, or over 40 words
  medium — everything else

Respond ONLY in this exact format (two lines, no other text):
intent: <intent>
complexity: <low|medium|high>

User message: {input}"""


def _parse_preparse_response(text: str) -> tuple[str, str]:
    """Extract (intent, complexity) from a model's preparse response."""
    intent = "unknown"
    complexity = "unknown"
    for line in text.lower().splitlines():
        line = line.strip()
        if line.startswith("intent:"):
            val = line[7:].strip().strip('"\'')
            for known in _PREPARSE_INTENTS:
                if known in val:
                    intent = known
                    break
        elif line.startswith("complexity:"):
            val = line[11:].strip().strip('"\'')
            if "high" in val:
                complexity = "high"
            elif "low" in val:
                complexity = "low"
            elif "medium" in val:
                complexity = "medium"
    return intent, complexity


def run_preparse_model(host: str, model: str, timeout: int = 60) -> dict:
    """#191 Part 1: benchmark intent classification accuracy for one Ollama model."""
    print(f"\n  ── {model} (preparse) ──")
    results = []
    correct_intent = 0
    correct_both = 0

    for q in _Q_PREPARSE:
        sys.stdout.write(f"    [{q['id']}] preparse  ")
        sys.stdout.flush()
        prompt = _PREPARSE_PROMPT_TPL.format(input=q["input"])
        try:
            r = ollama_generate(host, model, prompt, timeout=timeout)
            pred_intent, pred_complexity = _parse_preparse_response(r["response"])
            intent_ok = pred_intent == q["intent"]
            both_ok = intent_ok and pred_complexity == q["complexity"]
            if intent_ok:
                correct_intent += 1
            if both_ok:
                correct_both += 1
            results.append({
                "id":                   q["id"],
                "input":                q["input"],
                "expected_intent":      q["intent"],
                "expected_complexity":  q["complexity"],
                "predicted_intent":     pred_intent,
                "predicted_complexity": pred_complexity,
                "intent_correct":       intent_ok,
                "both_correct":         both_ok,
                "wall_ms":              r["wall_ms"],
                "tok_per_sec":          r["tok_per_sec"],
                "error":                None,
            })
            status = "✓" if both_ok else ("~" if intent_ok else "✗")
            print(f"{r['wall_ms']:>6}ms  {status}  "
                  f"intent={pred_intent}/{q['intent']}  "
                  f"c={pred_complexity}/{q['complexity']}")
        except Exception as exc:
            results.append({
                "id": q["id"], "input": q["input"],
                "expected_intent": q["intent"], "expected_complexity": q["complexity"],
                "predicted_intent": "error", "predicted_complexity": "error",
                "intent_correct": False, "both_correct": False,
                "wall_ms": None, "tok_per_sec": 0.0, "error": str(exc),
            })
            print(f"  ERROR: {exc}")

    n = len(_Q_PREPARSE)
    intent_acc = round(correct_intent / n * 100, 1) if n else 0.0
    both_acc   = round(correct_both   / n * 100, 1) if n else 0.0
    latencies  = sorted(r["wall_ms"] for r in results if r["wall_ms"] is not None)
    tok_rates  = [r["tok_per_sec"] for r in results if r["tok_per_sec"]]
    print(f"    intent={intent_acc}%  intent+complexity={both_acc}%")
    return {
        "model":   model,
        "host":    host,
        "regime":  "preparse",
        "results": results,
        "summary": {
            "intent_accuracy_pct": intent_acc,
            "both_accuracy_pct":   both_acc,
            "correct_intent":      correct_intent,
            "correct_both":        correct_both,
            "questions_run":       n,
            "errors":              sum(1 for r in results if r["error"]),
            "median_wall_ms":      _percentile(latencies, 50),
            "avg_tok_per_sec":     round(sum(tok_rates) / len(tok_rates), 1) if tok_rates else 0.0,
        },
    }


def run_preparse_or_model(model: str, api_key: str, timeout: int = 60) -> dict:
    """#191: preparse benchmark for one OpenRouter model."""
    print(f"\n  ── {model} (preparse/cloud) ──")
    results = []
    correct_intent = 0
    correct_both = 0

    for q in _Q_PREPARSE:
        sys.stdout.write(f"    [{q['id']}] preparse  ")
        sys.stdout.flush()
        prompt = _PREPARSE_PROMPT_TPL.format(input=q["input"])
        try:
            r = or_generate(model, prompt, api_key, timeout=timeout)
            pred_intent, pred_complexity = _parse_preparse_response(r["response"])
            intent_ok = pred_intent == q["intent"]
            both_ok = intent_ok and pred_complexity == q["complexity"]
            if intent_ok:
                correct_intent += 1
            if both_ok:
                correct_both += 1
            results.append({
                "id":                   q["id"],
                "input":                q["input"],
                "expected_intent":      q["intent"],
                "expected_complexity":  q["complexity"],
                "predicted_intent":     pred_intent,
                "predicted_complexity": pred_complexity,
                "intent_correct":       intent_ok,
                "both_correct":         both_ok,
                "wall_ms":              r["wall_ms"],
                "tok_per_sec":          r["tok_per_sec"],
                "error":                None,
            })
            status = "✓" if both_ok else ("~" if intent_ok else "✗")
            print(f"{r['wall_ms']:>6}ms  {status}  "
                  f"intent={pred_intent}/{q['intent']}  "
                  f"c={pred_complexity}/{q['complexity']}")
        except Exception as exc:
            results.append({
                "id": q["id"], "input": q["input"],
                "expected_intent": q["intent"], "expected_complexity": q["complexity"],
                "predicted_intent": "error", "predicted_complexity": "error",
                "intent_correct": False, "both_correct": False,
                "wall_ms": None, "tok_per_sec": 0.0, "error": str(exc),
            })
            print(f"  ERROR: {exc}")

    n = len(_Q_PREPARSE)
    intent_acc = round(correct_intent / n * 100, 1) if n else 0.0
    both_acc   = round(correct_both   / n * 100, 1) if n else 0.0
    latencies  = sorted(r["wall_ms"] for r in results if r["wall_ms"] is not None)
    tok_rates  = [r["tok_per_sec"] for r in results if r["tok_per_sec"]]
    print(f"    intent={intent_acc}%  intent+complexity={both_acc}%")
    return {
        "model":   model,
        "host":    "openrouter",
        "regime":  "preparse",
        "results": results,
        "summary": {
            "intent_accuracy_pct": intent_acc,
            "both_accuracy_pct":   both_acc,
            "correct_intent":      correct_intent,
            "correct_both":        correct_both,
            "questions_run":       n,
            "errors":              sum(1 for r in results if r["error"]),
            "median_wall_ms":      _percentile(latencies, 50),
            "avg_tok_per_sec":     round(sum(tok_rates) / len(tok_rates), 1) if tok_rates else 0.0,
        },
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

# ── #191 Part 2: model promotion ──────────────────────────────────────────────

def promote_winner(run: dict, machines_json: Path) -> str | None:
    """
    #191 Part 2: After a preparse benchmark run, write the winning model
    (highest intent_accuracy_pct) to machines.json for this hostname.
    """
    import socket
    hostname = socket.gethostname()
    preparse_models = [m for m in run.get("models", []) if m.get("regime") == "preparse"]
    if not preparse_models:
        print("  --promote-winner: no preparse results to promote.")
        return None
    winner = max(preparse_models, key=lambda m: m["summary"].get("intent_accuracy_pct", 0))
    winning_model = winner["model"]
    accuracy = winner["summary"]["intent_accuracy_pct"]
    if not machines_json.exists():
        print(f"  --promote-winner: machines.json not found at {machines_json}")
        return None
    try:
        data = json.loads(machines_json.read_text(encoding="utf-8"))
        matched = False
        for machine in data.get("machines", []):
            if machine.get("hostname") == hostname:
                machine["ollama_model"] = winning_model
                machine["ollama_model_winner_accuracy"] = accuracy
                machine["ollama_model_winner_date"] = datetime.now().isoformat(timespec="seconds")
                matched = True
                break
        if not matched:
            print(f"  --promote-winner: hostname '{hostname}' not found in machines.json")
            return None
        machines_json.write_text(json.dumps(data, indent=2), encoding="utf-8")
        print(f"  Promoted {winning_model} ({accuracy}% accuracy) → {machines_json}/{hostname}")
        return winning_model
    except Exception as exc:
        print(f"  WARNING: could not update machines.json: {exc}")
        return None


def print_preparse_summary(run: dict) -> None:
    """Print accuracy table for a preparse benchmark run."""
    models = run["models"]
    if not models:
        return
    print(f"\n{'─'*80}")
    print(f"Preparse benchmark  regime=preparse  questions={len(_Q_PREPARSE)}")
    print(f"{'─'*80}")
    print(f"  {'Model':<32}  {'Intent%':>8}  {'Both%':>8}  {'Median':>8}  {'tok/s':>7}  Errors")
    print(f"  {'─'*32}  {'─'*8}  {'─'*8}  {'─'*8}  {'─'*7}  {'─'*6}")
    for m in models:
        s = m["summary"]
        def _fmt(v):
            return f"{v}ms" if v is not None else "n/a"
        print(f"  {m['model'][:32]:<32}  "
              f"{s['intent_accuracy_pct']:>7.1f}%  "
              f"{s['both_accuracy_pct']:>7.1f}%  "
              f"{_fmt(s['median_wall_ms']):>8}  "
              f"{s['avg_tok_per_sec']:>7.1f}  "
              f"{s['errors']}")
    print()


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    ap = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    ap.add_argument("--models", nargs="+", default=None,
                    help="Ollama model tags (default: auto-discover from host)")
    ap.add_argument("--regime", choices=list(_REGIMES) + ["preparse"], default="fast",
                    help="Question set: fast (8q), overnight (25q), or preparse (20q accuracy)")
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
    ap.add_argument("--promote-winner", action="store_true",
                    help="After preparse run, write best model to machines.json for this host")
    ap.add_argument("--machines-json", type=Path,
                    default=Path.home() / ".TheIgors/local/machines.json",
                    help="Path to machines.json (used with --promote-winner)")
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

    run: dict = {
        "run_id": datetime.now().isoformat(timespec="seconds"),
        "regime": args.regime,
        "host":   args.host,
        "models": [],
    }

    if args.regime == "preparse":
        # #191: accuracy benchmark — no corpus needed
        print(f"\nStarting preparse benchmark ({len(_Q_PREPARSE)} questions), "
              f"host={args.host}, models={len(models)}")
        run["question_count"] = len(_Q_PREPARSE)
        run["corpus"] = "preparse_ground_truth"
        for model in models:
            run["models"].append(run_preparse_model(args.host, model, args.timeout))
        if args.or_models:
            import os as _os
            or_key = _os.getenv("OPENROUTER_API_KEY", "")
            if not or_key:
                print("WARNING: --or-models specified but OPENROUTER_API_KEY not set — skipping.")
            else:
                for model in args.or_models:
                    run["models"].append(run_preparse_or_model(model, or_key, args.timeout))
        out_path = save_results(run, args.output)
        print(f"\nResults saved → {out_path}")
        print_preparse_summary(run)
        if args.promote_winner:
            promote_winner(run, args.machines_json)
    else:
        questions = _REGIMES[args.regime]
        print(f"\nStarting benchmark: regime={args.regime} ({len(questions)} questions), "
              f"host={args.host}, models={len(models)}")
        run["question_count"] = len(questions)
        run["corpus"] = corpus_label
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
