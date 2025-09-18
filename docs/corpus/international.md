# International Legislative Portals

The following jurisdictions are candidates for future corpus expansions beyond Canada.

| Jurisdiction | Portal | Format Notes | Licensing / Usage | Ingestion Risks |
|--------------|--------|--------------|--------------------|-----------------|
| United States (Federal) | https://www.congress.gov/ (statutes), https://www.ecfr.gov/ (CFR), https://www.govinfo.gov/ (official XML/PDF) | HTML/PDF/XML | Public domain (US GOV) | Large volume, CloudFront “unblock” challenge for HTML |
| United Kingdom | https://www.legislation.gov.uk/ | HTML/XML | Open Government Licence | Robust API available |
| France | https://www.legifrance.gouv.fr/ | HTML/PDF | Conditions of use require attribution | Strong anti-bot measures (DataDome 403) |
| Australia | https://www.legislation.gov.au/ | HTML/XML | Creative Commons Attribution 4.0 | Comprehensive APIs |
| Germany | https://www.gesetze-im-internet.de/ | HTML | Licensed by juris GmbH; reuse conditions apply | German-only text; observe reuse clauses |
| Japan | https://laws.e-gov.go.jp/ | HTML (SPA) | Usage restrictions on bulk download | Single-page app; requires headless capture + translation |
| China | http://www.npc.gov.cn/ | HTML | PRC copyright; English translations partial | WAF redirects, inconsistent availability |

**Notes:** Prioritize UK, Australia, EU, and OSHA (robust APIs/licensing) before
tackling portals with heavier access controls (Legifrance, CanLII mirrors,
Germany, Japan SPA, PRC WAF). For DataDome or SPA-backed sites, archive with
`scripts/headless_fetch.py` then rerun ingestion with `--resume` to log
checksums.

## Targeted OHS Instruments
- **United States:** 29 CFR Part 1910 (General Industry); 29 CFR Part 1926 (Construction). Manifest: `docs/corpus/manifests/osha.json` (govinfo XML).
- **United Kingdom:** Health and Safety at Work etc. Act 1974; Management of Health and Safety at Work Regulations 1999.
- **France:** Code du travail (notably Livre IV – Santé et sécurité au travail).
- **Germany:** Arbeitsschutzgesetz (ArbSchG) and Betriebssicherheitsverordnung (BetrSichV). Manifest: `docs/corpus/manifests/germany.json`.
- **Japan:** Industrial Safety and Health Act and Industrial Safety and Health Ordinance (rope descent, scaffolding). Manifest: `docs/corpus/manifests/japan.json` (requires headless capture).
- **China:** Work Safety Law of the People’s Republic of China (Chapter V). Manifest: `docs/corpus/manifests/china.json`; additional sector rules pending stable sources.
- **Brazil:** NR-35 Trabalho em Altura (docs/corpus/manifests/brazil.json).
- **Mexico:** NOM-009-STPS-2011 (docs/corpus/manifests/mexico.json).
- **Spain:** Real Decreto 1627/1997 (docs/corpus/manifests/spain.json).
- **Portugal:** Lei n.º 102/2009 (docs/corpus/manifests/portugal.json).
- **Netherlands:** Working Conditions Act & Decree (docs/corpus/manifests/netherlands.json).
- **Sweden:** AFS 2006:4 Work at Height (docs/corpus/manifests/sweden.json).
- **Norway:** Workplace Regulations (docs/corpus/manifests/norway.json).
- **Finland:** Occupational Safety and Health Act (docs/corpus/manifests/finland.json).
- **Scandinavia (regional):** Nordic Safe Work at Height guidance (docs/corpus/manifests/scandinavia.json).
- **New Zealand:** Health and Safety at Work Act 2015 (docs/corpus/manifests/new_zealand.json).
- **South Korea:** Occupational Safety and Health Act (docs/corpus/manifests/south_korea.json).
- **Singapore:** Workplace Safety and Health Act (docs/corpus/manifests/singapore.json).
- **South Africa:** Occupational Health and Safety Act (docs/corpus/manifests/south_africa.json).
- **Morocco:** Code du Travail provisions on safety (docs/corpus/manifests/morocco.json).
- **Nigeria:** Factories Act (docs/corpus/manifests/nigeria.json).
- **Egypt:** Labour Law No. 12/2003 safety chapters (docs/corpus/manifests/egypt.json).
- **India:** Occupational Safety, Health and Working Conditions Code 2020 (docs/corpus/manifests/india.json).
- **Thailand:** Occupational Safety, Health and Environment Act 2011 (docs/corpus/manifests/thailand.json).
- **United Arab Emirates:** Federal Decree-Law 33/2021 (docs/corpus/manifests/uae.json).
- **Qatar:** Labour Law No. 14 of 2004 (docs/corpus/manifests/qatar.json).
- **Dubai:** Code of Construction Safety Practice (docs/corpus/manifests/dubai.json).
- **Italy:** Decreto Legislativo 81/2008 (docs/corpus/manifests/italy.json).
- **Greece:** Law 3850/2010 (docs/corpus/manifests/greece.json).
- **Romania:** Law 319/2006 (docs/corpus/manifests/romania.json).
- **Turkey:** Occupational Health and Safety Law 6331 (docs/corpus/manifests/turkey.json).
- **Israel:** Safety at Work Regulations (docs/corpus/manifests/israel.json).
- **Saudi Arabia:** Occupational Safety and Health provisions (docs/corpus/manifests/saudi_arabia.json).
- **Iran:** Labour Law safety chapters (docs/corpus/manifests/iran.json).
- **Lebanon:** Labour Code safety provisions (docs/corpus/manifests/lebanon.json).
- **Argentina:** Law 19.587 (docs/corpus/manifests/argentina.json).
- **Chile:** Decreto Supremo 594/1999 (docs/corpus/manifests/chile.json).
- **Colombia:** Resolution 1409/2012 (docs/corpus/manifests/colombia.json).
- **Peru:** DS 005-2012-TR (docs/corpus/manifests/peru.json).
- **Jamaica:** Occupational Safety and Health Bill 2017 (docs/corpus/manifests/jamaica.json).
- **Dominican Republic:** Law 87-01 safety chapters (docs/corpus/manifests/dominican_republic.json).
- **Cuba:** Decreto-Ley 146/2014 (docs/corpus/manifests/cuba.json).
- **Trinidad and Tobago:** OSH Act 2004 (docs/corpus/manifests/trinidad_and_tobago.json).
- **Barbados:** Safety and Health at Work Act 2005 (docs/corpus/manifests/barbados.json).

### Fall Protection & Window Cleaning Focus
- **United States:** 29 CFR 1910 Subpart D (Walking-Working Surfaces) — §§1910.27 & 1910.28 cover rope descent systems and duty to provide fall protection for window cleaners; 29 CFR 1926 Subpart M (Fall Protection) for construction-led exterior maintenance. Federal corpus manifest: `docs/corpus/manifests/osha.json`.
- **United States (State focus):** California Code of Regulations, Title 8 §1665–1671.1 (Fall Protection), §3282 (Powered Platforms and Equipment for Building Maintenance) and California Labor Code §7321–7332 (Window Cleaning Regulation) — confirm availability via `https://www.dir.ca.gov/Title8/` HTML endpoints; scaffold captured in `docs/corpus/manifests/california.json`.
- **United Kingdom:** Work at Height Regulations 2005 (SI 2005/735) with HSE guidance for rope access/window cleaning; consider Construction (Design and Management) Regulations 2015 for high-rise façade work planning.
- **France:** Code du travail Book IV, Title IV (travail en hauteur) and Arrêté du 1er août 2011 (utilisation des équipements de travail mobiles). `docs/corpus/manifests/france.json` mirrors both entries; use the headless fallback to satisfy the DataDome challenge noted in `docs/issues/france-legifrance-block.md`.
- **Australia:** Model Work Health and Safety Regulations Chapter 4 (Hazardous Work) and Safe Work Australia Code of Practice for managing risks of falls; `docs/corpus/manifests/australia.json` provides direct downloads from legislation.gov.au.
- **European Union:** Directive 2001/45/EC (Work at Height) and Directive 2009/104/EC (use of work equipment by workers). Manifest: `docs/corpus/manifests/eu.json` (EUR-Lex PDF).
- **European Union:** Directive 2001/45/EC (Work at Height) and Directive 2009/104/EC (use of work equipment by workers) — track official EUR-Lex XML feeds for future ingestion.
- **Germany:** ArbSchG §§3–12 (employer duties) and BetrSichV §§3–12 (work equipment, rope access). Use `docs/corpus/manifests/germany.json` and respect juris licensing.
- **Japan:** Industrial Safety and Health Ordinance Chapter 9 (Scaffolds) and Chapter 10 (Suspended Work Platforms). Capture via `scripts/headless_fetch.py` before running `docs/corpus/manifests/japan.json`.
- **China:** Work Safety Law Chapter V (Safety Assurance) and Article 44 (construction fall protection), plus the Regulation on Work Safety of Construction Projects (State Council Order No. 393). Both require the headless fallback to bypass WAF redirects; see `docs/corpus/manifests/china.json` for source URLs.
- **United States (Local bylaws):** New York City Local Law 11/98 (Façade Inspection & Safety Program) and Chicago Municipal Code 13-196-770 et seq. (Exterior Wall Maintenance) intersect with window cleaning rope access—confirm official PDF postings once federal ingestion stabilises. Manifests: `docs/corpus/manifests/nyc.json` (1 RCNY 103-04 PDF) and `docs/corpus/manifests/chicago.json` (AmLegal HTML endpoint).
- **Canada (Cities abroad list cross-ref):** See docs/corpus/canada.md for Montréal, Toronto, Vancouver, and Calgary façade/window-cleaning ordinances aligned with federal/provincial OHS laws.
- **Automation tip:** Run `scripts/headless_fetch.py --out <path>` when DataDome, SPA shells, or WAF redirects block scripted clients (Legifrance, CanLII mirrors, Japan e-Gov, P.R.C. portals). Follow with `corpus_ingest.py --resume` so the manifest logs checksums without repeating the blocked request.
