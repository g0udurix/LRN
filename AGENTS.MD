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
```
Flags allow opt-outs: `--no-annex-pdf-to-md`, `--no-history-sidecars`, etc. Prefer virtual environments and log new tooling in the issue before committing.

## Coding Style & Naming Conventions
Follow PEP 8 with four-space indentation, descriptive names, and type hints where feasible. Keep functions tight, add short comments only for non-obvious logic, and persist UTF-8 text files. Branches use `type/short-topic` (e.g., `feat/history-crawl`). Avoid bulk reformatting—touch only files required for the issue.

## Testing Guidelines
`pytest` is the testing framework. Name tests `test_<behavior>` and keep fixtures beside consumers. Pair each new behavior or bug fix with a regression test. Annex/history modules already have unit suites; extend them when behaviour changes. When touching annex or history handling, place representative HTML/PDF samples under a fixture subfolder in `tests/` and clear temporary artifacts in teardown helpers.

CI (`.github/workflows/ci.yml`) runs `python -m pytest -q` on Python 3.10 and 3.11.

## GitHub Workflow Integration
Track work through GitHub issues and milestones—use `gh issue list` to confirm ownership before starting. Synchronize labeling with repository defaults via `python runner.py --apply --self-test` or `gh label list`. Draft feature branches with `gh repo clone` and open reviews using `gh pr create --title "feat: …" --fill`. Monitor CI in the GitHub Actions tab or run `gh run watch` after pushing.

## Commit & Pull Request Guidelines
Commits and PR titles must follow Conventional Commits (`feat`, `fix`, `docs`, etc.). Reference the linked issue in both the commit body (when helpful) and the PR description, and state when the change was prepared by an AI agent. Complete the PR template, add `status/*`, `priority/*`, and `area/*` labels, and document a concise test plan (commands or data inspected). Run local checks before requesting review and update `CHANGELOG.md` for user-visible changes.

## Security & Data Handling
Never commit credentials or raw scraped data that violates source terms. Use `PROJECTS_PAT` only within GitHub secrets as documented in `runner.py`, and document any new environment variables in the PR.
