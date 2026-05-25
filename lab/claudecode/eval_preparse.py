#!/usr/bin/env python3
"""
eval_preparse.py — G23: Eval harness for CSB preparse quality.

Tests both the rule-based fallback (_rule_based_csb) and thalamus._classify_intent
against a labeled ground-truth set covering all 13 intents.

Usage:
  python claudecode/eval_preparse.py            # rule-based only (no Ollama needed)
  python claudecode/eval_preparse.py --ollama   # also test LLM preparse (Ollama must be running)

Output: per-intent accuracy table + confusion matrix rows for misses.
"""

import argparse
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent
sys.path.insert(0, str(REPO))

from devices.igor.cognition.reasoners.ollama_reasoner import _rule_based_csb, parse_preparse_csb
from devices.igor.cognition.thalamus import Thalamus

_thalamus = Thalamus()

# ── Ground-truth labeled examples ────────────────────────────────────────────
# Format: (input_text, expected_intent, expected_tone, expected_complexity)
# complexity is "low" / "medium" / "high"; tone is advisory (not strict-checked here)

EXAMPLES = [
    # greeting (5)
    ("Hello Igor!", "greeting", "friendly", "low"),
    ("Good morning!", "greeting", "friendly", "low"),
    ("Hey, how are you doing today?", "greeting", "friendly", "low"),
    ("Hi there", "greeting", "friendly", "low"),
    ("Howdy partner", "greeting", "friendly", "low"),

    # meta_question (4)
    ("How do you work?", "meta_question", "curious", "low"),
    ("What are you exactly?", "meta_question", "curious", "low"),
    ("Tell me about yourself", "meta_question", "friendly", "low"),
    ("What can you do?", "meta_question", "curious", "low"),

    # memory_instruction (4)
    ("Remember that my meeting is on Friday", "memory_instruction", "neutral", "low"),
    ("Note that I prefer dark mode", "memory_instruction", "neutral", "low"),
    ("Learn that Leah likes tea", "memory_instruction", "neutral", "low"),
    ("Save this: my laptop password is in keepass", "memory_instruction", "neutral", "low"),

    # code_task (4)
    ("Write code to parse a CSV file", "code_task", "neutral", "medium"),
    ("Debug this function — it's returning None", "code_task", "neutral", "medium"),
    ("Implement a binary search algorithm", "code_task", "neutral", "medium"),
    ("Refactor the cortex.py search method", "code_task", "neutral", "medium"),

    # analysis_task (4)
    ("Analyze the logs and tell me what went wrong", "analysis_task", "neutral", "medium"),
    ("Compare these two implementations", "analysis_task", "neutral", "medium"),
    ("Review my memory schema for gaps", "analysis_task", "curious", "medium"),
    ("Summarize everything we've built this week", "analysis_task", "neutral", "medium"),

    # explanation_request (4)
    ("How does the thalamus work?", "explanation_request", "curious", "low"),
    ("Explain why the habit score is capped at 0.70", "explanation_request", "curious", "medium"),
    ("Walk me through the tier ladder", "explanation_request", "curious", "medium"),
    ("Why did you escalate to tier.4?", "explanation_request", "curious", "low"),

    # factual_question (4)
    ("What is the capital of France?", "factual_question", "curious", "low"),
    ("What's the default value of IGOR_MAX_TURNS?", "factual_question", "curious", "low"),
    ("When did we implement the word graph?", "factual_question", "curious", "low"),
    ("Who invented the transformer architecture?", "factual_question", "curious", "low"),

    # action_request (4)
    ("Search for recent papers on cognitive architectures", "action_request", "neutral", "medium"),
    ("Find all Python files that import cortex", "action_request", "neutral", "medium"),
    ("Run the syntax check on main.py", "action_request", "neutral", "low"),
    ("Browse the latest GitHub issues", "action_request", "neutral", "medium"),

    # complaint (4)
    ("This is broken — the habit score is wrong", "complaint", "frustrated", "medium"),
    ("It's not working again", "complaint", "frustrated", "low"),
    ("The embedding search doesn't find anything relevant", "complaint", "frustrated", "medium"),
    ("That's frustrating, it keeps failing", "complaint", "frustrated", "low"),

    # command (3)
    ("/help", "command", "neutral", "low"),
    ("/status", "command", "neutral", "low"),
    ("/metrics show", "command", "neutral", "low"),

    # conversation (4)
    ("What do you think about the Centering Theory connection?", "conversation", "curious", "medium"),
    ("I find the milieu model really interesting", "conversation", "friendly", "medium"),
    ("Do you agree that prediction is the core of cognition?", "conversation", "curious", "medium"),
    ("That's an interesting idea, tell me more", "conversation", "friendly", "medium"),

    # creative_request (4)
    ("Read me a short story", "creative_request", "friendly", "medium"),
    ("Tell me a story about a brave robot", "creative_request", "friendly", "medium"),
    ("Read aloud from where we left off", "creative_request", "friendly", "low"),
    ("Write me a poem about memory", "creative_request", "friendly", "medium"),

    # general (3)
    ("fjkd skdjf something random", "general", "neutral", "low"),
    ("maybe later", "general", "neutral", "low"),
    ("let's see what happens", "general", "neutral", "low"),
]


def run_rule_based(examples):
    correct = 0
    misses = []
    by_intent: dict[str, dict] = {}

    for text, expected_intent, _tone, _complexity in examples:
        csb = _rule_based_csb(text, habits=[])
        parsed = parse_preparse_csb(csb, habits=[])
        got = parsed["intent"]

        if expected_intent not in by_intent:
            by_intent[expected_intent] = {"total": 0, "correct": 0}
        by_intent[expected_intent]["total"] += 1

        if got == expected_intent:
            correct += 1
            by_intent[expected_intent]["correct"] += 1
        else:
            misses.append((text[:60], expected_intent, got))

    return correct, misses, by_intent


def run_thalamus(examples):
    correct = 0
    misses = []
    by_intent: dict[str, dict] = {}

    for text, expected_intent, _tone, _complexity in examples:
        parsed = _thalamus.process(text)
        got = parsed.intent

        if expected_intent not in by_intent:
            by_intent[expected_intent] = {"total": 0, "correct": 0}
        by_intent[expected_intent]["total"] += 1

        if got == expected_intent:
            correct += 1
            by_intent[expected_intent]["correct"] += 1
        else:
            misses.append((text[:60], expected_intent, got))

    return correct, misses, by_intent


def run_ollama_preparse(examples):
    from devices.igor.cognition.reasoners.ollama_reasoner import preparse

    correct = 0
    misses = []
    by_intent: dict[str, dict] = {}

    for text, expected_intent, _tone, _complexity in examples:
        csb = preparse(text, habits=[])
        parsed = parse_preparse_csb(csb, habits=[])
        got = parsed["intent"]

        if expected_intent not in by_intent:
            by_intent[expected_intent] = {"total": 0, "correct": 0}
        by_intent[expected_intent]["total"] += 1

        if got == expected_intent:
            correct += 1
            by_intent[expected_intent]["correct"] += 1
        else:
            misses.append((text[:60], expected_intent, got))

    return correct, misses, by_intent


def print_report(label, correct, misses, by_intent, total):
    print(f"\n{'='*60}")
    print(f"  {label}")
    print(f"{'='*60}")
    print(f"  Overall: {correct}/{total}  ({100*correct//total}%)")
    print()
    print(f"  {'Intent':<22} {'Correct':>7} {'Total':>6} {'%':>5}")
    print(f"  {'-'*22} {'-'*7} {'-'*6} {'-'*5}")
    for intent in sorted(by_intent):
        d = by_intent[intent]
        pct = 100 * d["correct"] // d["total"] if d["total"] else 0
        flag = " !" if pct < 75 else ""
        print(f"  {intent:<22} {d['correct']:>7} {d['total']:>6} {pct:>4}%{flag}")

    if misses:
        print()
        print(f"  Misses ({len(misses)}):")
        for text, expected, got in misses:
            print(f"    [{expected:>20} → {got:<20}]  \"{text}\"")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--ollama", action="store_true", help="Also test LLM preparse via Ollama")
    args = parser.parse_args()

    total = len(EXAMPLES)
    print(f"G23 Preparse Eval Harness — {total} labeled examples, 13 intents")

    # Rule-based fallback
    correct, misses, by_intent = run_rule_based(EXAMPLES)
    print_report("_rule_based_csb (pure Python fallback)", correct, misses, by_intent, total)

    # Thalamus
    correct, misses, by_intent = run_thalamus(EXAMPLES)
    print_report("thalamus._classify_intent (rule-based, production path)", correct, misses, by_intent, total)

    # Ollama LLM preparse (optional)
    if args.ollama:
        from devices.igor.cognition.reasoners.ollama_reasoner import is_healthy
        if not is_healthy():
            print("\n[SKIP] Ollama not running — skipping LLM preparse test")
        else:
            print("\n[Running Ollama preparse — this may take ~30s...]")
            correct, misses, by_intent = run_ollama_preparse(EXAMPLES)
            print_report("Ollama preparse (LLM, 1B model)", correct, misses, by_intent, total)

    print()


if __name__ == "__main__":
    main()
