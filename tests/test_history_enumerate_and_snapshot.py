from pathlib import Path

from lrn.history import HistoryCrawler, HistoryOptions, HistorySnapshot, HistoryStatus

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

    monkeypatch.setattr(HistoryCrawler, "_cached_fetch", fake_fetch)

    hc = HistoryCrawler(tmp_path, HistoryOptions(base_url=""))
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

    monkeypatch.setattr(HistoryCrawler, "_cached_fetch", fake_fetch)

    hc = HistoryCrawler(tmp_path, HistoryOptions(base_url=""))
    fragment_html = """
    <?xml version=\"1.0\" encoding=\"UTF-8\"?>
    <!DOCTYPE div PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">
    <div xmlns=\"http://www.w3.org/1999/xhtml\">
      <div id=\"se:1\"><img src=\"history.png\"/></div>
    </div>
    """

    monkeypatch.setattr(hc, "discover_fragment_links", lambda _: ["/u#20200101", "/u#20240229"])
    monkeypatch.setattr(hc, "enumerate_versions", lambda link: [{"date": link.split('#')[-1], "href": link}])
    monkeypatch.setattr(hc, "snapshot", lambda code, date, href: HistorySnapshot(code, date, href, tmp_path / f"{date}.html", HistoryStatus.SNAPSHOT))

    result = hc.crawl(fragment_html)
    assert result.index
