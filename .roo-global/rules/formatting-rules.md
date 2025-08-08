# Global Formatting Rules

Indentation and spacing
- Python: 4 spaces; no tabs.
- One logical statement per line; wrap long expressions sensibly.

Line length
- Target ~100–120 characters for readability.

Imports
- Order: standard library, third-party, local; blank line between groups.
- No wildcard imports; prefer explicit names.

Strings and formatting
- Prefer f-strings for clarity and performance.

Encoding and newlines
- UTF-8 for all text IO.
- Ensure trailing newline at end of files.

File and path handling
- Normalize path separators to forward slashes in emitted links and outputs.

Examples
- Logging format:
  - [INFO] message
  - [WARN] message
- Python file writing:
  - See [python.open()](lrn/cli.py:1) usage pattern for encoding="utf-8".