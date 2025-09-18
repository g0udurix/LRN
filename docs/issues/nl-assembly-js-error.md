# Issue: Newfoundland and Labrador Legislature Returns JS Error Page

## Summary
Accessing Newfoundland and Labrador statutes/regulations via the Legislature
site (e.g., `https://www.assembly.nl.ca/legislation/sr/statutes/o03-01.htm`) from
non-browser clients yields an HTML response containing a JavaScript-based error
page, preventing automated downloads. `scripts/monitor_updates.py` treats the
response as a new version but the archived HTML is unusable, and no official PDF
link is exposed.

## Impact
- Automated archival captures the JS error page instead of the statute text.
- Batch ingestion cannot scrape the authoritative content directly.
- Manual downloads remain possible in a browser session, but the workflow is not
  automated or reproducible.

## Proposed Follow-up
1. Inspect network requests in a browser session to locate the real PDF/HTML
   endpoint (e.g., hidden behind a download handler or requiring specific
   headers/cookies).
2. Update `docs/corpus/manifests/nl.json` with the stable endpoint once found, or
   add a scripted login/fetch routine.
3. Re-run `scripts/monitor_updates.py` to confirm the archived content contains
   the actual statute text.

## References
- `docs/corpus/manifests/nl.json`
- `logs/update_states/nl.json`
- `docs/corpus/monitoring.md`
