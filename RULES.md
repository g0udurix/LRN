# LRN Development Guidelines

Core principle: deliver a reliable Python CLI extractor for LegisQuébec with verifiable behavior and minimal external coupling.

Languages and tools
- Language: Python 3.10+
- CLI: argparse
- Parsing: BeautifulSoup (lxml parser)
- HTTP: requests
- PDF→Markdown: marker (from your conda env)
- Optional OCR: ocrmypdf + tesseract (future)
- CI: GitHub Actions

Testing approach
- Prefer behavior-driven tests using pytest.
- Test behavior, not implementation details.
- Cover: inner XHTML detection, annex PDF processing via marker, history link discovery/indexing, and CLI flags.
- Use temporary directories for filesystem assertions.

Coding guidelines
- Keep side effects isolated (IO/network), pass dependencies where feasible for testability.
- Preserve original XHTML content and metadata; avoid lossy transforms unless behind explicit flags.
- Add clear logging for warnings (network failures, marker failures), but do not fail the whole run if enrichment fails.
- Small, focused modules: lrn/cli.py (entry), lrn/extract.py, lrn/annex.py, lrn/history.py (to be introduced as project grows).

CLI conventions
- Defaults: keep-all metadata; enable annex PDF→MD and history capture as requested.
- Flags:
  --out-dir, --base-url
  --annex-pdf-to-md (default on)
  --history-sidecars (default on)
  --history-markdown (default on)
  --metadata-exclusion (default empty)
  --ocr (future)

Commit discipline
- Group related changes; include concise messages.
- Reference issues and milestones in PRs.

Security and compliance
- Respect robots/terms for crawling history pages.
- Cache downloads; avoid hammering servers; implement timeouts and backoff.

Documentation
- README explains setup, usage, and flags.
- Add docs for marker installation/conda env expectations.

Remember
- Favor robustness over cleverness.
- When uncertain, keep the source data intact and add new outputs additively.
