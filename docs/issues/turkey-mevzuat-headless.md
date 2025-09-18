# Issue: Turkey Mevzuat Portal Requires Headless Capture

The Turkish Mevzuat portal injects legislation content via scripts and may block basic HTTP clients.

## Guidance
- Use `scripts/headless_fetch.py --wait-until domcontentloaded --timeout 120000` to fetch the page.
- Store HTML outside git and rerun ingestion with `--resume` to record checksums.
- Document capture details in `logs/manifest-expansion/turkey/`.
