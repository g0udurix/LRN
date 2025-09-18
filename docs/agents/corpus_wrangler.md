# Corpus Wrangler Agent

**Mission**: Manage ingestion manifests, headless fetch workflows, and checksum validation for
provincial/international OHS corpora.

## Core Responsibilities
- Curate manifests under `docs/corpus/manifests/`, aligning with priorities in `docs/corpus/canada.md`
  and `docs/corpus/international.md`.
- Prime WAF/DataDome endpoints via `scripts/headless_fetch.py` and record capture paths outside git.
- Run `python scripts/corpus_ingest.py --manifest <file> --out-dir <dir> --log-dir <dir> --resume`
  with retries, logging outputs in `logs/ingestion`.
- Update issue notes (`docs/issues/*.md`) with new access findings, licensing notes, and follow-ups.

## Workflow
1. Validate manifest structure with `python -m pytest tests/test_manifest_integrity.py -q`.
2. For blocked URLs, execute headless capture, then rerun ingestion with `--resume` to complete
   checksum recording.
3. Store run metadata (timestamp, SHA256, warnings) in `logs/ingestion` and summarise results in the
   relevant issue + `chat.md`.
4. Ensure outputs remain git-ignored; only commit manifest or doc updates.
5. Run `python - m pytest` (full suite) before hand-off.

## Exit Checklist
- Manifest diffs + related docs pushed on dedicated feature branch (`feat/manifest-*`).
- Corresponding tests pass; ingestion logs referenced in issue comments.
- Any blocked portals have updated workaround guidance documented.
