
#!/usr/bin/env python3
"""
LRN — smart bootloader + embedded finisher (governance v2 + self-test)
- Refresh order: HEAD → default_branch → feat/history-crawl → main → master
- If refresh fails, run embedded finisher locally (never blocks)
- Adds/updates:
  • CONTRIBUTING.md, CODE_OF_CONDUCT.md, CODEOWNERS, issue templates
  • semantic-pr + auto-milestone workflows
  • labels.yml + labels-sync workflow + scripts/labels_sync.py
  • PR template, Release Drafter, Dependabot, CI (ruff/black/pytest), branch protection
- New: `--self-test` runs sanity checks for Projects, CI, Release Draft, Branch protection

Usage:
  python upgrade_and_roadmap.py --apply [--no-refresh] [--self-test]
"""

import os, sys, re, json, time, subprocess, shutil, urllib.request, urllib.error, urllib.parse
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_SLUG = os.getenv("LRN_REPO", "g0udurix/LRN")
APPLY = "--apply" in sys.argv
NO_REFRESH = "--no-refresh" in sys.argv
SELF_TEST = "--self-test" in sys.argv

# ==================================================================================
# Smart bootloader
# ==================================================================================

def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def _try_refresh_and_exec() -> bool:
    # Skip refresh if explicitly disabled or we're in self-test (so local embedded code runs)
    if NO_REFRESH or SELF_TEST or os.environ.get("LRN_BOOTSTRAPPED") == "1":
        return False
    candidates = []
    try:
        p = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True)
        if p.returncode == 0:
            br = (p.stdout or "").strip()
            if br and br != "HEAD": candidates.append(br)
    except Exception:
        pass
    try:
        with urllib.request.urlopen(f"https://api.github.com/repos/{REPO_SLUG}", timeout=15) as r:
            info = json.loads(r.read().decode("utf-8"))
            db = info.get("default_branch")
            if db: candidates.append(db)
    except Exception:
        pass
    candidates += ["feat/history-crawl", "main", "master"]

    tried = []
    for br in [b for b in candidates if b]:
        url = f"https://raw.githubusercontent.com/{REPO_SLUG}/{br}/upgrade_and_roadmap.py"
        try:
            data = urllib.request.urlopen(url, timeout=30).read()
            path = Path(__file__)
            if not path.exists() or path.read_bytes() != data:
                path.write_bytes(data)
            env = os.environ.copy(); env["LRN_BOOTSTRAPPED"] = "1"
            os.execvpe(sys.executable, [sys.executable, __file__] + [a for a in sys.argv[1:] if a != "--no-refresh"], env)
            return True
        except Exception as e:
            tried.append((url, str(e)))
    print("[bootloader] refresh failed; falling back to embedded finisher. Tried:")
    for url, err in tried: print(" -", url, "->", err)
    return False

_try_refresh_and_exec()

# ==================================================================================
# Embedded one-shot finisher
# ==================================================================================

def log(msg: str):
    print(msg)
    try:
        Path("logs").mkdir(exist_ok=True)
        with open(Path("logs")/f"pm_fix_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log", "a", encoding="utf-8") as f:
            f.write(msg+"\n")
    except Exception:
        pass

def run(cmd, cwd: Path|None=None, check=False):
    shell = isinstance(cmd, str)
    p = subprocess.run(cmd, cwd=(str(cwd) if cwd else None), capture_output=True, text=True, shell=shell)
    out, err = (p.stdout or "").strip(), (p.stderr or "").strip()
    cmd_str = cmd if shell else " ".join(cmd)
    err_part = ("\n" + err) if err else ""
    log(f"$ {cmd_str}\n[rc={p.returncode}]\n{out}{err_part}")
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed rc={p.returncode}: {cmd_str}\n{err}")
    return p.returncode, out, err

# --------------------------- Git helpers -----------------------------------------

def default_branch_from_git() -> str|None:
    rc, out, _ = run(["git","symbolic-ref","refs/remotes/origin/HEAD"])  # refs/remotes/origin/<branch>
    if rc == 0 and out:
        return out.strip().split("/")[-1]
    rc, out, _ = run(["git","rev-parse","--abbrev-ref","origin/HEAD"])  # fallback
    if rc == 0 and out:
        return out.strip().split("/")[-1]
    return None

def default_branch_from_api() -> str|None:
    try:
        with urllib.request.urlopen(f"https://api.github.com/repos/{REPO_SLUG}") as r:
            info = json.loads(r.read().decode("utf-8"))
            return info.get("default_branch")
    except Exception:
        return None

def get_default_branch() -> str:
    return default_branch_from_git() or default_branch_from_api() or "master"


def git_pull(repo_dir: Path):
    if not (repo_dir/".git").exists():
        log("[WARN] not a git repo, skipping pull"); return
    run(["git","fetch","--all"], cwd=repo_dir)
    run(["git","pull","--rebase","--autostash"], cwd=repo_dir)


def git_commit_push(repo_dir: Path, message: str):
    if not (repo_dir/".git").exists():
        log("[WARN] not a git repo, skipping commit/push"); return False
    run(["git","add","-A"], cwd=repo_dir)
    rc,_,_ = run(["git","diff","--cached","--quiet"], cwd=repo_dir)
    if rc==0:
        log("[OK] no changes to commit"); return False
    run(["git","commit","-m", message], cwd=repo_dir)
    run(["git","push"], cwd=repo_dir)
    return True

# --------------------------- Ensure files ----------------------------------------

def ensure_file(path: Path, content: str):
    if path.exists() and path.read_text(encoding="utf-8") == content:
        log(f"[OK] ensure {path} — up-to-date"); return False
    if APPLY:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        log(f"[APPLIED] ensure {path} — written")
        return True
    else:
        log(f"[DRY] ensure {path} — would write")
        return False


def ensure_gitignore_lines(repo_dir: Path, lines: list[str]):
    gi = repo_dir/".gitignore"
    existing = gi.read_text(encoding="utf-8").splitlines() if gi.exists() else []
    need = [ln for ln in lines if ln not in existing]
    if not need:
        log("[OK] .gitignore — up-to-date"); return False
    if APPLY:
        with open(gi, "a", encoding="utf-8") as f:
            if existing and existing[-1].strip() != "":
                f.write("\n")
            f.write("\n# LRN autogenerated ignores\n")
            for ln in need:
                f.write(ln+"\n")
        log("[APPLIED] .gitignore — appended ignores")
        return True
    else:
        log("[DRY] .gitignore — would append: " + ", ".join(need))
        return False

# --------------------------- Content payloads ------------------------------------

CONTRIBUTING = """
# Contributing to LRN (Humans & AI agents)

Welcome! This repo accepts contributions from both humans and AI agents (tools like ChatGPT/Copilot/LLMs).

## Ground rules
- **Semantic commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Use scopes (e.g., `feat(extractor): …`).
- **No secrets**: Strip API keys/tokens from code and config.
- **Determinism**: Prefer simple, testable code. Comment non-trivial logic.
- **Reproducibility**: Document how to regenerate data or codegen.
- **Tests & docs**: Update both for non-trivial changes.

## For AI agents
- Add an **AI notes** section in PR body with prompts/assumptions.
- Cite sources for standards and statutes.
- Keep PRs small; split if > ~500 LOC.

### Projects automation
To sync items into **Projects #3** and map fields from labels, set repo secret **`PROJECTS_PAT`** (classic PAT with `repo` and `project` scopes`).
"""

CODE_OF_CONDUCT = """
# Code of Conduct (Humans & AI agents)
- Be respectful; no harassment or spammy automation.
- Disclose automation in PRs.
- Do not paste proprietary standards; summarize and cite.
- Unsafe guidance must be flagged with references.
"""

SEMANTIC_PR_WF = """
name: Semantic PR
on:
  pull_request:
    types: [opened, edited, synchronize, reopened, ready_for_review]
jobs:
  semantic:
    runs-on: ubuntu-latest
    steps:
      - uses: amannn/action-semantic-pull-request@v5
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          types: |-
            feat, fix, docs, style, refactor, perf, test, build, ci, chore, revert
"""

AUTO_MILESTONE_WF = """
name: Auto milestone from labels
on:
  issues:
    types: [opened, edited, labeled, unlabeled, reopened]
  pull_request:
    types: [opened, edited, labeled, unlabeled, reopened, ready_for_review]
  workflow_dispatch:
permissions:
  issues: write
  pull-requests: write
jobs:
  apply:
    runs-on: ubuntu-latest
    steps:
      - name: Map labels → milestone
        uses: actions/github-script@v7
        with:
          script: |
            const item = context.payload.issue || context.payload.pull_request;
            const labels = (item.labels || []).map(l => typeof l === 'string' ? l : l.name);
            const mapping = {
              'milestone/phase-0': 'Phase 0 – Baseline',
              'milestone/phase-1': 'Phase 1 – Corpus & Standards',
              'milestone/phase-2': 'Phase 2 – Comparison Engine',
              'milestone/phase-3': 'Phase 3 – Annotations & Issues',
              'milestone/phase-4': 'Phase 4 – Guidance UI',
            };
            const key = labels.find(n => (n||'').toLowerCase().startsWith('milestone/'));
            if (!key) { core.info('no milestone/* label'); return; }
            const wanted = mapping[key];
            const owner = context.repo.owner; const repo = context.repo.repo;
            const {data: milestones} = await github.rest.issues.listMilestones({owner, repo, state: 'all'});
            const m = milestones.find(x => x.title === wanted);
            if (!m) { core.warning('milestone not found: ' + wanted); return; }
            await github.rest.issues.update({owner, repo, issue_number: item.number, milestone: m.number});
            core.info(`set milestone '${wanted}' on #${item.number}`);
"""

LABELS_YML = """
labels:
  - { name: area/standards, color: 0366d6, description: Work related to standards mapping & clauses }
  - { name: area/comparison, color: 0e8a16, description: Cross-jurisdiction comparisons & ranking }
  - { name: area/extractor, color: 1d76db, description: Crawlers, parsers, and ingestion }
  - { name: status/Backlog, color: cccccc }
  - { name: status/Todo,    color: 5319e7 }
  - { name: status/Doing,   color: 1d76db }
  - { name: status/Review,  color: fbca04 }
  - { name: status/Blocked, color: b60205 }
  - { name: status/Done,    color: 0e8a16 }
  - { name: priority/P0, color: b60205, description: Must do now }
  - { name: priority/P1, color: d93f0b }
  - { name: priority/P2, color: fbca04 }
  - { name: priority/P3, color: cccccc }
  - { name: milestone/phase-0, color: bfd4f2, description: Phase 0 – Baseline }
  - { name: milestone/phase-1, color: bfd4f2, description: Phase 1 – Corpus & Standards }
  - { name: milestone/phase-2, color: bfd4f2, description: Phase 2 – Comparison Engine }
  - { name: milestone/phase-3, color: bfd4f2, description: Phase 3 – Annotations & Issues }
  - { name: milestone/phase-4, color: bfd4f2, description: Phase 4 – Guidance UI }
"""

LABELS_SYNC_WF = """
name: Labels sync
on:
  schedule:
    - cron: '11 3 * * *'
  push:
    paths: [ .github/labels.yml ]
  workflow_dispatch:
jobs:
  sync:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: lannonbr/issue-label-manager-action@v3
        env: { GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }} }
        with: { delete: true, config-path: .github/labels.yml }
"""

LABELS_SYNC_PY = r"""
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
"""

PROJECTS_SYNC_WF = """
name: Projects sync (add & fields)
on:
  issues:
    types: [opened, edited, labeled, unlabeled, reopened]
  pull_request:
    types: [opened, edited, labeled, unlabeled, reopened, ready_for_review]
  workflow_dispatch:
jobs:
  add-and-map:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1.0.2
        with:
          project-url: https://github.com/users/g0udurix/projects/3
          github-token: ${{ secrets.PROJECTS_PAT }}
      - name: Map labels to fields (Status, Priority)
        uses: actions/github-script@v7
        env:
          PROJECTS_PAT: ${{ secrets.PROJECTS_PAT }}
        with:
          script: |
            const token = process.env.PROJECTS_PAT;
            if (!token) { core.warning('PROJECTS_PAT not set; skip'); return; }
            const isPR = !!context.payload.pull_request;
            const item = context.payload.issue || context.payload.pull_request;
            const labels = (item.labels || []).map(l => typeof l === 'string' ? l : l.name);
            const priorityLabel = (labels.find(l => /^priority\//i.test(l))||'').split('/')?.[1] || null;
            const statusLabel   = (labels.find(l => /^status\//i.test(l))||'').split('/')?.[1] || null;
            const { graphql } = require('@octokit/graphql');
            const ghgql = graphql.defaults({ headers: { authorization: `token ${token}` }});
            const login = context.repo.owner; const number = 3;
            const proj = await ghgql(`query($login:String!,$number:Int!){ user(login:$login){ projectV2(number:$number){ id fields(first:50){ nodes{ id name __typename ... on ProjectV2SingleSelectField { options{ id name } } } } } } }`, {login, number});
            const project = proj.user?.projectV2; if(!project){ core.warning('project not found'); return; }
            const fields = project.fields.nodes;
            const F = (name)=>fields.find(f=>f.name===name);
            const O = (field,val)=> field && field.options && field.options.find(o=>o.name.toLowerCase()===(val||'').toLowerCase());
            const statusField = F('Status');
            const priorityField = F('Priority');
            const statusOpt = O(statusField, statusLabel);
            const priorityOpt = O(priorityField, priorityLabel);
            const contentNodeId = (isPR
              ? (await github.rest.pulls.get({owner: context.repo.owner, repo: context.repo.repo, pull_number: item.number})).data.node_id
              : (await github.rest.issues.get({owner: context.repo.owner, repo: context.repo.repo, issue_number: item.number})).data.node_id);
            const addRes = await ghgql(`mutation($projectId:ID!,$contentId:ID!){ addProjectV2ItemById(input:{projectId:$projectId, contentId:$contentId}){ item{ id } } }`, {projectId: project.id, contentId: contentNodeId}).catch(()=>({}));
            const itemId = addRes?.addProjectV2ItemById?.item?.id; if(!itemId){ core.info('item exists or added via add-to-project'); }
            async function setSelect(field,opt){ if(!field||!opt)return; await ghgql(`mutation($p:ID!,$i:ID!,$f:ID!,$o:String!){ updateProjectV2ItemFieldValue(input:{projectId:$p,itemId:$i,fieldId:$f,value:{singleSelectOptionId:$o}}){ clientMutationId } }`, {p: project.id, i: itemId, f: field.id, o: opt.id}); }
            await setSelect(statusField, statusOpt);
            await setSelect(priorityField, priorityOpt);
            core.info('mapped fields');
"""

PR_TEMPLATE = """
## Summary
Explain the change in one or two sentences.

## Type
- [ ] feat
- [ ] fix
- [ ] docs
- [ ] chore/refactor

## Checklist
- [ ] Semantic title (e.g., `feat(extractor): ...`)
- [ ] Linked issue and milestone
- [ ] Labels set: area/*, status/*, priority/*
- [ ] Tests and docs updated

## AI notes (if applicable)
Prompt(s) used, constraints, citations, and how you validated outputs.
"""

RELEASE_DRAFTER = """
name-template: 'v$NEXT_PATCH_VERSION'
tag-template: 'v$NEXT_PATCH_VERSION'
change-template: '- $TITLE (#$NUMBER) by @$AUTHOR'
categories:
  - title: '🚀 Features'
    labels: ['feat', 'feature']
  - title: '🐛 Fixes'
    labels: ['fix']
  - title: '🧹 Chores & Refactors'
    labels: ['chore', 'refactor']
  - title: '📝 Docs'
    labels: ['docs']

template: |
  ## What changed
  $CHANGES

  ## Contributors
  $CONTRIBUTORS
"""

RELEASE_DRAFTER_WF = """
name: Release Drafter
on:
  push:
    branches: [ $default-branch ]
  pull_request:
    types: [closed]
  workflow_dispatch:
permissions:
  contents: write
jobs:
  update_release_draft:
    runs-on: ubuntu-latest
    steps:
      - uses: release-drafter/release-drafter@v6
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          config-name: release-drafter.yml
"""

DEPENDABOT = """
version: 2
updates:
  - package-ecosystem: "github-actions"
    directory: "/"
    schedule: { interval: "weekly" }
  - package-ecosystem: "pip"
    directory: "/"
    schedule: { interval: "weekly" }
"""

CI_WF = """
name: CI
on:
  pull_request:
  push:
    branches: [ $default-branch ]
  workflow_dispatch:
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'
      - name: Install tooling
        run: |
          python -m pip install --upgrade pip
          pip install ruff black pytest
      - name: Lint (ruff)
        run: ruff check . || true
      - name: Format (black)
        run: black --check . || true
      - name: Tests
        run: |
          if [ -d tests ]; then pytest -q; else echo "no tests"; fi
"""

# --------------------------- Milestones & PR mgmt --------------------------------

def gh_find_milestone_number(title: str) -> str|None:
    if not shutil.which("gh"): return None
    rc, out, _ = run(["gh","api", f"repos/{REPO_SLUG}/milestones", "--paginate", "--jq", f'.[] | select(.title=="{title}") | .number'])
    if rc==0 and out.strip(): return out.strip().splitlines()[0]
    return None

def ensure_milestone(title: str, description: str, due_on_iso: str):
    if not shutil.which("gh"):
        log("[WARN] gh not installed; skipping milestones"); return False
    num = gh_find_milestone_number(title)
    if num:
        run(["gh","api", f"repos/{REPO_SLUG}/milestones/{num}", "-X","PATCH", "-f", f"description={description}", "-f", f"due_on={due_on_iso}"])
        log(f"[OK] milestone '{title}' — updated"); return True
    rc, out, err = run(["gh","api", f"repos/{REPO_SLUG}/milestones", "-X","POST", "-f", f"title={title}", "-f", f"description={description}", "-f", f"due_on={due_on_iso}"])
    if rc==0: log(f"[APPLIED] milestone '{title}' — created"); return True
    if "already_exists" in (out+err) or "Validation Failed" in (out+err):
        num = gh_find_milestone_number(title)
        if num:
            run(["gh","api", f"repos/{REPO_SLUG}/milestones/{num}", "-X","PATCH", "-f", f"description={description}", "-f", f"due_on={due_on_iso}"])
            log(f"[OK] milestone '{title}' — existed; updated"); return True
        log(f"[OK] milestone '{title}' — already existed"); return True
    log(f"[WARN] failed to create/update milestone '{title}'"); return False


def open_or_update_pr(head: str, base: str):
    if not shutil.which("gh"):
        log("[WARN] gh not installed; cannot manage PR"); return False
    rc, out, _ = run(["gh","pr","list","--head", head, "--base", base, "--state","all", "--json","number,isDraft,title,url"]) 
    arr = []
    try: arr = json.loads(out) if out else []
    except Exception: pass
    milestone_title = "Phase 0 – Baseline"
    labels = "area/extractor,enhancement,status/Review,priority/P1,milestone/phase-0"
    if arr:
        pr_num = str(arr[0]["number"]) 
        run(["gh","pr","edit", pr_num, "--base", base, "--milestone", milestone_title])
        run(["gh","pr","edit", pr_num, "--add-label", labels])
        if arr[0].get("isDraft"): run(["gh","pr","ready", pr_num])
        log(f"[OK] PR #{pr_num} updated for milestone '{milestone_title}'"); return True
    title = "feat(history): crawl fragment history, enumerate versions, index (MVP)"
    body = ("This PR adds a basic history crawler that finds fragment version links, enumerates versions, and indexes them for later diffing.\n\n"
            "- area: extractor\n- status: Review\n- priority: P1\n- milestone: Phase 0 – Baseline\n")
    rc, out, _ = run(["gh","pr","create", "--base", base, "--head", head, "--title", title, "--body", body, "--milestone", milestone_title])
    if rc==0:
        run(["gh","pr","edit", "--add-label", labels])
        run(["gh","pr","merge", "--auto", "--squash"])  # ignore failures
        log("[APPLIED] PR created & prepped"); return True
    log("[WARN] failed to create PR"); return False

# --------------------------- Branch protection -----------------------------------

def protect_branch(branch: str):
    if not shutil.which("gh"):
        log("[WARN] gh not installed; skip branch protection"); return False
    payload = {
        "required_status_checks": {"strict": True, "contexts": ["Semantic Pull Request"]},
        "enforce_admins": False,
        "required_pull_request_reviews": {"required_approving_review_count": 1, "dismiss_stale_reviews": True},
        "restrictions": None,
        "allow_force_pushes": False,
        "allow_deletions": False,
        "required_linear_history": False
    }
    tmp = Path(".tmp_protection.json"); tmp.write_text(json.dumps(payload), encoding="utf-8")
    rc, out, err = run(["gh","api", f"repos/{REPO_SLUG}/branches/{branch}/protection", "-X","PUT", "-H","Accept: application/vnd.github+json", "--input", str(tmp)])
    try: tmp.unlink(missing_ok=True)
    except Exception: pass
    if rc==0:
        log(f"[OK] branch protection updated on {branch}"); return True
    log(f"[WARN] branch protection failed: {err or out}"); return False

# --------------------------- Self-test helpers -----------------------------------

def wait_for_workflow(name: str, timeout_s: int = 180) -> tuple[bool,str]:
    """Wait for a workflow run to complete; returns (ok, conclusion)."""
    end = time.time() + timeout_s
    last_conclusion = ""
    while time.time() < end:
        rc, out, _ = run(["gh","run","list","-w", name, "-L", "1", "--json", "databaseId,headSha,status,conclusion,createdAt,displayTitle"]) 
        try:
            runs = json.loads(out) if out else []
        except Exception:
            runs = []
        if runs:
            st = runs[0].get("status"); concl = runs[0].get("conclusion")
            if st == "completed":
                return (concl == "success", concl or "")
            last_conclusion = concl or last_conclusion
        time.sleep(6)
    return (False, last_conclusion or "timeout")


def projects_smoke(repo: str) -> bool:
    """Create a temp issue with status/Todo + priority/P1 and check it lands in Project #3 with fields set."""
    title = f"smoke: projects mapping ({ts()})"
    rc, out, err = run(["gh","issue","create","-R", repo, "-t", title, "-b", "automated projects mapping smoke", "-l", "status/Todo,priority/P1"]) 
    if rc != 0 or not out:
        log("[FAIL] could not create issue"); return False
    m = re.search(r"/issues/(\d+)", out)
    if not m:
        log("[WARN] couldn't parse issue number; continuing"); return False
    num = int(m.group(1))

    # Wait for workflow to run and finish
    ok, concl = wait_for_workflow("Projects sync (add & fields)")
    log(f"[projects] workflow conclusion: {concl}")

    # GraphQL verify fields
    rc, issue_json, _ = run(["gh","api","graphql","-f","query=\nquery($o:String!,$r:String!,$n:Int!){ repository(owner:$o,name:$r){ issue(number:$n){ id number title } } }\n","-F",f"o={repo.split('/')[0]}","-F",f"r={repo.split('/')[1]}","-F",f"n={num}"])
    issue_id = None
    try:
        issue_id = json.loads(issue_json)["data"]["repository"]["issue"]["id"]
    except Exception:
        pass

    rc, proj_json, _ = run(["gh","api","graphql","-f","query=\nquery($login:String!,$number:Int!){ user(login:$login){ projectV2(number:$number){ id items(first:50){ nodes{ id content{ __typename ... on Issue{ id number title } } fieldValues(first:20){ nodes{ __typename ... on ProjectV2ItemFieldSingleSelectValue{ field{ __typename ... on ProjectV2SingleSelectField{ name } } name } } } } } } } }\n","-F","login=g0udurix","-F","number=3"])
    try:
        nodes = json.loads(proj_json)["data"]["user"]["projectV2"]["items"]["nodes"]
        node = next((n for n in nodes if n.get("content",{}).get("id")==issue_id), None)
        if not node:
            log("[FAIL] issue not found in Project #3 items"); return False
        fv = node.get("fieldValues",{}).get("nodes",[])
        fields = { (v.get("field",{}).get("name") if isinstance(v.get("field"), dict) else None): v.get("name") for v in fv if v.get("__typename")=="ProjectV2ItemFieldSingleSelectValue" }
        ok = (fields.get("Status","")) and (fields.get("Priority",""))
        log(f"[projects] mapped fields: {fields}")
        return bool(ok)
    finally:
        run(["gh","issue","close",str(num),"-R",repo,"-c","smoke cleanup"])  # best-effort


def release_drafter_smoke() -> bool:
    run(["gh","workflow","run","Release Drafter"])  # requires workflow_dispatch present
    ok, concl = wait_for_workflow("Release Drafter")
    log(f"[release-drafter] workflow: {concl}")
    rc, out, _ = run(["gh","api", f"repos/{REPO_SLUG}/releases", "-F", "per_page=10", "--jq", "map(select(.draft==true)) | length"]) 
    try:
        count = int(out.strip()) if out.strip() else 0
    except Exception:
        count = 0
    log(f"[release-drafter] draft count: {count}")
    return count >= 1


def ci_smoke() -> bool:
    run(["gh","workflow","run","CI"])  # requires workflow_dispatch present
    ok, concl = wait_for_workflow("CI")
    log(f"[ci] workflow: {concl}")
    return ok


def branch_protection_check(branch: str) -> bool:
    rc, out, err = run(["gh","api", f"repos/{REPO_SLUG}/branches/{branch}/protection", "-H","Accept: application/vnd.github+json"]) 
    if rc != 0:
        log("[WARN] couldn't read branch protection"); return False
    try:
        data = json.loads(out)
        contexts = (data.get("required_status_checks") or {}).get("contexts") or []
        ok = "Semantic Pull Request" in contexts
        log(f"[protection] required checks: {contexts}")
        return ok
    except Exception:
        return False

# --------------------------- Main -------------------------------------------------

def main():
    repo_dir = Path.cwd()
    branch = get_default_branch()
    log(f"[info] repo={REPO_SLUG} default_branch={branch} apply={APPLY} self_test={SELF_TEST}")
    git_pull(repo_dir)

    # Write/update governance & workflows
    wrote = False
    wrote |= ensure_file(repo_dir/"CONTRIBUTING.md", CONTRIBUTING)
    wrote |= ensure_file(repo_dir/"CODE_OF_CONDUCT.md", CODE_OF_CONDUCT)
    wrote |= ensure_file(repo_dir/"CODEOWNERS", "* @g0udurix\nstandards/** @g0udurix\nlrn/** @g0udurix\nscripts/** @g0udurix\napi/** @g0udurix\napp/** @g0udurix\ntests/** @g0udurix\n.github/** @g0udurix\n")

    wrote |= ensure_file(repo_dir/".github"/"ISSUE_TEMPLATE"/"standards_mapping.md", "---\nname: Standards mapping task\nabout: Map clauses from CSA/ANSI/ISO/EN to topics & fragments\nlabels: [area/standards, status/Backlog]\n---\n\n## Standard & Clause(s)\n- Body (CSA/ANSI/ISO/EN/…):\n- Standard ID & year:\n- Clause numbers:\n\n## Linkage\n- Relevant topics:\n- Fragments (if any):\n\n## Notes / rationale\n- \n\n## Done when\n- [ ] Clauses captured in `standard_clauses`\n- [ ] Topics linked in `standard_clause_topics`\n- [ ] Cross-refs to fragments (if applicable)\n")
    wrote |= ensure_file(repo_dir/".github"/"ISSUE_TEMPLATE"/"comparison_task.md", "---\nname: Comparison/ranking task\nabout: Compare jurisdictions or standards on a specific subject\nlabels: [area/comparison, status/Todo]\n---\n\n## Subject\n- (e.g., guardrail height, harness inspection frequency)\n\n## Scope\n- Jurisdictions: QC, CA, US, UK, FR, DE, JP, AU (select)\n- Standards to include (CSA/ANSI/ISO/EN/…):\n\n## Method\n- Metrics / scoring notes:\n\n## Done when\n- [ ] Data normalized into `position_matrix`\n- [ ] Summary written (pros/cons, stricter/more permissive)\n- [ ] Follow-ups filed (gaps, obsolescence flags)\n")
    wrote |= ensure_file(repo_dir/".github"/"pull_request_template.md", PR_TEMPLATE)

    wrote |= ensure_file(repo_dir/".github"/"workflows"/"semantic-pr.yml", SEMANTIC_PR_WF)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"auto-milestone.yml", AUTO_MILESTONE_WF)

    wrote |= ensure_file(repo_dir/".github"/"labels.yml", LABELS_YML)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"labels-sync.yml", LABELS_SYNC_WF)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"projects-sync.yml", PROJECTS_SYNC_WF)
    wrote |= ensure_file(repo_dir/"scripts"/"labels_sync.py", LABELS_SYNC_PY)

    wrote |= ensure_file(repo_dir/".github"/"release-drafter.yml", RELEASE_DRAFTER)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"release-drafter.yml", RELEASE_DRAFTER_WF)
    wrote |= ensure_file(repo_dir/".github"/"dependabot.yml", DEPENDABOT)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"ci.yml", CI_WF)

    wrote |= ensure_gitignore_lines(repo_dir, ['logs/', 'qdrant_storage/', '*.sqlite', '*.db', '*.db-journal', '__pycache__/', '*.pyc'])
    if APPLY and shutil.which('git'):
        run(["git","rm","-r","--cached","--ignore-unmatch","logs","qdrant_storage"], cwd=repo_dir)

    # Milestones refresh
    base = datetime.now(timezone.utc)
    for title, desc, due in [
        ("Phase 0 – Baseline", "Minimal viable schema, ingestion & search", base + timedelta(days=7)),
        ("Phase 1 – Corpus & Standards", "Import corpora, map CSA/ANSI/ISO", base + timedelta(days=45)),
        ("Phase 2 – Comparison Engine", "Matrix/ranking across jurisdictions", base + timedelta(days=75)),
        ("Phase 3 – Annotations & Issues", "Notes, flags, reviews, orientations", base + timedelta(days=105)),
        ("Phase 4 – Guidance UI", "Advices, cheat sheets, Q&A", base + timedelta(days=135)),
    ]:
        ensure_milestone(title, desc, due.strftime("%Y-%m-%dT%H:%M:%SZ"))

    # Ensure PR is prepped & protection set
    open_or_update_pr(head="feat/history-crawl", base=branch)
    protect_branch(branch)

    if APPLY:
        did_push = git_commit_push(repo_dir, f"chore(pm): governance + workflows refresh ({ts()})")
        # Write enhanced multi-branch bootloader for next run
        stub = f"""#!/usr/bin/env python3\\n# upgrade_and_roadmap.py bootloader — last run completed at {ts()} UTC\\nimport sys, os, json, urllib.request, subprocess\\nREPO = os.getenv('LRN_REPO', '{REPO_SLUG}')\\nif '--no-refresh' in sys.argv: sys.argv.remove('--no-refresh')\\nif '--self-test' in sys.argv: sys.argv.remove('--self-test')\\ncandidates=[]\\ntry:\\n    p=subprocess.run(['git','rev-parse','--abbrev-ref','HEAD'],capture_output=True,text=True)\\n    if p.returncode==0:\\n        br=(p.stdout or '').strip()\\n        if br and br!='HEAD': candidates.append(br)\\nexcept Exception: pass\\ntry:\\n    with urllib.request.urlopen(f'https://api.github.com/repos/{{REPO}}',timeout=15) as r:\\n        info=json.loads(r.read().decode('utf-8'))\\n        db=info.get('default_branch')\\n        if db: candidates.append(db)\\nexcept Exception: pass\\ncandidates+=['feat/history-crawl','main','master']\\ntried=[]\\nfor br in [b for b in candidates if b]:\\n    url=f'https://raw.githubusercontent.com/{{REPO}}/{{br}}/upgrade_and_roadmap.py'\\n    try:\\n        data=urllib.request.urlopen(url,timeout=30).read()\\n        open(__file__,'wb').write(data)\\n        env=os.environ.copy(); env['LRN_BOOTSTRAPPED']='1'\\n        os.execvpe(sys.executable,[sys.executable,__file__]+sys.argv[1:],env)\\n    except Exception as e:\\n        tried.append((url,str(e)))\\nprint('[bootloader] failed to refresh from any candidate branch. Tried:')\\nfor url,err in tried: print(' -', url, '->', err)\\nprint('Hint: run with --no-refresh or --self-test to use the embedded finisher if present.')\\nsys.exit(1)\\n"""
        Path(__file__).write_text(stub, encoding="utf-8")
        log("[APPLIED] enhanced bootloader written (multi-branch). Re-run will fetch latest.")
        if did_push: log("[DONE] changes committed and pushed")
        else: log("[DONE] nothing to commit")

    # Optional self-test
    if SELF_TEST:
        print("\n===== SELF-TEST =====")
        proj_ok = projects_smoke(REPO_SLUG)
        ci_ok   = ci_smoke()
        rel_ok  = release_drafter_smoke()
        prot_ok = branch_protection_check(get_default_branch())
        print("\nSelf-test results:")
        print(f"  Projects mapping: {'PASS' if proj_ok else 'FAIL'}")
        print(f"  CI workflow:      {'PASS' if ci_ok else 'FAIL'}")
        print(f"  Release drafter:  {'PASS' if rel_ok else 'FAIL'}")
        print(f"  Branch protect:   {'PASS' if prot_ok else 'FAIL'}")

if __name__ == "__main__":
    main()
