from lrn.history import HistoryCrawler

SAMPLE_XHTML = """
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<div xmlns="http://www.w3.org/1999/xhtml">
  <div class="section" id="se:1">
    <div class="HistoryLink"><a href="/fr/version/rc/S-2.1, r. 8.2 ?code=se:1&historique=20250804#20250804"><img src="/img/history.png"/></a></div>
  </div>
</div>
"""

def test_discover_fragment_history_links_basic():
    hc = HistoryCrawler(base_url="https://www.legisquebec.gouv.qc.ca", out_dir="/tmp/out")
    links = hc.discover_fragment_history_links(SAMPLE_XHTML)
    assert links and any('historique=' in x for x in links)