#!/usr/bin/env python3
"""Report manifest coverage based on roster and available JSON files."""
from __future__ import annotations

import argparse
import csv
from pathlib import Path


def load_roster(path: Path) -> list[dict[str, str]]:
    if not path.exists():
        return []
    with path.open(encoding='utf-8') as handle:
        reader = csv.DictReader(handle)
        return list(reader)


def main() -> int:
    parser = argparse.ArgumentParser(description="Report manifest coverage")
    parser.add_argument("--roster", type=Path, default=Path("docs/corpus/roster/who_members.csv"))
    parser.add_argument("--manifest-dir", type=Path, default=Path("docs/corpus/manifests"))
    args = parser.parse_args()

    roster = load_roster(args.roster)
    manifests = {path.stem for path in args.manifest_dir.glob('*.json')}

    total = len(roster)
    done = 0
    pending = []
    for row in roster:
        slug = row.get('slug', '')
        status = row.get('status', '').lower()
        if slug in manifests and status == 'done':
            done += 1
        else:
            pending.append(slug)

    print(f"Total roster entries: {total}")
    print(f"Done (status=done with manifest): {done}")
    print(f"Remaining (non-done or missing manifest): {total - done}")
    print("Next 10 pending:")
    for slug in pending[:10]:
        print(f" - {slug}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
