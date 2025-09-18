# Issue: Saudi BOE Portal Requires Headless Capture

The Saudi Board of Experts portal dynamically renders legislation and may return login pages to
non-headless clients.

## Guidance
- Capture with `scripts/headless_fetch.py --wait-until domcontentloaded --timeout 120000` and store
  HTML outside git (`logs/manifest-expansion/saudi/`).
- Rerun ingestion with `--resume` to avoid repeated requests.
- Monitor for official PDF publications for fallback.
