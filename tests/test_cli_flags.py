from pathlib import Path

from lrn.cli import extract


def test_extract_toggles_disable_annex_and_history(monkeypatch, tmp_path):
    html = """
    <html><body>
      <div id=\"mainContent-document\">
        <?xml version=\"1.0\" encoding=\"UTF-8\"?>
        <!DOCTYPE div PUBLIC \"-//W3C//DTD XHTML 1.0 Strict//EN\" \"http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd\">
        <div xmlns=\"http://www.w3.org/1999/xhtml\">
          <a href=\"/file.pdf\">PDF</a>
        </div>
      </div>
    </body></html>
    """
    src = tmp_path / "sample.html"
    src.write_text(html, encoding="utf-8")

    called = {"annex": False, "history": False}

    monkeypatch.setattr("lrn.cli.process_annexes", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("annex should not run")))
    monkeypatch.setattr("lrn.cli.build_history_sidecars", lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("history should not run")))

    extract(
        history_sidecars=False,
        history_markdown=False,
        annex_pdf_to_md=False,
        metadata_exclusion="",
        out_dir=str(tmp_path / "out"),
        inputs=[str(src)],
        base_url=None,
        pdf_to_md_engine="marker",
        ocr=False,
    )

    instrument = tmp_path / "out" / "sample"
    assert (instrument / "current.xhtml").exists()
