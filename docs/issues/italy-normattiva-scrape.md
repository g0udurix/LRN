# Issue: Italy Normattiva Portal Requires Headless Session

Normattiva renders consolidated legislation through dynamic scripts and requires session cookies.
Automated requests often return navigation stubs.

## Guidance
- Use `scripts/headless_fetch.py --wait-until domcontentloaded --timeout 120000` to capture the page.
- Store the rendered HTML outside git and rerun manifest ingestion with `--resume`.
- Record capture metadata in `logs/manifest-expansion/italy/`.
