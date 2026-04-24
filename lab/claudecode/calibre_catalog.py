#!/usr/bin/env python3
"""
calibre_catalog.py — Scan Calibre library and produce a CSV catalog with topic tags.

Reads all metadata.opf files in the Calibre library, extracts metadata,
infers topic tags from subjects + title + description keywords, outputs CSV.

Usage:
  python3 claudecode/calibre_catalog.py                          # → calibre_catalog.csv
  python3 claudecode/calibre_catalog.py --out /tmp/books.csv
  python3 claudecode/calibre_catalog.py --no-description        # skip description column
  python3 claudecode/calibre_catalog.py --limit 100             # first N books only

Output columns:
  calibre_id, title, authors, publisher, year, subjects,
  topic_tags, rating, formats, description
"""

import argparse
import csv
import os
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

# ── Topic tag rules — keyword → tag  ────────────────────────────────────────
# Checked against: title + subjects (joined, lowercased).
# First matching rule wins per tag; a book can have many tags.

TOPIC_RULES: list[tuple[str, list[str]]] = [
    (
        "ai_ml",
        [
            "artificial intelligence",
            "machine learning",
            "neural network",
            "deep learning",
            "llm",
            "language model",
            "natural language",
            "nlp",
            "reinforcement learning",
            "computer vision",
            "robotics",
            "intelligence (ai)",
            "ai ",
            " ai,",
            "openai",
            "chatgpt",
            "gpt",
        ],
    ),
    (
        "neuroscience",
        [
            "neuroscience",
            "neurology",
            "brain",
            "cortex",
            "neuron",
            "consciousness",
            "cognition",
            "cognitive science",
            "cognitive psychology",
            "perception",
            "memory",
            "damasio",
            "neurotransmitter",
            "synaptic",
            "prefrontal",
            "amygdala",
            "hippocampus",
        ],
    ),
    (
        "psychology",
        [
            "psychology",
            "psychotherapy",
            "behavioural",
            "behavioral",
            "motivation",
            "emotion",
            "personality",
            "psychiatry",
            "mental health",
            "wellbeing",
            "well-being",
            "cognitive behaviour",
            "cognitive behavior",
        ],
    ),
    (
        "philosophy",
        [
            "philosophy",
            "ethics",
            "epistemology",
            "metaphysics",
            "logic",
            "phenomenology",
            "ontology",
            "consciousness (philosophy)",
        ],
    ),
    (
        "fiction_sf",
        [
            "science fiction",
            "sci-fi",
            "sf ",
            " sf,",
            "speculative fiction",
            "space opera",
            "cyberpunk",
            "dystopia",
            "alternate history",
        ],
    ),
    (
        "fiction_fantasy",
        [
            "fantasy",
            "sword and sorcery",
            "epic fantasy",
            "urban fantasy",
            "magic",
            "pratchett",
            "discworld",
            "tolkien",
        ],
    ),
    (
        "fiction_general",
        [
            "fiction",
            "literary fiction",
            "novel",
            "short stories",
        ],
    ),
    (
        "computing",
        [
            "computer science",
            "software",
            "programming",
            "algorithms",
            "operating system",
            "database",
            "distributed",
            "systems",
            "python ",
            " c++",
            "java ",
            "linux",
            "unix",
        ],
    ),
    (
        "mathematics",
        [
            "mathematics",
            "statistics",
            "probability",
            "calculus",
            "linear algebra",
            "number theory",
            "combinatorics",
        ],
    ),
    (
        "biography",
        [
            "biography",
            "autobiography",
            "memoir",
            "personal narrative",
            "life story",
        ],
    ),
    (
        "business_management",
        [
            "business",
            "management",
            "leadership",
            "entrepreneurship",
            "productivity",
            "organization",
            "strategy",
            "marketing",
        ],
    ),
    (
        "self_help",
        [
            "self-help",
            "self help",
            "personal development",
            "habit",
            "motivation",
            "success",
            "mindset",
            "life improvement",
        ],
    ),
    (
        "history",
        [
            "history",
            "historical",
            "world war",
            "ancient",
            "medieval",
            "renaissance",
            "revolution",
        ],
    ),
    (
        "science_general",
        [
            "science",
            "physics",
            "chemistry",
            "biology",
            "evolution",
            "cosmology",
            "astronomy",
            "genetics",
        ],
    ),
    (
        "linguistics",
        [
            "linguistics",
            "language",
            "grammar",
            "syntax",
            "semantics",
            "pragmatics",
            "sociolinguistics",
            "lexicography",
            "etymology",
        ],
    ),
]

# ── XML namespace helpers ────────────────────────────────────────────────────

NS = {
    "opf": "http://www.idpf.org/2007/opf",
    "dc": "http://purl.org/dc/elements/1.1/",
}

# Register so ET.tostring shows clean tags (not needed for find, but cleaner)
for _prefix, _uri in NS.items():
    ET.register_namespace(_prefix, _uri)


def _text(root: ET.Element, tag: str, ns_key: str) -> str:
    el = root.find(f".//{{{NS[ns_key]}}}{tag}")
    return (el.text or "").strip() if el is not None else ""


def _all_text(root: ET.Element, tag: str, ns_key: str) -> list[str]:
    return [
        (el.text or "").strip()
        for el in root.findall(f".//{{{NS[ns_key]}}}{tag}")
        if el.text
    ]


def _meta(root: ET.Element, name: str) -> str:
    for el in root.findall(f".//{{{NS['opf']}}}meta"):
        if el.get("name") == name:
            return (el.get("content") or "").strip()
    # Also check bare <meta> without namespace
    for el in root.iter("meta"):
        if el.get("name") == name:
            return (el.get("content") or "").strip()
    return ""


def infer_tags(title: str, subjects: list[str]) -> list[str]:
    """Return topic tags inferred from title + subjects."""
    haystack = " ".join([title] + subjects).lower()
    tags = []
    for tag, keywords in TOPIC_RULES:
        if any(kw in haystack for kw in keywords):
            tags.append(tag)
    return tags


def parse_opf(opf_path: Path, include_description: bool = True) -> dict | None:
    """Parse a single metadata.opf file. Returns dict or None on error."""
    try:
        tree = ET.parse(opf_path)
    except ET.ParseError:
        return None

    root = tree.getroot()
    metadata = root.find(f"{{{NS['opf']}}}metadata")
    if metadata is None:
        metadata = root  # some files have metadata directly under root

    # Calibre ID
    calibre_id = ""
    for el in metadata.iter():
        if el.get(f"{{{NS['opf']}}}scheme") == "calibre":
            calibre_id = (el.text or "").strip()
            break

    title = _text(metadata, "title", "dc")
    authors = "; ".join(_all_text(metadata, "creator", "dc"))
    publisher = _text(metadata, "publisher", "dc")
    date_raw = _text(metadata, "date", "dc")
    year = date_raw[:4] if len(date_raw) >= 4 else ""
    subjects = _all_text(metadata, "subject", "dc")
    description = ""
    if include_description:
        raw_desc = _text(metadata, "description", "dc")
        # Strip any XML/HTML markup from description
        import re as _re

        raw_desc = _re.sub(r"<[^>]+>", " ", raw_desc)
        raw_desc = _re.sub(r"\s+", " ", raw_desc).strip()
        description = raw_desc[:400] + "…" if len(raw_desc) > 400 else raw_desc

    rating_raw = _meta(root, "calibre:rating")
    rating = rating_raw if rating_raw else ""

    # Detect available formats from sibling files
    book_dir = opf_path.parent
    formats = sorted(
        {
            p.suffix.lstrip(".").lower()
            for p in book_dir.iterdir()
            if p.suffix.lower()
            in {
                ".epub",
                ".mobi",
                ".pdf",
                ".azw",
                ".azw3",
                ".lit",
                ".lrf",
                ".cbz",
                ".cbr",
                ".djvu",
                ".fb2",
                ".rtf",
                ".txt",
                ".docx",
            }
        }
    )

    topic_tags = infer_tags(title, subjects)

    return {
        "calibre_id": calibre_id,
        "title": title,
        "authors": authors,
        "publisher": publisher,
        "year": year,
        "subjects": "; ".join(subjects),
        "topic_tags": "; ".join(topic_tags),
        "rating": rating,
        "formats": "; ".join(formats),
        "description": description,
    }


def scan_library(
    library_path: Path, limit: int | None, include_description: bool
) -> list[dict]:
    """Walk Calibre library, parse each OPF, return list of book dicts."""
    books = []
    opf_files = sorted(library_path.rglob("metadata.opf"))
    if limit:
        opf_files = opf_files[:limit]

    total = len(opf_files)
    for i, opf_path in enumerate(opf_files, 1):
        if i % 500 == 0 or i == total:
            print(f"  {i}/{total} scanned…", flush=True)
        book = parse_opf(opf_path, include_description)
        if book:
            books.append(book)

    return books


def write_csv(books: list[dict], out_path: Path, include_description: bool) -> None:
    fields = [
        "calibre_id",
        "title",
        "authors",
        "publisher",
        "year",
        "subjects",
        "topic_tags",
        "rating",
        "formats",
    ]
    if include_description:
        fields.append("description")

    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(books)

    print(f"Wrote {len(books)} books → {out_path}")


def print_tag_summary(books: list[dict]) -> None:
    from collections import Counter

    tag_counts: Counter = Counter()
    for b in books:
        for t in b.get("topic_tags", "").split("; "):
            if t:
                tag_counts[t] += 1
    print("\nTopic tag summary:")
    for tag, count in tag_counts.most_common():
        print(f"  {tag:30s} {count:5d}")
    untagged = sum(1 for b in books if not b.get("topic_tags"))
    print(f"\n  {'(untagged)':30s} {untagged:5d}")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        default="calibre_catalog.csv",
        help="Output CSV path (default: calibre_catalog.csv)",
    )
    parser.add_argument(
        "--library",
        default=None,
        help="Path to Calibre Library dir (auto-detected from paths.py if omitted)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Stop after N books (for testing)",
    )
    parser.add_argument(
        "--no-description",
        dest="include_description",
        action="store_false",
        help="Omit description column (smaller file)",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print topic tag summary after scan",
    )
    args = parser.parse_args()

    # Resolve library path
    if args.library:
        library_path = Path(args.library)
    else:
        # Use paths.py from the project
        project_root = Path(__file__).parent.parent
        sys.path.insert(0, str(project_root))
        # T-scan-ebooks-use-paths-abstraction: paths().calibre_library is the
        # single source of truth (EBOOKS_ROOT / CALIBRE_LIBRARY_PATH overrides
        # handled inside). The previous hardcoded fallback was user-hostile
        # for any other checkout.
        from wild_igor.igor.paths import paths

        library_path = paths().calibre_library

    if not library_path.exists():
        print(f"ERROR: Calibre library not found at: {library_path}", file=sys.stderr)
        sys.exit(1)

    print(f"Scanning {library_path}")
    books = scan_library(library_path, args.limit, args.include_description)
    print(f"Found {len(books)} books")

    out_path = Path(args.out)
    write_csv(books, out_path, args.include_description)

    if args.summary:
        print_tag_summary(books)


if __name__ == "__main__":
    main()
