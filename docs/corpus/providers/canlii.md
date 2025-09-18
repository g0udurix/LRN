# CanLII API Integration

CanLII (https://www.canlii.org/) exposes a REST API for primary law across Canadian jurisdictions. Access requires an API key provided by CanLII; set it locally (not committed) before running ingestion jobs:

```bash
set -a && source .env && set +a  # load secrets locally
export CANLII_API_KEY="<your-key>"
```

## Useful endpoints
- `https://api.canlii.org/v1/legislationBrowse/{lang}/{jurisdiction}` lists available statutes/regulations.
- `https://api.canlii.org/v1/legislationTopic/{lang}/{jurisdiction}/{legisId}` fetches metadata for a given work.
- `https://api.canlii.org/v1/legislation/{lang}/{jurisdiction}/{legisId}/{path}` retrieves consolidated text (`?resultFormat=xml|html|text`).

All requests require the header `X-API-Key: $CANLII_API_KEY` and optionally `Accept: application/json`.

## Rate & Access Limits
- 5,000 requests per day.
- 2 requests per second (single concurrent request).
- Responses provide **metadata only** (titles, citations, consolidation dates, URLs); the API does **not** return statute/bylaw text.
- Access to the underlying content must be sourced separately (e.g., provincial Queen’s Printer, municipal portals).
- The public HTML endpoints (`www.canlii.org`) are protected by DataDome. Use
  `scripts/headless_fetch.py` (requires Playwright: `pip install playwright`
  then `playwright install chromium`) to capture the rendered HTML when 403
  responses appear, then rerun ingestion with `--resume` so logging completes
  without re-triggering the block.

Violating these limits can result in throttling; CanLII does not extend quotas or grant text access.

## Health & Safety Targets
- Québec (QC): Occupational Health and Safety Act (`ohsa`), Safety Code for the construction industry, window-cleaning safety regulations.
- Ontario (ON): OHSA, Reg. 213/91, Reg. 851/90, Reg. 859/90.
- Federal (CA): Canada Labour Code Part II, Canada Occupational Health and Safety Regulations.
- Municipal (where available in metadata): Montréal façade maintenance (Règlement 15-096) and Ville de Québec façade safety bylaw.
- Additional coverage: British Columbia (Workers Compensation Act / OHS Reg), Alberta (OHS Act/Reg/Code), New Brunswick (OHS Act / Reg 91-191), Saskatchewan and Manitoba equivalents.
- Expected scope: CanLII surfaces statutes and regulations for every province and territory (AB, BC, MB, NB, NL, NS, NT, NU, ON, PE, QC, SK, YK) plus federal instruments. Municipal coverage is selective—major cities such as Montréal and Québec have metadata listings, while others (Toronto, Calgary, Vancouver) may rely on provincial repositories. Verify availability before relying on the API for municipal bylaws.

### Sample lookups
- Québec statutes (`qcs`): `python scripts/canlii_metadata.py qc --database qcs --match "occupational health" --raw` ⇒ `legislationId` `cqlr-c-s-2.1` (Act respecting occupational health and safety).
- Québec regulations (`qcr`): `python scripts/canlii_metadata.py qc --database qcr --match "construction safety" --raw` ⇒ `legislationId` `cqlr-c-s-2.1-r-4` (Safety Code for the Construction Industry).
- Ontario regulations (`onr`): `python scripts/canlii_metadata.py on --database onr --match "Window Cleaning" --raw` ⇒ `legislationId` `rro-1990-reg-859` (Window Cleaning Regulation).
- British Columbia statutes (`bcs`): `python scripts/canlii_metadata.py bc --database bcs --match "workers compensation" --raw` ⇒ `legislationId` `rsbc-2019-c-1` (Workers Compensation Act 2019 consolidation).
- British Columbia regulations (`bcr`): `python scripts/canlii_metadata.py bc --database bcr --match "occupational health" --raw` ⇒ `legislationId` `bc-reg-296-97` (Occupational Health and Safety Regulation).
- Alberta regulations (`abr`): `python scripts/canlii_metadata.py ab --database abr --match "occupational health and safety" --raw` ⇒ `legislationId` `alta-reg-191-2021` (Occupational Health and Safety Code) and `alta-reg-184-2021` (OHS Regulation).
- New Brunswick regulations (`nbr`): use a broader export then filter for citation `NB Reg 91-191`; e.g. `python scripts/canlii_metadata.py nb --database nbr --match "General" --raw --out logs/canlii_nb_general.json` and isolate `legislationId` `nb-reg-91-191` for the OHS General Regulation.
- Manitoba statutes/regulations (`mbs`/`mbr`): `python scripts/canlii_metadata.py mb --database mbs --match "Workplace Safety and Health" --raw` ⇒ `legislationId` `ccsm-c-w210`; pair with `python scripts/canlii_metadata.py mb --database mbr --match "Workplace Safety" --raw` ⇒ `legislationId` `man-reg-217-2006` (Workplace Safety and Health Regulation).
- Saskatchewan statutes/regulations (`sks`/`skr`): `python scripts/canlii_metadata.py sk --database sks --match "Occupational Health" --raw` ⇒ `legislationId` `ss-1993-c-o-1.1`; `python scripts/canlii_metadata.py sk --database skr --match "Occupational Health and Safety Regulations" --raw` ⇒ `legislationId` `rrs-c-o-1.1-reg-1`.
- Federal regulations (`car`): `python scripts/canlii_metadata.py ca --database car --match "Occupational Health and Safety" --raw` ⇒ `legislationId` `sor-86-304` (Canada Occupational Health and Safety Regulations) plus transport/offshore sector variants (SOR/2011-87, SOR/2010-120, etc.).

## Next Steps
1. Map each priority instrument to its `legisId` and `path` (see `legislationBrowse` payloads).
2. Use `python scripts/canlii_metadata.py <jurisdiction>` to export metadata snapshots for curation.
3. Record CanLII metadata inside manifests or sidecars while continuing to download full texts from authoritative sources.
3. Extend ingestion runners to persist CanLII metadata (citation, consolidation date, official URL) for traceability.
4. Monitor rate limits; batch requests with backoff to stay within terms of use.

## Testing
Use the sandbox fixtures first. When hitting the live API, the CLI automatically attaches the `X-API-Key` header when `CANLII_API_KEY` is present.
