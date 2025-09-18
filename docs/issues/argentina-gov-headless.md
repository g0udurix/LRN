# Issue: Argentina Official Portal Headless Requirement

The argentina.gob.ar portal renders consolidated legislation dynamically and may restrict scripted
clients.

## Guidance
- Capture with `scripts/headless_fetch.py --wait-until domcontentloaded --timeout 120000` before running
  ingestion.
- Cache HTML outside git (`logs/manifest-expansion/argentina/`) and rerun `scripts/corpus_ingest.py --resume`.
- Monitor for PDF attachments or alternative endpoints to stabilize ingestion.
