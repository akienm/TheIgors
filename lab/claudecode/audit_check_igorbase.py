#!/usr/bin/env python3
"""
audit_check_igorbase.py — D125 enforcement helper.

Walks wild_igor/igor/{cognition,memory,tools,network,brainstem}/ and finds
class definitions whose bases don't include IgorBase AND aren't exclusively
third-party (BaseModel, Enum, ABC, dataclass, Exception, Generic, Protocol,
NamedTuple, TypedDict, object).

Empty stdout = pass. Non-empty = list of violations, one per line.

Used as a registered audit check via `audit_add.py add forever
primary-classes-must-inherit-igorbase --kind shell --pattern
'python3 lab/claudecode/audit_check_igorbase.py'`.
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
SOURCE_ROOT = REPO_ROOT / "wild_igor" / "igor"

# Bases that exempt a class from the IgorBase requirement
THIRD_PARTY_BASES = {
    "BaseModel",
    "Enum",
    "IntEnum",
    "StrEnum",
    "NamedTuple",
    "TypedDict",
    "object",
    "ABC",
    "ABCMeta",
    "Protocol",
    "Generic",
    "Exception",
    "ValueError",
    "TypeError",
    "RuntimeError",
    "Tuple",
    "Dict",
    "List",
    "Set",
    "FrozenSet",
    "dataclass",
    "Thread",
    "Process",
    "Server",
    "BaseHTTPRequestHandler",
    "HTTPServer",
}

# Only enforce on these subdirectories
PRIMARY_DIRS = ("cognition", "memory", "tools", "network", "brainstem")


def _is_primary(path: Path) -> bool:
    rel = path.relative_to(SOURCE_ROOT)
    parts = rel.parts
    if not parts:
        return False
    if parts[0] not in PRIMARY_DIRS:
        return False
    if "__pycache__" in parts:
        return False
    if "tests" in parts or "test" in parts:
        return False
    name = parts[-1]
    if name.startswith("test_") or name.endswith("_test.py"):
        return False
    return True


def _base_name(node: ast.AST) -> str:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        return node.attr
    if isinstance(node, ast.Subscript):
        return _base_name(node.value)
    return "?"


def _check_file(path: Path) -> list[str]:
    out: list[str] = []
    try:
        tree = ast.parse(path.read_text())
    except (SyntaxError, UnicodeDecodeError):
        return out
    for node in ast.walk(tree):
        if not isinstance(node, ast.ClassDef):
            continue
        bases = [_base_name(b) for b in node.bases]
        if "IgorBase" in bases:
            continue
        # No bases = implicit object — must explicitly opt in or be exempted
        if bases and all(b in THIRD_PARTY_BASES for b in bases):
            continue
        # @dataclass classes are exempted (data containers, not components)
        if any(
            (isinstance(d, ast.Name) and d.id == "dataclass")
            or (
                isinstance(d, ast.Call)
                and isinstance(d.func, ast.Name)
                and d.func.id == "dataclass"
            )
            for d in node.decorator_list
        ):
            continue
        rel = path.relative_to(REPO_ROOT)
        bases_str = ", ".join(bases) if bases else ""
        out.append(f"{rel}:{node.lineno} class {node.name}({bases_str})")
    return out


def main() -> int:
    if not SOURCE_ROOT.exists():
        print(f"source root not found: {SOURCE_ROOT}", file=sys.stderr)
        return 2

    violations: list[str] = []
    for path in sorted(SOURCE_ROOT.rglob("*.py")):
        if not _is_primary(path):
            continue
        violations.extend(_check_file(path))

    for v in violations:
        print(v)
    return 0 if not violations else 1


if __name__ == "__main__":
    sys.exit(main())
