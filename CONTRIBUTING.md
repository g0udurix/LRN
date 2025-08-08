
# Contributing to LRN (Humans & AI agents)

Welcome! This repo accepts contributions from both humans and AI agents (tools like ChatGPT/Copilot/LLMs). To keep quality high and risk low, follow these rules:

## Ground rules
- **Follow semantic commits**: `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`, etc. Use scopes where meaningful (e.g., `feat(extractor): ...`).
- **No secrets**: Do not include API keys, tokens, or confidential content. If an AI wrote code, double-check for accidental credentials.
- **Determinism over cleverness**: Prefer simple, testable code over magic. Explain non-trivial logic in comments.
- **Reproducibility**: If you generate code or data, describe how to regenerate it (`make` targets or scripts).
- **Tests**: For non-trivial changes, include or update tests. For schema changes, include a migration and verification steps.
- **Docs**: Update README/ROADMAP and add upgrade notes when behavior changes.

## For AI agents specifically
- **Identify automated changes** in PR body: include a short “AI notes” section describing prompts, assumptions, and safeguards.
- **Avoid hallucinations**: Cite sources (standards, statutes) with exact references where applicable.
- **Respect licenses**: Do not paste content from proprietary standards. Summarize instead.
- **Keep PRs small**: Split large work into reviewable chunks; keep diffs under ~500 lines when possible.
- **Feedback loop**: If your generation relies on context, quote it in the PR so reviewers can validate.

## PR checklist
- [ ] Semantic title & commits
- [ ] Linked issue / milestone
- [ ] Labels: `area/*`, `priority/*`, `status/*`
- [ ] Tests/lint pass locally
- [ ] Docs updated

Thanks! ✨
