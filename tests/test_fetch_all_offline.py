import os, json
from pathlib import Path
from unittest.mock import patch
from lrn.cli import discover_bylaws

# Offline fixtures (minimal HTML) to simulate FR/EN discovery, rc pages, versions, and snapshots
FIXTURES = {
    # Landings
    "https://www.legisquebec.gouv.qc.ca/fr/document/lc/S-2.1": """
    <html><body>
      <a href="/fr/document/rc/S-2.1, r. 8.2 ">Bylaw FR 8.2</a>
      <a href="/fr/document/rc/S-2.1, r. 22 ">Bylaw FR 22</a>
    </body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/en/document/cs/S-2.1": """
    <html><body>
      <a href="/en/document/rc/S-2.1, r. 10 ">Bylaw EN 10</a>
    </body></html>
    """,
    # RC pages (mirrors)
    "https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%208.2": """
    <html><body><div id="mainContent-document">
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
      <div xmlns="http://www.w3.org/1999/xhtml">
        <div id="se:1"><div class="HistoryLink"><a href="/fr/version/rc/S-2.1,%20r.%208.2?code=se:1&historique=20240101#20240101"><img src="/img/history.png"/></a></div></div>
      </div>
    </div></body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%2022": """
    <html><body><div id="mainContent-document">
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
      <div xmlns="http://www.w3.org/1999/xhtml">
        <div id="se:2"><div class="HistoryLink"><a href="/fr/version/rc/S-2.1,%20r.%2022?code=se:2&historique=20240102#20240102"><img src="/img/history.png"/></a></div></div>
      </div>
    </div></body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/en/document/rc/S-2.1,%20r.%2010": """
    <html><body><div id="mainContent-document">
      <?xml version="1.0" encoding="UTF-8"?>
      <!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
      <div xmlns="http://www.w3.org/1999/xhtml">
        <div id="se:3"><div class="HistoryLink"><a href="/en/version/rc/S-2.1,%20r.%2010?code=se:3&historique=20240103#20240103"><img src="/img/history.png"/></a></div></div>
      </div>
    </div></body></html>
    """,
    # Version pages for enumerate_versions
    "https://www.legisquebec.gouv.qc.ca/fr/version/rc/S-2.1,%20r.%208.2?code=se:1&historique=20240101#20240101": """
    <html><body>
      <a href="/fr/version/rc/S-2.1,%20r.%208.2?code=se:1&historique=20240101#20240101">20240101</a>
    </body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/fr/version/rc/S-2.1,%20r.%2022?code=se:2&historique=20240102#20240102": """
    <html><body>
      <a href="/fr/version/rc/S-2.1,%20r.%2022?code=se:2&historique=20240102#20240102">20240102</a>
    </body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/en/version/rc/S-2.1,%20r.%2010?code=se:3&historique=20240103#20240103": """
    <html><body>
      <a href="/en/version/rc/S-2.1,%20r.%2010?code=se:3&historique=20240103#20240103">20240103</a>
    </body></html>
    """,
    # Snapshot HTML (section-only target present)
    "https://www.legisquebec.gouv.qc.ca/fr/version/rc/S-2.1,%20r.%208.2?code=se:1&historique=20240101#20240101": """
    <html><body><div id="se:1">HIST FR 8.2 se:1 @20240101</div></body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/fr/version/rc/S-2.1,%20r.%2022?code=se:2&historique=20240102#20240102": """
    <html><body><div id="se:2">HIST FR 22 se:2 @20240102</div></body></html>
    """,
    "https://www.legisquebec.gouv.qc.ca/en/version/rc/S-2.1,%20r.%2010?code=se:3&historique=20240103#20240103": """
    <html><body><div id="se:3">HIST EN 10 se:3 @20240103</div></body></html>
    """,
}

class DummyResp:
    def __init__(self, url: str, text: str, code: int = 200):
        self.url = url
        self.text = text
        self.status_code = code
        self.content = text.encode("utf-8")
    def raise_for_status(self):
        if self.status_code != 200:
            raise RuntimeError(f"HTTP {self.status_code}")

def _mock_get(url, *args, **kwargs):
    key = url.strip()
    if key in FIXTURES:
        return DummyResp(key, FIXTURES[key], 200)
    # Try with spaces normalized to %20
    key2 = key.replace(" ", "%20")
    if key2 in FIXTURES:
        return DummyResp(key, FIXTURES[key2], 200)
    # Minimal OK fallback
    return DummyResp(key, "<html><body>OK</body></html>", 200)

def test_fetch_all_offline(tmp_path, monkeypatch):
    # Run in tmp workspace
    os.chdir(tmp_path)
    cache_root = "Legisquebec originals"
    out_dir = "output"
    fr_landing = "https://www.legisquebec.gouv.qc.ca/fr/document/lc/S-2.1"
    en_landing = "https://www.legisquebec.gouv.qc.ca/en/document/cs/S-2.1"

    # Patch network
    with patch("requests.Session.get", side_effect=_mock_get):
        discover_bylaws(cache_root=cache_root, out_dir=out_dir,
                        fr_landing=fr_landing, en_landing=en_landing,
                        history_timeout=10, history_user_agent="LRN/Test")

    # 1) FR mirrors exist (path segments may be encoded on-disk, check both variants)
    # Expect sanitized filenames with encoded comma and no trailing %20
    fr82 = Path(cache_root) / "fr" / "document" / "rc" / "S-2.1%2C%20r.%208.2" / "index.html"
    fr22 = Path(cache_root) / "fr" / "document" / "rc" / "S-2.1%2C%20r.%2022" / "index.html"
    assert fr82.exists(), f"Missing FR mirror: {fr82}"
    assert fr22.exists(), f"Missing FR mirror: {fr22}"

    # 2) EN mirror exists
    en10 = Path(cache_root) / "en" / "document" / "rc" / "S-2.1%2C%20r.%2010" / "index.html"
    assert en10.exists(), f"Missing EN mirror: {en10}"

    # 3) Outputs created
    out_root = Path(out_dir)
    assert out_root.exists(), "output directory not created"
    instruments = [p for p in out_root.iterdir() if p.is_dir()]
    assert instruments, "no instruments extracted"

    # 4) At least one history index per instrument family
    any_hist_index = False
    for inst in instruments:
        idx = inst / "history" / "index.json"
        if idx.exists():
            data = json.loads(idx.read_text(encoding="utf-8"))
            assert isinstance(data, dict)
            # Each entry should contain date+path to .html
            for frag, items in data.items():
                for it in items:
                    assert "date" in it and "path" in it and it["path"].endswith(".html")
            any_hist_index = True
            break
    assert any_hist_index, "no history/index.json found in any instrument"

    # 5) Section-only snapshots
    found_section_only = False
    for inst in instruments:
        hist_dir = inst / "history"
        if hist_dir.exists():
            for frag_dir in hist_dir.iterdir():
                if frag_dir.is_dir():
                    for snap in frag_dir.glob("*.html"):
                        txt = snap.read_text(encoding="utf-8")
                        if 'HIST FR 8.2' in txt or 'HIST FR 22' in txt or 'HIST EN 10' in txt:
                            assert '<div id="se:' in txt
                            found_section_only = True
                            break
                if found_section_only:
                    break
        if found_section_only:
            break
    assert found_section_only, "snapshot does not appear to be section-only"