# Issue: Romania Justice Portal Blocking Scripted Clients

The Romanian legislation portal (just.ro) requires JavaScript execution and may redirect automated
requests to login pages.

## Guidance
- Run `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` to capture the rendered
  text and store the HTML outside git.
- Rerun manifest ingestion with `--resume` and log capture metadata in `logs/manifest-expansion/romania/`.
- Monitor for permanent download links or XML APIs as alternatives.
