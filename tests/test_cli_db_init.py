import os
import re
import sqlite3
from pathlib import Path
import io
import sys

# Prefer black-box invocation via lrn.cli.main() with argv emulation
import lrn.cli as cli


def run_cli_argv(argv: list[str]) -> tuple[int, str, str]:
    """
    Invoke lrn.cli.main() as a black-box by simulating sys.argv and capturing stdio.
    Returns (exit_code, stdout, stderr).
    """
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


def test_cli_db_init_echo_version_and_pragmas(tmp_path: Path):
    db_path = tmp_path / "legislation.db"

    # Act: lrn db init --db-path & --echo-version
    rc, out, err = run_cli_argv(["db", "init", "--db-path", str(db_path), "--echo-version"])

    # Assert: exit code 0 and echoed version integer >= 3
    assert rc == 0
    # Output may include logging lines; find the last integer on stdout or any integer line
    ints = [int(m.group(0)) for m in re.finditer(r"\b\d+\b", out)]
    assert ints, f"no integer found in stdout: {out!r}, stderr: {err!r}"
    echoed = ints[-1]
    assert isinstance(echoed, int) and echoed >= 3

    # Open the DB and verify PRAGMAs
    conn = sqlite3.connect(str(db_path))
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA user_version;")
        version = int(cur.fetchone()[0])
        assert version >= 3

        cur.execute("PRAGMA foreign_keys;")
        fk = int(cur.fetchone()[0])
        assert fk == 1
    finally:
        conn.close()