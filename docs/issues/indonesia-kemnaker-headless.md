# Issue: Indonesia Kemnaker Portal Requires Headless Capture

The Ministry of Manpower JDIH portal loads legislation details via client-side scripts and often
returns a minimal template to scripted HTTP clients.

## Guidance
- Use `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` to capture the rendered
  HTML and store it outside git (`logs/manifest-expansion/indonesia/`).
- Rerun `scripts/corpus_ingest.py --resume --manifest docs/corpus/manifests/indonesia.json` to record
  checksums without re-fetching.
- Monitor for an official PDF or static download endpoint to reduce headless dependencies.
