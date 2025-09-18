## Project Overview

This project, "LRN", is a community-driven legal/standards research workspace. It's a Python-based command-line interface (CLI) tool designed to extract and process legal documents from the LegisQuébec website. The core functionality revolves around extracting the inner XHTML from LegisQuébec HTML files while preserving metadata. It also has capabilities for handling annex PDFs and document history.

The project is heavily automated with GitHub Actions for CI, release drafting, and project management. It has a sophisticated set of scripts for bootstrapping and maintaining the repository's governance files, workflows, and other configurations.

## Building and Running

The main application logic is in `lrn/cli.py`. While there isn't a specific "build" process, the tool can be run directly as a Python script.

**Running the extractor:**

```bash
python -m lrn.cli --out-dir output/ "Legisquebec originals/fr/document/rc/S-2.1, r. 15 .html"
```

**Running tests:**

The project uses `pytest` for testing.

```bash
pytest
```

## Development Conventions

- **Conventional Commits:** All commits must follow the Conventional Commits specification (e.g., `feat:`, `fix:`, `chore:`).
- **Semantic Pull Requests:** Pull request titles must also follow the Conventional Commits format.
- **Small, Incremental Changes:** Contributions should be small, focused, and well-reviewed.
- **AI Agent Contributions:** The project has specific guidelines for contributions made by AI agents, which are detailed in `CONTRIBUTING.md` and `RULES.md`.
- **Repository Bootstrapping:** The `updatecodebase.py` and `upgrade_and_roadmap.py` scripts are used to bootstrap and maintain the repository's structure and governance files. These scripts ensure consistency across the project.
