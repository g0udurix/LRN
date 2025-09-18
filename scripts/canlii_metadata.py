#!/usr/bin/env python3
"""Helper for querying CanLII metadata for OHS instruments."""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import requests

API_ROOT = "https://api.canlii.org/v1"
REQUEST_DELAY = 0.6  # respect 2 req/sec limit with room to spare


class CanlIIAuthError(RuntimeError):
    """Raised when the API key is missing or rejected."""


def load_api_key() -> str:
    key = os.getenv("CANLII_API_KEY")
    if key:
        return key.strip()
    dotenv = Path(".env")
    if dotenv.exists():
        for line in dotenv.read_text().splitlines():
            if line.startswith("CANLII_API_KEY="):
                return line.split("=", 1)[1].strip()
    raise CanlIIAuthError("Set CANLII_API_KEY in the environment or .env (not committed).")


def get(
    session: requests.Session,
    endpoint: str,
    *,
    key: str,
    params: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    url = f"{API_ROOT}/{endpoint.lstrip('/')}"
    headers = {
        "X-API-Key": key,
        "Accept": "application/json",
    }
    params = dict(params or {})
    params.setdefault("api_key", key)
    response = session.get(url, headers=headers, params=params)
    if response.status_code in {401, 403}:
        raise CanlIIAuthError(
            "CanLII API rejected the request (check API key status and access permissions)."
        )
    response.raise_for_status()
    time.sleep(REQUEST_DELAY)
    return response.json()


def list_jurisdictions(session: requests.Session, key: str) -> List[Dict[str, Any]]:
    payload = get(session, "jurisdictions", key=key)
    return payload.get("jurisdictions", [])


def list_legislation_databases(session: requests.Session, key: str, lang: str) -> List[Dict[str, Any]]:
    payload = get(session, f"legislationBrowse/{lang}/", key=key)
    return payload.get("legislationDatabases", [])


def browse_legislation(
    session: requests.Session,
    key: str,
    lang: str,
    database_id: str,
) -> List[Dict[str, Any]]:
    endpoint = f"legislationBrowse/{lang}/{database_id}/"
    payload = get(session, endpoint, key=key)
    return payload.get("legislations", [])


def filter_entries(entries: Iterable[Dict[str, Any]], keywords: Iterable[str]) -> List[Dict[str, Any]]:
    lowered = [kw.lower() for kw in keywords]
    results: List[Dict[str, Any]] = []
    for entry in entries:
        label = entry.get("title", "") or entry.get("ref", "")
        target = label.lower()
        if all(kw in target for kw in lowered):
            results.append(entry)
    return results


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("jurisdiction", help="Jurisdiction code (e.g., qc, on, ca)")
    parser.add_argument(
        "--language",
        "-l",
        default="en",
        choices=["en", "fr"],
        help="Language for metadata (default: en)",
    )
    parser.add_argument(
        "--database",
        "-d",
        help="Specific legislation database id (e.g., qcs for QC statutes, qcr for QC regulations).",
    )
    parser.add_argument(
        "--list-databases",
        action="store_true",
        help="List available legislation databases for the language and exit.",
    )
    parser.add_argument(
        "--match",
        nargs="*",
        default=[],
        help="Keyword filter (logical AND across tokens) to narrow results",
    )
    parser.add_argument(
        "--raw",
        action="store_true",
        help="Dump full JSON payload instead of filtered summary",
    )
    parser.add_argument(
        "--out",
        type=Path,
        help="Optional path to write JSON output",
    )
    args = parser.parse_args(argv)

    session = requests.Session()
    try:
        key = load_api_key()
    except CanlIIAuthError as exc:  # pragma: no cover - configuration error
        parser.error(str(exc))

    jurisdiction = args.jurisdiction.lower()

    try:
        if args.list_databases or not args.database:
            dbs = list_legislation_databases(session, key, args.language)
        else:
            dbs = []
    except CanlIIAuthError as exc:
        parser.error(str(exc))

    if args.list_databases or not args.database:
        results = [db for db in dbs if db.get("jurisdiction") == jurisdiction]
        if args.list_databases:
            output = results or dbs
            print(json.dumps(output, indent=2, ensure_ascii=False))
            return 0
        if not results:
            parser.error(
                f"No legislation database found for jurisdiction '{jurisdiction}'. Use --list-databases to inspect availability."
            )
        # default to first database found for jurisdiction if not provided explicitly
        database_id = results[0]["databaseId"]
    else:
        database_id = args.database

    try:
        entries = browse_legislation(session, key, args.language, database_id)
    except CanlIIAuthError as exc:
        parser.error(str(exc))
    if args.match:
        entries = filter_entries(entries, args.match)

    if args.raw:
        output = {
            "database": database_id,
            "jurisdiction": jurisdiction,
            "language": args.language,
            "entries": entries,
        }
    else:
        output = [
            {
                "title": entry.get("title"),
                "cite": entry.get("citation"),
                "canlii_uri": entry.get("canliiUri"),
                "enactment": entry.get("enactment"),
                "type": entry.get("type"),
            }
            for entry in entries
        ]

    if args.out:
        args.out.write_text(json.dumps(output, indent=2, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(output, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
