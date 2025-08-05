# LRN Extractor

A CLI to extract inner XHTML from LegisQuébec HTML, keep all metadata, and optionally enrich with annex PDF→Markdown and history sidecars.

CLI Usage
- Extract subcommand
  - Syntax:
    - python lrn [python.extract()](lrn/cli.py:222) extract --out-dir OUT_DIR [--db-path DB_PATH] [--history]
  - Flags:
    - --out-dir OUT_DIR: Directory for on-disk artifacts (XHTML, annexes, history/ snapshots, indexes).
    - --db-path DB_PATH: SQLite destination. Defaults to OUT_DIR/legislation.db when omitted.
    - --history: When enabled, archives both current.xhtml and history snapshots.
  - Behavior:
    - With history enabled, both current.xhtml and discovered history snapshots are archived to SQLite additively; on-disk artifacts remain unchanged.
    - Default DB path semantics: If --db-path is not provided, database is created/updated at OUT_DIR/legislation.db.
    - Migration is automatic via PRAGMA user_version; forward-only v2 is applied when needed.
    - The SQLite DB is an artifact suitable for CI export; do not commit it to source control.

Implementation references
- CLI entrypoint and extract wiring: [python.extract()](lrn/cli.py:222)
- Persistence layer: [python.persist](lrn/persist.py:19)
- History logic: [python.history](lrn/history.py:1)

Notes
- Migration: Managed automatically on open using PRAGMA user_version; schema upgrades (e.g., jurisdictions, fragment hierarchy fields, snapshots table, and M3-ready tags/links) are applied without modifying existing on-disk outputs.
- CI: The DB file can be published as a build artifact for inspection and downstream processing.
