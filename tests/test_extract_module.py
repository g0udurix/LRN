from pathlib import Path

import pytest

from lrn.extract import FragmentExtractionError, load_fragment


def _write_fixture(tmp_path: Path, body: str) -> Path:
    html = f"""
    <html><body>
        <div id=\"mainContent-document\">
        <?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <!DOCTYPE div PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">
        <div xmlns=\"http://www.w3.org/1999/xhtml\">{body}</div>
        </div>
    </body></html>
    """
    path = tmp_path / "fixture.html"
    path.write_text(html, encoding="utf-8")
    return path


def test_load_fragment_extracts_heading_instrument(tmp_path):
    path = _write_fixture(tmp_path, "<h1>Safety Code</h1>")
    fragment = load_fragment(path)
    assert fragment.instrument_id.startswith("Safety_Code")
    assert "Safety Code" in fragment.xhtml
    assert fragment.soup.find("h1") is not None


def test_fragment_extraction_error_when_missing_fragment(tmp_path):
    path = tmp_path / "empty.html"
    path.write_text("<html><body>No fragment here</body></html>", encoding="utf-8")
    with pytest.raises(FragmentExtractionError):
        load_fragment(path)
