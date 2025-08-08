from pathlib import Path
import hashlib
import json
import sqlite3

from lrn.cli import extract

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

def _sha256_hex_text(text: str) -> str:
    h = hashlib.sha256()
    h.update(text.encode("utf-8"))
    return h.hexdigest()

SAMPLE_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<div xmlns="http://www.w3.org/1999/xhtml">
  <div class="section" id="se:1">
    <p>Body</p>
    <div class="HistoryLink"><a href="/fr/version/rc/S-2.1?code=se:1&historique=20250804#20250804"><img src="/img/history.png"/></a></div>
  </div>
</div>
"""

def test_content_hash_integrity_for_current_and_snapshot(tmp_path: Path, monkeypatch):
    # Arrange deterministic offline history similar to other tests
    version_page = """
    <html><body>
      <a href="/fr/version/rc/S-2.1?code=se:1#20200101">2020-01-01</a>
      <a href="/fr/version/rc/S-2.1?code=se:1#20240229">2024-02-29</a>
    </body></html>
    """
    snapshots = {
        "#20200101": '<html><body><div id="se:1">Snap 20200101</div></body></html>',
        "#20240229": '<html><body><div id="se:1">Snap 20240229</div></body></html>',
    }
    from lrn.history import HistoryCrawler
    def fake_fetch(self, url: str) -> str:
        if "#20200101" in url:
            return snapshots["#20200101"]
        if "#20240229" in url:
            return snapshots["#20240229"]
        return version_page
    monkeypatch.setattr(HistoryCrawler, "fetch", fake_fetch)

    # Build outer file that contains our XHTML fragment
    outer = f"<html><body>\n{SAMPLE_XHTML}\n</body></html>"
    src = tmp_path / "law.html"
    src.write_text(outer, encoding="utf-8")

    out_dir = tmp_path / "out"
    db_path = out_dir / "legislation.db"

    # Act
    extract(
        history_sidecars=True,
        history_markdown=False,
        annex_pdf_to_md=False,
        metadata_exclusion="",
        out_dir=str(out_dir),
        inputs=[str(src)],
        base_url="https://example.test",
        pdf_to_md_engine="marker",
        ocr=False,
        history_max_dates=None,
        history_cache_dir=None,
        history_timeout=5,
        history_user_agent="pytest-agent",
        db_path=str(db_path),
    )

    # Compute on-disk current.xhtml hash
    instrument_dir = out_dir / "law"
    current_path = instrument_dir / "current.xhtml"
    assert current_path.exists()
    current_text = current_path.read_text(encoding="utf-8")
    current_sha = _sha256_hex_text(current_text)

    # Open DB and compare current_pages.content_hash
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM instruments WHERE name = ?", ("law",))
        inst = cur.fetchone()
        assert inst is not None
        inst_id = int(inst["id"])
        cur.execute("SELECT id FROM fragments WHERE instrument_id=? AND code=?", (inst_id, "se:1"))
        frag = cur.fetchone()
        assert frag is not None
        frag_id = int(frag["id"])
        cur.execute("SELECT content_hash FROM current_pages WHERE fragment_id=?", (frag_id,))
        row = cur.fetchone()
        assert row is not None, "current_pages row should exist for fragment"
        assert row["content_hash"] == current_sha

        # For at least one snapshot: compare DB snapshots.content_hash to on-disk snapshot file hash
        index_path = instrument_dir / "history" / "index.json"
        assert index_path.exists()
        index = json.loads(index_path.read_text(encoding="utf-8") or "{}")
        entries = index.get("se:1") or []
        assert len(entries) >= 1
        # Pick the first entry deterministically
        first = entries[0]
        snap_rel = first["path"]
        snap_date = first["date"]
        snap_abs = instrument_dir / snap_rel
        assert snap_abs.exists()
        snap_html = snap_abs.read_text(encoding="utf-8")
        snap_sha = _sha256_hex_text(snap_html)

        # DB side snapshot hash
        cur.execute("SELECT content_hash FROM snapshots WHERE fragment_id=? AND date=?", (frag_id, snap_date))
        srow = cur.fetchone()
        assert srow is not None, "snapshot row should exist"
        assert srow["content_hash"] == snap_sha
    finally:
        conn.close()