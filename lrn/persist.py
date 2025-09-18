"""SQLite-backed persistence helpers for history snapshots."""
from __future__ import annotations

import json
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional


@dataclass
class PersistOptions:
    """Configuration for persistence operations."""

    db_path: Path


@dataclass
class SnapshotRecord:
    """Structured snapshot record returned from queries."""

    fragment_id: str
    snapshot_id: int
    fetched_at: str
    metadata: dict
    html: str


class Persistence:
    """Lightweight SQLite helper for history snapshot storage."""

    def __init__(self, options: PersistOptions):
        self.options = options
        self.options.db_path.parent.mkdir(parents=True, exist_ok=True)

    def connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.options.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def initialize(self) -> None:
        with self.connect() as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS fragments (
                    fragment_id TEXT PRIMARY KEY,
                    instrument TEXT NOT NULL
                )
                """
            )
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS snapshots (
                    snapshot_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    fragment_id TEXT NOT NULL,
                    fetched_at TEXT NOT NULL,
                    metadata TEXT NOT NULL,
                    html TEXT NOT NULL,
                    FOREIGN KEY(fragment_id) REFERENCES fragments(fragment_id)
                )
                """
            )
            conn.commit()

    def register_fragment(self, fragment_id: str, instrument: str) -> None:
        with self.connect() as conn:
            conn.execute(
                "INSERT OR REPLACE INTO fragments(fragment_id, instrument) VALUES (?, ?)",
                (fragment_id, instrument),
            )
            conn.commit()

    def store_snapshot(self, fragment_id: str, fetched_at: str, metadata: dict, html: str) -> int:
        with self.connect() as conn:
            cursor = conn.execute(
                """
                INSERT INTO snapshots(fragment_id, fetched_at, metadata, html)
                VALUES (?, ?, ?, ?)
                """,
                (fragment_id, fetched_at, json.dumps(metadata, ensure_ascii=False), html),
            )
            conn.commit()
            return int(cursor.lastrowid)

    def list_snapshots(self, fragment_id: str) -> List[SnapshotRecord]:
        with self.connect() as conn:
            rows = conn.execute(
                "SELECT fragment_id, snapshot_id, fetched_at, metadata, html FROM snapshots WHERE fragment_id = ? ORDER BY snapshot_id",
                (fragment_id,),
            ).fetchall()
        return [
            SnapshotRecord(
                fragment_id=row["fragment_id"],
                snapshot_id=int(row["snapshot_id"]),
                fetched_at=row["fetched_at"],
                metadata=json.loads(row["metadata"]),
                html=row["html"],
            )
            for row in rows
        ]


def default_db_path(base_dir: Optional[Path] = None) -> Path:
    base = base_dir or Path('logs/history-persist')
    base.mkdir(parents=True, exist_ok=True)
    return base / 'history_snapshots.sqlite'


__all__ = [
    'PersistOptions',
    'Persistence',
    'SnapshotRecord',
    'default_db_path',
]
