# Governance Helper Plan

This branch rebuilds the governance helper (`runner.py`) and supporting templates.

## Deliverables
- `runner.py` CLI with `--apply` and `--self-test` commands referencing files in `governance/templates/`.
- Template bundle for labels, workflows, issue templates, and configs.
- Integration tests (`tests/test_runner_cli.py`) covering dry-run/self-test flows.
- Documentation updates: `README.md`, `PLAN.md`, `CHANGELOG.md`, `docs/issues/bootstrap-workflows-redux.md`.
- Project 3 Gantt cards updated with start/end dates.

## Open Tasks
- [ ] Inventory required templates (labels, workflows, issue templates, codeowners as needed).
- [ ] Design runner CLI structure (argparse, dry-run vs apply).
- [ ] Implement filesystem sync + GitHub API placeholders (dry-run for CI).
- [ ] Write pytest coverage for runner.
- [ ] Update documentation + changelog.
- [ ] Record commands/logs in `logs/governance-runner/` and `chat.md`.

## Notes
- Keep generated artifacts out of git; operate on templates only.
- Require `gh auth status` check before running apply commands.
- Ensure `CHANGELOG.md` records user-visible updates before PR.
