#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
labels_sync.py — idempotent GitHub labels sync

Usage:
  python scripts/labels_sync.py --repo owner/repo

Auth:
  Uses GITHUB_TOKEN (default) or LABELS_SYNC_PAT / GH_TOKEN if provided.
"""
import os, sys, json, argparse, urllib.request, urllib.error, urllib.parse

LABELS = [
    ("priority/P0", "Blocker", "b60205"),
    ("priority/P1", "High", "d73a4a"),
    ("priority/P2", "Normal", "fbca04"),
    ("area/extractor", "Ingestion & crawling", "1d76db"),
    ("area/schema", "Database schema/migrations", "1d76db"),
    ("area/standards", "Standards mapping", "1d76db"),
    ("area/comparison", "Matrix/ranking engine", "1d76db"),
    ("area/annotations", "Notes, issues, orientations", "1d76db"),
    ("area/app", "API/UI", "1d76db"),
    ("jurisdiction/QC", "Québec", "0e8a16"),
    ("jurisdiction/CA", "Canada (Fed)", "0e8a16"),
    ("jurisdiction/US", "United States", "0e8a16"),
    ("jurisdiction/UK", "United Kingdom", "0e8a16"),
    ("jurisdiction/FR", "France", "0e8a16"),
    ("jurisdiction/DE", "Germany", "0e8a16"),
    ("jurisdiction/JP", "Japan", "0e8a16"),
    ("jurisdiction/AU", "Australia", "0e8a16"),
    ("standard/CSA", "CSA", "5319e7"), ("standard/ANSI", "ANSI", "5319e7"),
    ("standard/ISO", "ISO", "5319e7"), ("standard/EN", "EN", "5319e7"),
    ("standard/BS", "BSI", "5319e7"), ("standard/AS", "AS/NZS", "5319e7"),
    ("standard/JIS", "JIS", "5319e7"),
    ("documentation", "Docs & READMEs", "c5def5"),
    ("needs-triage", "New items to triage", "ededed"),
    ("status/Backlog", "Backlog", "8b949e"),
    ("status/Todo", "To-do", "8b949e"),
    ("status/Doing", "In progress", "8b949e"),
    ("status/Blocked", "Blocked", "d93f0b"),
    ("status/Review", "In review", "a371f7"),
    ("status/Done", "Done", "0e8a16"),
]

API = "https://api.github.com"

class Api:
    def __init__(self, token: str):
        self.token = token
    def call(self, method: str, path: str, data: dict | None = None):
        url = API + path
        req = urllib.request.Request(url, method=method)
        req.add_header('Accept', 'application/vnd.github+json')
        if self.token:
            req.add_header('Authorization', f'Bearer {self.token}')
        body = None
        if data is not None:
            body = json.dumps(data).encode('utf-8')
            req.add_header('Content-Type', 'application/json')
        try:
            with urllib.request.urlopen(req, body) as resp:
                raw = resp.read().decode('utf-8')
                return resp.getcode(), (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read().decode('utf-8')
            try:
                payload = json.loads(raw)
            except Exception:
                payload = raw
            return e.code, payload


def ensure_label(api: Api, owner: str, repo: str, name: str, color: str, desc: str):
    # Try create
    code, _ = api.call('POST', f'/repos/{owner}/{repo}/labels', {
        'name': name,
        'color': color,
        'description': desc
    })
    if code in (200, 201):
        print(f"[created] {name}")
        return True
    # If exists, patch
    code2, _ = api.call('PATCH', f"/repos/{owner}/{repo}/labels/{urllib.parse.quote(name, safe='')} ", {
        'new_name': name,
        'color': color,
        'description': desc
    })
    if code2 == 200:
        print(f"[updated] {name}")
        return True
    print(f"[failed] {name} (codes: create={code} patch={code2})")
    return False


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--repo', required=True, help='owner/repo')
    args = ap.parse_args()
    owner, repo = args.repo.split('/', 1)
    token = os.getenv('LABELS_SYNC_PAT') or os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
    if not token:
        print('ERROR: set GITHUB_TOKEN (repo write) or LABELS_SYNC_PAT')
        sys.exit(2)
    api = Api(token)
    ok = True
    for name, desc, color in LABELS:
        ok = ensure_label(api, owner, repo, name, color, desc) and ok
    sys.exit(0 if ok else 1)

if __name__ == '__main__':
    main()
