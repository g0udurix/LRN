from pathlib import Path

from scripts.corpus_ingest import load_manifest, summarise_run, write_manifest


def test_load_manifest_and_summary(tmp_path: Path):
    manifest = tmp_path / "manifest.json"
    manifest.write_text(
        """
        [
          {"url": "https://example.test/fr/document", "language": "fr", "instrument": "S-2.1"}
        ]
        """,
        encoding="utf-8",
    )
    entries = load_manifest(manifest)
    assert entries[0].language == "fr"

    summary = summarise_run(entries)
    assert summary['entries'][0]['status'] == 'pending'

    out_path = write_manifest(summary, tmp_path / "out")
    assert out_path.exists()
