# Issue: Portugal DRE Portal Dynamic Loading

The Portuguese DRE portal loads legislation content through client-side scripting. Direct `requests`
fetches may return navigation markup only.

## Guidance
- Use `scripts/headless_fetch.py --wait-until networkidle --timeout 90000 <url>` to capture the fully
  rendered page.
- Cache the HTML outside git (`logs/manifest-expansion/portugal/`) and rerun ingestion with `--resume`.
- Validate that the captured HTML retains the full legislative text; update the manifest if the DRE
  permalink redirects to a PDF.
