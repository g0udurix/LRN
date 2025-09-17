# LRN Extractor

Command-line tools for turning LegisQuébec HTML into clean XHTML fragments, annex Markdown sidecars, and history snapshots ready for downstream analysis.

## What It Does
- mirrors LegisQuébec landing pages (`Legisquebec originals/`) and extracts inner XHTML into `output/<instrument>/current.xhtml`.
- converts annex PDFs to GitHub-flavoured Markdown (via `marker`) and links the result back into the XHTML copy.
- crawls fragment history links and saves dated snapshots under `output/<instrument>/history/` with an accompanying `index.json`.
- operates fully offline with recorded fixtures so development and CI runs never touch production systems.

### Module Map
- `lrn/extract.py` — pure fragment loader (`load_fragment`) and instrument detection heuristics.
- `lrn/annex.py` — annex download + conversion pipeline with retries, size caps, and YAML provenance.
- `lrn/history.py` — history discovery, optional snapshotting, and HTML injection helpers.
- `lrn/cli.py` — orchestrates the modules and exposes the `extract` subcommand / fetch-all entrypoint.

## Quick Start
```bash
python -m lrn.cli extract --out-dir output path/to/local.html
# Prepare a manifest for batch ingestion (Phase 1 scaffold)
python scripts/corpus_ingest.py --manifest docs/corpus/example_phase1.json --out-dir logs/ingestion/demo
```
Common flags:
- `--base-url`: resolve relative URLs when you are running against downloaded mirrors.
- `--annex-pdf-to-md/--no-annex-pdf-to-md`: enable or skip PDF → Markdown conversion.
- `--history-sidecars/--no-history-sidecars`: control history crawling.
- `--history-cache-dir`: reuse cached HTML during tests.

The default invocation (`python -m lrn.cli`) runs the “fetch all” workflow: it discovers FR/EN RC links, mirrors the pages locally, then extracts, converts annexes, and crawls history in one go.

## Development
- Keep regenerated artifacts out of git. The `.gitignore` already excludes `Legisquebec originals/`, `output/`, and logs.
- Install test deps with `pip install beautifulsoup4 lxml requests pytest`.
- Run tests with `python -m pytest`. Fixtures cover bilingual extraction, annex conversion stubs, and history crawling (success/failure).
- CI (`.github/workflows/ci.yml`) runs pytest on Python 3.10 and 3.11 with pip caching.
- `pyproject.toml` configures pytest discovery; `sitecustomize.py` injects the repo root into `sys.path` for local runs.
- Standards helpers (`lrn/standards`) provide `validate_mapping_file`; run via `python -m lrn.standards validate docs/standards/examples/sample.json`.

## Troubleshooting
- If annex conversion fails, the CLI logs a warning and leaves the PDF in place.
- History crawling falls back to the history-link URL when intermediate listing pages are unavailable (useful for offline tests).
- For noisy BeautifulSoup XML warnings during tests, installing `lxml` or filtering the warning will silence them.

## Roadmap & Issues
Active work and triage live on [Project 3](https://github.com/users/g0udurix/projects/3). Phase 1 (Corpus & Standards) issues include:

- #20 Corpus scope & licensing notes
- #21 Batch ingestion command + metadata manifests
- #22 Standards mapping schema & types
- #23 Regression tests for ingestion and standards validation
- #24 Documentation refresh for corpus/standards workflows
- #27–#30 Provincial ingestion pilots (NB, ON, AB, BC)
- #31 OSHA 1910/1926 prototype
- #32–#33 UK & France ingestion planning
