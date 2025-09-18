# Repository Guidelines

## Project Structure & Module Organization
- `lrn/extract.py` exposes `load_fragment` + instrument detection heuristics.
- `lrn/annex.py` downloads PDFs with retries/caps and converts them to Markdown sidecars.
- `lrn/history.py` discovers history links, snapshots versions, and injects “LRN-Versions” markup.
- `lrn/cli.py` is the orchestrator/entrypoint. Automation helpers sit in `scripts/`, while generated artifacts belong in `output/` and `logs/`. Put tests in `tests/` and mirror each module with `test_<module>.py`. Governance, workflow, and labeling defaults live in the repo root and `.github/`.

## Build, Test, and Development Commands
Use Python 3.10+ from the repo root. Primary commands:
```bash
python -m lrn.cli --out-dir output sample.html  # run the extractor against saved HTML
python -m pytest tests                          # execute unit tests
python runner.py --apply --self-test            # refresh governance defaults and run sanity checks
python scripts/corpus_ingest.py --manifest docs/corpus/example_phase1.json --out-dir output --log-dir logs/ingestion --resume
# Health & safety manifests (examples)
python scripts/corpus_ingest.py --manifest docs/corpus/manifests/nb.json --out-dir output_nb --log-dir logs/ingestion
python scripts/corpus_ingest.py --manifest docs/corpus/manifests/on.json --out-dir output_on --log-dir logs/ingestion
```
Flags allow opt-outs: `--no-annex-pdf-to-md`, `--no-history-sidecars`, etc. Prefer virtual environments and log new tooling in the issue before committing.
403/DataDome responses (e.g., CanLII, Ville de Québec) require priming the
download with `scripts/headless_fetch.py --out <path>` and then rerunning
`corpus_ingest.py --resume` so checksum logging proceeds without another
blocked request. Install Playwright (`python -m pip install playwright &&
playwright install chromium`) before using the headless helper.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, descriptive names, and type hints where feasible. Keep functions tight, add short comments only for non-obvious logic, and persist UTF-8 text files. Branches use `type/short-topic` (e.g., `feat/history-crawl`). Avoid bulk reformatting—touch only files required for the issue.

## Testing Guidelines
`pytest` is the testing framework. Name tests `test_<behavior>` and keep fixtures beside consumers. Pair each new behavior or bug fix with a regression test. Annex/history modules already have unit suites; extend them when behaviour changes. When touching annex or history handling, place representative HTML/PDF samples under a fixture subfolder in `tests/` and clear temporary artifacts in teardown helpers.

CI (`.github/workflows/ci.yml`) runs `python -m pytest -q` on Python 3.10 and 3.11.

## GitHub Workflow Integration
Track work through GitHub issues and milestones—use `gh issue list` to confirm ownership before starting. Synchronize labeling with repository defaults via `python runner.py --apply --self-test` or `gh label list`. Draft feature branches with `gh repo clone` and open reviews using `gh pr create --title "feat: …" --fill`. Monitor CI in the GitHub Actions tab or run `gh run watch` after pushing.

Phase 1 focus (corpus & standards): issues #20–#24 coordinate scope, ingestion, schema, tests, and docs.
Upcoming high-priority ingestion pilots: provincial fall-protection coverage for New Brunswick (#27), Ontario (#28), Alberta (#29), British Columbia (#30); municipal façade/window-cleaning bylaws for Montréal and Ville de Québec; OSHA 1910/1926 (#31); UK Work at Height (#32); France/Legifrance (#33); plus follow-on tracks for Germany, Australia, Japan, and China documented on Project 3.
Window cleaning & fall protection emphasis: Ontario Reg 859/90 (Window Cleaning), BC Elevating Devices Safety Regulation, NYC Local Law 11/98 (1 RCNY 103-04), Calgary Building Maintenance Bylaw 33M2014, Toronto Chapters 363/629, Vancouver Building By-law Part 10, Montréal Règlement 15-096 (direct PDF resolved), Ville de Québec façade safety by-law (requires headless fetch to capture HTML), OSHA Subparts D/M, and EU/UK Work at Height frameworks—log findings in the linked issues before implementation. Provincial/federal manifests now include `ab.json`, `bc.json`, `mb.json`, `nb.json`, `nl.json`, `ns.json`, `on.json`, `pe.json`, `qc.json`, `sk.json`, `nt.json`, `nu.json`, `yk.json`, and `ca.json`, with municipal pilots in `montreal.json`, `quebec_city.json`, `toronto.json`, `vancouver.json`, `calgary.json`. International manifests: `osha.json` (US CFR XML), `uk.json` (legislation.gov.uk XML), `eu.json` (EUR-Lex PDFs), `australia.json` (legislation.gov.au downloads), `germany.json` (ArbSchG/BetrSichV), `japan.json` (e-Gov Industrial Safety & Health), `china.json` (Work Safety Law) and `france.json` (Legifrance). Some portals (Legifrance, CanLII, Ville de Québec, Nova Scotia, NL, NT, NU, YK) still gate scripted clients—`scripts/headless_fetch.py` plus `--resume` ingestion is the recommended workaround; see `docs/corpus/monitoring.md` and docs/issues for follow-up.

CanLII integration: store the private `CANLII_API_KEY` in your shell session or `.env` (never commit). Source it with `set -a && source .env && set +a` before running ingestion—the CLI auto-attaches the header for any `api.canlii.org` manifest entry. Remember the API is metadata-only; run `python scripts/canlii_metadata.py qc --match safety` (or similar) to capture citations, then follow the official URL for the actual statute/bylaw text. Use `python scripts/monitor_updates.py --manifest docs/corpus/manifests/<prov>.json` to archive new versions and refresh checksums outside the repo.

## Commit & Pull Request Guidelines
Commits and PR titles must follow Conventional Commits (`feat`, `fix`, `docs`, etc.). Reference the linked issue in both the commit body (when helpful) and the PR description, and state when the change was prepared by an AI agent. Complete the PR template, add `status/*`, `priority/*`, and `area/*` labels, and document a concise test plan (commands or data inspected). Run local checks before requesting review and update `CHANGELOG.md` for user-visible changes.

## Security & Data Handling
Never commit credentials or raw scraped data that violates source terms. Use `PROJECTS_PAT` only within GitHub secrets as documented in `runner.py`, and document any new environment variables in the PR.
