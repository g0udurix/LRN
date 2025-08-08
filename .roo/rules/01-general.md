# Workspace Rules - General

Source documents:
- Derived from [RULES.md](RULES.md) and [PLAN.md](PLAN.md)

Purpose:
Establish concise, workspace-wide guardrails for development behavior, defaults, and QA for the LRN project.

Core principles
- Deliver a reliable Python CLI extractor for LegisQuébec with verifiable behavior and minimal external coupling.
- Favor robustness over cleverness. When uncertain, keep the source data intact and add outputs additively.

Languages and tools
- Python 3.10+
- CLI: argparse
- Parsing: BeautifulSoup with lxml parser
- HTTP: requests
- PDF to Markdown: marker (available in conda environment)
- Optional OCR stack: ocrmypdf + tesseract (future)
- CI: GitHub Actions

Testing approach
- Prefer behavior-driven tests using pytest.
- Test behavior, not implementation details.
- Coverage focus:
  - Inner XHTML detection
  - Annex PDF processing via marker
  - History link discovery, version enumeration, snapshotting, and index emission
  - CLI flags, defaults, and end-to-end flows
- Use temporary directories and isolated caches for filesystem assertions.

Coding guidelines
- Isolate side effects (IO, network). Inject dependencies where feasible for testability.
- Preserve original XHTML content and metadata; avoid lossy transforms unless guarded by flags.
- Emit clear warnings for recoverable failures (network, marker); do not fail entire run when enrichment fails.
- Keep small, focused modules:
  - lrn/cli.py (entry)
  - lrn/extract.py (planned)
  - lrn/annex.py (planned)
  - lrn/history.py

CLI conventions
- Defaults emphasize preservation and additive enrichment.
- Key flags:
  --out-dir, --base-url
  --annex-pdf-to-md (default on)
  --history-sidecars (default on)
  --history-markdown (default on; future behavior)
  --metadata-exclusion (default empty)
  --ocr (future)

Commit discipline
- Group related changes with concise messages.
- Reference issues and milestones in PRs.

Security and compliance
- Respect robots and site terms for history crawling.
- Cache downloads; use timeouts and reasonable backoff to avoid hammering servers.

Documentation
- README covers setup, usage, flags, and dev workflow.
- Note marker installation and conda env expectations.
- Explain offline test philosophy and network isolation in CI.

Project scope constraints
- Keep original XHTML intact; enrichment is additive.
- Use marker when available; degrade gracefully with warnings if missing.
- Avoid committing large binaries; outputs are artifacts, not source.

Milestones alignment
- M1 Extractor core
- M2 Annex PDF to Markdown enrichment
- M3 History sidecars and index generation

Backlog references
- #1 Extractor core
- #2 Annex PDF→MD
- #3 History sidecars and index
- #4 CLI flags and defaults
- #5 CI pipeline