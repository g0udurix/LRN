import io
import sys
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


def test_cli_db_import_legacy_missing_path_exits_nonzero(tmp_path: Path):
    # Point to a non-existent legacy DB file
    missing_legacy = tmp_path / "does_not_exist.sqlite"
    target_db = tmp_path / "db.sqlite"

    rc, out, err = run_cli_argv([
        "db", "import-legacy",
        "--db-path", str(target_db),
        "--legacy-db", str(missing_legacy),
        "--preview",
    ])
    # The command should not crash; it should emit a concise warning and succeed overall or fail with nonzero.
    # Project guidelines: "verify a concise error message is printed and the command exits with nonzero status".
    # Enforce nonzero rc.
    assert rc != 0

    # A concise message should be printed to stderr; accept [WARN] or [ERROR] prefix per implementation.
    combined = (out + "\n" + err).strip()
    assert ("WARN" in combined or "ERROR" in combined) or ("failed" in combined.lower()), f"missing concise error message: {combined!r}"