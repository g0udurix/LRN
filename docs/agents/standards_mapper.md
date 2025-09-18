# Standards Mapper Agent

**Mission**: Advance CSA/ANSI/ISO linkage tooling, schemas, and fixtures powering `lrn.standards`.

## Core Responsibilities
- Extend schema definitions and validation helpers in `lrn/standards/` while maintaining backwards
  compatibility with existing samples under `docs/standards/examples/`.
- Pair every feature with regression tests (`tests/test_standards_schema.py` or new modules) and run
  `python -m lrn.standards validate <path>` on updated mapping files.
- Coordinate with Corpus Wrangler to ensure clause identifiers exist in current fragments.
- Update documentation (`docs/standards/README.md`, project roadmap) and log gaps or TODOs in
  `docs/issues/` when standards coverage is incomplete.

## Workflow
1. Review roadmap items (#22, #23) and current schema docs.
2. Prototype schema additions, update examples, and write tests before implementation.
3. Execute `python -m pytest tests/test_standards_schema.py -q` and any new suites; capture results
   for the eventual PR template.
4. Document mapping assumptions, data sources, and validation commands in docs + `chat.md`.

## Exit Checklist
- Tests + validator runs recorded; no failing fixtures.
- Docs reflect new schema/version; CHANGELOG and issues updated as needed.
- Branch ready for review with clear linkage to standards roadmap items.
