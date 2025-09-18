from pathlib import Path

from scripts.corpus_ingest import load_manifest

ROOT = Path(__file__).resolve().parents[1]
MANIFEST_DIR = ROOT / 'docs/corpus/manifests'

ALLOWED_FIELDS = {
    'url',
    'language',
    'instrument',
    'category',
    'requires_headless',
    'content_type',
    'issue_ref',
    'notes',
    'status'
}

def test_all_manifests_load():
    for manifest_path in MANIFEST_DIR.glob('*.json'):
        entries = load_manifest(manifest_path)
        assert entries, f"No entries in {manifest_path}"
        for entry in entries:
            status = getattr(entry, 'status', 'active').lower()
            if status == 'done':
                assert entry.url.startswith('http'), f"Invalid URL in {manifest_path}: {entry.url}"
                assert entry.language, f"Missing language in {manifest_path}"
            else:
                assert isinstance(entry.url, str)
                assert isinstance(entry.language, str)
            assert isinstance(entry.instrument, str)


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
        'netherlands.json',
        'sweden.json',
        'norway.json',
        'finland.json',
        'scandinavia.json',
        'brazil.json',
        'new_zealand.json',
        'south_korea.json',
        'singapore.json',
        'south_africa.json',
        'morocco.json',
        'nigeria.json',
        'egypt.json',
        'india.json',
        'thailand.json',
        'uae.json',
        'qatar.json',
        'italy.json',
        'greece.json',
        'romania.json',
        'turkey.json',
        'israel.json',
        'dubai.json',
        'mexico.json',
        'spain.json',
        'portugal.json',
    }
    present = {path.name for path in MANIFEST_DIR.glob('*.json')}
    missing = expected - present
    assert not missing, f"Missing priority manifests: {sorted(missing)}"


def test_manifest_fields():
    import json
    for manifest_path in MANIFEST_DIR.glob('*.json'):
        items = json.loads(manifest_path.read_text(encoding='utf-8'))
        for item in items:
            unexpected = set(item.keys()) - ALLOWED_FIELDS
            assert not unexpected, f"Unexpected keys in {manifest_path}: {sorted(unexpected)}"
            status = item.get('status', 'active').lower()
            url = item.get('url', '')
            language = item.get('language', '')
            if status == 'done':
                assert isinstance(url, str) and url, f"Missing url in {manifest_path}"
                assert isinstance(language, str) and language, f"Missing language in {manifest_path}"
            else:
                assert isinstance(url, str)
                assert isinstance(language, str)
            assert isinstance(item.get('instrument', ''), str), f"Instrument must be string in {manifest_path}"
            assert isinstance(item.get('category', 'unknown'), str)
            assert isinstance(item.get('requires_headless', False), bool)
            if 'content_type' in item:
                assert item['content_type'] in {'html', 'pdf', 'json'}, f"Unknown content_type in {manifest_path}: {item['content_type']}"
            if 'status' in item:
                assert isinstance(item['status'], str)
