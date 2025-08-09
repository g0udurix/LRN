

#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
updatecodebase.py — one-shot repo bootstrapper/keeper

Run with **no arguments**:

    python updatecodebase.py

What it does (idempotent):
- Ensures governance docs (README, CONTRIBUTING, CODE_OF_CONDUCT, CODEOWNERS, RULES, PR template, issue templates)
- Ensures GitHub workflows (CI, labels sync, projects sync, release drafter, semantic PR) — all include `workflow_dispatch`
- Ensures labels config and Dependabot
- Initializes or updates CHANGELOG.md
- Prints a short next-steps checklist

Notes:
- Uses your repo slug from `git remote get-url origin` for dynamic values
- Uses contact email: seemly-peer.0k@icloud.com
- Safe to re-run; only writes when content changes
"""

from __future__ import annotations
import os
import re
import sys
import json
import textwrap
from datetime import datetime, timezone
from pathlib import Path
from subprocess import run, PIPE

CONTACT_EMAIL = "seemly-peer.0k@icloud.com"

# --------------------------- helpers ---------------------------

def sh(cmd: list[str] | str, cwd: Path | None = None) -> tuple[int, str, str]:
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    p = run(cmd, cwd=str(cwd) if cwd else None, shell=shell, stdout=PIPE, stderr=PIPE, text=True)
    return p.returncode, p.stdout.strip(), p.stderr.strip()


def repo_root() -> Path:
    # Try git root; else current file's parent
    code, out, _ = sh(["git", "rev-parse", "--show-toplevel"])
    return Path(out) if code == 0 and out else Path(__file__).resolve().parent


def repo_slug() -> tuple[str, str]:
    # Parse owner/repo from `git config --get remote.origin.url`
    code, url, _ = sh(["git", "config", "--get", "remote.origin.url"])
    if code != 0 or not url:
        env = os.getenv("GITHUB_REPOSITORY", "owner/repo")
        owner, repo = env.split("/")
        return owner, repo
    # Accept SSH & HTTPS
    m = re.search(r"github\.com[:/](?P<owner>[^/]+)/(?P<repo>[^/.]+)", url)
    if not m:
        return "owner", "repo"
    return m.group("owner"), m.group("repo")


def norm_eol(s: str) -> str:
    return s.replace("\r\n", "\n").replace("\r", "\n")


def ensure_file(path: Path, content: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    new = norm_eol(content).rstrip() + "\n"
    if path.exists():
        old = norm_eol(path.read_text(encoding="utf-8", errors="ignore"))
        if old == new:
            return f"[OK] {path} — up-to-date"
    path.write_text(new, encoding="utf-8")
    return f"[APPLIED] {path} — written"


def ensure_changelog(path: Path) -> list[str]:
    msgs: list[str] = []
    if not path.exists():
        tmpl = f"""
        # Changelog
        
        All notable changes to this project will be documented in this file.
        This project adheres to [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) and
        [Semantic Versioning](https://semver.org/spec/v2.0.0.html).
        
        ## [Unreleased]
        - Bootstrap governance & workflows
        
        """
        msgs.append(ensure_file(path, textwrap.dedent(tmpl)))
        return msgs
    # If exists, ensure it at least has an Unreleased section
    txt = path.read_text(encoding="utf-8", errors="ignore")
    if "## [Unreleased]" not in txt:
        txt = txt.rstrip() + "\n\n## [Unreleased]\n- Bootstrap governance & workflows\n"
        path.write_text(txt, encoding="utf-8")
        msgs.append(f"[APPLIED] {path} — appended [Unreleased]")
    else:
        msgs.append(f"[OK] {path} — has [Unreleased]")
    return msgs

# --------------------------- content builders ---------------------------

def build_files(owner: str, repo: str) -> dict[str, str]:
    project_url = f"https://github.com/{owner}/{repo}"
    user_projects_url = f"https://github.com/users/{owner}/projects/3"
    now_iso = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

    README = f"""
    # {repo}

    *Community-driven legal/standards research workspace.*

    This repository is configured with sensible defaults for governance, CI, labeling, projects, and release drafting.\
    Automation is designed for both **humans** and **AI agents**.

    ## Quick start
    - Fork or branch from `master`.
    - Use **conventional commits** (e.g., `feat:`, `fix:`, `chore:`...).
    - Open a PR; the Semantic PR check will validate the title.
    - Label issues/PRs with `status/*`, `priority/*`, and `area/*` when relevant.

    ## Contributing (humans & AI agents)
    See [CONTRIBUTING.md](CONTRIBUTING.md) and [RULES.md](RULES.md) for the step-by-step flow, review etiquette,\
    dataset/standards mapping tasks, and AI-specific guidance.

    ## Governance
    - Code of Conduct: [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)
    - Ownership defaults: [CODEOWNERS](CODEOWNERS)
    - Project board (#3): {user_projects_url}

    ## Releases
    Draft release notes are auto-generated via Release Drafter based on labels and PR titles.

    ## Contact
    Questions, incidents, or moderation: **{CONTACT_EMAIL}**
    """

    CONTRIBUTING = f"""
    # Contributing Guide

    Welcome! This project supports contributions by both **humans** and **AI agents**.

    ## Principles
    - Incremental, reviewable changes
    - Reproducibility and traceability (issues link to sources; PRs link to issues)
    - Community safety and respect (see Code of Conduct)

    ## Workflow
    1. **Open / find an issue** and confirm scope. Use labels: `status/Todo`, `priority/P*`, `area/*`.
    2. **Create a branch**: `type/short-topic` (e.g., `feat/history-crawl`).
    3. **Commit with conventional commits**: `feat: add extractor for XY`.
    4. **PR checklist** (auto-included):
       - [ ] Title follows conventional commits
       - [ ] Linked issue & milestone
       - [ ] Labels added (`status/*`, `priority/*`, `area/*`)
       - [ ] Updated docs and CHANGELOG if user-facing
    5. **Reviews**: be kind, specific, and actionable; prefer follow-ups over scope creep.

    ## AI Contributor Guidance
    - Identify yourself in PR description: "This change was prepared by an AI agent".
    - Only modify files you are asked to. If something is ambiguous, open an issue first.
    - Provide a minimal, passing CI change; include sample data if needed.
    - Keep explanations concise; reference sources with links when possible.

    ## Local setup
    - Python 3.10+
    - `gh` CLI (optional) for milestone/branch-protection helpers

    ## Security / Reporting
    Email **{CONTACT_EMAIL}** for moderation or security concerns.
    """

    CODE_OF_CONDUCT = f"""
    # Code of Conduct (short)

    We are committed to a welcoming, harassment-free experience for everyone. Be respectful, assume goodwill, and collaborate constructively.

    Unacceptable behavior includes harassment, discrimination, doxxing, and sustained disruption. Maintainers may take action including warnings, temporary or permanent bans.

    Report incidents confidentially to **{CONTACT_EMAIL}**. Serious concerns may also be raised to the repository owner @{owner}.
    """

    CODEOWNERS = f"""
    # Default owners
    * @{owner}  # primary maintainer — contact: {CONTACT_EMAIL}
    """

    RULES = f"""
    # Project Rules

    ## Scope & Priorities
    - Prefer tasks that improve data quality, test coverage, or user documentation.
    - Avoid speculative features without an accepted issue & milestone.

    ## PR Titles (Semantic / Conventional commits)
    Allowed types: `feat`, `fix`, `docs`, `chore`, `refactor`, `test`, `build`, `ci`, `perf`, `style`, `revert`.

    ## Labels
    - `status/Todo`, `status/Doing`, `status/Review`, `status/Blocked`
    - `priority/P0..P3`
    - `area/*` (extractor, parser, ui, infra, data)

    ## AI Agents
    - Declare your intent and assumptions in the PR body.
    - Keep diffs small and isolated. If you need to touch many files, open multiple PRs.
    - Always include a brief test plan.

    ## Contact
    Moderation / questions: **{CONTACT_EMAIL}**
    """

    PR_TEMPLATE = """
    ### Summary

    _What does this change and why?_

    ### Issue / Milestone
    - Closes #
    - Milestone:

    ### Type
    - [ ] feat
    - [ ] fix
    - [ ] docs
    - [ ] chore
    - [ ] refactor

    ### Checklist
    - [ ] PR title follows conventional commits
    - [ ] Labels added (status/*, priority/*, area/*)
    - [ ] Updated docs
    - [ ] Updated CHANGELOG (if user-facing)
    - [ ] Test plan included
    """

    ISSUE_TEMPLATE_STANDARDS = """
    ---
    name: Standards mapping task
    about: Map standards (CSA/ANSI/ISO) to schema
    labels: status/Todo, area/data, priority/P2
    ---

    ## Goal
    
    ## Inputs / Sources
    
    ## Deliverables
    - Mapped fields
    - Notes & edge cases
    
    ## Review checklist
    - [ ] Links to sources
    - [ ] Test cases updated/added
    """

    ISSUE_TEMPLATE_COMPARISON = """
    ---
    name: Comparison engine task
    about: Add or improve matrix/ranking across jurisdictions
    labels: status/Todo, area/engine, priority/P2
    ---

    ## Goal

    ## Data required

    ## Acceptance criteria
    - [ ] Query works for examples X/Y
    - [ ] Documented assumptions
    """

    LABELS_YML = """
    - name: status/Todo
      color: 0366d6
      description: Not started
    - name: status/Doing
      color: fbca04
      description: In progress
    - name: status/Review
      color: 0e8a16
      description: In review
    - name: status/Blocked
      color: d73a4a
      description: Blocked by something else

    - name: priority/P0
      color: b60205
      description: Must do now
    - name: priority/P1
      color: d93f0b
      description: Important
    - name: priority/P2
      color: fbca04
      description: Useful
    - name: priority/P3
      color: cccccc
      description: Nice to have

    - name: area/extractor
      color: 1d76db
    - name: area/parser
      color: 1d76db
    - name: area/engine
      color: 1d76db
    - name: area/ui
      color: 1d76db
    - name: area/infra
      color: 1d76db
    - name: area/data
      color: 1d76db
    """

    DEPENDABOT = """
    version: 2
    updates:
      - package-ecosystem: "github-actions"
        directory: "/"
        schedule:
          interval: "monthly"
    """

    SEMANTIC_PR = """
    name: Semantic Pull Request
    on:
      pull_request:
        types: [opened, edited, synchronize]
      workflow_dispatch:
    jobs:
      semantic:
        permissions:
          pull-requests: read
        runs-on: ubuntu-latest
        steps:
          - uses: amannn/action-semantic-pull-request@v5
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            with:
              types: |
                chore,ci,docs,feat,fix,perf,refactor,revert,style,test,build
    """

    CI_YML = """
    name: CI
    on:
      push:
      pull_request:
      workflow_dispatch:
    jobs:
      verify:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Python checks (noop)
            run: |
              python -V
              echo "CI sanity OK"
    """

    RELEASE_DRAFTER_CFG = """
    name-template: "v$NEXT_PATCH_VERSION"
    tag-template: "v$NEXT_PATCH_VERSION"
    categories:
      - title: 🚀 Features
        labels: ["feat"]
      - title: 🐛 Fixes
        labels: ["fix"]
      - title: 🧰 Maintenance
        labels: ["chore", "refactor", "ci", "build"]
      - title: 📝 Docs
        labels: ["docs"]
    change-template: "- $TITLE (#$NUMBER)"
    template: |
      ## Changes

      $CHANGES
    """

    RELEASE_DRAFTER = """
    name: Release Drafter
    on:
      push:
        branches: [ master ]
      pull_request:
        types: [closed]
      workflow_dispatch:
    jobs:
      update_release_draft:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - uses: release-drafter/release-drafter@v5
            env:
              GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
            with:
              config-name: release-drafter.yml
    """

    LABELS_SYNC = """
    name: Labels sync
    on:
      push:
        branches: [ master ]
        paths:
          - .github/labels.yml
      workflow_dispatch:
    jobs:
      sync:
        runs-on: ubuntu-latest
        steps:
          - uses: actions/checkout@v4
          - name: Sync labels
            uses: crazy-max/ghaction-github-labeler@v5
            with:
              github-token: ${{ secrets.GITHUB_TOKEN }}
              yaml-file: .github/labels.yml
              skip-delete: false
    """

    PROJECTS_SYNC = f"""
    name: Projects sync (add & fields)
    on:
      issues:
        types: [opened, labeled]
      pull_request:
        types: [opened]
      workflow_dispatch:
    jobs:
      add_to_project:
        runs-on: ubuntu-latest
        permissions:
          contents: read
          issues: write
          pull-requests: write
          projects: write
        steps:
          - name: Add to project #{'{'}3{'}'}
            uses: actions/add-to-project@v0.5.0
            with:
              project-url: https://github.com/users/${{ '{{' }} github.repository_owner {{ '}}' }}/projects/3
              github-token: ${{ '{{' }} secrets.PROJECTS_PAT {{ '}}' }}
          - name: Set default fields via GraphQL (best-effort)
            env:
              GH_TOKEN: ${{ '{{' }} secrets.PROJECTS_PAT {{ '}}' }}
            run: |
              echo "Field sync placeholder at {now_iso}"
    """

    files = {
        "README.md": README,
        "CONTRIBUTING.md": CONTRIBUTING,
        "CODE_OF_CONDUCT.md": CODE_OF_CONDUCT,
        "CODEOWNERS": CODEOWNERS,
        "RULES.md": RULES,
        ".github/pull_request_template.md": PR_TEMPLATE,
        ".github/ISSUE_TEMPLATE/standards_mapping.md": ISSUE_TEMPLATE_STANDARDS,
        ".github/ISSUE_TEMPLATE/comparison_task.md": ISSUE_TEMPLATE_COMPARISON,
        ".github/labels.yml": LABELS_YML,
        ".github/dependabot.yml": DEPENDABOT,
        ".github/workflows/semantic-pr.yml": SEMANTIC_PR,
        ".github/workflows/ci.yml": CI_YML,
        ".github/release-drafter.yml": RELEASE_DRAFTER_CFG,
        ".github/workflows/release-drafter.yml": RELEASE_DRAFTER,
        ".github/workflows/labels-sync.yml": LABELS_SYNC,
        ".github/workflows/projects-sync.yml": PROJECTS_SYNC,
    }
    return files

# --------------------------- main ---------------------------

def main() -> int:
    root = repo_root()
    owner, repo = repo_slug()
    print(f"[info] repo={owner}/{repo} root={root}")

    msgs: list[str] = []
    files = build_files(owner, repo)
    for rel, content in files.items():
        msgs.append(ensure_file(root / rel, content))

    msgs.extend(ensure_changelog(root / "CHANGELOG.md"))

    print("\n".join(msgs))

    print("\nNext steps:\n" + textwrap.dedent(f"""
      1) git add -A
      2) git commit -m "chore(pm): bootstrap governance + workflows"
      3) git push
      4) Open/refresh a PR → check Actions:
         - CI (should pass)
         - Release Drafter (will update the draft)
         - Labels sync (after push to master)
         - Projects sync (needs secret PROJECTS_PAT; project #{'{'}3{'}'}: https://github.com/users/{owner}/projects/3)
      5) Create a test issue labeled `status/Todo, priority/P1` → it should be auto-added to the board.
    """))

    return 0


if __name__ == "__main__":
    sys.exit(main())