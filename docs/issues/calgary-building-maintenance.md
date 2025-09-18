# Issue: Calgary Building Maintenance Bylaw 33M2014 Download URL Needed

## Summary
All known public links to the City of Calgary's Building Maintenance Bylaw 33M2014
(e.g., `https://www.calgary.ca/content/dam/www/pda/pd/documents/about-planning/33M2014-building-maintenance-bylaw.pdf`) now return HTTP 404. Automated and
headless requests still fail. As an interim measure the manifest points to the
CanLII consolidation (`yyc-2014-33`), which requires the Playwright fallback for
HTML capture but provides a stable source for checksum monitoring.

## Next Steps
1. Contact City of Calgary or search their open-data portal for an updated PDF.
2. If only HTML is available, script a headless fetch and archive the result
   until an official PDF is restored.
3. Replace the CanLII manifest entry with the authoritative City-hosted PDF
   once it becomes accessible again.
