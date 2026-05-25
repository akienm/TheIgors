#!/usr/bin/env python3
"""
audit_cognition_modules.py — T-cognition-module-audit

# author-model: opus

Classify every devices/igor/cognition/*.py module as one of:

  LIVE          — imported by main.py, turn_pipeline.py, push_sources.py,
                  brainstem/, or another LIVE cognition module
  EXPERIMENTAL  — imported only by tests/ or behind a feature flag
  ORPHAN        — zero importers anywhere
  PLACEHOLDER   — module body is essentially empty / TODO-only / pass

Output:
  lab/claudecode/reports/cognition_module_audit_<ts>.md  — full report
  --json <path>  — machine-readable groupings (for follow-up tooling)

Read-only over the codebase. Doesn't write to the palace.
"""

from __future__ import annotations

import argparse
import ast
import json
import re
import subprocess
import sys
from collections import Counter, defaultdict
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

REPO_ROOT = Path(__file__).resolve().parents[2]
COG_ROOT = Path("/home/akien/dev/src/UnseenUniversity") / "devices" / "igor" / "cognition"

ANCHOR_PATHS = (
    Path("/home/akien/dev/src/UnseenUniversity") / "devices" / "igor" / "main.py",
    Path("/home/akien/dev/src/UnseenUniversity") / "devices" / "igor" / "cognition" / "turn_pipeline.py",
    Path("/home/akien/dev/src/UnseenUniversity") / "devices" / "igor" / "cognition" / "push_sources.py",
    Path("/home/akien/dev/src/UnseenUniversity") / "devices" / "igor" / "brainstem",
    Path("/home/akien/dev/src/UnseenUniversity") / "devices" / "igor" / "tools" / "pe_chain.py",
)


@dataclass
class ModuleInfo:
    name: str
    path: str
    docstring_first_line: str = ""
    imports_from: list[str] = field(default_factory=list)
    imported_by_anchors: list[str] = field(default_factory=list)
    imported_by_other_cognition: list[str] = field(default_factory=list)
    imported_by_tests: list[str] = field(default_factory=list)
    imported_by_other_repo: list[str] = field(default_factory=list)
    line_count: int = 0
    is_essentially_empty: bool = False
    has_feature_flag: bool = False
    classification: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


def _safe_parse(path: Path) -> Optional[ast.AST]:
    try:
        return ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError, OSError):
        return None


def _module_docstring(tree: ast.AST) -> str:
    if isinstance(tree, ast.Module) and tree.body:
        first = tree.body[0]
        if isinstance(first, ast.Expr) and isinstance(first.value, ast.Constant):
            text = first.value.value
            if isinstance(text, str):
                return text.strip().splitlines()[0] if text.strip() else ""
    return ""


def _cognition_imports(tree: ast.AST) -> list[str]:
    out: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom):
            mod = node.module or ""
            if mod.startswith("devices.igor.cognition."):
                out.add(mod.split(".")[-1])
            elif node.level >= 1 and mod:
                clean = mod.split(".")[0]
                if clean:
                    out.add(clean)
    return sorted(out)


def _has_feature_flag(content: str) -> bool:
    return bool(
        re.search(r"IGOR_[A-Z_]+_ENABLED|os\.getenv\([\"'][A-Z_]+_ENABLED", content)
    )


def _is_essentially_empty(tree: ast.AST, content: str) -> bool:
    code_lines = [
        ln
        for ln in content.splitlines()
        if ln.strip() and not ln.strip().startswith("#")
    ]
    if len(code_lines) > 60:
        return False
    body_text = "\n".join(code_lines)
    todo_density = body_text.lower().count("todo") + body_text.lower().count("fixme")
    pass_count = sum(1 for node in ast.walk(tree) if isinstance(node, ast.Pass))
    if pass_count >= 3 and len(code_lines) < 30:
        return True
    if todo_density >= 2 and len(code_lines) < 40:
        return True
    return False


def _grep_importers(module_name: str) -> list[str]:
    # Catches: relative imports (`.foo`, `..foo`), qualified relative
    # (`.cognition.foo`, `..cognition.foo`, `.reasoners.foo`), absolute
    # (`devices.igor.cognition.foo`), and the `.reasoners.<name>` shape
    # used by anchor files importing into cognition/reasoners/.
    patterns = (
        f"from .{module_name} import",
        f"from ..{module_name} import",
        f"from .cognition.{module_name} import",
        f"from ..cognition.{module_name} import",
        f"from .reasoners.{module_name} import",
        f"from .cognition.reasoners.{module_name} import",
        f"from ..cognition.reasoners.{module_name} import",
        f"from devices.igor.cognition.{module_name} import",
        f"from devices.igor.cognition.reasoners.{module_name} import",
        f"import devices.igor.cognition.{module_name}",
    )
    found: set[str] = set()
    for pat in patterns:
        result = subprocess.run(
            [
                "git",
                "-C",
                str(REPO_ROOT),
                "grep",
                "-l",
                pat,
                "--",
                ":!**/__pycache__/**",
            ],
            capture_output=True,
            text=True,
        )
        if result.returncode == 0:
            for line in result.stdout.splitlines():
                if line.strip():
                    found.add(line.strip())
    return sorted(found)


def _path_under(rel: str, anchor: Path) -> bool:
    abs_path = (REPO_ROOT / rel).resolve()
    if anchor.is_file():
        return abs_path == anchor.resolve()
    return str(abs_path).startswith(str(anchor.resolve()))


def _classify_importers(
    rel_paths: list[str],
) -> tuple[list[str], list[str], list[str], list[str]]:
    anchors: list[str] = []
    other_cog: list[str] = []
    tests: list[str] = []
    other: list[str] = []
    for rel in rel_paths:
        if "tests/" in rel or rel.startswith("tests/"):
            tests.append(rel)
            continue
        is_anchor = any(_path_under(rel, a) for a in ANCHOR_PATHS)
        if is_anchor:
            anchors.append(rel)
            continue
        if rel.startswith("devices/igor/cognition/"):
            other_cog.append(rel)
            continue
        other.append(rel)
    return anchors, other_cog, tests, other


def classify(info: ModuleInfo, live_set: set[str]) -> str:
    if info.is_essentially_empty and not info.imported_by_anchors:
        return "PLACEHOLDER"
    if info.imported_by_anchors:
        return "LIVE"
    if any(Path(p).stem in live_set for p in info.imported_by_other_cognition):
        return "LIVE"
    if info.imported_by_tests and not (
        info.imported_by_other_cognition or info.imported_by_other_repo
    ):
        return "EXPERIMENTAL"
    if info.has_feature_flag:
        return "EXPERIMENTAL"
    if (
        not info.imported_by_anchors
        and not info.imported_by_other_cognition
        and not info.imported_by_other_repo
    ):
        return "ORPHAN"
    return "EXPERIMENTAL"


def audit() -> list[ModuleInfo]:
    modules: list[ModuleInfo] = []
    for path in sorted(COG_ROOT.rglob("*.py")):
        if "__pycache__" in path.parts:
            continue
        if path.name == "__init__.py":
            continue
        rel = str(path.relative_to(REPO_ROOT))
        try:
            content = path.read_text(encoding="utf-8")
        except (OSError, UnicodeDecodeError):
            continue
        tree = _safe_parse(path)
        if tree is None:
            continue
        info = ModuleInfo(
            name=path.stem,
            path=rel,
            docstring_first_line=_module_docstring(tree),
            imports_from=_cognition_imports(tree),
            line_count=len(content.splitlines()),
            is_essentially_empty=_is_essentially_empty(tree, content),
            has_feature_flag=_has_feature_flag(content),
        )
        importers = [p for p in _grep_importers(info.name) if p != rel]
        anchors, other_cog, tests, other = _classify_importers(importers)
        info.imported_by_anchors = anchors
        info.imported_by_other_cognition = other_cog
        info.imported_by_tests = tests
        info.imported_by_other_repo = other
        modules.append(info)

    live_set: set[str] = set()
    for info in modules:
        if info.imported_by_anchors:
            info.classification = "LIVE"
            live_set.add(info.name)
    changed = True
    while changed:
        changed = False
        for info in modules:
            if info.classification:
                continue
            if any(Path(p).stem in live_set for p in info.imported_by_other_cognition):
                info.classification = "LIVE"
                live_set.add(info.name)
                changed = True
    for info in modules:
        if not info.classification:
            info.classification = classify(info, live_set)

    return modules


def write_report(modules: list[ModuleInfo], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    lines: list[str] = []
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    lines.append(f"# Cognition module audit — {ts}")
    lines.append("")
    lines.append(f"Modules scanned: {len(modules)}")
    counts = Counter(m.classification for m in modules)
    lines.append("")
    lines.append("## Classification summary")
    lines.append("")
    lines.append("| Class | Count |")
    lines.append("|---|---|")
    for cls in ("LIVE", "EXPERIMENTAL", "PLACEHOLDER", "ORPHAN"):
        lines.append(f"| {cls} | {counts.get(cls, 0)} |")
    lines.append("")

    by_class: dict[str, list[ModuleInfo]] = defaultdict(list)
    for m in modules:
        by_class[m.classification].append(m)

    for cls in ("ORPHAN", "PLACEHOLDER", "EXPERIMENTAL", "LIVE"):
        items = sorted(by_class.get(cls, []), key=lambda m: m.name)
        if not items:
            continue
        lines.append(f"## {cls} ({len(items)})")
        lines.append("")
        lines.append(
            "| Module | Path | LOC | Anchors | Cog | Test | Other | Docstring |"
        )
        lines.append("|---|---|---|---|---|---|---|---|")
        for m in items:
            doc = (m.docstring_first_line or "").replace("|", "\\|")[:60]
            short_path = m.path.replace("devices/igor/cognition/", "")
            lines.append(
                f"| `{m.name}` | `{short_path}` | {m.line_count} | {len(m.imported_by_anchors)} "
                f"| {len(m.imported_by_other_cognition)} | {len(m.imported_by_tests)} "
                f"| {len(m.imported_by_other_repo)} | {doc} |"
            )
        lines.append("")

    orphans = sorted(by_class.get("ORPHAN", []), key=lambda m: m.line_count)
    if orphans:
        lines.append("## Removal candidates (ORPHAN — verify before deleting)")
        lines.append("")
        for m in orphans:
            lines.append(
                f"- `{m.path}` ({m.line_count} LOC): "
                f"{m.docstring_first_line[:80] if m.docstring_first_line else '(no docstring)'}"
            )
        lines.append("")

    out.write_text("\n".join(lines))


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    parser.add_argument("--out", type=Path, default=None)
    parser.add_argument("--json", type=Path, default=None)
    args = parser.parse_args(argv)

    print("Scanning cognition/ modules...", file=sys.stderr)
    modules = audit()
    counts = Counter(m.classification for m in modules)
    print(
        f"Done: {len(modules)} modules — "
        f"LIVE={counts.get('LIVE', 0)} "
        f"EXPERIMENTAL={counts.get('EXPERIMENTAL', 0)} "
        f"PLACEHOLDER={counts.get('PLACEHOLDER', 0)} "
        f"ORPHAN={counts.get('ORPHAN', 0)}",
        file=sys.stderr,
    )

    if args.out is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
        args.out = (
            REPO_ROOT
            / "lab"
            / "claudecode"
            / "reports"
            / f"cognition_module_audit_{ts}.md"
        )
    write_report(modules, args.out)
    print(f"Wrote report: {args.out}", file=sys.stderr)

    if args.json:
        args.json.parent.mkdir(parents=True, exist_ok=True)
        args.json.write_text(json.dumps([m.to_dict() for m in modules], indent=2))
        print(f"Wrote JSON: {args.json}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    sys.exit(main())
