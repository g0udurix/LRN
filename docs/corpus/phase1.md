# Phase 1 Corpus Scope

This document captures the initial LegisQuébec corpus targeted for Phase 1 ingestion.

## Objectives
- Mirror a representative set of S-2.1 instruments (FR and EN) that exercise annex + history coverage.
- Record source URLs, expected update cadence, and any licensing constraints.
- Provide a manifest template for batch ingestion runs.

## Candidate Instruments (draft)
| Instrument | Language | URL | Update Cadence (est.) | Notes |
|------------|----------|-----|-----------------------|-------|
| S-2.1 law | FR | https://www.legisquebec.gouv.qc.ca/fr/document/lc/S-2.1 | Monthly | Frequently amended; rich history sidecars |
| S-2.1 law | EN | https://www.legisquebec.gouv.qc.ca/en/document/lc/S-2.1 | Monthly | English mirror |
| S-2.1, r. 8.2 | FR | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%208.2 | Quarterly | Annex-heavy regulation |
| S-2.1, r. 8.2 | EN | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%208.2?lang=en | Quarterly | English mirror (served via `?lang=en`) |
| S-2.1, r. 9 | FR | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%209 | Semi-annual | Historical versions spanning multiple years |
| S-2.1, r. 9 | EN | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%209?lang=en | Semi-annual | English mirror (served via `?lang=en`) |
| S-2.1, r. 3 | FR | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%203 | Annual | Occupational health references |
| S-2.1, r. 3 | EN | https://www.legisquebec.gouv.qc.ca/en/document/rc/S-2.1,%20r.%203 | Annual | English mirror |
| S-2.1, r. 12 | FR | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%2012 | As needed | Contains annex PDFs |
| S-2.1, r. 12 | EN | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%2012?lang=en | As needed | English mirror (served via `?lang=en`) |
| S-2.1, r. 4 | FR | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%204 | Annual | Safety code sections referenced by CSA |
| S-2.1, r. 4 | EN | https://www.legisquebec.gouv.qc.ca/fr/document/rc/S-2.1,%20r.%204?lang=en | Annual | English mirror (served via `?lang=en`) |

## Licensing / Terms of Use
- Respect the [LegisQuébec usage policy](https://www.legisquebec.gouv.qc.ca/fr/aide/conditions-d-utilisation): automated harvesting must not overload services; attribution to Éditeur officiel du Québec is required.
- Annex PDFs may include third-party materials—store locally for analysis only and avoid public redistribution without additional clearance.
- Honour `robots.txt` directives and throttle batch ingestion (Phase 1 target <= 1 request/sec).

## Next Steps
- Finalize the table above with additional instruments (at least 5 FR + 5 EN).
- Confirm update cadence and throttle recommendations with product stakeholders.
- Expand manifest (`docs/corpus/example_phase1.json`) with the finalized instrument list.
- Use this scope when creating the Phase 1 ingest runs (tracked in `logs/ingestion/`).
