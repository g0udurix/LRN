# Issue: Morocco Official Bulletin Access

Official Moroccan legislation is published on sgg.gov.ma as PDF scans. The portal occasionally blocks
scripted clients, returning empty responses.

## Guidance
- Prefetch the PDF with `scripts/headless_fetch.py --type pdf` (or manual download) before running the
  manifest ingestion. Store the file outside git under `logs/manifest-expansion/morocco/`.
- Note the download timestamp and checksum in the ingestion log for reproducibility.
- Monitor for alternate HTML renderings that might allow direct fetches without headless capture.
