import os
from pathlib import Path
from lrn.cli import extract

SAMPLE_XHTML = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<div xmlns="http://www.w3.org/1999/xhtml">
  <div class="section" id="se:1">
    <p>Body</p>
    <div class="HistoryLink"><a href="/fr/version/rc/S-2.1?code=se:1&historique=20250804#20250804"><img src="/img/history.png"/></a></div>
  </div>
</div>
"""

def test_cli_history_end_to_end_no_network(tmp_path: Path, monkeypatch):
    # Fake enumerate page and snapshots without network
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
    def fake_fetch(self, url: str) -> str:
        # Return version_page for enumerate_versions, snapshots for specific anchors
        if "#20200101" in url:
            return snapshots["#20200101"]
        if "#20240229" in url:
            return snapshots["#20240229"]
        return version_page
    from lrn.history import HistoryCrawler
    monkeypatch.setattr(HistoryCrawler, "_cached_fetch", fake_fetch)

    # Build minimal outer HTML that contains the inner fragment
    outer = f"""<html><body>
{SAMPLE_XHTML}
</body></html>"""
    src = tmp_path / "law.html"
    src.write_text(outer, encoding="utf-8")

    out_dir = tmp_path / "out"
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
        history_user_agent="pytest-agent"
    )
    # Verify outputs
    # Instrument directory is derived from filename stem
    instrument = out_dir / "law"
    current = instrument / "current.xhtml"
    assert current.exists()
    html = current.read_text(encoding="utf-8")
    # Versions injected
    assert "LRN-Versions" in html
    assert 'history/se:1/20200101.html' in html
    # Index exists
    index = instrument / "history" / "index.json"
    assert index.exists()
