from pathlib import Path

from scripts.corpus_ingest import IngestOptions, ingest, load_manifest


def _write_manifest(tmp_path: Path) -> Path:
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
        [
          {"url": "https://example.test/fr/document", "language": "fr", "instrument": "S-2.1"},
          {"url": "https://example.test/en/document", "language": "en", "instrument": "S-2.1"}
        ]
        """,
        encoding="utf-8",
    )
    return manifest


def test_load_manifest(tmp_path: Path):
    manifest = _write_manifest(tmp_path)
    entries = load_manifest(manifest)
    assert entries[0].instrument == "S-2.1"
    assert entries[1].language == "en"


def test_ingest_success_and_resume(monkeypatch, tmp_path: Path):
    manifest = _write_manifest(tmp_path)

    class FakeResponse:
        def __init__(self, content: bytes):
            self.content = content

        def raise_for_status(self):
            return None

    class FakeSession:
        def __init__(self):
            self.calls = []

        def get(self, url, timeout):
            self.calls.append(url)
            return FakeResponse(f"content-{url}".encode())

    fake_session = FakeSession()
    monkeypatch.setattr('scripts.corpus_ingest.requests.Session', lambda: fake_session)

    options = IngestOptions(
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
        timeout=5,
        retries=0,
        delay=0.0,
        resume=False,
    )
    results = ingest(manifest, options)
    assert all(r.status == 'fetched' for r in results)
    for r in results:
        assert r.path and r.path.exists()
    log_files = list((options.log_dir).glob('*/manifest.json'))
    assert log_files

    # Resume skips downloads
    fake_session.calls.clear()
    options.resume = True
    ingest(manifest, options)
    assert not fake_session.calls


def test_ingest_failure(monkeypatch, tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text('[{"url": "https://example.test/fr/document", "language": "fr", "instrument": "S-2.1"}]', encoding='utf-8')

    class FailingSession:
        def get(self, url, timeout):
            raise RuntimeError("boom")

    monkeypatch.setattr('scripts.corpus_ingest.requests.Session', lambda: FailingSession())

    options = IngestOptions(
        out_dir=tmp_path / "out",
        log_dir=tmp_path / "logs",
        timeout=5,
        retries=1,
        delay=0.0,
        resume=False,
    )
    results = ingest(manifest, options)
    assert results[0].status == 'failed'
    assert results[0].error is not None
