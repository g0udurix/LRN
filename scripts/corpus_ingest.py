#!/usr/bin/env python3
"""Batch ingestion command for Phase 1 corpus."""
from __future__ import annotations

import argparse
import csv
import json
import time
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional

import requests
from requests.utils import requote_uri


@dataclass
class CorpusEntry:
    url: str
    language: str
    instrument: str


@dataclass
class FetchResult:
    entry: CorpusEntry
    status: str
    path: Optional[Path]
    bytes: Optional[int]
    sha256: Optional[str]
    error: Optional[str]
    fetched_at: Optional[str]


@dataclass
class IngestOptions:
    out_dir: Path
    log_dir: Path
    timeout: int
    retries: int
    delay: float
    resume: bool
    user_agent: str = "LRN/CorpusIngest"


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


def _sha256(data: bytes) -> str:
    import hashlib

    h = hashlib.sha256()
    h.update(data)
    return h.hexdigest()


def fetch_entry(entry: CorpusEntry, session: requests.Session, options: IngestOptions) -> FetchResult:
    target_dir = options.out_dir / entry.instrument
    target_dir.mkdir(parents=True, exist_ok=True)
    target_path = target_dir / f"{entry.language}.html"

    if options.resume and target_path.exists():
        data = target_path.read_bytes()
        return FetchResult(
            entry=entry,
            status='skipped',
            path=target_path,
            bytes=len(data),
            sha256=_sha256(data),
            error=None,
            fetched_at=None,
        )

    attempt = 0
    last_error: Optional[str] = None
    while attempt <= options.retries:
        try:
            url = requote_uri(entry.url)
            headers: Dict[str, str] = {'Accept-Language': 'fr-CA,fr;q=0.9'} if entry.language.lower().startswith('fr') else {'Accept-Language': 'en-CA,en;q=0.9'}
            response = session.get(url, timeout=options.timeout, headers=headers)
            response.raise_for_status()
            data = response.content
            target_path.write_bytes(data)
            return FetchResult(
                entry=entry,
                status='fetched',
                path=target_path,
                bytes=len(data),
                sha256=_sha256(data),
                error=None,
                fetched_at=datetime.now(tz=timezone.utc).isoformat(),
            )
        except Exception as exc:  # pragma: no cover - network dependent
            last_error = str(exc)
            attempt += 1
            if attempt > options.retries:
                break
            time.sleep(options.delay or 0.0)
    return FetchResult(
        entry=entry,
        status='failed',
        path=target_path if target_path.exists() else None,
        bytes=None,
        sha256=None,
        error=last_error,
        fetched_at=None,
    )


def write_reports(results: List[FetchResult], log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    json_path = log_dir / 'manifest.json'
    csv_path = log_dir / 'manifest.csv'

    payload = [
        {
            'url': r.entry.url,
            'instrument': r.entry.instrument,
            'language': r.entry.language,
            'status': r.status,
            'path': str(r.path) if r.path else None,
            'bytes': r.bytes,
            'sha256': r.sha256,
            'error': r.error,
            'fetched_at': r.fetched_at,
        }
        for r in results
    ]
    json_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding='utf-8')

    with csv_path.open('w', encoding='utf-8', newline='') as fh:
        writer = csv.DictWriter(
            fh,
            fieldnames=['url', 'instrument', 'language', 'status', 'path', 'bytes', 'sha256', 'error', 'fetched_at'],
        )
        writer.writeheader()
        writer.writerows(payload)


def ingest(manifest: Path, options: IngestOptions) -> List[FetchResult]:
    entries = load_manifest(manifest)
    session = requests.Session()
    if not hasattr(session, 'headers'):
        session.headers = {}
    session.headers.setdefault('User-Agent', options.user_agent)

    results: List[FetchResult] = []
    for entry in entries:
        result = fetch_entry(entry, session, options)
        results.append(result)
        if options.delay and result.status == 'fetched':
            time.sleep(options.delay)
    timestamp = datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')
    log_dir = options.log_dir / timestamp
    write_reports(results, log_dir)
    return results


def main() -> None:
    parser = argparse.ArgumentParser(description='Batch ingest LegisQuébec corpus entries')
    parser.add_argument('--manifest', required=True, help='Path to manifest JSON (list of entries)')
    parser.add_argument('--out-dir', required=True, help='Directory to store fetched HTML')
    parser.add_argument('--log-dir', default='logs/ingestion', help='Directory for run manifests (default: logs/ingestion)')
    parser.add_argument('--timeout', type=int, default=30, help='Request timeout in seconds (default: 30)')
    parser.add_argument('--retries', type=int, default=2, help='Number of retry attempts (default: 2)')
    parser.add_argument('--delay', type=float, default=1.0, help='Delay (seconds) between successful fetches (default: 1.0)')
    parser.add_argument('--resume', action='store_true', help='Skip downloads if target file already exists')
    args = parser.parse_args()

    options = IngestOptions(
        out_dir=Path(args.out_dir),
        log_dir=Path(args.log_dir),
        timeout=args.timeout,
        retries=args.retries,
        delay=args.delay,
        resume=args.resume,
    )
    results = ingest(Path(args.manifest), options)
    successes = sum(1 for r in results if r.status == 'fetched')
    failures = sum(1 for r in results if r.status == 'failed')
    print(f"Ingestion complete: {successes} fetched, {failures} failed (logs in {options.log_dir})")


if __name__ == '__main__':
    main()
