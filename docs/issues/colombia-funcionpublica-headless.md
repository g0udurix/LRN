# Issue: Colombia Función Pública Portal

The Función Pública portal serves legislation through dynamic scripts and may return partial responses
if cookies/user-agent checks fail.

## Guidance
- Capture with `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` and store HTML in
  `logs/manifest-expansion/colombia/` outside git.
- Rerun ingestion with `--resume` to record checksums without re-fetching.
- Investigate whether PDF versions exist as more stable sources.
