# Roadmap

<!-- BEGIN:AUTO-ROADMAP -->
**Auto-generated on 2025-08-08 16:34:16Z (UTC).**

### What this run ensured
- • baseline v1 schema — already present
- ✅ topics taxonomy — tables: topics, fragment_topics, standard_clause_topics
- ✅ standards corpus — tables: standard_bodies, standards, standard_clauses
- ✅ citations mapping — table: fragment_citations
- ✅ annotations & issues — tables: notes, comments, issues
- ✅ orientations, QA, guides, attachments — tables: orientations, qa, guides, attachments
- ✅ comparisons & benchmarks — tables: position_matrix, benchmarks
- ✅ users & events — tables: users, events
- ✅ seed standard bodies — seeded 7 bodies
- ✅ seed topics (fall protection subset) — seeded 8 topics
- ✅ FTS5 on current_pages — table: fts_current + triggers
- • set PRAGMA user_version=5 — already 5

### How to run the pipeline (correct CLI usage)
```bash
python -m lrn.cli extract --db-path legislation.sqlite --out-dir output --preview
python -m lrn.cli extract --db-path legislation.sqlite --out-dir output
python -m lrn.cli db verify --db-path legislation.sqlite --strict
python -m lrn.cli db query --db-path legislation.sqlite current-by-fragment > output/current.csv
```

### Notes
- Roadmap section is maintained between markers. Edit around it, not inside.
- FTS5 is required for search; if missing, install a SQLite build with FTS5 (conda provides it).

### Conda quickstart
```bash
conda create -n legis python=3.11 -c conda-forge
conda activate legis
conda install -c conda-forge sqlite requests beautifulsoup4 lxml pytest
# optional for API: fastapi uvicorn
```

### Seeding
- The script seeds a minimal topic taxonomy and standard bodies on --apply (idempotent).
<!-- END:AUTO-ROADMAP -->


