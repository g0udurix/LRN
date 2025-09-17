from pathlib import Path

from scripts.corpus_ingest import load_manifest

MANIFEST_DIR = Path('docs/corpus/manifests')

def test_all_manifests_load():
    for manifest_path in MANIFEST_DIR.glob('*.json'):
        entries = load_manifest(manifest_path)
        assert entries, f"No entries in {manifest_path}"
        for entry in entries:
            assert entry.url.startswith('http'), f"Invalid URL in {manifest_path}: {entry.url}"
            assert entry.language, f"Missing language in {manifest_path}"
            assert entry.instrument, f"Missing instrument in {manifest_path}"
