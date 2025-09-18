# Issue: Salvage History Persistence Prototype

## Summary
Branch `feat/history-crawl` explored a database-backed persistence layer
(`lrn/persist.py`), extensive governance templates, and large fixture archives.
It diverges significantly from `master` and contains more than 180k lines of
tracked HTML exports, binary `.DS_Store` files, and compiled artifacts. Because of
this, the useful ideas in the branch (SQLite schema migrations, DB-focused test
suite, roadmap docs) were never merged.

## Required Work
1. Extract the reusable pieces (e.g., `lrn/persist.py`, DB-focused pytest cases)
   into a clean feature branch without any generated HTML/output directories.
2. Align the persistence API with current extractor modules (`Fragment`, annex
   processing, history snapshots) and add integration tests proving the round-trip
   from extraction → persistence → query.
3. Decide how the SQLite layer should coexist with the manifest-based corpus
   ingestion (document in `PLAN.md` and `docs/standards/README.md`).
4. Close the legacy branch once the cleaned feature branch merges; delete leftover
   artifacts in the repo or add ignore rules to prevent future reoccurrence.

## Acceptance Criteria
- New branch passes `python -m pytest` with the DB tests included.
- No generated HTML/PDF/SQLite assets committed.
- README/PLAN updated to describe the persistence layer and its maintenance plan.
