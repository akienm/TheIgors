#!/usr/bin/env python3
"""
audit_pass1_run.py — Kick off T-three-pass-audit Pass 1.

Assembles the repo payload, sends it to Gemini 2.5 Pro via OpenRouter with
the approved pass1 prompt, and saves the response to
lab/design_docs/audit_2026/pass1_output/.

Usage:
    python3 audit_pass1_run.py --dry-run      # assemble payload, show size, do not send
    python3 audit_pass1_run.py                # full run (sends to Gemini)
    python3 audit_pass1_run.py --max-payload-chars 2000000   # override size cap
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

REPO = Path("/home/akien/TheIgors")
PROMPT_FILE = REPO / "lab/design_docs/audit_2026/pass1_gemini_prompt.md"
OUTPUT_DIR = REPO / "lab/design_docs/audit_2026/pass1_output"

OR_BASE = "https://openrouter.ai/api/v1"
OR_MODEL = "google/gemini-2.5-pro"

# Include roots (relative to REPO)
# tests/ and lab/design_docs*/ dropped — Pass 1 fits 1M budget this way.
# Pass 2 subagents can read tests + design docs directly via file access.
INCLUDE_ROOTS = [
    "wild_igor",
    "lab/claudecode",
    "lab/utility_closet",
    "lab/tools",
    "lab/docs",
    "lab/recovery_help_from_akien",
    "CLAUDE.md",
]

# Specific standalone files worth including (relative to REPO).
# decisions_log.dsb is intentionally excluded — 24k tokens of historical
# decisions are accessible via the palace if needed; audit focuses on code.
EXTRA_REPO_FILES = [
    "lab/design_docs_for_igor/shape_lock_2026-04-20.md",
    "lab/design_docs/WorkingWithClaude.md",
]

# Additional non-repo inputs (absolute paths)
EXTRA_FILES = [
    Path.home() / ".claude/skills",  # CC skill definitions
]

# Hard "do not touch" exclusions (relative globs checked against posix path)
EXCLUDE_PATTERNS = [
    r"^archive/",
    r"^lab/theigors/",  # palace echo, not canonical
    r"^tests/fixtures/",
    r"__pycache__/",
    r"\.pyc$",
    r"^lab/design_docs/audit_2026/",  # don't feed the prompts to themselves
    r"^venv/",
    r"^\.venv/",
    r"node_modules/",
    r"^wild_igor/web_ui/",  # frontend — not core cognition audit surface
    r"^wild_igor/setup_assets/",  # installer, not cognition
    r"\.git/",
    r"^lab/claudecode/cc_skills/",  # mirror of ~/.claude/skills; avoid double-include
    r"^lab/claudecode/archive/",
    r"^lab/claudecode/cc_memory_seed/",  # data files
    r"^lab/notes\.log$",
    r"^lab/ebook_candidates\.md$",  # reference list, not code
    r"^lab/design_docs/gap_analysis\.md$",  # auto-generated
    r"^lab/design_docs/_snapshots/",
    r"^lab/design_docs_for_igor/gap_analysis\.dsb$",  # auto-generated
    r"^lab/docs/sessions\.md$",  # rendered from DB
    r"^wild_igor/igor/tools/ebook_drm/",  # kindle DRM, not cognition
    r"^wild_igor/igor/tools/browser_session/",  # browser session data
    r"^lab/hosted_igor/",  # deploy config, not core
    r"^lab/deploy/",
    r"^lab/seed/",  # seed data, not code
    r"^lab/audit_reports/",  # prior audit artifacts
    # Non-cognition lab/claudecode scripts (seeds, migrations) — trim for token budget
    r"^lab/claudecode/seed_",
    r"^lab/claudecode/migrate_",
    r"^lab/claudecode/audit_pass1_run\.py$",  # this file itself
    # Out-of-scope wild_igor subtrees for Pass 1 (not cognition core)
    r"^wild_igor/igor/network/",  # remote-instance daemon
    r"^wild_igor/igor/dashboard/",
    r"^wild_igor/igor/web/",  # gutted facade (UC is the server now)
    r"^wild_igor/igor/arbiter/",  # disabled
    r"\.pdf$",
    r"\.epub$",
    r"\.mobi$",
    r"\.zip$",
    r"\.tar\.gz$",
    r"\.jsonl$",  # channel / session logs are noise
    r"\.log$",
    r"\.lock$",
]

# File extensions to include (textual)
TEXT_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".dsb",
    ".csb",
    ".json",
    ".yml",
    ".yaml",
    ".toml",
    ".cfg",
    ".ini",
    ".sh",
    ".sql",
    ".html",
    ".css",
    ".js",
    ".ts",
    ".tsx",
    ".jsx",
    ".rs",
    ".go",
}

# Per-file size cap (chars) — avoid a single huge file dominating
PER_FILE_CAP = 50_000

# lab/claudecode whitelist — only these scripts matter for Persona 11
# (workflow audit). Everything else under lab/claudecode is excluded.
LAB_CLAUDECODE_WHITELIST = {
    "cc_queue.py",
    "session_manager.py",
    "channel.py",
    "palace_sync.py",
    "decision_manager.py",
    "igor_mcp.py",
    "utility_closet_server.py",
    "github_sync.py",
    "docs_sync.py",
    "export_chat.py",
    "book_learner.py",
    "reading_campaign.py",
    "worker_foreman.py",
    "stale_ticket_sweeper.py",
    "WorkingWithClaude.md",
    "WINDOWS_ONBOARDING.md",
    "superclaude",
}


def is_excluded(rel_path: str) -> bool:
    for pat in EXCLUDE_PATTERNS:
        if re.search(pat, rel_path):
            return True
    # lab/claudecode/ whitelist: only named scripts survive
    if rel_path.startswith("lab/claudecode/"):
        rest = rel_path[len("lab/claudecode/") :]
        if "/" in rest:
            return True  # no subdirs
        if rest not in LAB_CLAUDECODE_WHITELIST:
            return True
    return False


def iter_repo_files(repo: Path, roots: list[str]):
    for root in roots:
        root_path = repo / root
        if root_path.is_file():
            yield root_path
            continue
        if not root_path.exists():
            continue
        for p in root_path.rglob("*"):
            if not p.is_file():
                continue
            rel = p.relative_to(repo).as_posix()
            if is_excluded(rel):
                continue
            if p.suffix and p.suffix not in TEXT_EXTENSIONS:
                continue
            yield p


def iter_extra(paths: list[Path]):
    for base in paths:
        if not base.exists():
            continue
        if base.is_file():
            yield base, base.name
            continue
        for p in base.rglob("*"):
            if not p.is_file():
                continue
            if p.suffix and p.suffix not in TEXT_EXTENSIONS:
                continue
            rel = p.relative_to(base.parent).as_posix()
            if "__pycache__" in rel:
                continue
            yield p, rel


def read_text(p: Path, cap: int = PER_FILE_CAP) -> str:
    try:
        txt = p.read_text(errors="replace")
    except Exception as exc:
        return f"[[READ_ERROR: {exc}]]"
    if len(txt) > cap:
        return (
            txt[:cap]
            + f"\n\n[[FILE TRUNCATED at {cap} chars; original {len(txt)} chars]]"
        )
    return txt


def assemble_payload(repo: Path) -> tuple[str, int, int]:
    """Build the concat'd repo payload. Returns (payload, file_count, char_count)."""
    parts: list[str] = []
    parts.append(
        "# TheIgors — full repo payload for Pass 1 audit\n"
        f"# Generated: {datetime.now(timezone.utc).isoformat(timespec='seconds')}\n"
        "# Each section below is one file, bracketed by === FILE markers.\n\n"
    )
    count = 0
    # Main repo
    for p in sorted(iter_repo_files(repo, INCLUDE_ROOTS)):
        rel = p.relative_to(repo).as_posix()
        parts.append(f"=== FILE {rel} ===\n")
        parts.append(read_text(p))
        parts.append("\n=== END FILE ===\n\n")
        count += 1
    # Specific standalone files (outside INCLUDE_ROOTS)
    for rel in EXTRA_REPO_FILES:
        p = repo / rel
        if not p.exists():
            continue
        parts.append(f"=== FILE {rel} ===\n")
        parts.append(read_text(p, cap=150_000))
        parts.append("\n=== END FILE ===\n\n")
        count += 1
    # CC skills (external path)
    for p, rel in sorted(iter_extra(EXTRA_FILES), key=lambda x: x[1]):
        parts.append(f"=== FILE ~/.claude/skills/{rel} ===\n")
        parts.append(read_text(p))
        parts.append("\n=== END FILE ===\n\n")
        count += 1
    # Representative slate (most recent)
    slate_dir = Path.home() / ".TheIgors/claudecode"
    if slate_dir.exists():
        slates = sorted(slate_dir.glob("*.slate.txt"))
        if slates:
            recent = slates[-1]
            parts.append(f"=== FILE {recent.name} (recent slate) ===\n")
            parts.append(read_text(recent))
            parts.append("\n=== END FILE ===\n\n")
            count += 1

    payload = "".join(parts)
    return payload, count, len(payload)


def load_prompt() -> str:
    """Extract the prompt body. Strip the outer markdown frame; keep the fenced prompt block content."""
    raw = PROMPT_FILE.read_text()
    m = re.search(r"## Prompt\s*\n+```\s*\n(.*?)\n```", raw, re.DOTALL)
    if not m:
        raise SystemExit("Could not find '## Prompt' fenced block in pass1 prompt file")
    return m.group(1)


def call_gemini(
    system_prompt: str, user_payload: str, max_tokens: int = 65536, timeout: int = 1800
) -> dict:
    """Synchronous OR call. Returns the parsed JSON response."""
    api_key = os.environ.get("OPENROUTER_API_KEY")
    if not api_key:
        raise SystemExit("OPENROUTER_API_KEY not in environment")

    body = {
        "model": OR_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_payload},
        ],
        "max_tokens": max_tokens,
        "temperature": 0.2,  # breadth task, but keep findings repeatable
    }
    data = json.dumps(body).encode("utf-8")

    req = urllib.request.Request(
        f"{OR_BASE}/chat/completions",
        data=data,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/akienm/TheIgors",
            "X-Title": "TheIgors Pass 1 Audit",
        },
        method="POST",
    )
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        err_body = exc.read().decode("utf-8", errors="replace")
        raise SystemExit(f"OR returned HTTP {exc.code}:\n{err_body[:4000]}") from exc
    elapsed = time.time() - t0
    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"OR returned non-JSON: {exc}\nBody: {raw[:2000]}")
    parsed["_elapsed_s"] = elapsed
    return parsed


def save_response(response: dict, user_payload_chars: int) -> Path:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")

    # Save raw full response (for forensics)
    raw_path = OUTPUT_DIR / f"pass1_raw_{ts}.json"
    raw_path.write_text(json.dumps(response, indent=2))

    # Extract assistant content
    choices = response.get("choices", [])
    if not choices:
        raise SystemExit(f"No choices in response — raw saved to {raw_path}")
    content = choices[0].get("message", {}).get("content", "")
    finish_reason = choices[0].get("finish_reason", "?")
    usage = response.get("usage", {})

    report_path = OUTPUT_DIR / f"pass1_report_{ts}.md"
    header = (
        f"<!--\n"
        f"Pass 1 audit — Gemini 2.5 Pro\n"
        f"Generated: {ts}\n"
        f"Model: {response.get('model', OR_MODEL)}\n"
        f"Finish reason: {finish_reason}\n"
        f"Payload chars sent: {user_payload_chars:,}\n"
        f"Usage: {json.dumps(usage)}\n"
        f"Elapsed: {response.get('_elapsed_s', 0):.1f}s\n"
        f"-->\n\n"
    )
    report_path.write_text(header + content)
    return report_path


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument(
        "--dry-run",
        action="store_true",
        help="assemble payload + show size; do not call OR",
    )
    p.add_argument(
        "--max-payload-chars",
        type=int,
        default=4_500_000,
        help="abort if payload exceeds this many chars (default 4.5M, ~1.05M tokens)",
    )
    p.add_argument(
        "--max-tokens", type=int, default=65_536, help="max output tokens (default 64k)"
    )
    args = p.parse_args()

    print(f"Repo: {REPO}")
    print(f"Output: {OUTPUT_DIR}")
    print()
    print("Assembling payload...")
    payload, file_count, char_count = assemble_payload(REPO)
    # Rough token estimate: 1 token ≈ 4 chars
    est_tokens = char_count // 4
    print(f"  files:        {file_count}")
    print(f"  chars:        {char_count:,}")
    print(f"  ~tokens:      {est_tokens:,}")
    print()
    if char_count > args.max_payload_chars:
        raise SystemExit(
            f"Payload {char_count:,} chars exceeds cap {args.max_payload_chars:,} — "
            f"tighten EXCLUDE_PATTERNS or raise --max-payload-chars"
        )

    prompt = load_prompt()
    print(f"Prompt: {len(prompt):,} chars ({len(prompt)//4:,} tokens est.)")
    print()

    if args.dry_run:
        print("DRY RUN — not sending. First 500 chars of payload:")
        print(payload[:500])
        print("...")
        print("Last 500 chars:")
        print(payload[-500:])
        return 0

    print(f"Sending to {OR_MODEL} with max_tokens={args.max_tokens}...")
    print(f"(this can take a few minutes for a 1M-context call)")
    print()
    response = call_gemini(
        system_prompt=prompt,
        user_payload=payload,
        max_tokens=args.max_tokens,
    )
    report_path = save_response(response, char_count)
    usage = response.get("usage", {})
    print(f"Saved: {report_path}")
    print(f"Usage: {json.dumps(usage)}")
    print(f"Elapsed: {response.get('_elapsed_s', 0):.1f}s")
    print(
        f"Finish reason: {response.get('choices', [{}])[0].get('finish_reason', '?')}"
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
