#!/usr/bin/env python3
"""Check manifests for updated instruments and archive new versions."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path
import sys
from typing import Dict, List, Optional
from urllib.parse import urlparse

import requests

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from scripts.corpus_ingest import CorpusEntry, load_manifest

DEFAULT_USER_AGENT = "Mozilla/5.0 (compatible; LRN-UpdateMonitor/1.0; +https://example.com)"
DEFAULT_TIMEOUT = 30
REQUEST_DELAY = 0.0


def sha256_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def detect_extension(url: str, content_type: str) -> str:
    lowered = url.lower()
    if lowered.endswith('.pdf'):
        return '.pdf'
    if lowered.endswith('.json'):
        return '.json'
    if lowered.endswith('.xml'):
        return '.xml'
    if 'resultformat=html' in lowered:
        return '.html'
    if 'pdf' in content_type:
        return '.pdf'
    if 'json' in content_type:
        return '.json'
    if 'xml' in content_type:
        return '.xml'
    return '.html'


def load_state(path: Path) -> Dict[str, Dict[str, object]]:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding='utf-8'))


def save_state(path: Path, state: Dict[str, Dict[str, object]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(state, indent=2, ensure_ascii=False), encoding='utf-8')


def archive_path(base: Path, instrument: str, timestamp: str, suffix: str) -> Path:
    safe = instrument.replace('/', '-').replace(' ', '_')
    return base / safe / f"{timestamp}{suffix}"


def fetch_content(entry: CorpusEntry, session: requests.Session, timeout: int) -> Optional[requests.Response]:
    url = entry.url
    headers = {
        'Accept-Language': 'fr-CA,fr;q=0.9' if entry.language.lower().startswith('fr') else 'en-CA,en;q=0.9',
        'User-Agent': DEFAULT_USER_AGENT,
        'Accept': '*/*',
    }
    if 'resultformat=html' in url.lower():
        headers['Accept'] = 'text/html,application/xhtml+xml'
    host = (urlparse(url).hostname or '').lower()
    if 'api.canlii.org' in host:
        api_key = os.getenv('CANLII_API_KEY')
        if api_key:
            headers['X-API-Key'] = api_key
    response = session.get(url, timeout=timeout, headers=headers)
    response.raise_for_status()
    return response


def monitor_manifest(
    manifest_path: Path,
    archive_dir: Path,
    state_path: Path,
    timeout: int,
) -> Dict[str, Dict[str, object]]:
    entries = load_manifest(manifest_path)
    state = load_state(state_path)
    session = requests.Session()
    summary: Dict[str, Dict[str, object]] = {}
    for entry in entries:
        key = entry.instrument or entry.url
        summary[key] = {
            'url': entry.url,
            'language': entry.language,
            'status': 'unchanged',
        }
        try:
            response = fetch_content(entry, session, timeout)
        except Exception as exc:  # pragma: no cover - network dependent
            summary[key]['status'] = 'error'
            summary[key]['error'] = str(exc)
            continue

        content = response.content
        digest = sha256_digest(content)
        bytes_len = len(content)
        timestamp = datetime.now(tz=timezone.utc).strftime('%Y%m%dT%H%M%SZ')
        prev = state.get(key, {})
        history: List[Dict[str, object]] = list(prev.get('history', []))
        last_hash = history[-1]['sha256'] if history else None

        if digest != last_hash:
            suffix = detect_extension(entry.url, response.headers.get('Content-Type', ''))
            out_path = archive_path(archive_dir, entry.instrument or 'unknown', timestamp, suffix)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_bytes(content)
            history.append(
                {
                    'timestamp': timestamp,
                    'sha256': digest,
                    'bytes': bytes_len,
                    'path': str(out_path),
                }
            )
            summary[key]['status'] = 'updated' if last_hash else 'new'
            summary[key]['bytes'] = bytes_len
            summary[key]['path'] = str(out_path)
        else:
            summary[key]['status'] = 'unchanged'
            summary[key]['bytes'] = bytes_len

        state[key] = {
            'instrument': entry.instrument,
            'url': entry.url,
            'language': entry.language,
            'history': history,
            'last_checked': timestamp,
        }
    save_state(state_path, state)
    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest', required=True, help='Path to manifest JSON to monitor')
    parser.add_argument('--archive-dir', required=True, help='Base directory for archived versions (outside git)')
    parser.add_argument('--state', required=True, help='Path to JSON file storing checksum history')
    parser.add_argument('--timeout', type=int, default=DEFAULT_TIMEOUT, help='HTTP timeout per request (default: 30s)')
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    archive_dir = Path(args.archive_dir)
    state_path = Path(args.state)

    summary = monitor_manifest(manifest_path, archive_dir, state_path, args.timeout)
    print(json.dumps(summary, indent=2, ensure_ascii=False))


if __name__ == '__main__':
    main()
