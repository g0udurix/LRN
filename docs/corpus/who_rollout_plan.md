# WHO Manifest Rollout Plan

## Goal
Generate and curate manifest entries for all WHO member states (~195 jurisdictions) plus strategic
international bodies, ensuring reproducible ingestion guidance, tests, and documentation.

## Phases
1. **Scaffolding (done)**
   - Manifest schema documented (`docs/corpus/manifest_schema.md`).
   - Automation CLI (`scripts/generate_manifests.py`) and roster skeleton seeded.
   - Validation tests extended (`tests/test_manifest_integrity.py`).
2. **Wave 1 (In Progress)** – G20 + WHO strategy documents.
   - Status tracked in `docs/corpus/member_state_progress.md`.
   - Complete remaining G20 (Indonesia, Russia added; pending Saudi, etc.).
3. **Wave 2** – Regional batches (Africa, Americas, Asia-Pacific, Europe, Middle East).
   - For each region: research canonical portals, update roster CSV, generate manifests, add issue
     notes, run tests, record captures.
4. **Wave 3** – Special cases & non-digital sources.
   - Countries lacking online text: document manual download workflow, mark `status=pending` with
     `notes` describing the gap.

## Automation Workflow
1. Update `docs/corpus/roster/who_members.csv` with new country rows (slug, URLs, metadata).
2. Run `python scripts/generate_manifests.py --preview` to review output.
3. Run without `--preview` to create/update manifests.
4. Add/refresh issue notes for headless or licensing guidance.
5. Execute tests:
   ```bash
   python -m pytest tests/test_manifest_integrity.py -q
   python -m pytest -q
   ```
6. Update `docs/corpus/member_state_progress.md` (Status column).
7. Log changes in `chat.md` and `CHANGELOG.md` per branch.

## Research Checklist
- Confirm official portal + permitted reuse (WHO, ILO, government).
- Identify content type (HTML, PDF, JSON) and languages.
- Determine headless/browser requirements; create `docs/issues/<country>-*.md` as needed.
- Note any translation availability or licensing restrictions.

## Coordination
- Strategist agent maintains this plan and syncs progress weekly.
- Corpus Wrangler executes manifest generation, logging captures in `logs/manifest-expansion/`.
- Governance Runner ensures automation scripts and templates remain consistent.
- Persistence Architect monitors needs for fixtures once ingestion outputs are available.

## Metrics
- % WHO jurisdictions with manifests (`done` entries / total).
- Number of outstanding headless blockers.
- Tests pass rate across newly generated manifests.

