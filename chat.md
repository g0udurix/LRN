# Session Notes (2025-09-17)

## Context
- Expanded jurisdiction manifests for Canada (QC, municipal pilots) and international OHS coverage (France, China, Germany, Japan, OSHA, etc.).
- Added Playwright-backed fallback logic to `scripts/corpus_ingest.py` and `scripts/headless_fetch.py` to handle DataDome/WAF gateways (Legifrance, CanLII, Ville de Québec, gov.cn/npc.gov.cn).
- Documentation (README, AGENTS, docs/corpus/*, docs/issues/*) now reflects headless workflow, Playwright setup, municipal/federal manifests, and monitoring guidance.
- New manifests rely on external HTML/PDF copies stored outside git; ingestion tested via `python -m pytest` (pass).

## Outstanding Follow-ups
1. Locate an official Calgary-hosted PDF for Bylaw 33M2014 to replace the interim CanLII link (tracked in docs/issues/calgary-building-maintenance.md).
2. Explore Legifrance API/licensing for automated bulk access beyond Playwright captures.
3. Broaden China coverage (sector-specific regulations, municipal bylaws) once stable endpoints are confirmed.

## Environment Tips for Resume
- Reinstall Playwright dependencies if environment resets:
  ```bash
  python -m pip install playwright
  playwright install chromium
  ```
- Use headless helper when manifests hit DataDome/WAF:
  ```bash
  python scripts/headless_fetch.py <url> --out /tmp/page.html --timeout 120000 --wait-until domcontentloaded
  python scripts/corpus_ingest.py --manifest <manifest> --out-dir output_x --log-dir logs/ingestion --resume
  ```
- Reference updated manifests under `docs/corpus/manifests/` for ingestion targets.
- Manifest stream plan drafted in `docs/corpus/manifest_expansion_plan.md`; next step is auditing JSON manifests and scheduling headless capture runs.
- Added manifests for new jurisdictions (EU Framework Directive, Netherlands, Scandinavia, Brazil, New Zealand, Korea, Singapore, South Africa, Morocco, Nigeria, Egypt, India, Thailand, UAE, Qatar, Dubai, Mexico, Spain, Portugal) with metadata and issue references; updated `docs/corpus/international.md` and `tests/test_manifest_integrity.py`. Tests: `python -m pytest tests/test_manifest_integrity.py -q`, `python -m pytest -q`.
- Added G20 manifests for Indonesia and Russia plus Middle East/Latin America set (Saudi Arabia, Iran, Lebanon, Argentina, Chile, Colombia, Peru, Jamaica, Dominican Republic, Cuba, Trinidad & Tobago, Barbados) with headless notes. Tests: `python -m pytest tests/test_manifest_integrity.py -q`, `python -m pytest -q`.
- Added WHO occupational safety strategy manifest (`docs/corpus/manifests/who.json`); tests: `python -m pytest tests/test_manifest_integrity.py -q`, `python -m pytest -q`.
- Manifest schema + automation scaffolding added (`scripts/corpus_ingest.py` extensions, `docs/corpus/manifest_schema.md`, `scripts/generate_manifests.py`, roster skeleton). Tests: `python -m pytest tests/test_manifest_integrity.py -q`, `python -m pytest -q`.
