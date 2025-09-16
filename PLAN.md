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
- GitHub project board (Project 3) tracks Phase 0 work; issues #11–#19 form the execution backlog.

## Phase 0 (Baseline)
1. **Unify default branch** (#19) – done locally, awaiting push/protection updates.
2. **Modularize extractor core** (#11) – split CLI from pure extraction helpers so history/annex logic can be unit-tested in isolation.
3. **Harden annex pipeline** (#12) – retries, metadata, and conversion-adapter structure with regression fixtures.
4. **Ship history sidecars** (#13) – structured JSON plus optional snapshot limits/throttling.
5. **Fix CLI toggles** (#14) – introduce explicit `--no-*` counterparts and update docs/tests.
6. **Expand regression coverage** (#15) – fixtures for bilingual annex/history cases and tempdir assertions.
7. **Add pytest CI workflow** (#16) – Python 3.10/3.11 matrix running offline tests only.
8. **Sync documentation** (#17) – README, AGENTS.md, CHANGELOG updates once the above land.

## Principles & Constraints
- Never commit fetched HTML, snapshots, or SQLite artifacts; all outputs must be reproducible locally.
- Keep HTML untouched aside from additive enrichment; no destructive rewriting of the fragment.
- Treat annex/history network failures as warnings—report but continue extraction.
- Maintain bilingual parity (FR + EN) for discovery, extraction, and tests.

## Coordination
- Use labels `status/*`, `priority/*`, and `area/extractor` consistently.
- Run `python -m pytest` before every PR; for governance changes also run `python runner.py --apply --self-test`.
- Track progress and blockers in Project 3; move cards as issues transition from Todo → Doing → Review → Done.

## Upcoming (Post Phase 0)
- Refine module boundaries (`lrn/extract.py`, `lrn/annex.py`, `lrn/persist.py`) for reuse by future services.
- Explore structured persistence (SQLite or search index) once the extractor API stabilizes.
- Extend fixtures to cover OCR/scan edge cases before enabling `--ocr` flows.
