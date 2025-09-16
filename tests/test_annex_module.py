from pathlib import Path

import pytest

from lrn.annex import process_annexes
from lrn.extract import load_fragment


class DummyResponse:
    def __init__(self, content: bytes, *, status_code: int = 200):
        self.content = content
        self.status_code = status_code

    def raise_for_status(self):
        if self.status_code >= 400:
            raise RuntimeError("request failed")


def _fixture_fragment(tmp_path: Path) -> Path:
    html = """
    <html><body>
      <div id=\"mainContent-document\">
        <?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <!DOCTYPE div PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">
        <div xmlns=\"http://www.w3.org/1999/xhtml\">
          <a href=\"/files/sample.pdf\">PDF</a>
        </div>
      </div>
    </body></html>
    """
    path = tmp_path / "fragment.html"
    path.write_text(html, encoding="utf-8")
    return path


def test_process_annexes_downloads_and_converts(monkeypatch, tmp_path):
    fragment = load_fragment(_fixture_fragment(tmp_path))

    pdf_bytes = b"fake-pdf"

    def fake_get(url, timeout):
        assert url.endswith("sample.pdf")
        return DummyResponse(pdf_bytes)

    def fake_convert(pdf_path, markdown_path, engine):
        markdown_path.write_text("converted", encoding="utf-8")
        return None

    monkeypatch.setattr("lrn.annex.requests.get", fake_get)
    monkeypatch.setattr("lrn.annex._convert_pdf_to_markdown", fake_convert)

    inst_dir = tmp_path / "instrument"
    conversions = process_annexes(fragment, base_url="https://example.test", instrument_dir=inst_dir, engine="marker")

    assert conversions and conversions[0].markdown_path is not None
    md_text = conversions[0].markdown_path.read_text(encoding="utf-8")
    assert "source_url" in md_text
    assert "fake-pdf" not in md_text  # ensure not raw bytes


def test_process_annexes_records_warning(monkeypatch, tmp_path):
    fragment = load_fragment(_fixture_fragment(tmp_path))

    def fake_get(url, timeout):
        raise RuntimeError("network down")

    monkeypatch.setattr("lrn.annex.requests.get", fake_get)

    inst_dir = tmp_path / "instrument"
    conversions = process_annexes(fragment, base_url="https://example.test", instrument_dir=inst_dir, engine="marker")

    assert conversions[0].warning
    # markdown not created on failure
    assert conversions[0].markdown_path is None
