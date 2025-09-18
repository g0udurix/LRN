# Issue: Russia CNTD Portal Requires Headless Session

The CNTD legislative portal serves content via dynamic scripts and enforces cookie checks that block
basic HTTP clients.

## Guidance
- Capture pages with `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` and cache the
  HTML outside git (`logs/manifest-expansion/russia/`).
- Rerun ingestion with `--resume` to log checksums without triggering additional requests.
- Investigate alternate PDF sources (e.g., Ministry portals) for more stable ingestion.
