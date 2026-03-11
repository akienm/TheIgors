#!/usr/bin/env python3
"""
Hamlet reading comprehension test harness.
Tests local Ollama models on 5 fixed questions across 3 machine categories.

Usage:
  python3 hamlet_test.py [model] [host] [port] [machine_label]

Examples:
  python3 hamlet_test.py gemma3:1b localhost 11434 akiendelllinux
  python3 hamlet_test.py gemma3:1b akienyoga9i 11434 akienyoga9i
  python3 hamlet_test.py gemma3:1b akienyogai7 11434 akienyogai7
"""

import subprocess
import time
import json
import sys
import os
from datetime import datetime

# 5 fixed comprehension questions — plot, character, theme, quote, inference
QUESTIONS = [
    {
        "id": "Q1_plot",
        "q": "What does the ghost of Hamlet's father tell Hamlet in Act I?",
        "type": "plot"
    },
    {
        "id": "Q2_character",
        "q": "Describe Polonius's role in the play and his relationship to Ophelia.",
        "type": "character"
    },
    {
        "id": "Q3_theme",
        "q": "What is the central tension Hamlet faces throughout the play?",
        "type": "theme"
    },
    {
        "id": "Q4_quote",
        "q": "Who speaks the line 'To be, or not to be: that is the question' and in what context?",
        "type": "quote"
    },
    {
        "id": "Q5_inference",
        "q": "Why does Hamlet delay killing Claudius even after learning he murdered his father?",
        "type": "inference"
    },
]

# Minimal context excerpt — keeps prompt short enough for 1b models
HAMLET_EXCERPT = """[EXCERPT FROM HAMLET]

ACT I, SCENE V — The Ghost speaks to Hamlet:
Ghost: I am thy father's spirit, doomed for a certain term to walk the night...
       Know thou, noble youth,
       The serpent that did sting thy father's life
       Now wears his crown.
Hamlet: O my prophetic soul! My uncle!
Ghost: ...Thus was I, sleeping, by a brother's hand
       Of life, of crown, of queen, at once dispatched.

ACT III, SCENE I — Hamlet's soliloquy:
Hamlet: To be, or not to be: that is the question:
        Whether 'tis nobler in the mind to suffer
        The slings and arrows of outrageous fortune,
        Or to take arms against a sea of troubles,
        And by opposing end them?

[Polonius is a courtier and chief counsellor to King Claudius. He is the father of Laertes and Ophelia.]
[Hamlet delays killing Claudius throughout the play due to moral doubt, desire for certainty, and philosophical paralysis.]
"""


def ask_ollama(model: str, question: str, host: str = "localhost", port: int = 11434) -> dict:
    """Send a question to Ollama and return response + timing."""
    prompt = f"""You are answering questions about Shakespeare's Hamlet. Use the excerpt below to help answer.

{HAMLET_EXCERPT}

Question: {question}

Answer concisely in 2-4 sentences."""

    payload = json.dumps({
        "model": model,
        "prompt": prompt,
        "stream": False,
        "options": {"temperature": 0.1, "num_predict": 200}
    })

    start = time.time()
    try:
        result = subprocess.run(
            ["curl", "-s", "-X", "POST",
             f"http://{host}:{port}/api/generate",
             "-H", "Content-Type: application/json",
             "-d", payload],
            capture_output=True, text=True, timeout=120
        )
        elapsed = time.time() - start

        if result.returncode != 0:
            return {"error": result.stderr, "latency_s": elapsed}

        data = json.loads(result.stdout)
        return {
            "response": data.get("response", ""),
            "latency_s": round(elapsed, 2),
            "tokens_per_s": round(data.get("eval_count", 0) / max(elapsed, 0.001), 1),
            "eval_count": data.get("eval_count", 0)
        }
    except subprocess.TimeoutExpired:
        return {"error": "TIMEOUT", "latency_s": 120}
    except Exception as e:
        return {"error": str(e), "latency_s": time.time() - start}


def run_test(model: str, host: str = "localhost", port: int = 11434, machine_label: str = "local"):
    """Run all 5 questions against a model and print results."""
    print(f"\n{'='*60}")
    print(f"MODEL: {model}  |  MACHINE: {machine_label}  |  {datetime.now().strftime('%H:%M:%S')}")
    print(f"{'='*60}")

    results = []
    for q in QUESTIONS:
        print(f"\n[{q['id']}] {q['q']}")
        r = ask_ollama(model, q['q'], host, port)
        if "error" in r:
            print(f"  ERROR: {r['error']}  ({r['latency_s']}s)")
        else:
            print(f"  → {r['response'][:300]}{'...' if len(r['response']) > 300 else ''}")
            print(f"  timing: {r['latency_s']}s  |  {r['tokens_per_s']} tok/s")
        results.append({"question": q, "result": r})

    # Save to log
    log = {
        "timestamp": datetime.now().isoformat(),
        "model": model,
        "machine": machine_label,
        "host": host,
        "port": port,
        "results": results
    }
    safe_model = model.replace(":", "_").replace("/", "_")
    log_path = f"/home/akien/TheIgors/workspace/hamlet_{machine_label}_{safe_model}.json"
    with open(log_path, "w") as f:
        json.dump(log, f, indent=2)
    print(f"\nResults saved: {log_path}")
    return results


if __name__ == "__main__":
    model = sys.argv[1] if len(sys.argv) > 1 else "gemma3:1b"
    host = sys.argv[2] if len(sys.argv) > 2 else "localhost"
    port = int(sys.argv[3]) if len(sys.argv) > 3 else 11434
    label = sys.argv[4] if len(sys.argv) > 4 else host

    run_test(model, host, port, label)
