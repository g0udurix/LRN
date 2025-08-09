
#!/usr/bin/env python3
'''Sync repo labels to a fixed set. Usage: GITHUB_TOKEN=.. python scripts/labels_sync.py [owner/repo]
This script is idempotent and uses the REST API directly.
'''
import os, sys, json, urllib.request, urllib.parse
REPO = sys.argv[1] if len(sys.argv)>1 else os.getenv('LRN_REPO','g0udurix/LRN')
TOKEN = os.getenv('GITHUB_TOKEN')
if not TOKEN:
    print('Set GITHUB_TOKEN'); sys.exit(1)
labels = [
  {"name":"area/standards","color":"0366d6","description":"Work related to standards mapping & clauses"},
  {"name":"area/comparison","color":"0e8a16","description":"Cross-jurisdiction comparisons & ranking"},
  {"name":"area/extractor","color":"1d76db","description":"Crawlers, parsers, and ingestion"},
  {"name":"status/Backlog","color":"cccccc"},
  {"name":"status/Todo","color":"5319e7"},
  {"name":"status/Doing","color":"1d76db"},
  {"name":"status/Review","color":"fbca04"},
  {"name":"status/Blocked","color":"b60205"},
  {"name":"status/Done","color":"0e8a16"},
  {"name":"priority/P0","color":"b60205","description":"Must do now"},
  {"name":"priority/P1","color":"d93f0b"},
  {"name":"priority/P2","color":"fbca04"},
  {"name":"priority/P3","color":"cccccc"},
  {"name":"milestone/phase-0","color":"bfd4f2","description":"Phase 0 – Baseline"},
  {"name":"milestone/phase-1","color":"bfd4f2","description":"Phase 1 – Corpus & Standards"},
  {"name":"milestone/phase-2","color":"bfd4f2","description":"Phase 2 – Comparison Engine"},
  {"name":"milestone/phase-3","color":"bfd4f2","description":"Phase 3 – Annotations & Issues"},
  {"name":"milestone/phase-4","color":"bfd4f2","description":"Phase 4 – Guidance UI"},
]
base=f"https://api.github.com/repos/{REPO}/labels"
headers={"Authorization":f"Bearer {TOKEN}","Accept":"application/vnd.github+json","X-GitHub-Api-Version":"2022-11-28"}
req=urllib.request.Request(base, headers=headers)
with urllib.request.urlopen(req) as r:
    existing=json.loads(r.read().decode('utf-8'))
exist={x['name']:x for x in existing}
for lbl in labels:
    name=lbl['name']
    if name in exist:
        url=f"{base}/{urllib.parse.quote(name, safe='')}"
        data=json.dumps({k:v for k,v in lbl.items() if k!='name'}).encode('utf-8')
        req=urllib.request.Request(url, headers=headers, method='PATCH', data=data)
        try:
            urllib.request.urlopen(req); print('[OK] updated', name)
        except Exception as e:
            print('[WARN] update failed', name, e)
    else:
        data=json.dumps(lbl).encode('utf-8')
        req=urllib.request.Request(base, headers=headers, method='POST', data=data)
        try:
            urllib.request.urlopen(req); print('[OK] created', name)
        except Exception as e:
            print('[WARN] create failed', name, e)
