# Issue: Korea e-Law SPA Rendering

The Korean Law Information Center (`elaw.klri.re.kr`) serves legislation via a single-page
application. Automated clients need a headless browser to capture the rendered HTML.

## Guidance
- Use `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` to capture the page.
- Cache the output outside git and rerun ingestion with `--resume` to log checksums.
- Monitor for layout changes that alter the rendered HTML structure.
