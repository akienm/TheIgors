#!/usr/bin/env python3
"""
scan_ebooks.py — Produce a prioritized ebook reading list.

Sources:
  1. Calibre SQLite DB (primary — has descriptions + tags)
  2. OPF files under EBOOKS_ROOT (catch anything not in Calibre)

Output: ~/TheIgors/ebook_candidates.md

Priority tiers:
  P1 — Making Money (Terry Pratchett)
  P2 — Pratchett books featuring Igor characters
  P3 — Programming / tech / CS / software
  P4 — Non-fiction (science, psychology, business, etc.)
  P5 — Fiction (non-romance, non-filtered)
  SKIP — Romance / Erotica / filtered

Usage:
  python3 tools/scan_ebooks.py
  python3 tools/scan_ebooks.py --show-skipped   # include filtered books in output
"""

import argparse
import html
import re
import sqlite3
import sys
from pathlib import Path
from xml.etree import ElementTree as ET

CALIBRE_DB = Path(
    "/home/akien/.TheIgors/akien/onedrive/AkiensMedia/Ebooks/Calibre Portable/Calibre Library/metadata.db"
)
EBOOKS_ROOT = Path("/home/akien/.TheIgors/akien/onedrive/AkiensMedia/Ebooks")
OUTPUT = Path.home() / "TheIgors" / "ebook_candidates.md"

# ── Priority matchers ──────────────────────────────────────────────────────────

PRIORITY_1_TITLES = {"making money"}

PRATCHETT_IGOR_TITLES = {
    "carpe jugulum",
    "the fifth elephant",
    "thief of time",
    "monstrous regiment",
    "going postal",
    "thud!",
    "thud",
    "making money",
    "unseen academicals",
    "snuff",
    "raising steam",
    "the shepherd's crown",
}

SKIP_SUBJECTS = {
    "romance",
    "erotica",
    "erotic",
    "erotic fiction",
    "adult fiction",
    "erotic romance",
    "hentai",
    "explicit",
    "fan fiction",
    "fanfic",
}

PROGRAMMING_SUBJECTS = {
    "computers",
    "programming",
    "software",
    "computer science",
    "python",
    "javascript",
    "java",
    "c++",
    "ruby",
    "algorithms",
    "data structures",
    "machine learning",
    "artificial intelligence",
    "web development",
    "computer programming",
    "software engineering",
    "open source",
    "linux",
    "unix",
    "database",
}

# If a book has these subjects alongside programming subjects, it's fiction misfiled
FICTION_MARKERS = {
    "fiction",
    "action & adventure",
    "mafia",
    "espionage",
    "thriller",
    "bilingual education",
    "language arts & disciplines",
}

NONFICTION_SUBJECTS = {
    "science",
    "mathematics",
    "physics",
    "biology",
    "neuroscience",
    "psychology",
    "philosophy",
    "history",
    "biography",
    "business",
    "economics",
    "self-help",
    "health",
    "mathematics",
    "logic",
    "memoir",
    "true crime",
    "political science",
    "sociology",
}

PRATCHETT_IGOR_AUTHORS = {"terry pratchett"}


def clean_html(text: str) -> str:
    """Strip HTML tags and decode entities from Calibre comment fields."""
    if not text:
        return ""
    text = re.sub(r"<[^>]+>", " ", text)
    text = html.unescape(text)
    text = re.sub(r"\s+", " ", text).strip()
    return text[:400] + ("..." if len(text) > 400 else "")


def classify(
    title: str, author: str, subjects: set[str], series: str
) -> tuple[int, str]:
    """Return (priority, reason). Lower = higher priority."""
    t = title.lower().strip()
    a = author.lower().strip()
    s = {x.lower().strip() for x in subjects}
    ser = (series or "").lower()

    # P1 — Making Money
    if t in PRIORITY_1_TITLES:
        return 1, "Making Money — top priority"

    # P0 — Calibre-tagged for Igor by Akien (manual curation overrides SKIP)
    if "igor" in s:
        return 0, "calibre:igor-tagged"

    # Skip — don't let anything else slip through from skip categories
    if s & SKIP_SUBJECTS:
        matched = s & SKIP_SUBJECTS
        return 99, f"skip:{','.join(sorted(matched))}"

    # P2 — Pratchett Igor books
    if a in PRATCHETT_IGOR_AUTHORS and t in PRATCHETT_IGOR_TITLES:
        return 2, "Pratchett Igor book"
    if a in PRATCHETT_IGOR_AUTHORS and ser == "discworld":
        return 2, "Pratchett Discworld"

    # P3 — Programming / tech
    # Guard: if book has fiction markers alongside computer subjects, it's misfiled
    if s & PROGRAMMING_SUBJECTS and not (s & FICTION_MARKERS):
        matched = s & PROGRAMMING_SUBJECTS
        return 3, f"programming:{','.join(sorted(matched))}"

    # Also classify by title keywords when subjects are sparse — but not if fiction-tagged
    title_words = set(t.split())
    prog_title_keywords = {
        "python",
        "javascript",
        "java",
        "linux",
        "unix",
        "algorithm",
        "programming",
        "software",
        "coding",
        "developer",
        "kubernetes",
        "docker",
        "sql",
        "api",
        "devops",
        "agile",
        "c#",
        ".net",
        "wpf",
        "asp.net",
        "selenium",
        "playwright",
        "automation",
        "refactoring",
        "compiler",
        "debugger",
        "programmer",
    }
    if title_words & prog_title_keywords and not (s & FICTION_MARKERS):
        return 3, "programming:title-match"

    # P4 — Non-fiction
    if s & NONFICTION_SUBJECTS:
        matched = s & NONFICTION_SUBJECTS
        return 4, f"nonfiction:{','.join(sorted(matched))}"

    # P5 — Everything else (fiction, unclassified)
    return 5, "unclassified"


def load_calibre() -> list[dict]:
    """Query Calibre SQLite for all books with metadata."""
    if not CALIBRE_DB.exists():
        print(f"  WARN: Calibre DB not found at {CALIBRE_DB}", file=sys.stderr)
        return []

    conn = sqlite3.connect(str(CALIBRE_DB))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("""
        SELECT
            b.id,
            b.title,
            a.name AS author,
            c.text AS description,
            s.name AS series,
            b.series_index
        FROM books b
        LEFT JOIN books_authors_link bal ON b.id = bal.book
        LEFT JOIN authors a ON bal.author = a.id
        LEFT JOIN comments c ON b.id = c.book
        LEFT JOIN books_series_link bsl ON b.id = bsl.book
        LEFT JOIN series s ON bsl.series = s.id
        ORDER BY b.id
    """)
    rows = cur.fetchall()

    # Fetch tags per book
    cur.execute("""
        SELECT btl.book, t.name
        FROM books_tags_link btl
        JOIN tags t ON btl.tag = t.id
    """)
    tags_by_book: dict[int, set] = {}
    for row in cur.fetchall():
        tags_by_book.setdefault(row[0], set()).add(row[1])

    conn.close()

    books = []
    seen_ids = set()
    for row in rows:
        if row["id"] in seen_ids:
            continue
        seen_ids.add(row["id"])
        books.append(
            {
                "source": "calibre",
                "calibre_id": row["id"],
                "title": row["title"] or "",
                "author": row["author"] or "Unknown",
                "description": clean_html(row["description"] or ""),
                "subjects": tags_by_book.get(row["id"], set()),
                "series": row["series"] or "",
            }
        )

    print(f"  Calibre: {len(books)} books loaded", file=sys.stderr)
    return books


NS = {"dc": "http://purl.org/dc/elements/1.1/", "opf": "http://www.idpf.org/2007/opf"}


def parse_opf(path: Path) -> dict | None:
    """Parse a single OPF file into a book dict."""
    try:
        tree = ET.parse(str(path))
        root = tree.getroot()
        meta = root.find(".//{http://www.idpf.org/2007/opf}metadata")
        if meta is None:
            meta = root.find(".//metadata")

        def get(tag):
            el = (
                (meta or root).find(f"dc:{tag}", NS)
                if meta is not None
                else root.find(f".//{tag}")
            )
            return el.text.strip() if el is not None and el.text else ""

        def get_all(tag):
            els = (meta or root).findall(f"dc:{tag}", NS)
            return {el.text.strip() for el in els if el is not None and el.text}

        # Check if this is a Calibre-managed book (has calibre_id) — skip, already in Calibre
        calibre_id_el = root.find(
            ".//*[@{http://www.idpf.org/2007/opf}scheme='calibre']"
        )
        if calibre_id_el is not None:
            return None  # covered by Calibre DB

        title = get("title")
        author = get("creator")
        description = clean_html(get("description"))
        subjects = get_all("subject")

        if not title:
            # Fall back to filename
            stem = path.stem
            parts = stem.split(" - ", 1)
            title = parts[0].strip() if parts else stem
            author = parts[1].strip() if len(parts) > 1 else "Unknown"

        return {
            "source": "opf",
            "calibre_id": None,
            "title": title,
            "author": author,
            "description": description,
            "subjects": subjects,
            "series": "",
        }
    except Exception as e:
        print(f"  WARN: failed to parse {path}: {e}", file=sys.stderr)
        return None


def load_opf_files() -> list[dict]:
    """Scan EBOOKS_ROOT for OPF files not already tracked by Calibre."""
    if not EBOOKS_ROOT.exists():
        print(f"  WARN: Ebooks root not found at {EBOOKS_ROOT}", file=sys.stderr)
        return []

    books = []
    opf_files = list(EBOOKS_ROOT.rglob("*.opf"))
    print(f"  OPF scan: {len(opf_files)} files found", file=sys.stderr)

    for opf_path in opf_files:
        book = parse_opf(opf_path)
        if book:
            books.append(book)

    print(f"  OPF: {len(books)} books not in Calibre", file=sys.stderr)
    return books


def dedup(books: list[dict]) -> list[dict]:
    """Deduplicate by normalized (title, author) — Calibre wins over OPF."""
    seen: dict[tuple, dict] = {}
    for book in books:
        key = (book["title"].lower().strip(), book["author"].lower().strip())
        if key not in seen or book["source"] == "calibre":
            seen[key] = book
    return list(seen.values())


def render_md(books: list[dict], show_skipped: bool = False) -> str:
    """Render the prioritized list as Markdown."""
    tier_labels = {
        0: "P0 — Igor-Curated (Calibre tag: Igor)",
        1: "P1 — Making Money",
        2: "P2 — Pratchett / Igor",
        3: "P3 — Programming & Tech",
        4: "P4 — Non-Fiction",
        5: "P5 — Fiction / Unclassified",
        99: "SKIP — Filtered Out",
    }
    tier_books: dict[int, list] = {k: [] for k in tier_labels}

    for book in books:
        priority, reason = classify(
            book["title"], book["author"], book["subjects"], book["series"]
        )
        book["_priority"] = priority
        book["_reason"] = reason
        tier_books.setdefault(priority, []).append(book)

    lines = ["# Ebook Candidates\n"]
    total_shown = 0

    for tier in sorted(tier_labels.keys()):
        if tier == 99 and not show_skipped:
            skipped = len(tier_books.get(99, []))
            if skipped:
                lines.append(
                    f"\n---\n\n*{skipped} books filtered (romance/erotica) — run with --show-skipped to see them.*\n"
                )
            continue

        bucket = tier_books.get(tier, [])
        if not bucket:
            continue

        bucket.sort(key=lambda b: (b["title"].lower()))
        lines.append(f"\n## {tier_labels[tier]} ({len(bucket)} books)\n")

        for b in bucket:
            series_note = f" *(Series: {b['series']})*" if b.get("series") else ""
            subjects_note = ""
            if b["subjects"]:
                subjects_note = f" `[{', '.join(sorted(b['subjects'])[:5])}]`"
            desc = b["description"]
            desc_line = f"\n  > {desc}" if desc else ""
            lines.append(
                f"- **{b['title']}** — {b['author']}{series_note}{subjects_note}"
                f"  *(source: {b['source']}, reason: {b['_reason']})*"
                f"{desc_line}\n"
            )
            total_shown += 1

    lines.insert(
        1, f"\n*{total_shown} books across all tiers. Generated by scan_ebooks.py.*\n"
    )
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(
        description="Scan ebooks and produce prioritized reading list."
    )
    parser.add_argument(
        "--show-skipped", action="store_true", help="Include filtered books in output"
    )
    parser.add_argument(
        "--dry-run", action="store_true", help="Print to stdout instead of writing file"
    )
    parser.add_argument(
        "--calibre-only",
        action="store_true",
        help="Skip OPF file scan (fast mode — use when all books are in Calibre)",
    )
    args = parser.parse_args()

    print("Scanning ebooks...", file=sys.stderr)
    calibre_books = load_calibre()
    opf_books = [] if args.calibre_only else load_opf_files()

    all_books = dedup(calibre_books + opf_books)
    print(f"  Total after dedup: {len(all_books)} books", file=sys.stderr)

    md = render_md(all_books, show_skipped=args.show_skipped)

    if args.dry_run:
        print(md)
    else:
        OUTPUT.parent.mkdir(parents=True, exist_ok=True)
        OUTPUT.write_text(md, encoding="utf-8")
        print(f"Written to {OUTPUT}", file=sys.stderr)
        # Quick summary to stdout
        lines = md.splitlines()
        for line in lines[:30]:
            print(line)


if __name__ == "__main__":
    main()
