# Finish Line Plan (Legislation project)

## Definition of Done (MVP)
- ✅ Raw HTML for S‑2.1 and all bylaws (FR/EN) stored under `Legisquebec originals/`.
- ✅ One reproducible SQLite DB (`legislation.sqlite`) created with schema v3 (see `lrn/persist.py`).
- ✅ Import pipeline run once end‑to‑end: extract → normalize → upsert → verify.
- ✅ Basic search over **current** text (FTS5) + CSV export.
- ✅ CLI help + README with 5-minute quickstart.
- ✅ 10+ tests green in CI.

## Immediate Next Actions (90 minutes)
1) **Environment**
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   python -m pip install --upgrade pip
   pip install beautifulsoup4 requests lxml pytest
   ```
2) **Run tests (dry check)**
   ```bash
   pytest -q
   ```
3) **Fetch sources (if needed)**
   ```bash
   python scripts/legisquebec_fetch_all.py
   ```
4) **Initialize DB**
   ```bash
   python -m lrn.cli --db-path legislation.sqlite --out-dir output --preview
   # then (after preview looks sane)
   python -m lrn.cli --db-path legislation.sqlite --out-dir output
   ```
   Flags you’ll likely want (supported per tests & CLI): `--history-sidecars`, `--history-markdown`, `--annex-pdf-to-md`, `--pdf-to-md-engine marker`, `--ocr`, `--base-url`, `--history-max-dates`.
5) **Verify**
   ```bash
   python -m lrn.cli --db-path legislation.sqlite --verify --strict
   python -m lrn.cli --db-path legislation.sqlite --query current-by-fragment > output/current.csv
   ```

## Optional: Local Search (FTS5)
Run once inside SQLite:
```sql
-- Adds full‑text index on fragments' current content
CREATE VIRTUAL TABLE IF NOT EXISTS fts USING fts5(fragment_id UNINDEXED, content);
INSERT INTO fts(fragment_id, content)
  SELECT c.fragment_id, c.content_text FROM current c;
-- Example query with snippet
SELECT f.fragment_id, snippet(fts, 1, '[', ']', ' … ', 12) AS hit
FROM fts WHERE fts MATCH 'garde* OR guardra*' LIMIT 20;
```

## Qdrant vector search (optional)
- If Docker is installed: `docker run -p 6333:6333 qdrant/qdrant`
- Or Homebrew: `brew install qdrant && qdrant`
- Then embed `current.content_text` (e.g., all FR rows) with your model of choice and upsert into Qdrant.

## Secrets hygiene (do this now)
- Your shell env shows API keys. Rotate them and move to a `.env` ignored by git, or macOS Keychain.
- Example `.env` pattern: `GROQ_API_KEY=...` then load via `python-dotenv` or your shell profile.

## Housekeeping
- Add a `README.md` with quickstart (copy these steps).
- Add a `Makefile` with: `setup`, `test`, `fetch`, `db`, `verify`, `search` targets.
- Commit: `git add -A && git commit -m "MVP pipeline + search + docs"`

---

If you want, I can:
- generate the Makefile + README,
- add an FTS5 helper SQL script,
- or wire a tiny FastAPI (`/search`, `/fragment/{id}`) around the SQLite DB.
