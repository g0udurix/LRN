# Changelog

All notable changes to this project are documented in this file.

This project follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and uses [Conventional Commits](https://www.conventionalcommits.org/) for commit messages.

## [Unreleased]

### Added
- Unified contributor documentation for **humans and AI agents** in `CONTRIBUTING.md`.
- Updated `CODE_OF_CONDUCT.md` with enforcement contact (seemly-peer.0k@icloud.com).
- Enhanced PR template with checklists and AI‑specific safeguards.
- Overhauled **CONTRIBUTING.md** with human + AI playbook, labels/milestones, and PAT setup (`PROJECTS_PAT`).
- Rewrote **CODE_OF_CONDUCT.md** with clear enforcement contact (seemly-peer.0k@icloud.com).
- Improved **PR template** with human and AI checklists.
- Added **RULES.md** as a compact decision guide.
- Updated **README.md** to reflect governance, automation, and roadmap.

## 2025-08-09 — Bootstrap governance & workflows ([#6])
### Added
- Governance files: `CODE_OF_CONDUCT.md`, `CONTRIBUTING.md`, `CODEOWNERS`.
- CI/GitHub workflows: `labels-sync`, `projects-sync`, `release-drafter`, `semantic-pr`.
- Branch protection on `master` (strict status checks, 1 approving review).
- Milestones for Phase 0–4 with descriptions and due dates.

### Removed
- Old logs and local `qdrant_storage` artifacts cleaned from the repo.

[#6]: https://github.com/g0udurix/LRN/pull/6
