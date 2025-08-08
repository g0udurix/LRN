import io
import sys
import json
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


def build_out_dir_with_history(base: Path) -> Path:
    out_dir = base / "outA"
    inst = out_dir / "instrumentA"
    (inst / "history" / "se:1").mkdir(parents=True, exist_ok=True)

    # current.xhtml deterministic
    (inst / "current.xhtml").write_text(
        '<?xml version="1.0" encoding="UTF-8?>\n'
        '<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<div xmlns="http://www.w3.org/1999/xhtml"><div id="se:1"><h1>Instrument A</h1></div></div>',
        encoding="utf-8",
    )

    index = {
        "se:1": [
            {"date": "20200101", "path": "history/se:1/20200101.html"},
            {"date": "20240229", "path": "history/se:1/20240229.html"},
        ]
    }
    (inst / "history" / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (inst / "history" / "se:1" / "20200101.html").write_text('<div id="se:1">A-20200101</div>', encoding="utf-8")
    (inst / "history" / "se:1" / "20240229.html").write_text('<div id="se:1">A-20240229</div>', encoding="utf-8")
    return out_dir


def build_minimal_legacy_db(path: Path) -> None:
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
    cur.execute("INSERT INTO instruments(id, name, source_url) VALUES(1, 'InstrumentLegacy', NULL)")
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(1, 1, 1, 'One')")
    cur.execute("INSERT INTO fragments(id, instrument_id, section_num, title) VALUES(2, 1, 2, 'Two')")
    cur.execute("INSERT INTO current(instrument_id, fragment_id, html, url) VALUES(1, 1, '<div id=\"se:1\">Current1</div>', NULL)")
    cur.execute("INSERT INTO snapshots(id, fragment_id, date, html, url) VALUES(1, 1, '2021-01-02', '<div id=\"se:1\">Snap1</div>', NULL)")
    cur.execute("INSERT INTO snapshots(id, fragment_id, date, html, url) VALUES(2, 1, '2021/03/04', '<div id=\"se:1\">Snap2</div>', NULL)")
    cur.execute("INSERT INTO tags(id, name) VALUES(1, 'alpha')")
    cur.execute("INSERT INTO tag_map(fragment_id, tag_id) VALUES(1, 1)")
    cur.execute("INSERT INTO tag_map(fragment_id, tag_id) VALUES(2, 1)")
    conn.commit()
    conn.close()


def test_cli_db_import_legacy_preview_with_outdir_reuses_summary(tmp_path: Path):
    out_dir = build_out_dir_with_history(tmp_path)
    legacy = tmp_path / "legacy.db"
    build_minimal_legacy_db(legacy)
    target_db = tmp_path / "db.sqlite"

    rc, out, err = run_cli_argv([
        "db", "import-legacy",
        "--db-path", str(target_db),
        "--out-dir", str(out_dir),
        "--legacy-db", str(legacy),
        "--preview",
    ])
    assert rc == 0, f"stderr: {err}"

    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    # Expect at least one DRY-RUN line from import-history preview
    dry_lines = [ln for ln in lines if ln.startswith("DRY-RUN out-dir=")]
    assert len(dry_lines) >= 1, f"missing DRY-RUN summary, got: {out!r}"
    # Expect exactly one PREVIEW line for legacy
    preview_lines = [ln for ln in lines if ln.startswith("PREVIEW legacy-db=")]
    assert len(preview_lines) == 1, f"missing legacy PREVIEW, got: {out!r}"
    pl = preview_lines[0]
    assert "instruments=1" in pl and "fragments=2" in pl and "current=1" in pl and "snapshots=2" in pl