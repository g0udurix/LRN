from pathlib import Path
import json
import sqlite3

from lrn.cli import extract

def _connect(db_path: Path) -> sqlite3.Connection:
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    return conn

SAMPLE_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<div xmlns="http://www.w3.org/1999/xhtml">
  <div class="section" id="se:1">
    <p>Body</p>
    <div class="HistoryLink"><a href="/fr/version/rc/S-2.1?code=se:1&historique=20250804#20250804"><img src="/img/history.png"/></a></div>
  </div>
</div>
"""

def test_snapshot_link_parity(tmp_path: Path, monkeypatch):
    # Arrange fake enumerate and snapshots (reuse approach from test_cli_history_integration)
    version_page = """
    <html><body>
      <a href="/fr/version/rc/S-2.1?code=se:1#20200101">2020-01-01</a>
      <a href="/fr/version/rc/S-2.1?code=se:1#20240229">2024-02-29</a>
    </body></html>
    """
    snapshots = {
        "#20200101": "<html><body>Snap 20200101</body></html>",
        "#20240229": "<html><body>Snap 20240229</body></html>",
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

    # Count snapshots in index.json for fragment se:1
    instrument_dir = out_dir / "law"
    index_path = instrument_dir / "history" / "index.json"
    assert index_path.exists()
    data = json.loads(index_path.read_text(encoding="utf-8") or "{}")
    entries = data.get("se:1") or []
    expected_count = len(entries)

    # Count DB fragment_links of type "version" for the fragment "se:1"
    conn = _connect(db_path)
    try:
        cur = conn.cursor()
        # instrument name is deterministically the stem 'law'
        cur.execute("SELECT id FROM instruments WHERE name = ?", ("law",))
        inst = cur.fetchone()
        assert inst is not None
        inst_id = int(inst["id"])
        cur.execute("SELECT id FROM fragments WHERE instrument_id=? AND code=?", (inst_id, "se:1"))
        frag = cur.fetchone()
        assert frag is not None
        frag_id = int(frag["id"])
        cur.execute("SELECT COUNT(*) AS c FROM fragment_links WHERE from_fragment_id=? AND link_type='version'", (frag_id,))
        got = int(cur.fetchone()["c"])
    finally:
        conn.close()

    # Assert parity
    assert got == expected_count