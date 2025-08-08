# {Mode} - Mode-Specific Rules (Template)

Scope
This template defines constraints and expectations for a specific mode. Replace "{Mode}" with the actual mode name and tailor each section accordingly.

Allowed operations
- Describe permitted actions for this mode (e.g., read files, write new docs, refactor code).
- Clarify boundaries (e.g., behavioral edits only, no network calls, docs-only changes).

Restricted files
- List disallowed paths or patterns explicitly (e.g., no edits under tests/, or no changes to pyproject.toml).
- If needed, specify allowed patterns to make constraints unambiguous.

Logging expectations
- Emit concise progress and warnings:
  - [INFO] high-level steps completed
  - [WARN] degraded behavior and recoverable failures
- Avoid verbose logs; logs must be actionable.

QA checks
- Validate outputs are deterministic and reproducible.
- Ensure UTF-8 encoding in text files and normalize path separators in emitted links.
- Run or reference behavior tests where relevant:
  - Example entrypoint: [lrn/cli.py](lrn/cli.py)
  - Example tests: [python.test_extract_basic()](tests/test_extract_basic.py:1)

Completion criteria
- Clearly list artifacts produced or files modified.
- Confirm no restricted files were changed.
- Summarize any warnings and recovery actions taken.

Notes
- Follow repository-wide standards in:
  - [rules/coding-standards.md](../rules/coding-standards.md)
  - [rules/formatting-rules.md](../rules/formatting-rules.md)
  - [rules/security-guidelines.md](../rules/security-guidelines.md)
  - [rules-code/testing-requirements.md](../rules-code/testing-requirements.md)