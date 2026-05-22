#!/usr/bin/env python3
"""
build_ebook_index.py — T-ebook-master-index
Scans all 4 ebook trees and produces a master index JSON.

Trees:
  1. Calibre Library (via metadata.db — 3,700+ books with author/title metadata)
  2. Kindle          (flat directory, .azw/.mobi/.epub files)
  3. SORTUS-EBOOKS   (flat directory, .epub/.pdf files)
  4. TheIgorsProject/Readings  (.txt/.md/.docx conversation logs)

Output: ~/.TheIgors/local/ebooks/master_index.json
        ~/.TheIgors/local/ebooks/master_index_summary.txt  (human-readable)

Cross-references reading_list table to mark absorbed/in-progress books.

Usage:
    cd ~/TheIgors
    source venv/bin/activate
    python3 tools/build_ebook_index.py
"""

import hashlib
import json
import os
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "wild_igor"))


from igor.paths import paths as _paths  # noqa: E402

_p = _paths()
CALIBRE_LIBRARY = _p.calibre_library
KINDLE_DIR = _p.kindle_dir
EBOOKS_ROOT = _p.ebooks_root
SORTUS_DIR = EBOOKS_ROOT / "SORTUS-EBOOKS"
READINGS_DIR = Path.home() / "TheIgorsProject" / "akien" / "Readings"
LOCAL_EBOOKS_DIR = Path.home() / ".TheIgors" / "local" / "ebooks"
OUT_JSON = LOCAL_EBOOKS_DIR / "master_index.json"
OUT_TXT = LOCAL_EBOOKS_DIR / "master_index_summary.txt"

EBOOK_EXTS = {".epub", ".mobi", ".azw", ".azw3", ".pdf", ".djvu", ".lit", ".fb2"}
TEXT_EXTS = {".txt", ".md", ".rst", ".docx", ".doc", ".odt", ".rtf"}


def _sha8(path: str) -> str:
    return hashlib.sha256(path.encode()).hexdigest()[:8]


# ── Reading list lookup ────────────────────────────────────────────────────────


def _load_reading_list() -> dict[str, str]:
    """title_lower → status from reading_list. Returns {} on failure."""
    try:
        import psycopg2

        conn = psycopg2.connect(os.environ["IGOR_HOME_DB_URL"])
        cur = conn.cursor()
        cur.execute("SELECT title, status FROM reading_list")
        result = {row[0].lower().strip(): row[1] for row in cur.fetchall()}
        conn.close()
        return result
    except Exception as e:
        print(f"  WARN: reading_list lookup failed: {e}", file=sys.stderr)
        return {}


# ── Calibre scan ───────────────────────────────────────────────────────────────


def _scan_calibre() -> list[dict]:
    """Query Calibre's metadata.db for all books with file paths."""
    entries = []
    db_path = CALIBRE_LIBRARY / "metadata.db"
    if not db_path.exists():
        print(f"  SKIP Calibre: metadata.db not found at {db_path}")
        return entries

    try:
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row

        # books join book_authors + data (formats)
        rows = conn.execute("""
            SELECT
                b.id,
                b.title,
                b.author_sort,
                b.path AS book_path,
                GROUP_CONCAT(d.format) AS formats,
                GROUP_CONCAT(d.name) AS names
            FROM books b
            LEFT JOIN books_authors_link bal ON bal.book = b.id
            LEFT JOIN authors a ON a.id = bal.author
            LEFT JOIN data d ON d.book = b.id
            GROUP BY b.id
            ORDER BY b.author_sort, b.title
        """).fetchall()

        for row in rows:
            formats_raw = (row["formats"] or "").split(",")
            names_raw = (row["names"] or "").split(",")
            fmt = formats_raw[0].lower() if formats_raw else "unknown"
            name = names_raw[0] if names_raw else row["title"]

            # Reconstruct path: Calibre Library/<book_path>/<name>.<fmt>
            if row["book_path"] and name and fmt != "unknown":
                file_path = str(CALIBRE_LIBRARY / row["book_path"] / f"{name}.{fmt}")
            else:
                file_path = str(CALIBRE_LIBRARY / (row["book_path"] or ""))

            # Parse author from author_sort ("Last, First" or "First Last")
            author_sort = row["author_sort"] or ""
            if ", " in author_sort:
                parts = author_sort.split(", ", 1)
                author = f"{parts[1]} {parts[0]}"
            else:
                author = author_sort

            entries.append(
                {
                    "id": _sha8(f"calibre:{row['id']}"),
                    "tree": "calibre",
                    "calibre_id": row["id"],
                    "title": row["title"] or "",
                    "author": author.strip(),
                    "format": fmt,
                    "formats_available": [f.lower() for f in formats_raw if f],
                    "path": file_path,
                    "reading_list_status": None,
                }
            )

        conn.close()
        print(f"  Calibre: {len(entries)} books")
    except Exception as e:
        print(f"  ERROR scanning Calibre: {e}", file=sys.stderr)

    return entries


# ── Kindle scan ────────────────────────────────────────────────────────────────


def _scan_kindle() -> list[dict]:
    entries = []
    if not KINDLE_DIR.exists():
        print(f"  SKIP Kindle: {KINDLE_DIR} not found")
        return entries

    for p in sorted(KINDLE_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in EBOOK_EXTS:
            continue
        stem = p.stem
        # Kindle filenames often "Author - Title" or just "Title"
        if " - " in stem:
            parts = stem.split(" - ", 1)
            author, title = parts[0].strip(), parts[1].strip()
        else:
            author, title = "", stem.strip()
        entries.append(
            {
                "id": _sha8(f"kindle:{p}"),
                "tree": "kindle",
                "title": title,
                "author": author,
                "format": p.suffix.lower().lstrip("."),
                "path": str(p),
                "reading_list_status": None,
            }
        )

    print(f"  Kindle: {len(entries)} files")
    return entries


# ── SORTUS-EBOOKS scan ─────────────────────────────────────────────────────────


def _scan_sortus() -> list[dict]:
    entries = []
    if not SORTUS_DIR.exists():
        print(f"  SKIP SORTUS-EBOOKS: {SORTUS_DIR} not found")
        return entries

    for p in sorted(SORTUS_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in EBOOK_EXTS:
            continue
        stem = p.stem
        if " - " in stem:
            parts = stem.split(" - ", 1)
            author, title = parts[0].strip(), parts[1].strip()
        else:
            author, title = "", stem.strip()
        entries.append(
            {
                "id": _sha8(f"sortus:{p}"),
                "tree": "sortus",
                "title": title,
                "author": author,
                "format": p.suffix.lower().lstrip("."),
                "path": str(p),
                "reading_list_status": None,
            }
        )

    print(f"  SORTUS-EBOOKS: {len(entries)} files")
    return entries


# ── Readings scan ──────────────────────────────────────────────────────────────


def _scan_readings() -> list[dict]:
    entries = []
    if not READINGS_DIR.exists():
        print(f"  SKIP Readings: {READINGS_DIR} not found")
        return entries

    for p in sorted(READINGS_DIR.rglob("*")):
        if not p.is_file():
            continue
        if p.suffix.lower() not in TEXT_EXTS:
            continue
        # Filename format: YYYYMMDDHHMMSS_title.txt or YYYYMMDD.topic.txt or topic.txt
        stem = p.stem
        # Strip leading timestamp if present
        import re

        title = (
            re.sub(r"^\d{8,14}[._]?", "", stem)
            .replace("_", " ")
            .replace(".", " ")
            .strip()
        )
        entries.append(
            {
                "id": _sha8(f"readings:{p}"),
                "tree": "readings",
                "title": title or stem,
                "author": "Akien/Claude",
                "format": p.suffix.lower().lstrip("."),
                "path": str(p),
                "reading_list_status": None,
            }
        )

    print(f"  Readings: {len(entries)} files")
    return entries


# ── Cross-reference reading_list ──────────────────────────────────────────────


def _enrich_with_reading_list(entries: list[dict], rl: dict[str, str]) -> None:
    for e in entries:
        title_key = e["title"].lower().strip()
        if title_key in rl:
            e["reading_list_status"] = rl[title_key]


# ── Main ──────────────────────────────────────────────────────────────────────


def main():
    print("Building master ebook index...")
    print(f"  Calibre: {CALIBRE_LIBRARY}")
    print(f"  Kindle:  {KINDLE_DIR}")
    print(f"  SORTUS:  {SORTUS_DIR}")
    print(f"  Readings:{READINGS_DIR}")
    print()

    print("Loading reading_list...")
    rl = _load_reading_list()
    print(f"  {len(rl)} entries in reading_list")
    print()

    print("Scanning trees...")
    calibre = _scan_calibre()
    kindle = _scan_kindle()
    sortus = _scan_sortus()
    readings = _scan_readings()
    all_entries = calibre + kindle + sortus + readings

    print(f"\nTotal: {len(all_entries)} entries")
    print("Enriching with reading_list status...")
    _enrich_with_reading_list(all_entries, rl)

    # Summary stats
    by_tree = {}
    by_status = {}
    by_format = {}
    for e in all_entries:
        by_tree[e["tree"]] = by_tree.get(e["tree"], 0) + 1
        s = e["reading_list_status"] or "untracked"
        by_status[s] = by_status.get(s, 0) + 1
        f = e.get("format", "?")
        by_format[f] = by_format.get(f, 0) + 1

    index = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "total": len(all_entries),
        "by_tree": by_tree,
        "by_status": by_status,
        "by_format": dict(sorted(by_format.items(), key=lambda x: -x[1])[:15]),
        "entries": all_entries,
    }

    LOCAL_EBOOKS_DIR.mkdir(parents=True, exist_ok=True)
    OUT_JSON.write_text(
        json.dumps(index, indent=2, ensure_ascii=False), encoding="utf-8"
    )
    print(f"\nWrote {OUT_JSON} ({OUT_JSON.stat().st_size // 1024}KB)")

    # Human-readable summary
    lines = [
        f"MASTER EBOOK INDEX — {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Total: {len(all_entries)} entries",
        "",
        "By tree:",
    ]
    for tree, count in sorted(by_tree.items()):
        lines.append(f"  {tree:<20} {count:>6}")
    lines.append("")
    lines.append("By reading status:")
    for status, count in sorted(by_status.items(), key=lambda x: -x[1]):
        lines.append(f"  {status:<20} {count:>6}")
    lines.append("")
    lines.append("Top formats:")
    for fmt, count in list(index["by_format"].items())[:10]:
        lines.append(f"  {fmt:<20} {count:>6}")

    summary = "\n".join(lines)
    OUT_TXT.write_text(summary, encoding="utf-8")
    print(f"Wrote {OUT_TXT}")
    print()
    print(summary)


if __name__ == "__main__":
    main()
