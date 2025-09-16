# LRN Extractor

Command-line tools for turning LegisQuébec HTML into clean XHTML fragments, annex Markdown sidecars, and history snapshots ready for downstream analysis.

## What It Does
- mirrors LegisQuébec landing pages (`Legisquebec originals/`) and extracts inner XHTML into `output/<instrument>/current.xhtml`.
- converts annex PDFs to GitHub-flavoured Markdown (via `marker`) and links the result back into the XHTML copy.
- crawls fragment history links and saves dated snapshots under `output/<instrument>/history/` with an accompanying `index.json`.
- operates fully offline with recorded fixtures so development and CI runs never touch production systems.

## Quick Start
```bash
python -m lrn.cli extract --out-dir output path/to/local.html
```
Common flags:
- `--base-url`: resolve relative URLs when you are running against downloaded mirrors.
- `--annex-pdf-to-md/--no-annex-pdf-to-md`: enable or skip PDF → Markdown conversion.
- `--history-sidecars/--no-history-sidecars`: control history crawling.
- `--history-cache-dir`: reuse cached HTML during tests.

The default invocation (`python -m lrn.cli`) runs the “fetch all” workflow: it discovers FR/EN RC links, mirrors the pages locally, then extracts, converts annexes, and crawls history in one go.

## Development
- Keep regenerated artifacts out of git. The `.gitignore` already excludes `Legisquebec originals/`, `output/`, and logs.
- Run tests with `python -m pytest`. Offline fixtures cover bilingual extraction, annex conversion stubs, and history crawling.
- `pyproject.toml` configures pytest to find the `lrn` package without installation; `sitecustomize.py` injects the repo root into `sys.path`.

## Troubleshooting
- If annex conversion fails, the CLI logs a warning and leaves the PDF in place.
- History crawling falls back to the history-link URL when intermediate listing pages are unavailable (useful for offline tests).
- For noisy BeautifulSoup XML warnings during tests, installing `lxml` or filtering the warning will silence them.

## Roadmap & Issues
Active work and triage live on [Project 3](https://github.com/users/g0udurix/projects/3). Phase 0 tasks (#11–#19) track modularization, annex hardening, bilingual coverage, CI, and documentation refresh.
