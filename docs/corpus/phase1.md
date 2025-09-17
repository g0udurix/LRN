# Phase 1 Corpus Scope

This document captures the initial LegisQuébec corpus targeted for Phase 1 ingestion.

## Objectives
- Mirror a representative set of S-2.1 instruments (FR and EN) that exercise annex + history coverage.
- Record source URLs, expected update cadence, and any licensing constraints.
- Provide a manifest template for batch ingestion runs.

## Candidate Instruments (draft)
| Instrument | Language | URL | Notes |
|------------|----------|-----|-------|
| S-2.1 law | FR | https://www.legisquebec.gouv.qc.ca/fr/document/lc/S-2.1 | Frequently updated; includes history widget |
| S-2.1 law | EN | https://www.legisquebec.gouv.qc.ca/en/document/lc/S-2.1 | English mirror |
| S-2.1, r. 8.2 | FR | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%208.2 | Annex-heavy regulation |
| S-2.1, r. 8.2 | EN | https://www.legisquebec.gouv.qc.ca/en/document/rc/S-2.1,%20r.%208.2 | English mirror |

## Licensing / Terms of Use
- LegisQuébec content may be mirrored for research purposes; ensure attribution and respect robots/exclusion directives.
- Annex PDFs may include third-party materials; confirm usage limits before redistribution.

## Next Steps
- Finalize the table above with additional instruments (at least 5 FR + 5 EN).
- Confirm update cadence and throttle recommendations with product stakeholders.
- Use this scope when creating the Phase 1 manifest consumed by `scripts/corpus_ingest.py`.
