# Issue: Montréal Règlement 15-096 Access (Resolved)

## Summary
A stable PDF endpoint is now available for Règlement 15-096 sur l'entretien des
façades (`https://ville.montreal.qc.ca/pls/portal/docs/page/cons_pub_fr/media/documents/15-096.pdf`).
The manifest `docs/corpus/manifests/montreal.json` mirrors this URL and
`docs/corpus/canada.md` references the workflow.

## Follow-up
1. Monitor the PDF for revisions with `scripts/monitor_updates.py --manifest docs/corpus/manifests/montreal.json --archive-dir "$HOME/lrn-archives/montreal"`.
2. Keep the archived copies outside the repository to avoid committing city
   documents.
