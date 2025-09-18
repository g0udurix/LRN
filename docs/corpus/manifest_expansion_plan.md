# Manifest Expansion Plan

## Objectives
- Update priority manifests with verified URLs and metadata (NB, ON, AB, BC, OSHA, UK, France, Japan, China).
- Add municipal pilots (Montréal, Québec City, Toronto, Vancouver, NYC, Chicago, Calgary) with headless capture notes.
- Ensure manifests reference external archives (out of git) and include `instrument`, `language`, `source`, and `fetch` metadata.

## Tasks
- [ ] Audit existing JSON manifests for missing fields or outdated URLs.
- [ ] Capture WAF-protected resources with `scripts/headless_fetch.py` and record paths under `logs/manifest-expansion/`.
- [ ] Update `docs/issues/*.md` for each jurisdiction after verification.
- [ ] Regenerate or create fixtures for new manifests in `tests/fixtures/manifests/` (if needed).
- [ ] Run `python -m pytest tests/test_manifest_integrity.py -q` and `python -m pytest`.

## Logging
- Store ingestion runs in `logs/manifest-expansion/<manifest>/<timestamp>.log` (git-ignored).
- Document command list and SHA checksums in `chat.md` and issue files.

## Dependencies
- Requires Playwright headless capture for DataDome-hosted sites (Legifrance, CanLII, Ville de Québec).
- Coordinates with Persistence Architect to supply updated fixtures for persistence tests.
