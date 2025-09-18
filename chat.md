# Session Notes (2025-09-17)

## Context
- Expanded jurisdiction manifests for Canada (QC, municipal pilots) and international OHS coverage (France, China, Germany, Japan, OSHA, etc.).
- Added Playwright-backed fallback logic to `scripts/corpus_ingest.py` and `scripts/headless_fetch.py` to handle DataDome/WAF gateways (Legifrance, CanLII, Ville de Québec, gov.cn/npc.gov.cn).
- Documentation (README, AGENTS, docs/corpus/*, docs/issues/*) now reflects headless workflow, Playwright setup, municipal/federal manifests, and monitoring guidance.
- New manifests rely on external HTML/PDF copies stored outside git; ingestion tested via `python -m pytest` (pass).

## Outstanding Follow-ups
1. Locate an official Calgary-hosted PDF for Bylaw 33M2014 to replace the interim CanLII link (tracked in docs/issues/calgary-building-maintenance.md).
2. Explore Legifrance API/licensing for automated bulk access beyond Playwright captures.
3. Broaden China coverage (sector-specific regulations, municipal bylaws) once stable endpoints are confirmed.

## Environment Tips for Resume
- Reinstall Playwright dependencies if environment resets:
  ```bash
  python -m pip install playwright
  playwright install chromium
  ```
- Use headless helper when manifests hit DataDome/WAF:
  ```bash
  python scripts/headless_fetch.py <url> --out /tmp/page.html --timeout 120000 --wait-until domcontentloaded
  python scripts/corpus_ingest.py --manifest <manifest> --out-dir output_x --log-dir logs/ingestion --resume
  ```
- Reference updated manifests under `docs/corpus/manifests/` for ingestion targets.

## Continuity Plan (2025-09-18)
- **Branches to create**: `chore/runner-cli` (governance helper rebuild), `feat/manifest-expansion` (manifest/headless updates), `feat/history-persist` (clean persistence layer).
- **Agents + duties**:
  - Strategist — carve branches, maintain plan, log stand-ups in `chat.md`.
  - Governance Runner — implement `runner.py`, sync `.github/`, run `python -m pytest tests/test_runner_cli.py -q`, `python runner.py --self-test`, `python runner.py --apply --dry-run`.
  - Corpus Wrangler — validate manifests via `python -m pytest tests/test_manifest_integrity.py -q`, run `scripts/corpus_ingest.py --manifest <file> --out-dir logs/manifest-expansion/<instrument> --log-dir logs/manifest-expansion` after priming blocked URLs with `scripts/headless_fetch.py`.
  - Persistence Architect — design new `lrn/persist.py`, add integration tests, execute `python -m pytest` (focus on new persistence suite) and store outputs in `logs/history-persist/`.
- **Auth prerequisite**: refresh GitHub PAT; run `gh auth login` so governance tasks can push.
- **Logging**: keep run artifacts under `logs/governance-runner/`, `logs/manifest-expansion/`, `logs/history-persist/`. No artifacts committed.
- **Docs to update**: `PLAN.md` (branch status), `README.md` (runner usage once rebuilt), relevant `docs/issues/*.md` with findings.
- **Checkpoints**: daily stand-up in this file; 48h async sync covering blockers + next steps. Always finish with full `python -m pytest` before hand-off.

## Execution Plan Snapshot (pre-run)

### Goal
Deliver three coordinated streams:
1. Governance helper rebuild (`chore/runner-cli`).
2. Manifest/headless expansion (`feat/manifest-expansion`).
3. History persistence refactor (`feat/history-persist`).

### Branch Prep
- Strategist to create branches from latest `master`:
  - `git checkout -b chore/runner-cli`
  - `git checkout -b feat/manifest-expansion`
  - `git checkout -b feat/history-persist`
- Record branch creation + scope in `chat.md` and link to relevant `docs/issues/*.md`.

### Stream Owners & Tasks
- **Governance Runner** (`docs/agents/governance_runner.md`)
  - Refresh GitHub PAT; `gh auth login`.
  - Scaffold `governance/` templates, implement `runner.py` CLI.
  - Update docs (`README.md`, `PLAN.md`) with new usage.
  - Tests: `python -m pytest tests/test_runner_cli.py -q`, `python runner.py --self-test`, `python runner.py --apply --dry-run`.
  - Logs: `logs/governance-runner/`.

- **Corpus Wrangler** (`docs/agents/corpus_wrangler.md`)
  - Validate manifests: `python -m pytest tests/test_manifest_integrity.py -q`.
  - For blocked URLs: run `python scripts/headless_fetch.py --out <tmp>`.
  - Re-run ingestion: `python scripts/corpus_ingest.py --manifest docs/corpus/manifests/<file> --out-dir output_<name> --log-dir logs/manifest-expansion --resume`.
  - Update `docs/issues/*` with findings.
  - Logs: `logs/manifest-expansion/` (git-ignored).

- **Persistence Architect** (`docs/agents/persistence_architect.md`)
  - Draft new `lrn/persist.py`, migrations, integration tests.
  - Coordinate with Governance Runner if new commands/hooks required.
  - Tests: targeted persistence suite + `python -m pytest`.
  - Update `PLAN.md` / `README.md` with persistence strategy.
  - Logs: `logs/history-persist/`.

### Cadence & Reporting
- Daily stand-up in `chat.md` summarizing each stream (status, blockers, next steps).
- 48h sync entry capturing cross-stream dependencies and actions (e.g., PAT refresh complete, manifests updated).
- Before branch hand-off or PR: run full `python -m pytest`, capture command list in `chat.md`, and attach to issue notes.

### Dependencies & Risks
- Governance stream must enable PAT-based operations before persistence branch requires governance hooks.
- Manifest updates should land ahead of persistence integration to ensure fixtures exist.
- Track Project 3 Gantt cleanup alongside governance work to remove Phase 0 leftovers.

### Recovery Checklist
If interrupted, resume by:
1. Reading this `Execution Plan Snapshot`.
2. Checking branch status via `git status -sb`.
3. Reviewing `docs/agents/*.md` for role-specific steps.
4. Confirming latest logs under `logs/<stream>/` and updating `chat.md` with new actions.

## How to Continue the Active Plan
1. **Sync & authenticate**
   - `git fetch origin` then `git checkout master && git pull --ff-only`.
   - Generate/refresh the GitHub PAT, run `gh auth login`, and confirm with `gh auth status`.
2. **Branch creation**
   - From `master`, create each stream branch:
     - `git checkout -b chore/runner-cli`
     - `git checkout master && git checkout -b feat/manifest-expansion`
     - `git checkout master && git checkout -b feat/history-persist`
   - Note branch creation + owner in `chat.md` and update the linked issue file.
3. **Kick off streams**
   - Governance Runner follows `docs/agents/governance_runner.md` (scaffold templates, implement `runner.py`, run CLI tests, update docs, clean Project 3 Phase 0 cards).
   - Corpus Wrangler follows `docs/agents/corpus_wrangler.md` (validate manifests, headless captures, ingestion logs, issue updates).
   - Persistence Architect follows `docs/agents/persistence_architect.md` (schema design, persistence module/tests, documentation updates).
4. **Testing & logging expectations**
   - Each stream runs its module tests plus `python -m pytest` before hand-off.
   - Save command outputs under `logs/<stream>/` and mention log paths in `chat.md` updates.
5. **Reporting cadence**
   - Post a daily stand-up entry (status, blockers, next steps) referencing each branch.
   - Every 48 hours, add a sync note summarizing cross-stream dependencies and upcoming work.
6. **Before PRs or merges**
   - Ensure docs (`PLAN.md`, `README.md`, relevant `docs/issues/*.md`) reflect changes.
   - Record the executed commands in the PR template/test plan.
   - Confirm `git status` is clean apart from intentional diffs; no outputs committed.
7. **If interrupted**
   - Re-read this section, confirm branch state via `git status -sb`, re-open agent briefs, and continue from the last logged stand-up.

## Project 3 Gantt Reminder
- Governance Runner must set explicit start and target dates on every Project 3 card during the `chore/runner-cli` stream so the Gantt view renders correctly.
- Use `gh project item-update` (once PAT/auth is ready) or the web UI to populate `start_date` and `due_date` fields, matching the timeline in `docs/diagrams/multitasking.md`.
- Governance Runner to open/edit `CHANGELOG.md` on each stream, capturing highlights before PR submission.

## Stand-up 2025-09-18
- Status: repo currently on `docs/project-diagrams-and-branch-policy` with doc/test additions (agent briefs, diagrams, changelog). Next action is to split into three feature branches per execution plan once these supporting docs are committed or parked.
- Blockers: working tree dirty; need to finalize/stage documentation before branching off `master`.
- Next steps: wrap doc/test scaffolding into a branch (or baseline), sync `master`, then create `chore/runner-cli`, `feat/manifest-expansion`, `feat/history-persist` for parallel streams.
- Branches carved (2025-09-18): `chore/runner-cli`, `feat/manifest-expansion`, `feat/history-persist`.
- Governance stream scaffolding ready (`governance/README.md`, templates dir); proceeding with runner implementation next.
