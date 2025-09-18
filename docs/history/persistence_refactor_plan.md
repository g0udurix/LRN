# History Persistence Refactor Plan

## Objectives
- Introduce `lrn/persist.py` providing a SQLite persistence layer for history snapshots.
- Add regression tests (`tests/test_history_persist.py`) validating initialization and snapshot storage.
- Outline future integration steps with the history crawler.

## Status
- [x] Persistence module scaffolded with fragment registration and snapshot storage.
- [x] Tests created covering default paths, initialize/store/list behaviour.
- [ ] Integrate persistence into `lrn/history.py` workflows (future).
- [ ] Capture sample database outputs under `logs/history-persist/` (git-ignored).

## Next Steps
1. Wire persistence calls into history snapshot generation once acceptance criteria defined.
2. Add error handling tests for IO failures or malformed metadata.
3. Document migration strategy if schema evolves beyond current tables.
