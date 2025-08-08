# Documentation Extraction Style

Scope
Applies to documentation extracted, generated, or curated for this repository. Derived from [RULES.md](RULES.md) and [PLAN.md](PLAN.md).

Headings
- Use sentence-case headings with at most three levels: H1, H2, H3.
- Keep titles concise and action-oriented.

Code fences
- Use language-tagged fences for syntax highlighting.
- Prefer minimal runnable snippets; avoid verbose boilerplate.
- Any language construct or filename reference must use clickable notation per workspace rules:
  - Files: [lrn/cli.py](lrn/cli.py)
  - Constructs: [python.main()](lrn/cli.py:1), [python.fetch_history()](lrn/history.py:1)

Metadata blocks
- Optional YAML front matter at file top for toolchain consumption:
  ---
  title: Short title
  source: RULES.md
  last_reviewed: YYYY-MM-DD
  ---

Cross-references
- Reference repository files directly using clickable links.
- Reference test examples sparingly to illustrate behavior:
  - [python.test_extract_basic()](tests/test_extract_basic.py:1)

Examples (concise)
- Logging conventions:
  ```
  [INFO] Crawling history for se:1
  [WARN] marker conversion failed for path/to/file.pdf: error text
  ```
- File writing (UTF-8):
  - See [python.open()](lrn/cli.py:1) usage pattern with encoding="utf-8".

Style notes
- Prefer clarity over completeness; link to sources for details.
- Keep line length ~100–120.
- Normalize path separators in emitted links to forward slashes.