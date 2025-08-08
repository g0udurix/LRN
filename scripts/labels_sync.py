#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Idempotent labels sync (uses GitHub API)."""
import os, sys, json, argparse, urllib.request, urllib.parse, urllib.error
LABELS = [
    ("priority/P0","Blocker","b60205"),("priority/P1","High","d73a4a"),("priority/P2","Normal","fbca04"),
    ("area/extractor","Ingestion & crawling","1d76db"),("area/schema","Database schema/migrations","1d76db"),
    ("area/standards","Standards mapping","1d76db"),("area/comparison","Matrix/ranking engine","1d76db"),
    ("area/annotations","Notes, issues, orientations","1d76db"),("area/app","API/UI","1d76db"),
    ("jurisdiction/QC","Québec","0e8a16"),("jurisdiction/CA","Canada (Fed)","0e8a16"),
    ("jurisdiction/US","United States","0e8a16"),("jurisdiction/UK","United Kingdom","0e8a16"),
    ("jurisdiction/FR","France","0e8a16"),("jurisdiction/DE","Germany","0e8a16"),
    ("jurisdiction/JP","Japan","0e8a16"),("jurisdiction/AU","Australia","0e8a16"),
    ("standard/CSA","CSA","5319e7"),("standard/ANSI","ANSI","5319e7"),("standard/ISO","ISO","5319e7"),
    ("standard/EN","EN","5319e7"),("standard/BS","BSI","5319e7"),("standard/AS","AS/NZS","5319e7"),
    ("standard/JIS","JIS","5319e7"),("documentation","Docs & READMEs","c5def5"),("needs-triage","New items to triage","ededed"),
    ("status/Backlog","Backlog","8b949e"),("status/Todo","To-do","8b949e"),("status/Doing","In progress","8b949e"),
    ("status/Blocked","Blocked","d93f0b"),("status/Review","In review","a371f7"),("status/Done","Done","0e8a16"),
]
API="https://api.github.com"
class Api:
  def __init__(self, tok): self.tok=tok
  def call(self, m, p, d=None):
    u=API+p; r=urllib.request.Request(u, method=m); r.add_header('Accept','application/vnd.github+json');
    if self.tok: r.add_header('Authorization', f'Bearer {self.tok}')
    b=None
    if d is not None:
      b=json.dumps(d).encode('utf-8'); r.add_header('Content-Type','application/json')
    try:
      with urllib.request.urlopen(r,b) as resp:
        raw=resp.read().decode('utf-8'); return resp.getcode(), (json.loads(raw) if raw else None)
    except urllib.error.HTTPError as e:
      raw=e.read().decode('utf-8');
      try: pl=json.loads(raw)
      except Exception: pl=raw
      return e.code, pl

def up(api, owner, repo, name, color, desc):
  c,_=api.call('POST', f'/repos/{owner}/{repo}/labels', {'name':name,'color':color,'description':desc})
  if c in (200,201): print('[created]',name); return True
  c2,_=api.call('PATCH', f"/repos/{owner}/{repo}/labels/{urllib.parse.quote(name, safe='')}", {'new_name':name,'color':color,'description':desc})
  if c2==200: print('[updated]',name); return True
  print('[failed]', name, 'codes', c, c2); return False

def main():
  import argparse
  ap=argparse.ArgumentParser(); ap.add_argument('--repo',required=True); args=ap.parse_args(); owner,repo=args.repo.split('/')
  tok=os.getenv('LABELS_SYNC_PAT') or os.getenv('GITHUB_TOKEN') or os.getenv('GH_TOKEN')
  if not tok: print('ERROR: set GITHUB_TOKEN'); sys.exit(2)
  api=Api(tok); ok=True
  for n,d,c in LABELS: ok=up(api, owner, repo, n, c, d) and ok
  sys.exit(0 if ok else 1)
if __name__=='__main__': main()
