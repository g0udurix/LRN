# LRN Project Plan

Goal
Build a Python CLI to extract the inner XHTML from LegisQuébec HTML while preserving all metadata, with enrichment for annex PDFs (Markdown via marker) and fragment history sidecars and index.

Roadmap
- M1 “SQLite Archive: current.xhtml persistence” — Completed
  - Persist the latest current.xhtml per fragment into SQLite alongside metadata.
  - Initial CLI flags scaffold and basic tests.
- M2 “Snapshots persistence with v2 migration” — Completed
  - Forward-only v2 migration using PRAGMA user_version:
    - Adds jurisdictions and fragment hierarchy fields.
    - Introduces snapshots table.
    - Pre-wires tags/links for upcoming M3.
  - Post-crawl DB sync preserves existing filesystem outputs and tests; DB writes are additive.
- M3 “Annex provenance + tags/links/jurisdictions wiring” — Next
  - Wire annex provenance details and fully activate tags/links/jurisdictions features across persisted records.

Scopes and constraints
- Keep original XHTML intact; enrichment is additive.
- Use marker from conda env; if missing, degrade gracefully and log warnings.
- Avoid storing binaries in git in large volumes (outputs are artifacts, not committed).

Repository structure (current and planned)
- lrn/cli.py (exists)
- lrn/extract.py (planned)
- lrn/annex.py (planned)
- lrn/history.py (exists)
- lrn/persist.py (exists)
- tests/ (pytest suite)
- unused/ (legacy scripts and data not used by LRN)

Backlog (tracked as issues)
- #1 Extractor core
- #2 Annex PDF→MD
- #3 History sidecars and index
- #4 CLI flags and defaults
- #5 CI pipeline

Next steps
- Flesh out modules (extract, annex, history) from [python.extract()](lrn/cli.py:1) logic.
- Add pytest tests for extraction and enrichment flows.
- Add GitHub Actions workflow to run tests and optionally a sample extraction.

Notes
- For annex PDF→MD quality, marker is preferred; OCR pipeline to be added later for scanned PDFs.
- History crawl volume should be bounded via flags; implement caching by URL and ETag when available.

### Next Steps (Tasks 7–10)
- [ ] Tests: enumerate_versions parsing with recorded HTML fixtures (no network)
- [ ] Tests: snapshot pathing and history/index.json schema validation
- [ ] End-to-end: small offline fixture test wiring CLI + history to verify outputs and injected Versions
- [ ] CI: GitHub Actions workflow to run tests offline (disable network), cache fixtures, and report artifacts
