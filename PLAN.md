# LRN Project Plan

Goal
Build a Python CLI to extract the inner XHTML from LegisQuébec HTML while preserving all metadata, with enrichment for annex PDFs (Markdown via marker) and fragment history sidecars and index.

Milestones (Repo milestones exist: M1, M2, M3)
- M1 Extractor core
  - Extract inner XHTML, keep-all metadata and integrity attributes
  - Provide CLI flags scaffold
  - Basic tests with pytest
- M2 Annex PDF→MD
  - Detect annex .pdf links, download to annexes/
  - Convert to Markdown via marker; prepend YAML provenance
  - Inject sibling “Version Markdown” links in saved XHTML
  - Handle failures gracefully
- M3 History sidecars
  - Discover fragment HistoryLink URLs; crawl dates
  - Save snapshots under history/<fragment-code>/<YYYYMMDD>.html (+.md as future)
  - Inject per-fragment “Versions” list and build index.json/md

Scopes and constraints
- Keep original XHTML intact; enrichment is additive.
- Use marker from conda env; if missing, degrade gracefully and log warnings.
- Avoid storing binaries in git in large volumes (outputs are artifacts, not committed).

Repository structure (current and planned)
- lrn/cli.py (exists)
- lrn/extract.py (planned)
- lrn/annex.py (planned)
- lrn/history.py (planned)
- tests/ (planned pytest suite)
- unused/ (legacy scripts and data not used by LRN)

Backlog (tracked as issues)
- #1 Extractor core
- #2 Annex PDF→MD
- #3 History sidecars and index
- #4 CLI flags and defaults
- #5 CI pipeline

Next steps
- Flesh out modules (extract, annex, history) from lrn/cli.py logic.
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
