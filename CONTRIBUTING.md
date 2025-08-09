
# Contributing to LRN (Humans & AI agents)

Welcome! This repo accepts contributions from both humans and AI agents (tools like ChatGPT/Copilot/LLMs).

## Ground rules
- **Semantic commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Use scopes (e.g., `feat(extractor): …`).
- **No secrets**: Strip API keys/tokens from code and config.
- **Determinism**: Prefer simple, testable code. Comment non-trivial logic.
- **Reproducibility**: Document how to regenerate data or codegen.
- **Tests & docs**: Update both for non-trivial changes.

## For AI agents
- Add an **AI notes** section in PR body with prompts/assumptions.
- Cite sources for standards and statutes.
- Keep PRs small; split if > ~500 LOC.

### Projects automation
To sync items into **Projects #3** and map fields from labels, set repo secret **`PROJECTS_PAT`** (classic PAT with `repo` and `project` scopes`).
