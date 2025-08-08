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


def build_minimal_legacy_db(path: Path) -> None:
    """
    Same schema/data as preview test.
    """
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.executescript(
        """
        CREATE TABLE instruments(
          id INTEGER PRIMARY KEY,
          name TEXT,
          source_url TEXT
        );
        CREATE TABLE fragments(
          id INTEGER PRIMARY KEY,
          instrument_id INT,
          section_num INT,
          title TEXT
        );
        CREATE TABLE current(
          instrument_id INT,
          fragment_id INT,
          html TEXT,
          url TEXT
        );
        CREATE TABLE snapshots(
          id INTEGER PRIMARY KEY,
          fragment_id INT,
          date TEXT,
          html TEXT,
          url TEXT
        );
        CREATE TABLE tags(
          id INTEGER PRIMARY KEY,
          name TEXT
        );
        CREATE TABLE tag_map(
          fragment_id INT,
          tag_id INT
        );
        """
    )
    # deterministic rows
    cur.execute("INSERT INTO instruments(id, name, source_url) VALUES(1, ?, ?)", ("InstrumentLegacy", "https://example.test/inst"))
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(1, 1, 1, 'One')")
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(2, 1, 2, 'Two')")
    cur.execute("INSERT INTO current(instrument_id, fragment_id, html, url) VALUES(1, 1, ?, ?)", ("<div id='se:1'>Current1</div>", "https://example.test/cur"))
    cur.execute("INSERT INTO snapshots(id, fragment_id, date, html, url) VALUES(1, 1, ?, ?, ?)", ("2021-01-02", "<div id='se:1'>Snap1</div>", "https://example.test/s1"))
    cur.execute("INSERT INTO snapshots(id, fragment_id, date, html, url) VALUES(2, 1, ?, ?, ?)", ("2021/03/04", "<div id='se:1'>Snap2</div>", "https://example.test/s2"))
    cur.execute("INSERT INTO tags(id, name) VALUES(1, 'alpha')")
    cur.execute("INSERT INTO tag_map(fragment_id, tag_id) VALUES(1, 1)")
    cur.execute("INSERT INTO tag_map(fragment_id, tag_id) VALUES(2, 1)")
    conn.commit()
    conn.close()


def parse_csv(text: str) -> tuple[list[str], list[list[str]]]:
    reader = csv.reader(io.StringIO(text))
    rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def get_idx(header: list[str]) -> dict[str, int]:
    return {h: i for i, h in enumerate(header)}


def test_cli_db_import_legacy_apply_and_idempotent(tmp_path: Path):
    legacy = tmp_path / "legacy.db"
    build_minimal_legacy_db(legacy)

    target_db = tmp_path / "target.db"

    # First apply
    rc, out, err = run_cli_argv([
        "db", "import-legacy",
        "--db-path", str(target_db),
        "--legacy-db", str(legacy),
    ])
    assert rc == 0, f"stderr: {err}"

    # Query current-by-fragment for se:1 and se:2
    rc, out_cur1, err = run_cli_argv([
        "db", "query",
        "--name", "current-by-fragment",
        "--db-path", str(target_db),
        "--instrument-name", "InstrumentLegacy",
    ])
    assert rc == 0
    header, rows = parse_csv(out_cur1)
    assert set(header) >= {"instrument_name", "fragment_code", "content_hash", "extracted_at"}
    idx = get_idx(header)
    # We expect at most 2 rows (se:1 has current from legacy; se:2 may have none)
    # Ensure se:1 exists and has non-empty content_hash; se:2 presence is allowed (depending on importer), but not required
    codes = [r[idx["fragment_code"]] for r in rows] if rows else []
    assert "se:1" in codes
    # content_hash for se:1 non-empty
    for r in rows:
        if r[idx["fragment_code"]] == "se:1":
            assert r[idx["content_hash"]] != ""

    # Query snapshots for se:1
    rc, out_snap1, err = run_cli_argv([
        "db", "query",
        "--name", "snapshots-by-fragment",
        "--db-path", str(target_db),
        "--instrument-name", "InstrumentLegacy",
        "--fragment-code", "se:1",
    ])
    assert rc == 0
    shead, srows = parse_csv(out_snap1)
    assert set(shead) >= {"instrument_name", "fragment_code", "date", "content_hash"}
    sidx = get_idx(shead)
    # Expect exactly 2 snapshots with normalized YYYYMMDD dates and ascending order
    assert len(srows) == 2
    dates = [r[sidx["date"]] for r in srows]
    assert dates == ["20210102", "20210304"]

    # Re-run apply to test idempotency
    rc, out2, err = run_cli_argv([
        "db", "import-legacy",
        "--db-path", str(target_db),
        "--legacy-db", str(legacy),
    ])
    assert rc == 0

    # Re-query snapshots for se:1 and ensure still exactly 2 rows and same order
    rc, out_snap2, err = run_cli_argv([
        "db", "query",
        "--name", "snapshots-by-fragment",
        "--db-path", str(target_db),
        "--instrument-name", "InstrumentLegacy",
        "--fragment-code", "se:1",
    ])
    assert rc == 0
    shead2, srows2 = parse_csv(out_snap2)
    assert len(srows2) == 2
    dates2 = [r[get_idx(shead2)["date"]] for r in srows2]
    assert dates2 == dates