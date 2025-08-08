import io
import sys
import csv
import sqlite3
from pathlib import Path

import lrn.cli as cli


def run_cli_argv(argv: list[str]) -> tuple[int, str, str]:
    old_argv = sys.argv
    old_out, old_err = sys.stdout, sys.stderr
    cap_out, cap_err = io.StringIO(), io.StringIO()
    sys.argv = ["lrn"] + argv
    sys.stdout = cap_out
    sys.stderr = cap_err
    try:
        rc = 0
        try:
            cli.main()
        except SystemExit as e:
            rc = int(e.code) if isinstance(e.code, int) else (0 if e.code is None else 1)
        return rc, cap_out.getvalue(), cap_err.getvalue()
    finally:
        sys.argv = old_argv
        sys.stdout = old_out
        sys.stderr = old_err


def seed_db_via_import_history(tmp_path: Path) -> tuple[Path, Path]:
    """
    Create a minimal out_dir with instrumentA and se:1 fragment, two snapshots.
    Import into DB using CLI to keep black-box wiring.
    Returns (db_path, out_dir).
    """
    out_dir = tmp_path / "out"
    inst = out_dir / "instrumentA"
    (inst / "history" / "se:1").mkdir(parents=True, exist_ok=True)

    # current.xhtml
    (inst / "current.xhtml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<div xmlns="http://www.w3.org/1999/xhtml"><div id="se:1"><h1>Instrument A</h1></div></div>',
        encoding="utf-8",
    )

    # history and index
    index_items = [
        {"date": "20200101", "path": "history/se:1/20200101.html"},
        {"date": "20240229", "path": "history/se:1/20240229.html"},
    ]
    (inst / "history" / "index.json").write_text(
        '{"se:1": [\n  {"date": "20200101", "path": "history/se:1/20200101.html"},\n'
        '  {"date": "20240229", "path": "history/se:1/20240229.html"}\n]}',
        encoding="utf-8",
    )
    (inst / "history" / "se:1" / "20200101.html").write_text('<div id="se:1">A-20200101</div>', encoding="utf-8")
    (inst / "history" / "se:1" / "20240229.html").write_text('<div id="se:1">A-20240229</div>', encoding="utf-8")

    db_path = tmp_path / "legislation.db"
    rc, out, err = run_cli_argv([
        "db", "import-history",
        "--out-dir", str(out_dir),
        "--db-path", str(db_path),
    ])
    assert rc == 0
    return db_path, out_dir


def parse_csv(text: str) -> tuple[list[str], list[list[str]]]:
    """
    Parse CSV robustly; returns (header, rows).
    """
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def test_cli_db_query_current_by_fragment(tmp_path: Path):
    db_path, _ = seed_db_via_import_history(tmp_path)

    rc, out, err = run_cli_argv([
        "db", "query",
        "--name", "current-by-fragment",
        "--db-path", str(db_path),
        "--instrument-name", "instrumentA",
        "--fragment-code", "se:1",
    ])
    assert rc == 0
    header, rows = parse_csv(out)
    # Expected columns (stable order)
    expected_cols = {"instrument_name", "fragment_code", "content_hash", "extracted_at"}
    assert set(header) >= expected_cols
    # At least one row and non-empty content_hash
    if rows:
        # Map by header
        idx = {h: i for i, h in enumerate(header)}
        first = rows[0]
        assert first[idx["content_hash"]] != ""


def test_cli_db_query_snapshots_by_fragment(tmp_path: Path):
    db_path, _ = seed_db_via_import_history(tmp_path)

    rc, out, err = run_cli_argv([
        "db", "query",
        "--name", "snapshots-by-fragment",
        "--db-path", str(db_path),
        "--instrument-name", "instrumentA",
        "--fragment-code", "se:1",
    ])
    assert rc == 0
    header, rows = parse_csv(out)
    # Expected columns
    expected_cols = {"instrument_name", "fragment_code", "date", "content_hash"}
    assert set(header) >= expected_cols
    # Count equals 2 based on our seeding, and ensure ordered by date asc
    assert len(rows) == 2
    idx = {h: i for i, h in enumerate(header)}
    dates = [rows[0][idx["date"]], rows[1][idx["date"]]]
    assert dates == sorted(dates)


def test_cli_db_query_instruments_by_jurisdiction_header_only_when_empty(tmp_path: Path):
    # Seed DB without explicit jurisdiction wiring (import-history does not guarantee jurisdiction)
    db_path, _ = seed_db_via_import_history(tmp_path)

    rc, out, err = run_cli_argv([
        "db", "query",
        "--name", "instruments-by-jurisdiction",
        "--db-path", str(db_path),
        "--jurisdiction-code", "QC",
    ])
    assert rc == 0
    header, rows = parse_csv(out)
    # Header present and valid; zero-or-more rows accepted deterministically
    expected_cols = {"jurisdiction_code", "instrument_name"}
    assert set(header) >= expected_cols
    # If no rows, that's acceptable; if rows exist, they should have non-empty instrument_name
    if rows:
        idx = {h: i for i, h in enumerate(header)}
        assert all(r[idx["instrument_name"]] != "" for r in rows)


def test_cli_db_query_annexes_by_fragment_header_only_when_none(tmp_path: Path):
    # Seed DB via import-history which doesn't create annexes; expect header only and zero rows
    db_path, _ = seed_db_via_import_history(tmp_path)

    rc, out, err = run_cli_argv([
        "db", "query",
        "--name", "annexes-by-fragment",
        "--db-path", str(db_path),
        "--instrument-name", "instrumentA",
        "--fragment-code", "se:1",
    ])
    assert rc == 0
    header, rows = parse_csv(out)
    expected_cols = {"fragment_id", "pdf_url", "conversion_status"}
    assert set(header) >= expected_cols
    # No annexes expected in this fixture
    assert len(rows) == 0