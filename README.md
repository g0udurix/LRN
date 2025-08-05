# LRN extractor

A CLI to extract inner XHTML from LegisQuébec HTML, keep all metadata, and optionally enrich with annex PDF→Markdown and history sidecars.

CLI usage
- Extract subcommand
  - Syntax:
    - python -m [python.extract()](lrn/cli.py:222) extract --out-dir OUT_DIR [--db-path DB_PATH] [--history]
  - Flags:
    - --out-dir OUT_DIR: directory for on-disk artifacts (XHTML, annexes, history snapshots, indexes).
    - --db-path DB_PATH: SQLite destination. Defaults to OUT_DIR/legislation.db when omitted.
    - --history: when enabled, archives both current.xhtml and history snapshots.
  - Behavior:
    - With history enabled, both current.xhtml and discovered history snapshots are archived to SQLite additively; on-disk artifacts remain unchanged.
    - Default DB path semantics: if --db-path is not provided, database is created/updated at OUT_DIR/legislation.db.
    - Migration is automatic via PRAGMA user_version; forward-only migrations are applied when needed.
    - The SQLite DB is an artifact suitable for CI export; do not commit it to source control.

SQLite archive
- Default path
  - By default, the database is created in OUT_DIR as OUT_DIR/legislation.db. Override with --db-path.
- Schema overview (M1–M3)
  - M1–M2:
    - instruments, fragments, current_pages, snapshots
  - M3:
    - jurisdictions, tags/fragment_tags, fragment_links, annexes
- Migrations
  - Managed via PRAGMA user_version; forward-only and idempotent.
  - Opening a DB runs migrations as needed. Existing filesystem outputs remain unchanged; DB writes are additive.

Example usage
- Run extract and persist to a specific DB path:
  - python -m [python.extract()](lrn/cli.py:222) extract ... --db-path path/to/legislation.db
- When data is persisted
  - current.xhtml: after versions injection during extract, the page is persisted to current_pages.
  - snapshots: after history crawl/sync, discovered versions are persisted to snapshots and version links added via [python.insert_fragment_version_link()](lrn/persist.py:521).
  - annexes: after PDF→Markdown conversion, annex metadata and provenance are upserted via [python.upsert_annex()](lrn/persist.py:549).

Example queries
- Get current page for a fragment:
  - SELECT url, extracted_at FROM current_pages WHERE fragment_id = ?;
- List snapshots for a fragment (with date):
  - SELECT date, id FROM snapshots WHERE fragment_id = ? ORDER BY date;
- List all instruments by jurisdiction “Québec” (QC):
  - SELECT i.id, i.name FROM instruments i JOIN jurisdictions j ON i.jurisdiction_id = j.id WHERE j.code = 'QC' ORDER BY i.name;
- List annexes by fragment:
  - SELECT id, md_path, pdf_path, conversion_status FROM annexes WHERE fragment_id = ? ORDER BY converted_at DESC;

Determinism and offline guarantees
- DB writes are additive; existing filesystem outputs are unchanged.
- All operations are deterministic and offline-safe for fixtures used by tests.

Implementation references
- CLI entrypoint and extract wiring: [python.extract()](lrn/cli.py:222)
- Persistence layer: [python.persist](lrn/persist.py:1)
- History logic: [python.history](lrn/history.py:1)

Notes
- Migration: managed automatically on open using PRAGMA user_version; schema upgrades (M1–M3) are applied without modifying existing on-disk outputs.
- CI: the DB file can be published as a build artifact for inspection and downstream processing.
