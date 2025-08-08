#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sqlite3
import hashlib
import os
from datetime import datetime, timezone
from typing import Optional

# Public API:
# - init_db(db_path: str) -> sqlite3.Connection
# - sha256_hex(text: str) -> str
# - utc_now() -> str
# - upsert_instrument(conn, name: str, source_url: str | None = None, metadata_json: str | None = None) -> int
# - upsert_fragment(conn, instrument_id: int, code: str, metadata_json: str | None = None) -> int
# - upsert_current(conn, fragment_id: int, url: str | None, content_text: str, content_hash: str, extracted_at: str, metadata_json: str | None = None) -> None
# - upsert_snapshot(conn, fragment_id: int, date: str, url: str | None, content_text: str, content_hash: str, retrieved_at: str | None, etag: str | None, last_modified: str | None, metadata_json: str | None = None) -> None

def _apply_connection_pragmas(conn: sqlite3.Connection) -> None:
    cur = conn.cursor()
    cur.execute("PRAGMA foreign_keys=ON;")
    # WAL journaling for better concurrency; ensure deterministic connection-scoped setting
    cur.execute("PRAGMA journal_mode=WAL;")
    cur.close()

def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.cursor()
    try:
        cur.execute(f"PRAGMA table_info({table});")
        for row in cur.fetchall():
            if row[1] == column:
                return True
        return False
    finally:
        cur.close()

def migrate_2_to_3(conn: sqlite3.Connection) -> None:
    """
    Forward-only, additive migration to schema v3.
    - Annexes table
    - Jurisdictions table shape (ensure minimal form exists) and instruments.jurisdiction_id column/index
    - Tags/fragment_tags (ensure minimal form exists with required constraints)
    - Fragment links updated to from_fragment_id->snapshots to_snapshot_id with unique constraint
    Sets PRAGMA user_version=3 on success.
    Idempotent: guarded by IF NOT EXISTS and _column_exists() checks; unique constraints prevent duplication.
    Backward-compatible: if a legacy fragment_links table exists with src_fragment_id/dst_fragment_id,
    rename it aside to avoid DDL conflicts and create the v3 table fresh.
    """
    cur = conn.cursor()
    try:
        conn.execute("BEGIN;")

        # Annexes
        cur.executescript("""
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
  converted_at TEXT,
  conversion_status TEXT,
  warnings_json TEXT,
  metadata_json TEXT,
  UNIQUE(fragment_id, pdf_url)
);
CREATE INDEX IF NOT EXISTS idx_annexes_fragment_id ON annexes(fragment_id);
""")

        # Jurisdictions: ensure minimal table exists (code UNIQUE NOT NULL, name NOT NULL, level)
        cur.executescript("""
CREATE TABLE IF NOT EXISTS jurisdictions (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  level TEXT
);
""")

        # instruments.jurisdiction_id column and index (guarded)
        if not _column_exists(conn, "instruments", "jurisdiction_id"):
            cur.execute("ALTER TABLE instruments ADD COLUMN jurisdiction_id INTEGER REFERENCES jurisdictions(id);")
        cur.execute("CREATE INDEX IF NOT EXISTS idx_instruments_jurisdiction ON instruments(jurisdiction_id);")

        # Tags and fragment_tags minimal presence
        cur.executescript("""
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  name TEXT UNIQUE NOT NULL
);
CREATE TABLE IF NOT EXISTS fragment_tags (
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  tag_id INTEGER NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
  PRIMARY KEY(fragment_id, tag_id)
);
CREATE INDEX IF NOT EXISTS idx_fragment_tags_tag ON fragment_tags(tag_id);
""")

        # Fragment links:
        # If a legacy table exists with old columns, rename it to avoid conflicts.
        try:
            cur.execute("PRAGMA table_info(fragment_links);")
            cols = [r[1] for r in cur.fetchall()]
        except Exception:
            cols = []
        if cols and ("src_fragment_id" in cols or "dst_fragment_id" in cols):
            # Drop legacy indexes if present (best-effort, ignore failures)
            for idx in ("idx_fragment_links_src", "idx_fragment_links_dst", "idx_fragment_links_type"):
                try:
                    cur.execute(f"DROP INDEX IF EXISTS {idx};")
                except Exception:
                    pass
            # Rename legacy table aside
            cur.execute("ALTER TABLE fragment_links RENAME TO fragment_links_legacy;")

        # Create the v3 structure pointing to snapshots with unique constraint
        cur.executescript("""
CREATE TABLE IF NOT EXISTS fragment_links (
  id INTEGER PRIMARY KEY,
  from_fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  to_snapshot_id INTEGER NOT NULL REFERENCES snapshots(id) ON DELETE CASCADE,
  link_type TEXT NOT NULL,
  created_at TEXT,
  UNIQUE(from_fragment_id, to_snapshot_id, link_type)
);
CREATE INDEX IF NOT EXISTS idx_fragment_links_from ON fragment_links(from_fragment_id);
""")

        # Set user_version=3
        cur.execute("PRAGMA user_version = 3;")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def migrate_1_to_2(conn: sqlite3.Connection) -> None:
    """
    Forward-only, additive migration to schema v2.
    Applies guarded ALTER TABLE ADD COLUMNs and creates new tables/indexes/triggers.
    Sets PRAGMA user_version=2 on success.
    """
    cur = conn.cursor()
    try:
        conn.execute("BEGIN;")
        # jurisdictions and indexes/triggers
        cur.executescript("""
CREATE TABLE IF NOT EXISTS jurisdictions (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE,
  name TEXT NOT NULL,
  type TEXT,
  parent_id INTEGER NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  metadata_json TEXT,
  FOREIGN KEY (parent_id) REFERENCES jurisdictions(id) ON DELETE SET NULL ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_jurisdictions_parent ON jurisdictions(parent_id);
CREATE INDEX IF NOT EXISTS idx_jurisdictions_code ON jurisdictions(code);
CREATE TRIGGER IF NOT EXISTS trg_jurisdictions_updated_at
AFTER UPDATE ON jurisdictions
FOR EACH ROW WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE jurisdictions SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;
""")
        # instruments additive columns (guarded)
        if not _column_exists(conn, "instruments", "official_number"):
            cur.execute("ALTER TABLE instruments ADD COLUMN official_number TEXT;")
        if not _column_exists(conn, "instruments", "publication_date"):
            cur.execute("ALTER TABLE instruments ADD COLUMN publication_date TEXT;")
        if not _column_exists(conn, "instruments", "jurisdiction_id"):
            cur.execute("ALTER TABLE instruments ADD COLUMN jurisdiction_id INTEGER NULL;")
        if not _column_exists(conn, "instruments", "is_archived"):
            cur.execute("ALTER TABLE instruments ADD COLUMN is_archived INTEGER NOT NULL DEFAULT 0;")
        cur.executescript("""
CREATE INDEX IF NOT EXISTS idx_instruments_jurisdiction_id ON instruments(jurisdiction_id);
CREATE INDEX IF NOT EXISTS idx_instruments_official_number ON instruments(official_number);
""")
        # fragments additive columns (guarded)
        if not _column_exists(conn, "fragments", "parent_id"):
            cur.execute("ALTER TABLE fragments ADD COLUMN parent_id INTEGER NULL;")
        if not _column_exists(conn, "fragments", "display_order"):
            cur.execute("ALTER TABLE fragments ADD COLUMN display_order INTEGER NULL;")
        if not _column_exists(conn, "fragments", "source_id"):
            cur.execute("ALTER TABLE fragments ADD COLUMN source_id TEXT NULL;")
        if not _column_exists(conn, "fragments", "block_type"):
            cur.execute("ALTER TABLE fragments ADD COLUMN block_type TEXT NULL;")
        cur.executescript("""
CREATE INDEX IF NOT EXISTS idx_fragments_parent_id ON fragments(parent_id);
CREATE INDEX IF NOT EXISTS idx_fragments_instrument_display ON fragments(instrument_id, display_order);
""")
        # snapshots table and indexes
        cur.executescript("""
CREATE TABLE IF NOT EXISTS snapshots (
  id INTEGER PRIMARY KEY,
  fragment_id INTEGER NOT NULL,
  date TEXT NOT NULL,
  url TEXT,
  content_text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  retrieved_at TEXT,
  etag TEXT,
  last_modified TEXT,
  metadata_json TEXT,
  UNIQUE(fragment_id, date),
  FOREIGN KEY (fragment_id) REFERENCES fragments(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_snapshots_fragment_date ON snapshots(fragment_id, date);
CREATE INDEX IF NOT EXISTS idx_snapshots_etag ON snapshots(etag);
CREATE INDEX IF NOT EXISTS idx_snapshots_last_modified ON snapshots(last_modified);
CREATE INDEX IF NOT EXISTS idx_snapshots_hash ON snapshots(content_hash);
""")
        # M3-ready inert structures
        cur.executescript("""
CREATE TABLE IF NOT EXISTS tags (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  category TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  metadata_json TEXT
);
CREATE TRIGGER IF NOT EXISTS trg_tags_updated_at
AFTER UPDATE ON tags
FOR EACH ROW WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE tags SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;
CREATE TABLE IF NOT EXISTS fragment_tags (
  fragment_id INTEGER NOT NULL,
  tag_id INTEGER NOT NULL,
  PRIMARY KEY(fragment_id, tag_id),
  FOREIGN KEY (fragment_id) REFERENCES fragments(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fragment_tags_tag ON fragment_tags(tag_id);
CREATE TABLE IF NOT EXISTS fragment_links (
  id INTEGER PRIMARY KEY,
  src_fragment_id INTEGER NOT NULL,
  dst_fragment_id INTEGER NOT NULL,
  link_type TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  metadata_json TEXT,
  FOREIGN KEY (src_fragment_id) REFERENCES fragments(id) ON DELETE CASCADE ON UPDATE CASCADE,
  FOREIGN KEY (dst_fragment_id) REFERENCES fragments(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fragment_links_src ON fragment_links(src_fragment_id);
CREATE INDEX IF NOT EXISTS idx_fragment_links_dst ON fragment_links(dst_fragment_id);
CREATE INDEX IF NOT EXISTS idx_fragment_links_type ON fragment_links(link_type);
""")
        # set user_version=2 and commit
        cur.execute("PRAGMA user_version = 2;")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

def init_db(db_path: str) -> sqlite3.Connection:
    """
    Open/create DB at db_path, enable pragmas, and initialize schema v1 if user_version = 0.
    Migrate forward-only through v2 and v3 as needed.
    Return an open connection with row_factory = sqlite3.Row.
    """
    # Ensure parent directory exists deterministically to avoid "unable to open database file"
    try:
        parent = os.path.dirname(db_path) or "."
        os.makedirs(parent, exist_ok=True)
    except Exception:
        # Let sqlite connect raise a clear error if path is invalid; tests expect robustness
        pass
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    _apply_connection_pragmas(conn)

    cur = conn.cursor()
    try:
        # Determine current schema version
        cur.execute("PRAGMA user_version;")
        row = cur.fetchone()
        user_version = int(row[0]) if row is not None else 0

        if user_version == 0:
            # Create schema v1 atomically
            conn.execute("BEGIN")
            # Tables
            cur.executescript("""
            -- instruments
            CREATE TABLE IF NOT EXISTS instruments (
              id INTEGER PRIMARY KEY,
              name TEXT NOT NULL UNIQUE,
              source_url TEXT,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
              metadata_json TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_instruments_source_url ON instruments(source_url);

            -- fragments
            CREATE TABLE IF NOT EXISTS fragments (
              id INTEGER PRIMARY KEY,
              instrument_id INTEGER NOT NULL,
              code TEXT NOT NULL,
              created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
              updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
              metadata_json TEXT,
              UNIQUE(instrument_id, code),
              FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE ON UPDATE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_fragments_instrument_code ON fragments(instrument_id, code);

            -- current_pages
            CREATE TABLE IF NOT EXISTS current_pages (
              id INTEGER PRIMARY KEY,
              fragment_id INTEGER NOT NULL UNIQUE,
              url TEXT,
              content_text TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              extracted_at TEXT NOT NULL,
              metadata_json TEXT,
              FOREIGN KEY (fragment_id) REFERENCES fragments(id) ON DELETE CASCADE ON UPDATE CASCADE
            );
            CREATE INDEX IF NOT EXISTS idx_current_pages_url ON current_pages(url);
            CREATE INDEX IF NOT EXISTS idx_current_pages_hash ON current_pages(content_hash);

            -- Housekeeping triggers
            CREATE TRIGGER IF NOT EXISTS trg_instruments_updated_at
            AFTER UPDATE ON instruments
            FOR EACH ROW WHEN NEW.updated_at = OLD.updated_at
            BEGIN
              UPDATE instruments SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
            END;

            CREATE TRIGGER IF NOT EXISTS trg_fragments_updated_at
            AFTER UPDATE ON fragments
            FOR EACH ROW WHEN NEW.updated_at = OLD.updated_at
            BEGIN
              UPDATE fragments SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
            END;

            -- historical_fragments
            CREATE TABLE IF NOT EXISTS historical_fragments (
              id INTEGER PRIMARY KEY,
              fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
              content_text TEXT NOT NULL,
              content_hash TEXT NOT NULL,
              date TEXT NOT NULL,
              metadata_json TEXT
            );

            -- fragment_changes
            CREATE TABLE IF NOT EXISTS fragment_changes (
              id INTEGER PRIMARY KEY,
              historical_fragment_id INTEGER NOT NULL REFERENCES historical_fragments(id) ON DELETE CASCADE,
              change_type TEXT NOT NULL,
              old_value TEXT,
              new_value TEXT
            );
            """)
            # Bump user_version to 1
            cur.execute("PRAGMA user_version = 1;")
            conn.commit()
            user_version = 1

        if user_version == 1:
            # Apply v2 additive migration
            migrate_1_to_2(conn)
            # refresh version
            cur.execute("PRAGMA user_version;")
            row = cur.fetchone()
            user_version = int(row[0]) if row is not None else 0

        if user_version == 2:
            # Apply v3 additive migration
            migrate_2_to_3(conn)

        if user_version == 3:
            # Apply v4 additive migration
            migrate_3_to_4(conn)
        elif user_version >= 4:
            # Already at or above v4; no-op
            pass
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()

    return conn


def migrate_3_to_4(conn: sqlite3.Connection) -> None:
    """
    Forward-only, additive migration to schema v4.
    Creates the historical_fragments and fragment_changes tables.
    Sets PRAGMA user_version=4 on success.
    """
    cur = conn.cursor()
    try:
        conn.execute("BEGIN;")

        # historical_fragments and fragment_changes tables
        cur.executescript("""
CREATE TABLE IF NOT EXISTS historical_fragments (
  id INTEGER PRIMARY KEY,
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  content_text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  date TEXT NOT NULL,
  metadata_json TEXT
);

CREATE TABLE IF NOT EXISTS fragment_changes (
  id INTEGER PRIMARY KEY,
  historical_fragment_id INTEGER NOT NULL REFERENCES historical_fragments(id) ON DELETE CASCADE,
  change_type TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT
);
""")

        # Set user_version=4
        cur.execute("PRAGMA user_version = 4;")
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        cur.close()


def sha256_hex(text: str) -> str:
    h = hashlib.sha256()
    # Ensure deterministic UTF-8 encoding
    h.update(text.encode("utf-8"))
    return h.hexdigest()

def utc_now() -> str:
    # ISO 8601 UTC with Z, e.g., 2025-08-05T00:00:00Z
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")

def upsert_instrument(conn: sqlite3.Connection, name: str, source_url: Optional[str] = None, metadata_json: Optional[str] = None) -> int:
    """
    Upsert instruments by (name) with DO UPDATE for source_url and updated_at.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO instruments(name, source_url, metadata_json)
            VALUES(?, ?, ?)
            ON CONFLICT(name) DO UPDATE SET
              source_url=excluded.source_url,
              metadata_json=COALESCE(excluded.metadata_json, instruments.metadata_json),
              updated_at=strftime('%Y-%m-%dT%H:%M:%fZ','now')
            """,
            (name, source_url, metadata_json),
        )
        conn.commit()
        cur.execute("SELECT id FROM instruments WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("upsert_instrument failed to retrieve id")
        return int(row[0])
    finally:
        cur.close()

def upsert_fragment(conn: sqlite3.Connection, instrument_id: int, code: str, metadata_json: Optional[str] = None) -> int:
    """
    Upsert fragments by (instrument_id, code).
    Prefer INSERT ... ON CONFLICT DO NOTHING then SELECT id.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO fragments(instrument_id, code, metadata_json)
            VALUES(?, ?, ?)
            ON CONFLICT(instrument_id, code) DO NOTHING
            """,
            (instrument_id, code, metadata_json),
        )
        conn.commit()
        cur.execute("SELECT id FROM fragments WHERE instrument_id = ? AND code = ?", (instrument_id, code))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("upsert_fragment failed to retrieve id")
        return int(row[0])
    finally:
        cur.close()

def upsert_current(conn: sqlite3.Connection, fragment_id: int, url: Optional[str], content_text: str, content_hash: str, extracted_at: str, metadata_json: Optional[str] = None) -> None:
    """
    Upsert current_pages by (fragment_id) with DO UPDATE for url, content_text, content_hash, extracted_at.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO current_pages(fragment_id, url, content_text, content_hash, extracted_at, metadata_json)
            VALUES(?, ?, ?, ?, ?, ?)
            ON CONFLICT(fragment_id) DO UPDATE SET
              url=excluded.url,
              content_text=excluded.content_text,
              content_hash=excluded.content_hash,
              extracted_at=excluded.extracted_at,
              metadata_json=COALESCE(excluded.metadata_json, current_pages.metadata_json)
            """,
            (fragment_id, url, content_text, content_hash, extracted_at, metadata_json),
        )
        conn.commit()
    finally:
        cur.close()

def upsert_snapshot(conn: sqlite3.Connection,
                    fragment_id: int,
                    date: str,
                    url: Optional[str],
                    content_text: str,
                    content_hash: str,
                    retrieved_at: Optional[str],
                    etag: Optional[str],
                    last_modified: Optional[str],
                    metadata_json: Optional[str]) -> None:
    """
    Idempotently upsert a snapshot by unique (fragment_id, date).
    Compatible with migrate_1_to_2 snapshots schema.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO snapshots(fragment_id, date, url, content_text, content_hash, retrieved_at, etag, last_modified, metadata_json)
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fragment_id, date) DO UPDATE SET
              url=excluded.url,
              content_text=excluded.content_text,
              content_hash=excluded.content_hash,
              retrieved_at=excluded.retrieved_at,
              etag=COALESCE(excluded.etag, snapshots.etag),
              last_modified=COALESCE(excluded.last_modified, snapshots.last_modified),
              metadata_json=COALESCE(excluded.metadata_json, snapshots.metadata_json)
            """,
            (fragment_id, date, url, content_text, content_hash, retrieved_at, etag, last_modified, metadata_json),
        )
        conn.commit()
    finally:
        cur.close()

# ---------- M3 Persistence APIs ----------

def upsert_jurisdiction(conn: sqlite3.Connection, code: str, name: str, level: Optional[str]) -> int:
    """
    Idempotently upsert a jurisdiction by code. Updates mutable fields.
    Returns id.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO jurisdictions(code, name, level)
            VALUES(?, ?, ?)
            ON CONFLICT(code) DO UPDATE SET
              name=excluded.name,
              level=excluded.level
            """,
            (code, name, level),
        )
        conn.commit()
        cur.execute("SELECT id FROM jurisdictions WHERE code = ?", (code,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("upsert_jurisdiction failed to retrieve id")
        return int(row[0])
    finally:
        cur.close()


def set_instrument_jurisdiction(conn: sqlite3.Connection, instrument_id: int, jurisdiction_id: int) -> None:
    """
    Set instruments.jurisdiction_id for a given instrument idempotently.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            "UPDATE instruments SET jurisdiction_id = ? WHERE id = ?",
            (jurisdiction_id, instrument_id),
        )
        conn.commit()
    finally:
        cur.close()


def upsert_tag(conn: sqlite3.Connection, name: str) -> int:
    """
    Upsert tag by name, return id.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO tags(name)
            VALUES(?)
            ON CONFLICT(name) DO NOTHING
            """,
            (name,),
        )
        conn.commit()
        cur.execute("SELECT id FROM tags WHERE name = ?", (name,))
        row = cur.fetchone()
        if not row:
            raise RuntimeError("upsert_tag failed to retrieve id")
        return int(row[0])
    finally:
        cur.close()


def upsert_fragment_tag(conn: sqlite3.Connection, fragment_id: int, tag_id: int) -> None:
    """
    Associate a tag to a fragment idempotently.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO fragment_tags(fragment_id, tag_id)
            VALUES(?, ?)
            ON CONFLICT(fragment_id, tag_id) DO NOTHING
            """,
            (fragment_id, tag_id),
        )
        conn.commit()
    finally:
        cur.close()


def insert_fragment_version_link(conn: sqlite3.Connection, from_fragment_id: int, to_snapshot_id: int, link_type: str = "version", created_at: Optional[str] = None) -> int:
    """
    Insert a fragment link (from fragment to snapshot) idempotently by unique constraint.
    Returns id of the link.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO fragment_links(from_fragment_id, to_snapshot_id, link_type, created_at)
            VALUES(?, ?, ?, ?)
            ON CONFLICT(from_fragment_id, to_snapshot_id, link_type) DO NOTHING
            """,
            (from_fragment_id, to_snapshot_id, link_type, created_at),
        )
        conn.commit()
        cur.execute(
            "SELECT id FROM fragment_links WHERE from_fragment_id=? AND to_snapshot_id=? AND link_type=?",
            (from_fragment_id, to_snapshot_id, link_type),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("insert_fragment_version_link failed to retrieve id")
        return int(row[0])
    finally:
        cur.close()


def upsert_annex(
    conn: sqlite3.Connection,
    fragment_id: int,
    pdf_url: str,
    pdf_path: Optional[str],
    md_path: Optional[str],
    content_sha256: Optional[str],
    converter_tool: Optional[str],
    converter_version: Optional[str],
    provenance_yaml: Optional[str],
    converted_at: Optional[str],
    conversion_status: Optional[str],
    warnings_json: Optional[str],
    metadata_json: Optional[str],
) -> int:
    """
    Upsert annex by (fragment_id, pdf_url). Updates mutable fields on conflict.
    Returns id.
    """
    cur = conn.cursor()
    try:
        cur.execute(
            """
            INSERT INTO annexes(
              fragment_id, pdf_url, pdf_path, md_path, content_sha256,
              converter_tool, converter_version, provenance_yaml,
              converted_at, conversion_status, warnings_json, metadata_json
            )
            VALUES(?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(fragment_id, pdf_url) DO UPDATE SET
              pdf_path=excluded.pdf_path,
              md_path=excluded.md_path,
              content_sha256=excluded.content_sha256,
              converter_tool=excluded.converter_tool,
              converter_version=excluded.converter_version,
              provenance_yaml=excluded.provenance_yaml,
              converted_at=excluded.converted_at,
              conversion_status=excluded.conversion_status,
              warnings_json=excluded.warnings_json,
              metadata_json=excluded.metadata_json
            """,
            (
                fragment_id, pdf_url, pdf_path, md_path, content_sha256,
                converter_tool, converter_version, provenance_yaml,
                converted_at, conversion_status, warnings_json, metadata_json,
            ),
        )
        conn.commit()
        cur.execute(
            "SELECT id FROM annexes WHERE fragment_id = ? AND pdf_url = ?",
            (fragment_id, pdf_url),
        )
        row = cur.fetchone()
        if not row:
            raise RuntimeError("upsert_annex failed to retrieve id")
        return int(row[0])
    finally:
        cur.close()