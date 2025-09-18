from __future__ import annotations

from pathlib import Path

from lrn.persist import Persistence, PersistOptions, default_db_path


def test_default_db_path(tmp_path: Path) -> None:
    db_path = default_db_path(tmp_path / "logs")
    assert db_path.parent.exists()
    assert db_path.name == "history_snapshots.sqlite"


def test_initialize_and_store(tmp_path: Path) -> None:
    db_path = tmp_path / "history.db"
    persistence = Persistence(PersistOptions(db_path=db_path))
    persistence.initialize()
    assert db_path.exists()

    persistence.register_fragment("frag-1", "S-2.1")
    snapshot_id = persistence.store_snapshot(
        fragment_id="frag-1",
        fetched_at="2025-09-18T00:00:00Z",
        metadata={"source": "test", "status": "ok"},
        html="<div>payload</div>",
    )
    assert snapshot_id == 1

    records = persistence.list_snapshots("frag-1")
    assert len(records) == 1
    assert records[0].metadata["status"] == "ok"


def test_list_snapshots_empty(tmp_path: Path) -> None:
    db_path = tmp_path / "history.db"
    persistence = Persistence(PersistOptions(db_path=db_path))
    persistence.initialize()
    assert persistence.list_snapshots("missing") == []
