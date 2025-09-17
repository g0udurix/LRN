#!/usr/bin/env python3
"""Batch ingestion scaffold for Phase 1 corpus."""
from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import List


@dataclass
class CorpusEntry:
    url: str
    language: str
    instrument: str


def load_manifest(path: Path) -> List[CorpusEntry]:
    data = json.loads(path.read_text(encoding='utf-8'))
    entries: List[CorpusEntry] = []
    for item in data:
        entries.append(
            CorpusEntry(
                url=item['url'],
                language=item['language'],
                instrument=item.get('instrument', ''),
            )
        )
    return entries


def summarise_run(entries: List[CorpusEntry]) -> dict:
    return {
        'run_timestamp': datetime.now(tz=timezone.utc).isoformat(),
        'entries': [asdict(e) | {'status': 'pending'} for e in entries],
    }


def write_manifest(summary: dict, out_dir: Path) -> Path:
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / 'manifest.json'
    path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding='utf-8')
    return path


def main() -> None:
    parser = argparse.ArgumentParser(description='Generate Phase 1 corpus manifest scaffold')
    parser.add_argument('--manifest', required=True, help='JSON file describing corpus entries')
    parser.add_argument('--out-dir', required=True, help='Output directory for manifest summary')
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    entries = load_manifest(manifest_path)
    summary = summarise_run(entries)
    out_path = write_manifest(summary, Path(args.out_dir))
    print(f"Manifest written to {out_path}")


if __name__ == '__main__':
    main()
