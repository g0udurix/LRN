# Issue: Chile BCN Portal SPA Rendering

The Biblioteca del Congreso Nacional portal loads legislation via JavaScript, returning minimal markup
to simple HTTP clients.

## Guidance
- Use `scripts/headless_fetch.py --wait-until networkidle --timeout 120000` to capture the rendered HTML.
- Store the capture outside git and rerun ingestion with `--resume`.
- Record capture metadata in `logs/manifest-expansion/chile/`.
