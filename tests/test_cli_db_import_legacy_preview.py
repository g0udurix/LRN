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


def build_minimal_legacy_db(path: Path) -> None:
    """
    Schema subset:
      instruments(id INTEGER PRIMARY KEY, name TEXT, source_url TEXT)
      fragments(id INTEGER PRIMARY KEY, instrument_id INT, section_num INT, title TEXT)
      current(instrument_id INT, fragment_id INT, html TEXT)
      snapshots(fragment_id INT, date TEXT, html TEXT)
      tags(id INTEGER PRIMARY KEY, name TEXT)
      tag_map(fragment_id INT, tag_id INT)
      links (optional dangling)
    Data:
      - 1 instrument
      - 2 fragments (section_num 1 and 2)
      - current for fragment 1
      - 2 snapshots for fragment 1 with dates 2021-01-02 and 2021/03/04
      - 1 tag applied to both fragments
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
        -- optional dangling links table
        CREATE TABLE links(
          fragment_id INT,
          to_fragment_id INT,
          kind TEXT
        );
        """
    )
    # insert deterministic rows
    cur.execute("INSERT INTO instruments(id, name, source_url) VALUES(1, ?, ?)", ("InstrumentLegacy", "https://example.test/inst"))
    # fragments 1 and 2
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(1, 1, 1, 'One')")
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(2, 1, 2, 'Two')")
    # current for fragment 1
    cur.execute("INSERT INTO current(instrument_id, fragment_id, html, url) VALUES(1, 1, ?, ?)", ("<div id='se:1'>Current1</div>", "https://example.test/cur"))
    # snapshots for fragment 1
    cur.execute("INSERT INTO snapshots(id, fragment_id, date, html, url) VALUES(1, 1, ?, ?, ?)", ("2021-01-02", "<div id='se:1'>Snap1</div>", "https://example.test/s1"))
    cur.execute("INSERT INTO snapshots(id, fragment_id, date, html, url) VALUES(2, 1, ?, ?, ?)", ("2021/03/04", "<div id='se:1'>Snap2</div>", "https://example.test/s2"))
    # tag and map to both fragments
    cur.execute("INSERT INTO tags(id, name) VALUES(1, 'alpha')")
    cur.execute("INSERT INTO tag_map(fragment_id, tag_id) VALUES(1, 1)")
    cur.execute("INSERT INTO tag_map(fragment_id, tag_id) VALUES(2, 1)")
    conn.commit()
    conn.close()


def test_cli_db_import_legacy_preview_counts(tmp_path: Path):
    legacy = tmp_path / "legacy.db"
    build_minimal_legacy_db(legacy)

    target_db = tmp_path / "new.db"  # preview mode should not write, but a db-path is still supplied
    rc, out, err = run_cli_argv([
        "db", "import-legacy",
        "--db-path", str(target_db),
        "--legacy-db", str(legacy),
        "--preview",
    ])
    assert rc == 0, f"stderr: {err}"

    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # Exactly one PREVIEW line
    preview_lines = [ln for ln in lines if ln.startswith("PREVIEW legacy-db=")]
    assert len(preview_lines) == 1, f"unexpected stdout: {out}"
    line = preview_lines[0]
    # Deterministic counts (tags reflect tag assignments per fragment)
    assert "instruments=1" in line
    assert "fragments=2" in line
    assert "current=1" in line
    assert "snapshots=2" in line
    # tags=2 as tag applied to both fragments; links=0 not counted from optional dangling table
    # The CLI may not include tags/links in preview line unless present; tolerate absence by using contains check.
    # If the implementation includes them, ensure they match:
    if "tags=" in line:
        assert "tags=2" in line
    if "links=" in line:
        assert "links=0" in line
    # Do not assert the absolute path beyond the prefix to avoid temp dir noise
    assert line.startswith("PREVIEW legacy-db=")