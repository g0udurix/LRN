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


def build_out_dir_with_history(base: Path) -> tuple[Path, dict]:
    """
    Construct a minimal out_dir:
      out_dir/instrumentA/current.xhtml
      out_dir/instrumentA/history/index.json with se:1 two entries
      snapshot files for those entries
    Returns (out_dir, index_dict)
    """
    out_dir = base / "out"
    inst = out_dir / "instrumentA"
    (inst / "history" / "se:1").mkdir(parents=True, exist_ok=True)

    # current.xhtml (simple deterministic content with section se:1)
    (inst / "current.xhtml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" '
        '"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<div xmlns="http://www.w3.org/1999/xhtml"><div id="se:1"><h1>Instrument A</h1></div></div>',
        encoding="utf-8",
    )

    # snapshots + index.json
    index = {
        "se:1": [
            {"date": "20200101", "path": "history/se:1/20200101.html"},
            {"date": "20240229", "path": "history/se:1/20240229.html"},
        ]
    }
    (inst / "history" / "index.json").write_text(json.dumps(index, ensure_ascii=False, indent=2), encoding="utf-8")
    (inst / "history" / "se:1" / "20200101.html").write_text('<div id="se:1">A-20200101</div>', encoding="utf-8")
    (inst / "history" / "se:1" / "20240229.html").write_text('<div id="se:1">A-20240229</div>', encoding="utf-8")
    return out_dir, index


def test_cli_db_import_history_dry_run_and_real(tmp_path: Path):
    out_dir, index = build_out_dir_with_history(tmp_path)
    db_path = tmp_path / "legislation.db"

    # Dry-run
    rc, out, err = run_cli_argv([
        "db", "import-history",
        "--out-dir", str(out_dir),
        "--db-path", str(db_path),
        "--dry-run",
    ])
    assert rc == 0
    lines = [ln.strip() for ln in out.splitlines() if ln.strip()]
    assert lines and lines[0].startswith("DRY-RUN")
    joined = "\n".join(lines).lower()
    # Summary lines for instrument and fragment counts should be present
    assert "instrument" in joined
    assert "fragment" in joined

    # Real import
    rc, out, err = run_cli_argv([
        "db", "import-history",
        "--out-dir", str(out_dir),
        "--db-path", str(db_path),
    ])
    assert rc == 0

    # Assertions directly against DB
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        cur = conn.cursor()

        # instruments has instrumentA
        cur.execute("SELECT id FROM instruments WHERE name=?", ("instrumentA",))
        row_inst = cur.fetchone()
        assert row_inst is not None
        instrument_id = int(row_inst["id"])

        # fragments has se:1 for instrumentA
        cur.execute("SELECT id FROM fragments WHERE instrument_id=? AND code=?", (instrument_id, "se:1"))
        row_frag = cur.fetchone()
        assert row_frag is not None
        fragment_id = int(row_frag["id"])

        # current_pages exists for that fragment
        cur.execute("SELECT id, content_hash FROM current_pages WHERE fragment_id=?", (fragment_id,))
        row_cur = cur.fetchone()
        assert row_cur is not None
        assert (row_cur["content_hash"] or "") != ""

        # snapshots count equals index.json entries
        expected_snaps = len(index["se:1"])
        cur.execute("SELECT COUNT(*) AS c FROM snapshots WHERE fragment_id=?", (fragment_id,))
        snap_count = int(cur.fetchone()["c"])
        assert snap_count == expected_snaps

        # fragment_links with link_type='version' count matches snapshots
        cur.execute("SELECT COUNT(*) AS c FROM fragment_links WHERE from_fragment_id=? AND link_type='version'", (fragment_id,))
        link_count = int(cur.fetchone()["c"])
        assert link_count == expected_snaps
    finally:
        conn.close()