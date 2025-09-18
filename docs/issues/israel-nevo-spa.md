# Issue: Israel Nevo SPA Rendering

Nevo legal portal loads legislation via a single-page application that requires JavaScript execution.

## Guidance
- Capture content with `scripts/headless_fetch.py --wait-until networkidle --timeout 120000`.
- Cache HTML outside git (`logs/manifest-expansion/israel/`) and rerun ingestion with `--resume`.
- Monitor for official PDF alternatives on the Labour Ministry site.
