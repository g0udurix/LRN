from pathlib import Path
import json

from lrn.history import HistoryOptions, HistorySnapshot, HistoryStatus, build_history_sidecars


def test_build_history_sidecars_creates_placeholder(tmp_path: Path):
    fragment_html = """
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <div class=\"section\" id=\"se:1\">Body</div>
    </div>
    """
    inst_dir = tmp_path / "instrument"
    result = build_history_sidecars(
        fragment_html,
        instrument_dir=inst_dir,
        options=HistoryOptions(base_url=""),
    )

    assert "LRN-Versions" in result.html
    index_path = inst_dir / "history" / "index.json"
    assert index_path.exists()
    data = json.loads(index_path.read_text(encoding="utf-8"))
    assert data == {}


def test_build_history_sidecars_respects_limits(tmp_path: Path, monkeypatch):
    fragment_html = """
    <?xml version="1.0" encoding="UTF-8"?>
    <!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
    <div xmlns="http://www.w3.org/1999/xhtml">
      <div class=\"section\" id=\"se:1\"><img src=\"history.png\"/></div>
    </div>
    """

    from lrn.history import HistoryCrawler

    inst_dir = tmp_path / "instrument"
    monkeypatch.setattr(HistoryCrawler, "discover_fragment_links", lambda self, html: ["/u#20200101", "/u#20240229"])
    monkeypatch.setattr(HistoryCrawler, "enumerate_versions", lambda self, link: [{"date": link.split('#')[-1], "href": link}])
    def fake_snapshot(self, code, date, href):
        path = inst_dir / "history" / code / f"{date}.html"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("snapshot", encoding="utf-8")
        return HistorySnapshot(code, date, href, path, HistoryStatus.SNAPSHOT)

    monkeypatch.setattr(HistoryCrawler, "snapshot", fake_snapshot)
    result = build_history_sidecars(
        fragment_html,
        instrument_dir=inst_dir,
        options=HistoryOptions(base_url="", max_dates=1),
    )

    for snapshots in result.index.values():
        assert len(snapshots) == 1
