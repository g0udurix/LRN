# Issue: Yukon Legislation PDFs Blocked by Cloudflare

## Summary
Attempts to download Yukon occupational health and safety statutes and
regulations (e.g., `https://yukon.ca/sites/yukon.ca/files/eco/eco-occupational-health-and-safety-act.pdf`) result in an HTTP 403 due to Cloudflare/DataDome challenges. Automated fetches via `requests`/`curl` are blocked, preventing `monitor_updates.py` and ingestion from accessing the authoritative documents even though the content is accessible in a browser. Manifests currently fall back to the CanLII consolidation, which is also protected by DataDome and may refuse scripted requests.

## Impact
- No archival or automated ingestion for Yukon OHS instruments.
- Need to rely on manual downloads until a scripted authentication/challenge bypass
  is implemented or a public API/static hosting is identified.

## Proposed Follow-up
1. Investigate whether Yukon provides an alternative open-data API or static
   download endpoint that bypasses Cloudflare protection.
2. If not, script a headless browser flow (e.g., Playwright/Selenium) capable of
   solving the challenge in a compliant manner, while respecting the site’s terms.
3. Once a stable access method is available, update `docs/corpus/manifests/yk.json`
   and integrate with `monitor_updates.py`.

## References
- Cloudflare 403 response (see logs of attempted download).
- `docs/corpus/monitoring.md` for monitoring workflow.
