#!/usr/bin/env python3
# LRN PM Finisher — one-shot
# Does:
#  - Writes CONTRIBUTING/CODE_OF_CONDUCT for humans + AI
#  - Enforces semantic PR titles
#  - Creates/updates milestones and milestone/* labels
#  - Adds auto-milestone workflow (labels → milestone)
#  - Expands CODEOWNERS per folder
#  - Adds issue templates for standards mapping & comparison tasks
#  - Opens/updates PR: feat/history-crawl → default branch, sets milestone & labels
# Then self-flushes back to a tiny bootloader.

import os, sys, json, subprocess, shutil, urllib.request, urllib.error
from pathlib import Path
from datetime import datetime, timezone, timedelta

REPO_SLUG = os.getenv("LRN_REPO", "g0udurix/LRN")
APPLY = "--apply" in sys.argv

# ----------------------------------------------------------------------------------
# Utilities
# ----------------------------------------------------------------------------------

def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def log(msg: str):
    print(msg)
    try:
        Path("logs").mkdir(exist_ok=True)
        with open(Path("logs")/f"pm3_{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}.log", "a", encoding="utf-8") as f:
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

# ----------------------------------------------------------------------------------
# Git helpers
# ----------------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------------
# Ensure files
# ----------------------------------------------------------------------------------

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

# ----------------------------------------------------------------------------------
# Content payloads
# ----------------------------------------------------------------------------------

CONTRIBUTING = """
# Contributing to LRN (Humans & AI agents)

Welcome! This repo accepts contributions from both humans and AI agents (tools like ChatGPT/Copilot/LLMs). To keep quality high and risk low, follow these rules:

## Ground rules
- **Follow semantic commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Use scopes where meaningful (e.g., `feat(extractor): ...`).
- **No secrets**: Do not include API keys, tokens, or confidential content. If an AI wrote code, double-check for accidental credentials.
- **Determinism over cleverness**: Prefer simple, testable code over magic. Explain non-trivial logic in comments.
- **Reproducibility**: If you generate code or data, describe how to regenerate it (`make` targets or scripts).
- **Tests**: For non-trivial changes, include or update tests. For schema changes, include a migration and verification steps.
- **Docs**: Update README/ROADMAP and add upgrade notes when behavior changes.

## For AI agents specifically
- **Identify automated changes** in PR body: include a short “AI notes” section describing prompts, assumptions, and safeguards.
- **Avoid hallucinations**: Cite sources (standards, statutes) with exact references where applicable.
- **Respect licenses**: Do not paste content from proprietary standards. Summarize instead.
- **Keep PRs small**: Split large work into reviewable chunks; keep diffs under ~500 lines when possible.
- **Feedback loop**: If your generation relies on context, quote it in the PR so reviewers can validate.

## PR checklist
- [ ] Semantic title & commits
- [ ] Linked issue / milestone
- [ ] Labels: `area/*`, `priority/*`, `status/*`
- [ ] Tests/lint pass locally
- [ ] Docs updated

Thanks! ✨
"""

CODE_OF_CONDUCT = """
# Code of Conduct (Humans & AI agents)

We commit to respectful, transparent collaboration.

- **Respect**: No harassment, personal attacks, or spammy automation.
- **Honesty**: AI agents must not misrepresent generated content as human-written; disclose automation clearly.
- **Safety**: Do not propose or implement unsafe guidance. Flag risks and cite standards.
- **Accountability**: Maintainers may close or revert PRs that violate these rules. Repeated violations may result in bans.

This policy applies to all participants. Report violations to @g0udurix.
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
            const isPR = !!context.payload.pull_request;
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
            if (!wanted) { core.info('label not mapped: ' + key); return; }
            const owner = context.repo.owner; const repo = context.repo.repo;
            const {data: milestones} = await github.rest.issues.listMilestones({owner, repo, state: 'open'});
            let m = milestones.find(x => x.title === wanted);
            if (!m) {
              // Fallback: check closed too
              const {data: all} = await github.rest.issues.listMilestones({owner, repo, state: 'all'});
              m = all.find(x => x.title === wanted);
            }
            if (!m) { core.warning('milestone not found: ' + wanted); return; }
            await github.rest.issues.update({owner, repo, issue_number: item.number, milestone: m.number});
            core.info(`set milestone '${wanted}' on #${item.number}`);
"""

CODEOWNERS = """
# Default owner
* @g0udurix

# Ownership by area
standards/* @g0udurix
standards/** @g0udurix
lrn/** @g0udurix
scripts/** @g0udurix
api/** @g0udurix
app/** @g0udurix
tests/** @g0udurix
.github/** @g0udurix
"""

ISSUE_TEMPLATE_STANDARDS = """
---
name: Standards mapping task
about: Map clauses from CSA/ANSI/ISO/EN to topics & fragments
labels: [area/standards, status/Backlog]
---
## Standard & Clause(s)
- Body (CSA/ANSI/ISO/EN/…):
- Standard ID & year:
- Clause numbers:

## Linkage
- Relevant topics:
- Fragments (if any):

## Notes / rationale
- 

## Done when
- [ ] Clauses captured in `standard_clauses`
- [ ] Topics linked in `standard_clause_topics`
- [ ] Cross-refs to fragments (if applicable)
"""

ISSUE_TEMPLATE_COMPARISON = """
---
name: Comparison/ranking task
about: Compare jurisdictions or standards on a specific subject
labels: [area/comparison, status/Todo]
---
## Subject
- (e.g., guardrail height, harness inspection frequency)

## Scope
- Jurisdictions: QC, CA, US, UK, FR, DE, JP, AU (select)
- Standards to include (CSA/ANSI/ISO/EN/…):

## Method
- Metrics / scoring notes:

## Done when
- [ ] Data normalized into `position_matrix`
- [ ] Summary written (pros/cons, stricter/more permissive)
- [ ] Follow-ups filed (gaps, obsolescence flags)
"""

# ----------------------------------------------------------------------------------
# Labels (ensure milestone/* exist now)
# ----------------------------------------------------------------------------------

def ensure_milestone_labels():
    if not shutil.which("gh"):
        log("[WARN] gh not installed; skipping label sync for milestones"); return False
    pairs = [
        ("milestone/phase-0", "Phase 0 – Baseline", "bfd4f2"),
        ("milestone/phase-1", "Phase 1 – Corpus & Standards", "bfd4f2"),
        ("milestone/phase-2", "Phase 2 – Comparison Engine", "bfd4f2"),
        ("milestone/phase-3", "Phase 3 – Annotations & Issues", "bfd4f2"),
        ("milestone/phase-4", "Phase 4 – Guidance UI", "bfd4f2"),
    ]
    ok=True
    for name, desc, color in pairs:
        rc,_,_ = run(["gh","label","create", name, "-R", REPO_SLUG, "--color", color, "--description", desc, "--force"])
        ok = ok and (rc==0)
    return ok

# ----------------------------------------------------------------------------------
# Milestones (create/update via gh api)
# ----------------------------------------------------------------------------------

def ensure_milestone(title: str, description: str, due_on_iso: str):
    if not shutil.which("gh"):
        log("[WARN] gh not installed; skipping milestones"); return False
    # try find by title
    rc, out, _ = run(["gh","api", f"repos/{REPO_SLUG}/milestones", "--paginate", "-q", f".[?title=='{title}']|[0].number"])
    num = (out or "").strip()
    if num:
        run(["gh","api", f"repos/{REPO_SLUG}/milestones/{num}", "-X","PATCH", "-f", f"description={description}", "-f", f"due_on={due_on_iso}"])
        log(f"[OK] milestone '{title}' — updated"); return True
    rc, out, err = run(["gh","api", f"repos/{REPO_SLUG}/milestones", "-X","POST", "-f", f"title={title}", "-f", f"description={description}", "-f", f"due_on={due_on_iso}"])
    if rc==0:
        log(f"[APPLIED] milestone '{title}' — created"); return True
    log(f"[WARN] failed to create milestone '{title}': {err}"); return False

# ----------------------------------------------------------------------------------
# PR: feat/history-crawl → default branch
# ----------------------------------------------------------------------------------

def open_or_update_pr(head: str, base: str):
    if not shutil.which("gh"):
        log("[WARN] gh not installed; cannot manage PR"); return False
    rc, out, _ = run(["gh","pr","list","--head", head, "--base", base, "--state","all", "--json","number,isDraft,title,url"])
    try:
        arr = json.loads(out) if out else []
    except Exception:
        arr = []
    milestone_title = "Phase 0 – Baseline"
    labels = "area/extractor,enhancement,status/Review,priority/P1,milestone/phase-0"
    if arr:
        pr_num = str(arr[0]["number"])
        run(["gh","pr","edit", pr_num, "--base", base, "--milestone", milestone_title])
        run(["gh","pr","edit", pr_num, "--add-label", labels])
        if arr[0].get("isDraft"):
            run(["gh","pr","ready", pr_num])
        log(f"[OK] PR #{pr_num} updated for milestone '{milestone_title}'")
        return True
    title = "feat(history): crawl fragment history, enumerate versions, index (MVP)"
    body = (
        "This PR adds a basic history crawler that finds fragment version links, "
        "enumerates versions, and indexes them for later diffing.\n\n"
        "- area: extractor\n- status: Review\n- priority: P1\n- milestone: Phase 0 – Baseline\n"
    )
    rc, out, _ = run(["gh","pr","create", "--base", base, "--head", head, "--title", title, "--body", body, "--milestone", milestone_title])
    if rc==0:
        run(["gh","pr","edit", "--add-label", labels])
        run(["gh","pr","merge", "--auto", "--squash"])  # ignore failures
        log("[APPLIED] PR created & prepped")
        return True
    log("[WARN] failed to create PR"); return False

# ----------------------------------------------------------------------------------
# Bootloader
# ----------------------------------------------------------------------------------

def write_bootloader(branch: str):
    raw = f"https://raw.githubusercontent.com/{REPO_SLUG}/{branch}/upgrade_and_roadmap.py"
    stub = (
        "#!/usr/bin/env python3\n"
        f"# upgrade_and_roadmap.py bootloader — last run completed at {ts()} UTC\n"
        "import sys, urllib.request\n"
        f"RAW = \"{raw}\"\n"
        "try:\n"
        "    data = urllib.request.urlopen(RAW, timeout=30).read()\n"
        "    open(__file__, \"wb\").write(data)\n"
        "    print(\"[bootloader] refreshed upgrade_and_roadmap.py from\", RAW)\n"
        "    print(\"[bootloader] run it again to execute the latest version.\")\n"
        "except Exception as e:\n"
        "    print(\"[bootloader] failed to refresh:\", e)\n"
        "    sys.exit(1)\n"
    )
    Path(__file__).write_text(stub, encoding="utf-8")

# ----------------------------------------------------------------------------------
# Main
# ----------------------------------------------------------------------------------

def main():
    repo_dir = Path.cwd()
    branch = get_default_branch()
    log(f"[info] repo={REPO_SLUG} default_branch={branch} apply={APPLY}")

    git_pull(repo_dir)

    wrote = False
    wrote |= ensure_file(repo_dir/"CONTRIBUTING.md", CONTRIBUTING)
    wrote |= ensure_file(repo_dir/"CODE_OF_CONDUCT.md", CODE_OF_CONDUCT)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"semantic-pr.yml", SEMANTIC_PR_WF)
    wrote |= ensure_file(repo_dir/".github"/"workflows"/"auto-milestone.yml", AUTO_MILESTONE_WF)
    wrote |= ensure_file(repo_dir/"CODEOWNERS", CODEOWNERS)
    wrote |= ensure_file(repo_dir/".github"/"ISSUE_TEMPLATE"/"standards_mapping.md", ISSUE_TEMPLATE_STANDARDS)
    wrote |= ensure_file(repo_dir/".github"/"ISSUE_TEMPLATE"/"comparison_task.md", ISSUE_TEMPLATE_COMPARISON)

    # Ensure labels for milestones
    ensure_milestone_labels()

    # Create/update milestones with a rolling schedule
    base = datetime.now(timezone.utc)
    phases = [
        ("Phase 0 – Baseline", "Minimal viable schema, ingestion & search", base + timedelta(days=7)),
        ("Phase 1 – Corpus & Standards", "Import corpora, map CSA/ANSI/ISO", base + timedelta(days=45)),
        ("Phase 2 – Comparison Engine", "Matrix/ranking across jurisdictions", base + timedelta(days=75)),
        ("Phase 3 – Annotations & Issues", "Notes, flags, reviews, orientations", base + timedelta(days=105)),
        ("Phase 4 – Guidance UI", "Advices, cheat sheets, Q&A", base + timedelta(days=135)),
    ]
    for title, desc, due in phases:
        ensure_milestone(title, desc, due.strftime("%Y-%m-%dT%H:%M:%SZ"))

    # PR for feat/history-crawl
    open_or_update_pr(head="feat/history-crawl", base=branch)

    if APPLY:
        did_push = git_commit_push(repo_dir, f"chore(governance): AI contributing, CoC, milestone automation, templates ({ts()})")
        write_bootloader(branch)
        log("[APPLIED] self-flush bootloader written")
        if did_push:
            log("[DONE] changes committed and pushed")
        else:
            log("[DONE] nothing to commit")
    else:
        log("[DRY-RUN] pass --apply to write files and commit")

if __name__ == "__main__":
    main()
