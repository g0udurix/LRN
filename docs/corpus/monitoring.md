# Update Monitoring & Versioning

This note captures the current state of automated monitoring for occupational
health & safety instruments.

## Scripted Checks
- `scripts/monitor_updates.py --manifest <path> --archive-dir <dir> --state logs/update_states/<name>.json`
  downloads each manifest entry, compares against the last archived checksum, and
  stores new versions under `~/lrn-archives/<jurisdiction>/` (keeping history out
  of git).
- `scripts/canlii_metadata.py <jurisdiction>` lists current metadata and
  `legislationId` values so we can cross-reference CanLII’s catalogue when the
  authoritative site changes structure.

Run both scripts on a schedule (e.g., nightly). If CanLII reports new
consolidation dates but `monitor_updates` did not detect a delta, inspect the
official portal for HTML changes (dynamic rendering, access restrictions, etc.).
Store script outputs under `logs/update_states/` (git-ignored) so CI or cron jobs
can diff recent runs. Use `scripts/headless_fetch.py` (Playwright-based) when a
site requires a real browser session (e.g., Nova Scotia Justice portal). Archive
the fetched HTML/PDF in the same jurisdiction-specific directory (outside git).

## Known Gaps & Follow-up
- **Nova Scotia General & Fall Protection Regulations**: direct HTTP requests to
  `https://novascotia.ca/just/regulations/regs/ohsgens.htm` and
  `https://novascotia.ca/just/regulations/regs/ohsfall.htm` return a Drupal 404
  template. We currently rely on the CanLII consolidation
  (`ns-reg-52-2013`), although CanLII itself is protected by DataDome and may
  return HTTP 403 to non-browser clients. Official download remains a TODO—see
  `docs/issues/ns-justice-portal.md`.
- **Newfoundland & Labrador statutes/regulations**: Legislature pages serve a
  JS-driven “error page” to non-browser clients. Manifest now uses the CanLII
  consolidation (`nlr-5-12`), but CanLII’s web front-end also employs DataDome;
  automation may require a manual download until a scripted solution is in
  place. Official endpoint tracked in `docs/issues/nl-assembly-js-error.md`.
- **Northwest Territories regulations**: no public download endpoint located; we
  temporarily point to CanLII (`rrnwt-1990-c-o-1.1-reg-1`). DataDome 403s may
  block automation—follow-up captured in
  `docs/issues/nt-regs-access.md`.
- **Nunavut**: consolidated pages return 404 for scripted clients; manifests use
  CanLII (`nu-reg-003-2016`) which also sits behind DataDome. Manual downloads
  may still be required until a compliant fetch strategy is developed. See
  `docs/issues/nu-legislation-access.md`.
- **Yukon**: Cloudflare/DataDome blocks direct downloads (`403`). Manifests rely
  on CanLII (`yoic-2006-161`), but expect automation challenges. Issue details
  recorded in `docs/issues/yk-cloudflare-block.md`.
- **Ville de Québec façade by-law**: the Charte et règlements portal returns a
  branded 404 template to scripted clients. Capture the page with
  `scripts/headless_fetch.py --out output_quebec_city/QUE_Reglement_RVQ_1272_Facades/fr.html`
  before running `python scripts/corpus_ingest.py --manifest docs/corpus/manifests/quebec_city.json --resume` so reports include the entry without retrying the
  blocked request.
- **Legifrance (France)**: DataDome challenges result in HTTP 403. The Playwright
  fallback handles the challenge after a short delay; keep captures outside git
  and respect the reuse notice printed at the bottom of each page.
- **gov.cn / npc.gov.cn**: WAF redirects or 404s occur for older HTML pages.
  Use the headless fallback; it typically renders within two seconds, but store
  the resulting HTML/PDF outside of the repository.

## Future Automation
- **CanLII metadata diffing**: periodically call `scripts/canlii_metadata.py`
  and compare `legislationId` records or publication timestamps against the
  existing archive state. This can flag updates before the official portal
  publishes the new HTML/PDF (e.g., metadata lists a new revision, but the site
  has not yet changed).
- **Automated reporting**: aggregate the JSON outputs from
  `monitor_updates.py` into a daily summary (e.g., combine the `status` entries
  for all manifests and email/Slack the list of changed documents). Future work
  could tie this to CI to fail builds when a critical instrument changes without
  updated fixtures.

## Issue Tracking
Open follow-up issues for the blocked portals (Nova Scotia Justice 404, NL House
of Assembly JS error) once the approach is finalized or assistance is required.
Include:
- URLs attempted and HTTP responses (e.g., 404 template, 200 + error page)
- Logs from `scripts/monitor_updates.py`
- Interim workaround (manual download, alternate PDF, etc.)
- Whether headless capture succeeded (record destination path and timestamp)
  so future runs can diff the archived asset without re-triggering rate limits.
