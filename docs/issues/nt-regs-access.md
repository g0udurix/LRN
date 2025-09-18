# Issue: Northwest Territories OHS Regulations Not Downloadable Programmatically

## Summary
The GNWT Justice portal returns 404 pages for regulation PDFs (e.g.,
`https://www.justice.gov.nt.ca/en/files/legislation/safety/safety.r2.pdf`) when
requested by automated tools. Alternative hosts (WSCC) also return 404/JS error
pages. Only the Safety Act PDF (`safety.a.pdf`) is accessible. Without a stable
regulation download URL, `docs/corpus/manifests/nt.json` cannot be completed and
`monitor_updates.py` cannot archive NWT OHS regulations.

## Impact
- No automated coverage for NWT Occupational Health and Safety Regulations.
- Monitoring/ingestion pipelines report errors for the regulation entry.

## Proposed Follow-up
1. Inspect browser network calls to capture the actual regulation URL (if it
   exists) or confirm if regulations are only available via the WSCC site.
2. Contact the publisher (Justice/WSCC) or obtain an official link for
   automation.
3. Integrate the working URL into the manifest and re-run monitoring.

## References
- 404 responses logged in `logs/update_states/ns.json` (for the similar Nova Scotia issue) and new state file for NWT once manifest is added.
- `docs/corpus/monitoring.md` for overall monitoring guidance.
