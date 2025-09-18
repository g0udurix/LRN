#!/usr/bin/env python3
"""Seed WHO roster CSV with placeholder rows for member states."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import requests

WHO_MEMBERS_SOURCE = "https://restcountries.com/v3.1/all?fields=name,cca2,cca3"


def fetch_countries() -> list[dict[str, str]]:
    resp = requests.get(WHO_MEMBERS_SOURCE, timeout=60, headers={'User-Agent': 'LRN/ManifestGenerator'})
    resp.raise_for_status()
    data = resp.json()
    countries: list[dict[str, str]] = []
    for entry in data:
        name = entry.get("name", {}).get("common")
        if not name:
            continue
        cca3 = entry.get("cca3") or entry.get("cca2") or name[:3].upper()
        countries.append({
            "slug": name.lower().replace(" ", "_").replace("'", ""),
            "iso": cca3,
            "country": name,
        })
    countries.sort(key=lambda c: c["country"])
    return countries


def load_existing(path: Path) -> set[str]:
    if not path.exists():
        return set()
    with path.open(encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        return {row.get("slug", "") for row in reader}


def append_rows(path: Path, countries: list[dict[str, str]]) -> None:
    existing = load_existing(path)
    is_new = not path.exists()
    with path.open("a", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=[
            "slug",
            "country",
            "iso",
            "url",
            "language",
            "instrument",
            "category",
            "requires_headless",
            "content_type",
            "issue_ref",
            "notes",
            "status",
        ])
        if is_new:
            writer.writeheader()
        for entry in countries:
            if entry["slug"] in existing:
                continue
            writer.writerow({
                "slug": entry["slug"],
                "country": entry["country"],
                "iso": entry["iso"],
                "url": "",  # to be filled
                "language": "",
                "instrument": "",
                "category": "unknown",
                "requires_headless": "false",
                "content_type": "html",
                "issue_ref": "",
                "notes": "WHO member placeholder",
                "status": "todo",
            })
            print(f"[ADD] {entry['country']} ({entry['slug']})")


def main() -> int:
    parser = argparse.ArgumentParser(description="Seed WHO roster CSV with placeholder rows")
    parser.add_argument("--out", type=Path, default=Path("docs/corpus/roster/who_members.csv"))
    args = parser.parse_args()

    countries = fetch_countries()
    append_rows(args.out, countries)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
