# Canadian Legislative Portals

This document tracks official legal information sources across Canadian jurisdictions for future ingestion phases.

| Jurisdiction | Portal | Format Notes | Licensing / Usage | Automation Considerations | Priority |
|--------------|--------|--------------|--------------------|---------------------------|----------|
| Canada (Federal) | https://laws-lois.justice.gc.ca/eng/ | HTML/XML (also bilingual) | Crown copyright, open data reuse with attribution | XML dumps, bilingual texts | P2 |
| Alberta | https://www.qp.alberta.ca/ | HTML/PDF | Alberta Queen's Printer requires attribution; check reuse clause | Session cookie + JavaScript redirect; need headless fetch | **P1** |
| British Columbia | https://www.bclaws.gov.bc.ca/ | HTML | Open data terms allow reuse with attribution | Site map & JSON API; straightforward crawling | **P1** |
| Manitoba | https://web2.gov.mb.ca/laws/ | HTML | Licensing TBD | Simple HTML; some PDFs | P3 |
| New Brunswick | https://laws.gnb.ca/en/ | HTML/PDF | Standard terms permit reuse with attribution | Bilingual; HTML structure similar to Québec | **P1** |
| Newfoundland & Labrador | https://www.assembly.nl.ca/Legislation/sr/ | HTML/PDF | Licensing TBD | Index pages require recursion | P3 |
| Nova Scotia | https://nslegislature.ca/legc/ | HTML/PDF | Licensing TBD | Many PDF-only statutes | P3 |
| Ontario | https://www.ontario.ca/laws | HTML/PDF | Open Government Licence – Ontario | REST API available; bilingual where applicable | **P1** |
| Prince Edward Island | https://www.princeedwardisland.ca/en/information/justice-and-public-safety/acts-and-regulations | HTML/PDF | Licensing TBD | Primarily PDF | P3 |
| Québec | https://www.legisquebec.gouv.qc.ca/ | HTML/PDF | Already ingested | Bilingual with annexes | ✓ |
| Saskatchewan | https://www.qp.gov.sk.ca/ | HTML | Licensing TBD; copyright Crown | Requires login for consolidated statutes | P3 |
| Northwest Territories | https://www.justice.gov.nt.ca/en/legislation/ | HTML/PDF | Licensing TBD | Mix of PDF/HTML | P3 |
| Nunavut | https://www.nunavutlegislation.ca/ | HTML/PDF | Licensing TBD | Many PDFs; limited English coverage | P3 |
| Yukon | https://laws.yukon.ca/ | HTML/PDF | Licensing TBD | Simple HTML index | P3 |

**Next Steps:** Confirm licensing for TBD entries and prioritize jurisdictions for Phase 2 ingestion.
