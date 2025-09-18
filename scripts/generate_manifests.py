#!/usr/bin/env python3
"""Utility to generate manifest JSON files from a CSV roster."""
from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from pathlib import Path

FIELD_NAMES = [
    "slug",
    "url",
    "language",
    "instrument",
    "category",
    "requires_headless",
    "content_type",
    "issue_ref",
    "notes",
    "status",
]

DEFAULTS = {
    "category": "unknown",
    "requires_headless": "false",
    "content_type": "html",
    "status": "active",
}


def load_roster(path: Path) -> dict[str, list[dict[str, str]]]:
    grouped: dict[str, list[dict[str, str]]] = defaultdict(list)
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        missing = [field for field in ["slug", "url", "language"] if field not in reader.fieldnames]
        if missing:
            raise ValueError(f"Roster missing required columns: {missing}")
        for row in reader:
            slug = row.get("slug", "").strip()
            if not slug:
                raise ValueError(f"Row missing slug: {row}")
            entry = {field: row.get(field, '').strip() for field in FIELD_NAMES if field != "slug"}
            for key, default in DEFAULTS.items():
                if not entry.get(key):
                    entry[key] = default
            entry["requires_headless"] = entry["requires_headless"].lower() in {"true", "1", "yes"}
            grouped[slug].append(entry)
    return grouped


def write_manifests(manifests: dict[str, list[dict[str, str]]], out_dir: Path, preview: bool) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    for slug, entries in manifests.items():
        path = out_dir / f"{slug}.json"
        if preview:
            print(f"[PREVIEW] Would write {path}")
            continue
        for entry in entries:
            if entry.get("content_type") not in {"html", "pdf", "json"}:
                raise ValueError(f"Invalid content_type for {slug}: {entry['content_type']}")
        json_payload = json.dumps(entries, ensure_ascii=False, indent=2) + "\n"
        path.write_text(json_payload, encoding="utf-8")
        print(f"[WRITE] {path}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Generate manifests from roster CSV")
    parser.add_argument("--roster", type=Path, default=Path("docs/corpus/roster/who_members.csv"))
    parser.add_argument("--out-dir", type=Path, default=Path("docs/corpus/manifests"))
    parser.add_argument("--preview", action="store_true", help="Show actions without writing files")
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    manifests = load_roster(args.roster)
    write_manifests(manifests, args.out_dir, args.preview)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
