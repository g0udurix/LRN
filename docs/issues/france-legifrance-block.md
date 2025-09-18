# Issue: Legifrance Blocks Automated Access

## Summary
Requests to Legifrance for the Code du travail (e.g.,
`https://www.legifrance.gouv.fr/codes/texte_lc/LEGITEXT000006072050/`) return HTTP 403
(DataDome challenge). A Playwright-based fallback now captures the HTML after a
short delay, so manifests can include Legifrance endpoints while respecting
robots policies (downloaded artefacts remain outside git).

## Proposed Follow-up
1. Investigate Legifrance APIs or open-data dumps that allow scripted access.
2. Monitor the headless workflow for stability; if DataDome introduces captcha
   challenges, document the manual intervention process.
3. Keep manifests aligned with any licensing notices and archive captures
   outside the repository.
