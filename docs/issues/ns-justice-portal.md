# Issue: Nova Scotia Justice Regulations Return 404 for Direct Downloads

## Summary
Direct HTTP requests to Nova Scotia Department of Justice regulation pages
(e.g., `https://novascotia.ca/just/regulations/regs/ohsgens.htm` and
`https://novascotia.ca/just/regulations/regs/ohsfall.htm`) return a Drupal 404
template when accessed without a browser. As a result, `scripts/monitor_updates.py`
flags these entries as errors and cannot archive the latest versions of the OHS
General or Fall Protection Regulations. The manifest temporarily points to the
CanLII consolidation (`ns-reg-52-2013`), but CanLII's DataDome protection may
also block scripted access.

## Impact
- Automated monitoring fails for `docs/corpus/manifests/ns.json` entries aside
  from the OHS Act PDF.
- Batch ingestion cannot rely on the manifest to fetch these regulations.
- Manual retrieval is still possible via the Nova Scotia Legislature site, so the
  content has to be captured by hand.

## Proposed Follow-up
1. Investigate whether Nova Scotia publishes static PDF versions (possibly under
   `nslegislature.ca` or another domain) that can be referenced instead.
2. If only HTML is provided, implement a headless fetch workflow (e.g., using
   `requests_html`, Selenium, or cached static HTML) that can bypass the Drupal
   protection.
3. Once a stable URL or scripted fetch is available, update `docs/corpus/manifests/ns.json`
   and re-run `scripts/monitor_updates.py` to verify no errors occur.

## References
- `docs/corpus/manifests/ns.json`
- `logs/update_states/ns.json`
- `docs/corpus/monitoring.md`
