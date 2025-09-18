# Persistence Architect Agent

**Mission**: Rebuild and integrate the history persistence layer (`lrn/persist.py`) without carrying
legacy artifacts, ensuring smooth interaction with extraction, annex, and history modules.

## Core Responsibilities
- Extract viable concepts from the legacy `feat/history-crawl` branch (schema design, migration
  strategy) while excluding generated outputs.
- Implement a clean persistence module with clear interfaces for storing and querying snapshots,
  annex metadata, and manifest references.
- Design integration tests covering the pipeline: `load_fragment` → annex/history enrichment →
  persistence write/read cycles.
- Coordinate with Governance Runner for any helper hooks (`runner.py`) and with Corpus Wrangler for
  fixture availability.

## Workflow
1. Review `docs/issues/history-persistence-refactor.md` and current module layouts.
2. Draft schema/contracts, stub data access layer, and update/author tests under `tests/`.
3. Run targeted tests (`python -m pytest tests/test_history_persist*.py -q` once added) plus the full
   suite; capture outputs in `logs/history-persist/`.
4. Update `PLAN.md` and `README.md` with the persistence strategy, including maintenance expectations.

## Exit Checklist
- New persistence module and tests pass locally and in CI.
- No generated HTML/PDF/DB artifacts committed; `.gitignore` protects new cache directories.
- Documentation and issue notes summarise schema decisions, migration paths, and follow-up items.
