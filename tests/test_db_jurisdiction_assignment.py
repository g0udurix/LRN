import os
import sqlite3
from pathlib import Path
import json
import hashlib
import pytest

from lrn.cli import extract

# Helpers
def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def _write_outer_with_inner(tmp_path: Path, inner: str) -> Path:
    outer = f"<html><body>\n{inner}\n</body></html>"
    # Use real angle brackets
    outer = outer.replace("<", "<").replace(">", ">")
    src = tmp_path / "law.html"
    src.write_text(outer, encoding="utf-8")
    return src

def test_jurisdiction_assignment_for_legisquebec(tmp_path: Path):
    # Arrange: minimal XHTML with a section id that our pipeline supports
    inner = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<div xmlns="http://www.w3.org/1999/xhtml">
  <div class="section" id="se:1">
    <p>Body</p>
    <div class="HistoryLink"><a href="/fr/version/rc/S-2.1?code=se:1&historique=20250804#20250804"><img src="/img/history.png"/></a></div>
  </div>
</div>
"""
    src = _write_outer_with_inner(tmp_path, inner)
    out_dir = tmp_path / "out"
    db_path = out_dir / "legislation.db"

    # Act: run extract with a LegisQuébec-like base_url to trigger jurisdiction wiring
    extract(
        history_sidecars=True,
        history_markdown=False,
        annex_pdf_to_md=False,
        metadata_exclusion="",
        out_dir=str(out_dir),
        inputs=[str(src)],
        base_url="https://www.legisquebec.gouv.qc.ca",  # LegisQuébec host
        pdf_to_md_engine="marker",
        ocr=False,
        history_max_dates=None,
        history_cache_dir=None,
        history_timeout=5,
        history_user_agent="pytest-agent",
        db_path=str(db_path),
    )

    # Assert DB state
    assert db_path.exists(), "DB should be created by extract()"

    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        # Find instrument created for file 'law.html' (instrument name is stem 'law')
        cur.execute("SELECT id, name, jurisdiction_id FROM instruments WHERE name = ?", ("law",))
        row = cur.fetchone()
        assert row is not None, "Instrument row must exist"
        inst_id = row["id"]
        assert row["jurisdiction_id"] is not None, "Instrument must be associated to a jurisdiction"

        # Check jurisdiction details are QC / Québec / province
        cur.execute(
            """
            SELECT j.code, j.name, j.level
            FROM instruments i
            JOIN jurisdictions j ON j.id = i.jurisdiction_id
            WHERE i.id = ?
            """,
            (inst_id,),
        )
        jrow = cur.fetchone()
        assert jrow is not None, "Jurisdiction join should return one row"
        assert jrow["code"] == "QC"
        assert jrow["name"] == "Québec"
        assert jrow["level"] == "province"
    finally:
        conn.close()