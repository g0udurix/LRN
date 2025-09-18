# Issue: Ville de Québec Façade Safety By-law (R.V.Q. 1272)

## Summary
The Ville de Québec "Charte et règlements" portal serves a branded 404 template
when accessed programmatically. The façade safety by-law (R.V.Q. 1272) is
accessible via browser rendering, but scripted requests from `requests` fail
with HTTP 404, preventing direct ingestion.

## Current Workaround
1. Launch a headless Chromium session with `scripts/headless_fetch.py` while
   targeting `https://www.ville.quebec.qc.ca/apropos/charte-reglements/reglements/reglement.aspx?id=2822`.
2. Write the rendered HTML to
   `output_quebec_city/QUE_Reglement_RVQ_1272_Facades/fr.html` (or equivalent),
   then rerun `python scripts/corpus_ingest.py --manifest docs/corpus/manifests/quebec_city.json --resume`.
3. Archive the captured HTML outside the repository for diffing and historical
   tracking; the manifest entry now logs a checksum even though the network fetch
   is skipped.

## Next Steps
- Investigate whether the city exposes a PDF download or open-data dataset for
  R.V.Q. 1272 to replace the dynamic HTML.
- Determine if the portal allows authenticated access tokens; if so, document
  the workflow and update ingestion scripts accordingly.
- Capture bilingual requirements (if any) once a stable endpoint is secured.
