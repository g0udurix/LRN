# Auxiliary Agent Playbook

This folder defines focused assistant profiles that mirror the multi-agent setup in `~/.codex/`.
Use these briefs when spinning up specialised helpers so each can operate fast without re-learning
project norms from scratch. Every agent references canonical docs (`AGENTS.MD`, `PLAN.md`,
`README.md`, `docs/corpus/*`, `docs/issues/*`) and records outcomes in `chat.md` or per-issue notes.

## Agent Index
- `strategist.md` – planning + orchestration lead; keeps branches aligned with roadmap.
- `governance_runner.md` – automates repo hygiene (`runner.py`, `.github/`, label sync).
- `corpus_wrangler.md` – handles ingestion manifests, headless fetch prep, checksum validation.
- `standards_mapper.md` – drives CSA/ANSI/ISO crosswalk tooling and schema regression tests.

## Usage Pattern
1. Pick the agent whose charter matches the task; share the relevant issue/branch context.
2. Provide the agent with recent plan + diagrams (see `PLAN.md`, `README.md:114-207`).
3. Have the agent draft a minimal checklist, run the necessary commands (pytest, ingestion smoke,
   governance sync), and log commands + outcomes.
4. Merge artifacts into the active feature branch (`type/topic`), update docs, and hand off to the
   next agent or human maintainer via `chat.md`.

## Integration Checklist
- Always run `python -m pytest` before handing off work between agents.
- For manifests or ingestion runs, cache outputs under `logs/` / `output/` (git-ignored) and link
  the run metadata in the issue tracker.
- Governance actions must cite the PAT or secrets used (never commit them) and confirm changes via
  `git status` + summary in the PR template.
- Standards work must include validation with `python -m lrn.standards validate <file>` and update
  `docs/standards/README.md` when new schemas land.
