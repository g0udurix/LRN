# LRN project plan

Goal
Build a Python CLI to extract the inner XHTML from LegisQuébec HTML while preserving all metadata, with enrichment for annex PDFs (Markdown via marker) and fragment history sidecars and index.

Roadmap
- M1 “SQLite archive: current.xhtml persistence” — Completed
  - Persist the latest current.xhtml per fragment into SQLite alongside metadata.
  - Initial CLI flags scaffold and basic tests.
- M2 “Snapshots persistence with v2 migration” — Completed
  - Forward-only v2 migration using PRAGMA user_version:
    - Adds jurisdictions and fragment hierarchy fields.
    - Introduces snapshots table.
    - Pre-wires tags/links for upcoming M3.
  - Post-crawl DB sync preserves existing filesystem outputs and tests; DB writes are additive.
- M3 “Annex provenance + tags/links/jurisdictions wiring” — Completed
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
## Post-M3

Optional future utilities for the CLI and data workflows:

- db-init: initialize an empty DB at a specified path using [python.init_db()](lrn/persist.py:249).
- db-verify: run integrity checks (schema version, FK checks, sample queries).
- db-import-history: import legacy snapshot archives into snapshots and link via [python.insert_fragment_version_link()](lrn/persist.py:521).
- Legacy DB import: adapters to migrate data from prior SQLite layouts into M3 schema.

## M3 — Annex provenance, jurisdictions, tags/links (Finalized plan)

This milestone is DB-additive and does not alter any on-disk artifacts. All changes are forward-only and idempotent. Existing tests remain green; new DB tests validate persistence.

### v3 schema deltas (forward-only)

Migration rules
- Guard with existence checks; do nothing if already applied.
- Bump PRAGMA user_version to 3.
- Add minimal supporting indexes for query performance.

DDL snippets
```sql
-- 1) Annexes table
CREATE TABLE IF NOT EXISTS annexes (
  id INTEGER PRIMARY KEY,
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  pdf_url TEXT NOT NULL,
  pdf_path TEXT,
  md_path TEXT,
  content_sha256 TEXT,
  converter_tool TEXT,
  converter_version TEXT,
  provenance_yaml TEXT,
  converted_at TEXT, -- UTC ISO8601
  conversion_status TEXT, -- success / failed / skipped
  warnings_json TEXT,
  metadata_json TEXT,
  UNIQUE(fragment_id, pdf_url)
);

CREATE INDEX IF NOT EXISTS idx_annexes_fragment_id ON annexes(fragment_id);

-- 2) Jurisdictions table (minimal form)
CREATE TABLE IF NOT EXISTS jurisdictions (
  id INTEGER PRIMARY KEY,
  code TEXT NOT NULL UNIQUE,
  name TEXT NOT NULL,
  level TEXT
);

-- 3) Instruments gain jurisdiction_id if missing
-- (guarded at migration time)

-- 4) Tags and fragment_tags (minimal presence)
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE
);
CREATE TABLE IF NOT EXISTS fragment_tags (
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY(fragment_id, tag_id)
);

-- 5) Fragment links (version links to snapshots)
CREATE TABLE IF NOT EXISTS fragment_links (
  id INTEGER PRIMARY KEY,
  from_fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  to_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
  link_type TEXT NOT NULL,
  created_at TEXT,
  UNIQUE(from_fragment_id, to_snapshot_id, link_type)
);

-- 6) Bump schema version
PRAGMA user_version = 3;
```

Rationale
- annexes stores one row per fragment and annex source PDF; provenance_yaml and warnings_json preserve conversion details; md_path allows navigation from DB to generated Markdown.
- jurisdictions normalizes instrument location, enabling queries and filtering.
- tags and fragment_tags provide optional labeling without impacting existing behavior.
- fragment_links adds explicit linkage from current fragments to snapshots with link_type='version' ensuring referential integrity via FK to snapshots.

### Persistence API additions in [python.persist](lrn/persist.py:1)

- [python.upsert_jurisdiction()](lrn/persist.py:436)
- [python.set_instrument_jurisdiction()](lrn/persist.py:463)
- [python.upsert_tag()](lrn/persist.py:478)
- [python.upsert_fragment_tag()](lrn/persist.py:502)
- [python.insert_fragment_version_link()](lrn/persist.py:521)
- [python.upsert_annex()](lrn/persist.py:549)

Idempotency
- Unique constraints and ON CONFLICT guards make operations safe to re-run.
- DB writes are additive and do not modify existing on-disk outputs.

### Integration points in [python.extract()](lrn/cli.py:222)

- Annex persistence after PDF→MD conversion with provenance and hashes.
- Jurisdiction wiring inferred from source URL (e.g., legisquebec).
- Deterministic tags (e.g., 'legisquebec').
- Version links created after history crawl parity with snapshots.

### Tests

- tests/test_db_annex_persistence.py
- tests/test_db_jurisdiction_assignment.py
- tests/test_db_snapshot_link_parity.py
- tests/test_db_content_hash_integrity.py
