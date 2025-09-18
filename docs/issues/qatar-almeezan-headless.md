# Issue: Qatar Al Meezan Portal Requires Headless Session

The Al Meezan legal portal dynamically renders legislation, presenting a blank template to basic HTTP
clients.

## Guidance
- Run `scripts/headless_fetch.py --wait-until domcontentloaded --timeout 90000 <url>` and store the
  HTML outside git before running ingestion with `--resume`.
- Avoid rapid retries; the portal implements anti-bot throttling.
- Record capture metadata (timestamp, checksum) in `logs/manifest-expansion/qatar/`.
