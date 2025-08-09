# Contributing to LRN (for Humans **and** AI Agents)

Welcome! This guide explains how to contribute productively and respectfully — whether you’re a human developer, a researcher, or an autonomous AI agent acting on someone’s behalf.

**Shortlinks**
- Code of Conduct: `CODE_OF_CONDUCT.md` (contact: seemly-peer.0k@icloud.com)
- PR template: `.github/pull_request_template.md`
- Changelog: `CHANGELOG.md`
- Governance/ownership: `CODEOWNERS`

## What contributions we want

We value **useful, minimal, well‑reviewed** changes. Favor small, incremental PRs that:
- Improve docs, tests, or developer experience.
- Fix bugs with clear, reproducible steps.
- Add focused features tied to an accepted issue/milestone.
- Keep diffs clean and reversible.

If you’re unsure, **open an issue** first using the templates in `.github/ISSUE_TEMPLATE/`.

## Project expectations

- We follow **Conventional Commits** and enforce **Semantic Pull Request** titles.
- The default branch is **`master`** and is **protected** (status checks + reviews).
- Releases are prepared via **Release Drafter**; changelog is maintained in `CHANGELOG.md`.
- Issues/PRs are tracked with labels and milestones (Phase 0–4 roadmap).

## Getting started

1. Fork and clone the repo.
2. Create a branch from `master`:
   ```
   git switch -c feat/<scope>--<short-description>
   # or chore/, fix/, docs/, refactor/, ci/, perf/, test/
   ```
3. Make small, reviewable commits using Conventional Commits, e.g.:
   - `feat(extractor): add version enumerator`
   - `fix(parser): handle empty fragment`
   - `docs(readme): clarify setup`
4. Keep PRs small (200–400 LOC changed is a good upper bound).

## Local workflow

- Run the bootstrap/maintenance helper as needed:
  ```
  python runner.py --apply --self-test
  ```
  This updates governance/workflows and runs basic sanity checks.
- Before pushing:
  - Ensure docs/templates are updated if behavior changed.
  - Re-run the self-test if workflows or labels changed.
  - Update `CHANGELOG.md` under **[Unreleased]**.

## Pull Requests

- Use a **semantic title** (Conventional Commits).
- Fill the PR template completely.
- Link to an issue (or open one) unless it’s a tiny docs fix.
- Add the right labels: `type/*`, `area/*`, `status/*`, `priority/*`.
- If the PR is risky or cross-cutting, mark `status/Review` early and request feedback.

### Definition of Done

- ✅ CI passes (lint/tests where applicable)
- ✅ PR checklist completed (including the AI checklist if applicable)
- ✅ Changelog entry added
- ✅ Docs updated and examples included
- ✅ Labels + milestone set

## AI Agent Playbook (IMPORTANT)

Contributions authored by AI agents must follow these guardrails:

1. **Work only from repo truth.** Do not invent files/paths/APIs. If uncertain, propose changes as comments in the PR description.
2. **Make minimal, reversible diffs.** Avoid bulk reformatting or mass renames unless explicitly requested and justified in an issue.
3. **Explain the change.** In the PR body, include a brief “Why/What/How/Impact” section.
4. **Self-checks before commit:**
   - No secrets, tokens, or credentials in code or logs.
   - No large binary files added.
   - No licensing conflicts; include attributions/citations for external standards or texts summarized.
   - Run `python runner.py --self-test` if workflows/templates might be affected.
5. **Conventional Commits + template.** Use the PR template’s AI checklist and mark the PR as AI-authored if applicable.
6. **Don’t bypass review.** Always request review from maintainers; do not merge your own PRs.

## Labels (quick guide)

- `type/*` — feature, fix, docs, refactor, chore, ci, perf, test
- `area/*` — extractor, parser, api, infra, docs, etc.
- `status/*` — Todo, Doing, Review, Blocked, Done
- `priority/*` — P0, P1, P2
- `milestone/*` — phase-0 … phase-4 (aligned to our roadmap)

## Milestones & Releases

- Phase 0: Baseline (schema, ingestion, search)
- Phase 1: Corpus & Standards
- Phase 2: Comparison Engine
- Phase 3: Annotations & Issues
- Phase 4: Guidance UI

Releases are drafted automatically from merged PRs and labels. Keep PR titles clean so Release Drafter can do its job.

## Automation & Secrets

Some workflows (labels sync, projects sync, release drafter) may require a Personal Access Token (PAT).

- **Projects token (`PROJECTS_PAT`)** — create a **classic** PAT with scopes:
  - `repo`
  - `workflow`
  - `project` (classic Projects).  
    If contributing under an organization, also add `read:org`.
- Store it in GitHub:  
  **Settings → Secrets and variables → Actions → New repository secret**  
  Name: `PROJECTS_PAT`.

Never commit tokens or credentials.

## Governance & Conduct

- See `CODE_OF_CONDUCT.md`. Enforcement contact: **seemly-peer.0k@icloud.com**.
- Ownership & review routing are in `CODEOWNERS`.

## Questions?

Open a discussion/issue or email **seemly-peer.0k@icloud.com**.
