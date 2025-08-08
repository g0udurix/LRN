import io
import sys
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


def build_legacy_without_jurisdiction(path: Path) -> None:
    """
    Legacy DB with instrument missing jurisdiction info; importer should apply --jurisdiction-default.
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
        """
    )
    cur.execute("INSERT INTO instruments(id, name, source_url) VALUES(1, 'NoJurisInstrument', NULL)")
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(1, 1, 1, 'One')")
    cur.execute("INSERT INTO current(instrument_id, fragment_id, html, url) VALUES(1, 1, '<div id=\"se:1\">C</div>', NULL)")
    conn.commit()
    conn.close()


def parse_csv(text: str) -> tuple[list[str], list[list[str]]]:
    import csv, io as _io
    reader = csv.reader(_io.StringIO(text))
    rows = list(reader)
    if not rows:
        return [], []
    return rows[0], rows[1:]


def test_cli_db_import_legacy_jurisdiction_default_qc(tmp_path: Path):
    legacy = tmp_path / "legacy.db"
    build_legacy_without_jurisdiction(legacy)
    target_db = tmp_path / "target.db"

    # Apply with jurisdiction default QC
    rc, out, err = run_cli_argv([
        "db", "import-legacy",
        "--db-path", str(target_db),
        "--legacy-db", str(legacy),
        "--jurisdiction-default", "QC",
    ])
    assert rc == 0, f"stderr: {err}"

    # Query instruments-by-jurisdiction code QC
    rc, out2, err2 = run_cli_argv([
        "db", "query",
        "--name", "instruments-by-jurisdiction",
        "--db-path", str(target_db),
        "--jurisdiction-code", "QC",
    ])
    assert rc == 0, f"stderr: {err2}"
    header, rows = parse_csv(out2)
    assert set(header) >= {"jurisdiction_code", "instrument_name"}
    # Ensure the imported instrument is listed under QC
    found = any(r[header.index("instrument_name")] == "NoJurisInstrument" for r in rows)
    assert found, f"expected instrument in QC listing; got: {out2!r}"