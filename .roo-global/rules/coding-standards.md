# Global Coding Standards

Purpose
Provide repository-wide defaults derived from [RULES.md](RULES.md) and [PLAN.md](PLAN.md). These apply across languages with priority on Python.

Languages
- Primary: Python 3.10+ for CLI and data processing.
- Secondary: Shell/TypeScript as needed for tooling, tests, or docs.

Naming conventions
- Modules, packages: snake_case.
- Variables, functions: snake_case; descriptive, avoid abbreviations.
- Classes: PascalCase.
- Constants: UPPER_SNAKE_CASE.
- CLI flags: kebab-case (e.g., --out-dir).

Dependencies
- Prefer standard library; add third-party only with clear benefit.
- Python parsing: BeautifulSoup with "lxml". HTTP: requests.
- PDF→Markdown enrichment: marker (if available).
- Degrade gracefully when optional tools are absent; warn, do not fail entire run.

Errors and Logging
- Isolate side effects (IO, network, subprocess).
- Fail soft for enrichment: log [WARN] and continue.
- Use stdout for progress: [INFO] message; stderr for warnings: [WARN] message.
- Use explicit timeouts for all network requests.
- Keep functions small and focused; return early on invalid inputs.

Security
- Respect robots.txt and site terms for crawling.
- Cache downloads; implement reasonable backoff and user-agent control.
- Avoid committing large binaries; treat outputs as artifacts.
- Preserve provenance: record source URLs and timestamps where applicable.

Commits and Reviews
- One topic per commit; imperative mood: "Add", "Fix", "Refactor".
- Reference issues/milestones. Keep diffs minimal and coherent.
- Prefer small PRs with clear descriptions and test coverage notes.