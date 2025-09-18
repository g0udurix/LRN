# LRN Project Plan

## Goal
Deliver a dependable Python extractor that:
- isolates the LegisQuébec inner XHTML fragment for every instrument;
- enriches annex links with Markdown sidecars and provenance metadata;
- captures version history snapshots with deterministic file layouts; and
- remains reproducible through offline fixtures and automated tests.

## Current Status
- CLI orchestrates mirror → extract → annex → history flows (`lrn/cli.py`, `lrn/history.py`).
- Offline pytest suite exercises extraction, annex placeholders, and history crawling.
- GitHub project board (Project 3) tracks Phase 0 work; issues #11–#19 were executed in this phase.

## Phase 0 (Baseline)
1. **Unify default branch** (#19) – ✅ merged & pushed; master is canonical.
2. **Modularize extractor core** (#11) – ✅ modules landed (`lrn/extract.py`, `lrn/annex.py`, `lrn/history.py`).
3. **Harden annex pipeline** (#12) – ✅ retries/size caps + typed records.
4. **Ship history sidecars** (#13) – ✅ structured snapshots & injection warnings.
5. **Fix CLI toggles** (#14) – ✅ `--no-annex-pdf-to-md` / `--no-history-sidecars` supported.
6. **Expand regression coverage** (#15) – ✅ annex/history/RC-path fixtures in pytest.
7. **Add pytest CI workflow** (#16) – ✅ GitHub Actions matrix (3.10/3.11) in place.
8. **Sync documentation** (#17) – ✅ README/AGENTS reflect modular architecture and CI/testing model.

## Phase 1 – Corpus & Standards
**Objective:** ingest a representative LegisQuébec corpus (FR + EN) alongside CSA/ANSI/ISO metadata, establishing the groundwork for standards crosswalks.

### Key Tracks
1. **Corpus Scoping**
   - Identify priority instruments/bylaws for ingestion (Phase 1 subset).
   - Document source URLs, licensing/terms of use, and required frequency.
2. **Batch Ingestion Pipeline**
   - Extend or add scripts to mirror the scoped corpus in bulk with resilience (retry/backoff, checksum logging).
   - Write metadata manifests (JSON/CSV) summarising instrument IDs, language, fetch timestamp, SHA256.
3. **Standards Mapping Scaffold**
   - Introduce `lrn/standards/` with typed models (e.g., `StandardRef`, `ComplianceMapping`).
   - Prototype a YAML/JSON schema for mapping LegisQuébec clauses to CSA/ANSI/ISO references.
4. **Testing & Validation**
   - Add fixtures for at least one FR/EN pair plus sample standards references.
   - Expand pytest coverage to verify batch ingestion output and schema validation.
5. **Documentation & Tracking**
   - Update README/AGENTS with corpus ingestion instructions and standards schema overview.
   - Record ingestion runs (date, scope) under `logs/` with a standardized template.

### Priority Jurisdictions (current focus)
- New Brunswick, Ontario, Alberta, British Columbia (Canada)
- OSHA 29 CFR 1910 & 1926 (USA)
- United Kingdom & France (Europe)

### Deliverables (issues to file)
- #20 Corpus scope & licensing notes.
- #21 Batch ingestion command with manifests + retries.
- #22 Standards mapping schema + types.
- #23 Regression tests for ingestion + standards validation.
- #24 Docs update & onboarding for Phase 1 workflows.
- #25 Map Canadian federal/provincial portals for future ingestion.
- #26 Survey international legislative portals (US, UK, FR, AU, JP, CN, DE).

## Principles & Constraints
- Never commit fetched HTML, snapshots, or SQLite artifacts; all outputs must be reproducible locally.
- Keep HTML untouched aside from additive enrichment; no destructive rewriting of the fragment.
- Treat annex/history network failures as warnings—report but continue extraction.
- Maintain bilingual parity (FR + EN) for discovery, extraction, and tests.

## Branch Audit — 2025-09-18
| Branch | Status vs `master` | Next Action |
| --- | --- | --- |
| `chore/rules-and-plan-update` | Fully merged | Local branch deleted. Delete remote with `git push origin --delete chore/rules-and-plan-update` (requires auth). |
| `feat/extractor-core` | Fully merged | Local branch deleted. Delete remote with `git push origin --delete feat/extractor-core`. |
| `test/pytest-and-ci` | Fully merged | Local branch deleted. Delete remote with `git push origin --delete test/pytest-and-ci`. |
| `chore/bootstrap-workflows` | Stale, contains generated artifacts and prose `runner.py` | Track cleanup in `docs/issues/bootstrap-workflows-redux.md`; rebuild executable runner and clean workflows. |
| `feat/history-crawl` | Stale persistence prototype with large tracked HTML | Track salvage in `docs/issues/history-persistence-refactor.md`; rebuild persistence layer without committing outputs. |

> Note: Remote deletions failed locally due to missing push credentials; run the commands above from an authenticated environment to finish the cleanup.

## Governance Helper Rebuild
- Implement `runner.py` with `--apply` / `--self-test` and template bundle under `governance/templates/`.
- Provide pytest coverage (`tests/test_runner_cli.py`) verifying dry-run and apply behaviour.
- Document workflows in `README.md` and `CHANGELOG.md`; ensure Project 3 cards include dates.

## Project Management Rhythm
- Update [Project 3 / Gantt view](https://github.com/users/g0udurix/projects/3/views/2) after every planning session. Map each active branch to a single project item.
- Ensure each Project 3 card has explicit start and target dates so the Gantt view renders correctly.
- Keep only one feature branch in flight per engineer; park additional ideas as issues.
- Document every test command run before opening a PR (tests + ingestion smoke). Attach the command list to the issue or PR template.
- Maintain `CHANGELOG.md` for user-visible changes; update it as part of each feature branch wrap-up.
- Re-run the governance helper (`python runner.py --apply --self-test`) once the executable version lands; record changes in `CHANGELOG.md`.

## Coordination
- Use labels `status/*`, `priority/*`, and `area/extractor` consistently.
- Run `python -m pytest` before every PR; for governance changes also run `python runner.py --apply --self-test`.
- Track progress and blockers in Project 3; move cards as issues transition from Todo → Doing → Review → Done.

## Upcoming (Beyond Phase 1)
- Structured persistence (`lrn/persist.py` or external DB) for corpus snapshots.
- OCR/scan support to handle non-text PDFs.
- Integration with comparison/annotation features planned for Phase 2+.
