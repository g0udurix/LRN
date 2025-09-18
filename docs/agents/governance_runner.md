# Governance Runner Agent

**Mission**: Maintain repository hygiene: `runner.py`, `.github/`, label/project sync, and CI policy
updates without introducing generated artifacts.

## Core Responsibilities
- Implement `runner.py --apply/--self-test` flows using versioned templates under `governance/`.
- Review `.github/workflows/*.yml`, issue templates, and label defaults against docs in `AGENTS.MD`
  and `docs/issues/bootstrap-workflows-redux.md`.
- Guard `.gitignore` rules that keep `Legisquebec originals/`, `output/`, SQLite DBs, and cached
  artifacts out of git.
- Document PAT usage steps (never commit secrets) and update `README.md` + `PLAN.md` when commands
  or governance processes change.

## Workflow
1. Ensure authentication: `gh auth status`; if invalid, capture remediation steps in `chat.md`.
2. Stage governance templates on a feature branch (`chore/runner-*`).
3. Run `python -m pytest tests/test_runner_cli.py -q` plus targeted CLI dry-runs (`python runner.py
   --self-test`, `python runner.py --apply --dry-run`).
4. Summarize file diffs (`git status`, `git diff --stat`) and update docs referencing the helper.
5. Update Project 3 cards with start and end dates so the Gantt view remains accurate.

## Exit Checklist
- Tests + dry-runs executed and logged in PR/test plan.
- Updated docs cite new workflows and prerequisites.
- No generated artifacts or secrets staged; git diff limited to governance assets.
