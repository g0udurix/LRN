# Issue: Greece e-Nomothesia Dynamic Page

The e-Nomothesia portal loads legislation content dynamically and may present empty templates to
non-headless clients.

## Guidance
- Capture with `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` and store HTML
  outside git prior to ingestion.
- Rerun `scripts/corpus_ingest.py --resume` to log checksums without another fetch.
- Note capture path and timestamp in `logs/manifest-expansion/greece/`.
