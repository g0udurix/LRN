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

## Municipal Façade / Window-Cleaning Bylaws

| Municipality | Portal | Format Notes | Automation Considerations | Manifest |
|--------------|--------|--------------|---------------------------|----------|
| Montréal | https://ville.montreal.qc.ca/pls/portal/docs/page/cons_pub_fr/media/documents/15-096.pdf | PDF (FR) | Stable direct download; archive outside repo | `docs/corpus/manifests/montreal.json` |
| Ville de Québec | https://www.ville.quebec.qc.ca/apropos/charte-reglements/reglements/reglement.aspx?id=2822 | HTML (dynamic) | Returns 404 template to bots; use `scripts/headless_fetch.py` then ingest with `--resume` | `docs/corpus/manifests/quebec_city.json` |
| Toronto | https://www.toronto.ca/ | PDF (EN) | Consolidated Municipal Code PDFs (Ch. 363/629) | `docs/corpus/manifests/toronto.json` |
| Vancouver | https://bylaws.vancouver.ca/ | PDF (EN) | Direct consolidated PDF for Part 10 | `docs/corpus/manifests/vancouver.json` |
| Calgary | https://www.calgary.ca/ | HTML via CanLII | City PDF still 404; manifest targets CanLII consolidation (requires headless fetch) | `docs/corpus/manifests/calgary.json` |

## Targeted OHS Instruments
- **New Brunswick:** Occupational Health and Safety Act (O-0.5); General Regulation 91-191 (Part VII & VIII cover fall protection, suspended staging, and rope descent for window cleaning).
- **Ontario:** Occupational Health and Safety Act (R.S.O. 1990, c. O.1); Regulation 213/91 (Construction Projects, incl. Subsection 26 – Fall Protection); Regulation 851/90 (Industrial Establishments, Guardrails & aerial devices).
- **Alberta:** Occupational Health and Safety Act (SA 2017, c. O-2.1); Occupational Health and Safety Regulation (AR 183/2021); Occupational Health and Safety Code (March 31, 2025 consolidation) Parts 8–10 (elevating work platforms, scaffolds, swing stages, window cleaning safety) — all available through the open.alberta.ca datasets with direct Kings Printer downloads.
- **British Columbia:** Workers Compensation Act (Part 2 & 3); Occupational Health and Safety Regulation (BC Reg 296/97) Parts 11, 13, and 34 (fall protection, ladders/scaffolds, rope access & window cleaning).
- **Manitoba:** Workplace Safety and Health Act (CCSM c W210); Workplace Safety and Health Regulation (Man Reg 217/2006) covering fall protection, scaffolding, and window cleaning operations.
- **Saskatchewan:** The Saskatchewan Employment Act (S-15.1) Parts II & III; Occupational Health and Safety Regulations, 2020 (S-15.1 Reg 10) including rope access and suspended platform provisions.
- **Nova Scotia:** Occupational Health and Safety Act; OHS General Regulations and OHS Fall Protection Regulations (Part 21) for suspended stage/window cleaning controls.
- **Newfoundland & Labrador:** Occupational Health and Safety Act; Occupational Health and Safety Regulations, 2012 (parts addressing fall protection, window cleaning, suspended work platforms).
- **Prince Edward Island:** Occupational Health and Safety Act; General Regulations (EC180/87) regulating fall protection and window cleaning (see `docs/corpus/manifests/pe.json`).
- **Northwest Territories:** Safety Act (accessible via GNWT Justice); OHS Regulations (2015) currently unavailable through public download endpoints—see `docs/issues/nt-regs-access.md`.
- **Yukon:** Occupational Health and Safety Act and Regulations are gated behind Cloudflare challenges (`docs/issues/yk-cloudflare-block.md`).
- **Nunavut:** Safety Act and OHS Regulations pages return 404 for automated clients (`docs/issues/nu-legislation-access.md`).
- **Canada (Federal):** Canada Labour Code Part II; Canada Occupational Health and Safety Regulations (SOR/86-304) plus sector OHS regulations (aviation, maritime, rail, offshore).

### Fall Protection & Window Cleaning Focus
- **Ontario (Window Cleaning):** Regulation 859/90 (Window Cleaning) (English & French consolidated texts) — prioritize ingestion for high-rise maintenance procedures and fall arrest anchors. See `docs/corpus/manifests/on.json` for ready-to-run endpoints.
- **British Columbia (Window Cleaning):** WorkSafeBC OHS Regulation Part 34.11–34.17 (rope access) and associated guidelines for building maintenance; confirm if separate ministerial orders require mirroring. `docs/corpus/manifests/bc.json` includes the Workers Compensation Act, OHS Regulation, and elevating devices regulation.
- **New Brunswick (Municipal bylaws):** Survey Saint John, Fredericton, Moncton bylaws for supplementary fall protection and exterior maintenance requirements linked to 91-191 enforcement.
- **Ontario (Municipal bylaws):** Toronto Municipal Code Chapter 363 (Construction & Demolition) and Chapter 629 (Property Standards) reference window cleaning safety plans—verify citations and collect authoritative PDFs where available. `docs/corpus/manifests/toronto.json` captures the current consolidated PDFs.
- **Québec (Montréal):** Règlement 15-096 sur l'entretien des façades (direct PDF) and CNESST rope-access bulletins; `docs/corpus/manifests/montreal.json` now mirrors the authoritative download. `docs/issues/montreal-facade-15096.md` tracks historical access problems.
- **Québec (Ville de Québec):** Règlement municipal sur l'entretien et la sécurité des façades (R.V.Q. 1272) served via a dynamic ASP.NET portal—use `scripts/headless_fetch.py` to capture the HTML, then rerun `corpus_ingest.py --resume` against `docs/corpus/manifests/quebec_city.json`.
- **British Columbia (Vancouver):** Vancouver Building By-law 2019 (Book I, Part 10) and associated Safety Standards Board directives governing permanent façade access (BMU) and rope descent for window cleaning. `docs/corpus/manifests/vancouver.json` points to the consolidated Part 10 PDF.
- **Alberta (Calgary):** Building Maintenance Bylaw 33M2014 (façade/fall protection) and related Occupational Health & Safety inspection bulletins—coordinate with provincial OHS code for swing stage operations; track city-hosted PDF location for manifest integration.
- **Québec (Ville de Québec):** Règlement municipal sur l'entretien et la sécurité des façades (confirm current R.V.Q. numbering via the Charte et règlements portal). Identify a stable `ville.quebec.qc.ca` download endpoint—portal result pages return 404 status codes despite HTML payloads, so build a scraper that follows their POST-backed search API before adding manifests.
- **Manitoba (Fall protection & rope access):** Workplace Safety and Health Regulation Part 14 (Fall Protection) and Part 22 (Powered Mobile Equipment); see `docs/corpus/manifests/mb.json` for canonical URLs.
- **Saskatchewan (OHS 2020 update):** Part III of The Saskatchewan Employment Act and Sections 214–231 of the OHS Regulations, 2020 address fall protection/suspended platforms; sources captured in `docs/corpus/manifests/sk.json`.
- **Nova Scotia:** OHS General Regulations Part 21 and Fall Protection Regulations cover rope access and window cleaning. Refer to `docs/corpus/manifests/ns.json` for authoritative links. Note: direct HTTPS requests to `novascotia.ca/just/regulations` currently return legacy 404 templates; manual retrieval (browser + download) or an authenticated scraper may be required until a stable static location is confirmed (tracked in `logs/update_states/ns.json`).
- **Newfoundland & Labrador:** OHS Regulations, 2012 Part X (Fall Protection) and Part XII (Aerial Devices, Scaffolds and Scaffolding); manifests in `docs/corpus/manifests/nl.json`. The House of Assembly site currently serves JS-driven error pages to non-browser clients; capture downloads manually or update the manifest with a stable PDF endpoint once identified (see `logs/update_states/nl.json`).
- **Canada (Federal):** Canada Occupational Health and Safety Regulations Part XII (Safety Materials, Equipment, Devices and Clothing) and sector-specific regs—`docs/corpus/manifests/ca.json` offsets downloads from Justice Laws.
- **CanLII fallback:** Leverage the CanLII API for consolidated provincial statutes (OHS Act, Construction Safety Code, window-cleaning regulations). Requires `CANLII_API_KEY`; see `docs/corpus/providers/canlii.md` for endpoint mapping before generating manifests.
- **CanLII limits:** API responses surface metadata only (no statute text). Use `python scripts/canlii_metadata.py <jurisdiction>` to confirm citations/consolidation dates, then fetch the full text from the authoritative provincial or municipal source before ingestion. Example commands captured in `docs/corpus/providers/canlii.md` (e.g., QC `cqlr-c-s-2.1`, BC `bc-reg-296-97`, AB `alta-reg-191-2021`, NB `nb-reg-91-191`, MB `man-reg-217-2006`, SK `rrs-c-o-1.1-reg-1`, federal `sor-86-304`). Pair this with `python scripts/monitor_updates.py --manifest <manifest> --archive-dir <path> --state logs/update_states/<manifest>.json` to detect content changes and maintain local historical copies outside the repository. When automated requests hit DataDome (HTTP 403) on CanLII or Ville de Québec, prime the target with `scripts/headless_fetch.py --out <expected-path>` and rerun ingestion with `--resume` so checksum logging succeeds without re-triggering the block.
- **National Standards:** Cross-reference CSA Z91 (Health & Safety Code for Suspended Equipment Operations) and CSA Z271 (Elevating Work Platforms) to flag derivative provincial requirements.
