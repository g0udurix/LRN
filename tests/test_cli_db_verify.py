import os
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


def seed_minimal_out_dir(out_dir: Path):
    """
    Build a small offline fixture with one instrument and deterministic history.
    """
    inst = out_dir / "instrumentA"
    (inst / "history").mkdir(parents=True, exist_ok=True)
    # current.xhtml
    (inst / "current.xhtml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
        '<div xmlns="http://www.w3.org/1999/xhtml"><div id="se:1"><h1>Instrument A</h1></div></div>',
        encoding="utf-8",
    )
    # snapshots for se:1
    hist = {
        "se:1": [
            {"date": "20200101", "path": "history/se:1/20200101.html"},
            {"date": "20240229", "path": "history/se:1/20240229.html"},
        ]
    }
    (inst / "history" / "se:1").mkdir(parents=True, exist_ok=True)
    (inst / "history" / "se:1" / "20200101.html").write_text('<div id="se:1">v1</div>', encoding="utf-8")
    (inst / "history" / "se:1" / "20240229.html").write_text('<div id="se:1">v2</div>', encoding="utf-8")
    (inst / "history" / "index.json").write_text(json.dumps(hist, ensure_ascii=False, indent=2), encoding="utf-8")


def test_cli_db_verify_basic_and_parity(tmp_path: Path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    seed_minimal_out_dir(out_dir)

    db_path = tmp_path / "legislation.db"

    # Import into DB to seed content
    rc, out, err = run_cli_argv([
        "db", "import-history",
        "--out-dir", str(out_dir),
        "--db-path", str(db_path),
        "--dry-run"
    ])
    assert rc == 0
    assert out.strip().startswith("DRY-RUN")

    rc, out, err = run_cli_argv([
        "db", "import-history",
        "--out-dir", str(out_dir),
        "--db-path", str(db_path),
    ])
    assert rc == 0

    # Verify without parity out_dir
    rc, out, err = run_cli_argv([
        "db", "verify",
        "--db-path", str(db_path),
    ])
    assert rc == 0
    lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
    assert lines, f"no output: stdout={out!r} stderr={err!r}"
    assert lines[0] == "OK"
    # Expect presence of version/pragma/counts/referential checks lines somewhere
    joined = "\n".join(lines)
    assert "version" in joined.lower() or "user_version" in joined.lower()
    assert "pragma" in joined.lower() or "foreign_keys" in joined.lower()
    assert "count" in joined.lower() or "counts" in joined.lower() or "snapshots" in joined.lower()
    assert "referential" in joined.lower() or "foreign" in joined.lower() or "links" in joined.lower()

    # Verify with parity out_dir
    rc, out, err = run_cli_argv([
        "db", "verify",
        "--db-path", str(db_path),
        "--out-dir", str(out_dir),
    ])
    assert rc == 0
    lines = [ln.strip() for ln in out.strip().splitlines() if ln.strip()]
    assert lines and lines[0] == "OK"
    joined = "\n".join(lines)
    assert "parity" in joined.lower() or "out_dir" in joined.lower() or "history" in joined.lower()


def test_cli_db_verify_strict_mismatch(tmp_path: Path):
    out_dir = tmp_path / "out"
    out_dir.mkdir()
    seed_minimal_out_dir(out_dir)

    db_path = tmp_path / "legislation.db"

    # Import to make DB consistent first
    rc, out, err = run_cli_argv([
        "db", "import-history",
        "--out-dir", str(out_dir),
        "--db-path", str(db_path),
    ])
    assert rc == 0

    # Create a deterministic mismatch: add an extra snapshot file not recorded in index.json
    extra_dir = out_dir / "instrumentA" / "history" / "se:1"
    (extra_dir / "20210102.html").write_text('<div id="se:1">extra</div>', encoding="utf-8")

    # Strict verify should fail (exit code 2, first line FAIL)
    rc, out, err = run_cli_argv([
        "db", "verify",
        "--db-path", str(db_path),
        "--out-dir", str(out_dir),
        "--strict",
    ])
    assert rc == 2
    first = (out.strip().splitlines() or [""])[0].strip()
    assert first == "FAIL"