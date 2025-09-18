#!/usr/bin/env python3
"""Batch ingestion command for Phase 1 corpus."""
from __future__ import annotations

import argparse
import csv
import json
import os
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests
from requests import HTTPError
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


def _should_use_headless(exc: HTTPError, entry: CorpusEntry, suffix: str) -> bool:
    response = exc.response
    if response is None:
        return False
    status = response.status_code
    if suffix == '.pdf':
        return False  # headless PDF capture not yet supported

    host = (urlparse(response.url or entry.url).hostname or '').lower()
    lowered_headers = {key.lower() for key in response.headers.keys()}

    if 'x-datadome' in lowered_headers:
        return True

    datadome_hosts = {
        'canlii.org',
        'ville.quebec.qc.ca',
        'legifrance.gouv.fr',
        'legifrance.fr',
    }
    wafi_hosts = {
        'gov.cn',
        'npc.gov.cn',
    }

    if any(host.endswith(h) for h in datadome_hosts) and status in {403, 429, 500, 503}:
        return True

    if any(host.endswith(h) for h in wafi_hosts) and status in {302, 403, 404, 503}:
        return True

    return False


def _headless_fetch(url: str, timeout: int) -> bytes:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:  # pragma: no cover - optional dep
        raise RuntimeError('Playwright is required for headless fallback') from exc

    timeout_ms = max(timeout * 1000, 10000)
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until='domcontentloaded', timeout=timeout_ms)
        page.wait_for_timeout(2000)
        content = page.content().encode('utf-8')
        browser.close()
    return content


def fetch_entry(entry: CorpusEntry, session: requests.Session, options: IngestOptions) -> FetchResult:
    target_dir = options.out_dir / entry.instrument
    target_dir.mkdir(parents=True, exist_ok=True)

    suffix = '.html'
    lowered_url = entry.url.lower()
    if lowered_url.endswith('.pdf'):
        suffix = '.pdf'
    elif lowered_url.endswith('.json') or 'format=json' in lowered_url:
        suffix = '.json'
    elif 'resultformat=html' in lowered_url:
        suffix = '.html'
    target_path = target_dir / f"{entry.language}{suffix}"

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
            host = (urlparse(url).hostname or '').lower()
            if 'api.canlii.org' in host:
                api_key = os.getenv('CANLII_API_KEY')
                if api_key:
                    headers['X-API-Key'] = api_key
            response = session.get(url, timeout=options.timeout, headers=headers)
            response.raise_for_status()
            data = response.content
            if suffix == '.html' and response.headers.get('Content-Type', '').startswith('application/json'):
                suffix = '.json'
                target_path = target_path.with_suffix('.json')
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
        except HTTPError as exc:  # pragma: no cover - network dependent
            if _should_use_headless(exc, entry, suffix):
                try:
                    data = _headless_fetch(entry.url, options.timeout)
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
                except Exception as headless_exc:  # pragma: no cover - depends on playwright
                    last_error = f"headless fallback failed: {headless_exc}"
            else:
                last_error = str(exc)
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
