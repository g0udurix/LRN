# Issue: Nunavut Legislation Site Returns 404 for Consolidated OHS Pages

## Summary
Requests to the Nunavut legislation portal (e.g.,
`https://www.nunavutlegislation.ca/en/consolidated-regulations/occupational-health-and-safety-regulations`) return 404 responses even though the content is publicly accessible via a browser. This prevents automated downloads for the Safety Act and OHS Regulations.

## Impact
- No reliable URL for manifests/monitoring to fetch Nunavut OHS materials.
- Manual intervention required to acquire updated PDFs/HTML.

## Proposed Follow-up
1. Investigate whether the site requires query parameters, session cookies, or a
   specific user agent to serve the content.
2. Explore alternate hosts (e.g., Government of Nunavut departmental sites or
   CanLII hosted PDFs) that provide direct downloads.
3. Once confirmed, update `docs/corpus/manifests/nu.json` with functional URLs
   and add the jurisdiction to monitoring.

## References
- `scripts/canlii_metadata.py` results (`logs/canlii_nu_*`)
- Attempts logged in terminal (HTTP 404).
