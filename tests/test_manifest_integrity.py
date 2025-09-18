from pathlib import Path

from scripts.corpus_ingest import load_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / 'docs/corpus/manifests'

def test_all_manifests_load():
    for manifest_path in MANIFEST_DIR.glob('*.json'):
        entries = load_manifest(manifest_path)
        assert entries, f"No entries in {manifest_path}"
        for entry in entries:
            assert entry.url.startswith('http'), f"Invalid URL in {manifest_path}: {entry.url}"
            assert entry.language, f"Missing language in {manifest_path}"
            assert entry.instrument, f"Missing instrument in {manifest_path}"


def test_priority_manifests_present():
    expected = {
        'ab.json',
        'bc.json',
        'ca.json',
        'germany.json',
        'japan.json',
        'china.json',
        'montreal.json',
        'quebec_city.json',
        'qc.json',
        'osha.json',
        'uk.json',
        'eu.json',
        'australia.json',
        'toronto.json',
        'vancouver.json',
        'calgary.json',
        'nyc.json',
        'chicago.json',
        'california.json',
    }
    present = {path.name for path in MANIFEST_DIR.glob('*.json')}
    missing = expected - present
    assert not missing, f"Missing priority manifests: {sorted(missing)}"
