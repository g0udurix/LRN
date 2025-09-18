# Manifest Schema Overview

Each JSON file under `docs/corpus/manifests/` contains an array of entries describing a source
instrument. Fields:

- `url` (str, required): Canonical source URL.
- `language` (str, required): Language tag (ISO code or descriptive string).
- `instrument` (str, recommended): Identifier slug used for output directory names.
- `category` (str, optional, default `unknown`): Jurisdiction type (`national`, `provincial`, `municipal`, `international`, etc.).
- `requires_headless` (bool, optional, default `False`): Whether the source typically requires the Playwright headless helper.
- `content_type` (str, optional, default `html`): One of `html`, `pdf`, `json`.
- `issue_ref` (str, optional): Path to an issue note documenting special handling (e.g., WAF guidance).
- `notes` (str, optional): Free-form metadata for maintainers.
- `status` (str, optional, default `active`): Lifecycle marker (`active`, `pending`, `deprecated`).

Automation (`scripts/generate_manifests.py`) and validation tests ensure manifests only use these
fields and that types are consistent. Headless captures should be stored outside git; link to the
supporting issue in `issue_ref` for future maintainers.
