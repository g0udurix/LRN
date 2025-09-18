# Issue: Iran Majlis Portal Requires Headless Session

The Majlis regulatory portal loads content via scripts and may require session cookies.

## Guidance
- Use `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` to capture the page.
- Store HTML outside git (`logs/manifest-expansion/iran/`) and rerun ingestion with `--resume`.
- Note that English translations are limited; captured Farsi HTML should be preserved for reference.
