from pathlib import Path

import requests
import pytest

from lrn.annex import AnnexOptions, AnnexStatus, process_annexes
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

    class _Resp(DummyResponse):
        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, exc_type, exc, tb):
            return False

        def iter_content(self_inner, chunk_size):
            yield pdf_bytes

    def fake_convert(pdf_path, markdown_path, engine):
        markdown_path.write_text("converted", encoding="utf-8")
        return None

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda url, timeout, stream=True: _Resp(pdf_bytes))
    monkeypatch.setattr("lrn.annex._convert_pdf", fake_convert)

    inst_dir = tmp_path / "instrument"
    options = AnnexOptions(engine="marker", base_url="https://example.test", session=session)

    conversions = process_annexes(fragment, instrument_dir=inst_dir, options=options)

    assert conversions and conversions[0].markdown_path is not None
    assert conversions[0].status == AnnexStatus.CONVERTED
    md_text = conversions[0].markdown_path.read_text(encoding="utf-8")
    assert "source_url" in md_text
    assert "fake-pdf" not in md_text  # ensure not raw bytes


def test_process_annexes_records_warning(monkeypatch, tmp_path):
    fragment = load_fragment(_fixture_fragment(tmp_path))

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda url, timeout, stream=True: (_ for _ in ()).throw(RuntimeError("network down")))
    options = AnnexOptions(engine="marker", base_url="https://example.test", session=session)

    inst_dir = tmp_path / "instrument"
    conversions = process_annexes(fragment, instrument_dir=inst_dir, options=options)

    assert conversions[0].status == AnnexStatus.FAILED
    # markdown not created on failure
    assert conversions[0].markdown_path is None


def test_process_annexes_skips_existing(monkeypatch, tmp_path):
    fragment = load_fragment(_fixture_fragment(tmp_path))

    pdf_path = tmp_path / "instrument" / "annexes" / "sample.pdf"
    pdf_path.parent.mkdir(parents=True, exist_ok=True)
    pdf_path.write_bytes(b"existing")
    pdf_path.with_suffix('.md').write_text("existing md", encoding="utf-8")

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("should not request")))
    options = AnnexOptions(engine="marker", base_url="https://example.test", skip_existing=True, session=session)

    inst_dir = tmp_path / "instrument"
    conversions = process_annexes(fragment, instrument_dir=inst_dir, options=options)

    assert conversions[0].status == AnnexStatus.SKIPPED


def test_process_annexes_conversion_warning(monkeypatch, tmp_path):
    fragment = load_fragment(_fixture_fragment(tmp_path))

    pdf_bytes = b"fake"

    class _Resp(DummyResponse):
        def __enter__(self_inner):
            return self_inner

        def __exit__(self_inner, exc_type, exc, tb):
            return False

        def iter_content(self_inner, chunk_size):
            yield pdf_bytes

    session = requests.Session()
    monkeypatch.setattr(session, "get", lambda url, timeout, stream=True: _Resp(pdf_bytes))

    monkeypatch.setattr("lrn.annex._convert_pdf", lambda *args, **kwargs: "conversion failed")

    options = AnnexOptions(engine="marker", base_url="https://example.test", session=session)
    inst_dir = tmp_path / "instrument"
    conversions = process_annexes(fragment, instrument_dir=inst_dir, options=options)

    record = conversions[0]
    assert record.status == AnnexStatus.DOWNLOADED
    assert record.message and "conversion failed" in record.message
