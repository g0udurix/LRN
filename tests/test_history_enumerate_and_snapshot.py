from pathlib import Path
import json, os
from lrn.history import HistoryCrawler

def test_enumerate_versions_parsing_from_fixture(tmp_path: Path, monkeypatch):
    # Fixture page with multiple anchors carrying YYYYMMDD
    fixture = tmp_path / "version_list.html"
    fixture.write_text("""
    <html><body>
      <a href="/fr/version/rc/S-2.1?code=se:1#20200101">2020-01-01</a>
      <a href="/fr/version/rc/S-2.1?code=se:1#20240229">2024-02-29</a>
      <a href="/fr/version/rc/S-2.1?code=se:1&historique=20250804#20250804">2025-08-04</a>
    </body></html>
    """, encoding="utf-8")

    def fake_fetch(self, url: str) -> str:
        return fixture.read_text(encoding="utf-8")

    monkeypatch.setattr(HistoryCrawler, "fetch", fake_fetch)

    hc = HistoryCrawler(base_url="", out_dir=str(tmp_path), cache_dir=None, max_dates=None)
    items = hc.enumerate_versions("/whatever")
    dates = [i["date"] for i in items]
    assert {"20200101", "20240229", "20250804"}.issubset(set(dates))

def test_snapshot_and_index_content(tmp_path: Path, monkeypatch):
    # Fake snapshot content that reflects date for assertion clarity
    def fake_fetch(self, url: str) -> str:
        import re
        m = re.search(r'#(\d{8})', url)
        d = m.group(1) if m else "na"
        return f"<html><body>Snapshot {d}</body></html>"

    monkeypatch.setattr(HistoryCrawler, "fetch", fake_fetch)

    hc = HistoryCrawler(base_url="", out_dir=str(tmp_path), cache_dir=None, max_dates=None)
    inst_dir = tmp_path / "instrument"
    frag_code = "se:1"

    p1 = hc.snapshot(str(inst_dir), frag_code, "20200101", "/u#20200101")
    p2 = hc.snapshot(str(inst_dir), frag_code, "20240229", "/u#20240229")
    assert p1 and p2
    assert Path(p1).exists() and Path(p2).exists()

    entries = {frag_code: [
        {"date": "20200101", "path": str(Path(p1).relative_to(inst_dir)).replace(os.sep, "/")},
        {"date": "20240229", "path": str(Path(p2).relative_to(inst_dir)).replace(os.sep, "/")},
    ]}
    hc.build_index(str(inst_dir), entries)

    idx_path = inst_dir / "history" / "index.json"
    assert idx_path.exists()
    data = json.loads(idx_path.read_text(encoding="utf-8"))
    assert frag_code in data
    assert any(it["date"] == "20200101" for it in data[frag_code])
    assert any(it["path"].endswith("/20240229.html") for it in data[frag_code])