from pathlib import Path
import json

from lrn.history import HistoryOptions, build_history_sidecars


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
