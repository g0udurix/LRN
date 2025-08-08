#!/usr/bin/env python3
# Last run: 2025-08-08T16:14:42Z
# -*- coding: utf-8 -*-
"""
upgrade_and_roadmap.py

Idempotent "v5" upgrade + roadmap updater for the Regulation Intelligence project.

- Adds schema slices for topics, standards, citations, annotations, issues, orientations, Q&A, guides, attachments,
  comparison matrices, benchmarks, events, users
- Ensures FTS5 index on current_pages with triggers
- Bumps PRAGMA user_version to 5 (if lower)
- Updates ROADMAP.md auto-generated section (between markers)

Usage:
  python upgrade_and_roadmap.py --db legislation.sqlite --roadmap ROADMAP.md --apply
  python upgrade_and_roadmap.py --db legislation.sqlite --roadmap ROADMAP.md            # dry-run (default)

Safe to re-run. Only uses stdlib.
"""
from __future__ import annotations
import argparse, sqlite3, sys, json, os, subprocess, shutil, re
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Tuple
from datetime import datetime, timezone

BEGIN = "<!-- BEGIN:AUTO-ROADMAP -->"
END   = "<!-- END:AUTO-ROADMAP -->"

# --- Utility: timestamp header for sanity check ---------------------------------

def self_update_header_timestamp(apply: bool, log_fn=print):
    """Update or insert a '# Last run:' header line at top of this file.
    Safe to run repeatedly. Only writes when apply=True.
    """
    try:
        here = Path(__file__).resolve()
        txt = here.read_text(encoding="utf-8")
        ts  = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        lines = txt.splitlines()
        marker = "# Last run: "
        changed = False
        # If we find a line starting with marker in first 10 lines, replace it
        for i in range(min(10, len(lines))):
            if lines[i].startswith(marker):
                if lines[i] != marker + ts:
                    lines[i] = marker + ts
                    changed = True
                break
        else:
            # Insert after shebang if present, else at very top
            insert_at = 1 if lines and lines[0].startswith("#!/") else 0
            lines.insert(insert_at, marker + ts)
            changed = True
        if apply and changed:
            here.write_text("\n".join(lines) + "\n", encoding="utf-8")
            log_fn(f"[APPLIED] header timestamp -> {ts}")
        else:
            log_fn(f"[OK] header timestamp would be -> {ts}")
    except Exception as e:
        log_fn(f"[WARN] header timestamp update failed: {e}")

# --- Utility: logging to file ----------------------------------------------------
LOG_DIR = Path("logs"); LOG_DIR.mkdir(exist_ok=True)
LOG_PATH = LOG_DIR / ("upgrade_" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + ".log")

def log(msg: str):
    try:
        with LOG_PATH.open("a", encoding="utf-8") as f:
            f.write(msg + "\n")
    except Exception:
        pass
    print(msg)

# --- Utility: subprocess runner --------------------------------------------------

def run(cmd, cwd: Path | None = None, check: bool = False):
    if isinstance(cmd, str):
        shell = True
    else:
        shell = False
    p = subprocess.run(cmd, cwd=str(cwd) if cwd else None, shell=shell,
                       capture_output=True, text=True)
    out = (p.stdout or "").strip(); err = (p.stderr or "").strip()
    log(f"$ {' '.join(cmd) if not shell else cmd}\n[rc={p.returncode}]\n{out}\n{err if err else ''}")
    if check and p.returncode != 0:
        raise RuntimeError(f"Command failed ({p.returncode}): {cmd}\n{err}")
    return p.returncode, out, err

# --- Git helpers -----------------------------------------------------------------

def ensure_git_pull(repo_dir: Path, apply: bool):
    if not (repo_dir / ".git").exists():
        log("[WARN] Not a git repo; skipping pull")
        return {"name": "git pull", "applied": False, "detail": "not a git repo"}
    if apply:
        run(["git", "fetch", "--all"], cwd=repo_dir)
        rc, _, _ = run(["git", "pull", "--rebase", "--autostash"], cwd=repo_dir)
        return {"name": "git pull", "applied": rc == 0, "detail": "rebase+autostash"}
    else:
        return {"name": "git pull", "applied": False, "detail": "dry-run"}


def ensure_git_commit_push(repo_dir: Path, message: str, push: bool, apply: bool):
    if not (repo_dir / ".git").exists():
        log("[WARN] Not a git repo; skipping commit/push")
        return {"name": "git commit/push", "applied": False, "detail": "not a git repo"}
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    full_msg = f"{message} (at {ts} UTC)"
    if apply:
        run(["git", "add", "-A"], cwd=repo_dir)
        rc, out, _ = run(["git", "diff", "--cached", "--quiet"], cwd=repo_dir)
        if rc != 0:  # there are staged changes
            run(["git", "commit", "-m", full_msg], cwd=repo_dir)
            pushed = False
            if push:
                run(["git", "push"], cwd=repo_dir)
                pushed = True
            return {"name": "git commit/push", "applied": True, "detail": f"committed; pushed={pushed}"}
        else:
            return {"name": "git commit/push", "applied": False, "detail": "no changes"}
    else:
        return {"name": "git commit/push", "applied": False, "detail": "dry-run"}

# --- File ensure helper ----------------------------------------------------------

def ensure_file(path: Path, content: str, apply: bool):
    name = f"write {path}"
    if path.exists():
        existing = path.read_text(encoding="utf-8")
        if existing == content:
            return {"name": name, "applied": False, "detail": "up-to-date"}
    if apply:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
        return {"name": name, "applied": True, "detail": "written"}
    else:
        return {"name": name, "applied": False, "detail": "dry-run"}

# --- GitHub labels sync (via gh CLI if available) --------------------------------

def gh_available():
    return shutil.which("gh") is not None

LABELS = [
    ("priority/P0", "Blocker", "b60205"),
    ("priority/P1", "High", "d73a4a"),
    ("priority/P2", "Normal", "fbca04"),
    ("area/extractor", "Ingestion & crawling", "1d76db"),
    ("area/schema", "Database schema/migrations", "1d76db"),
    ("area/standards", "Standards mapping", "1d76db"),
    ("area/comparison", "Matrix/ranking engine", "1d76db"),
    ("area/annotations", "Notes, issues, orientations", "1d76db"),
    ("area/app", "API/UI", "1d76db"),
    ("jurisdiction/QC", "Québec", "0e8a16"),
    ("jurisdiction/CA", "Canada (Fed)", "0e8a16"),
    ("jurisdiction/US", "United States", "0e8a16"),
    ("jurisdiction/UK", "United Kingdom", "0e8a16"),
    ("jurisdiction/FR", "France", "0e8a16"),
    ("jurisdiction/DE", "Germany", "0e8a16"),
    ("jurisdiction/JP", "Japan", "0e8a16"),
    ("jurisdiction/AU", "Australia", "0e8a16"),
    ("standard/CSA", "CSA", "5319e7"), ("standard/ANSI", "ANSI", "5319e7"),
    ("standard/ISO", "ISO", "5319e7"), ("standard/EN", "EN", "5319e7"),
    ("standard/BS", "BSI", "5319e7"), ("standard/AS", "AS/NZS", "5319e7"),
    ("standard/JIS", "JIS", "5319e7"),
    ("documentation", "Docs & READMEs", "c5def5"),
    ("needs-triage", "New items to triage", "ededed"),
]


def sync_labels_with_gh(repo_slug: str, apply: bool):
    name = f"sync labels for {repo_slug}"
    if not gh_available():
        return {"name": name, "applied": False, "detail": "gh not installed"}
    applied_any = False
    for lab, desc, color in LABELS:
        cmd = ["gh", "label", "create", lab, "-R", repo_slug, "--color", color, "--description", desc]
        rc, out, err = run(cmd)
        if rc != 0 and "already exists" not in (out + err):
            # try update
            run(["gh", "label", "edit", lab, "-R", repo_slug, "--color", color, "--description", desc])
        else:
            applied_any = applied_any or (rc == 0)
    return {"name": name, "applied": applied_any, "detail": "ensured label set"}

# --- Workflows to auto-add to Projects v2 ---------------------------------------

WORKFLOW_ADD_TO_PROJECT = """
name: Add new items to Project 3
on:
  issues:
    types: [opened, reopened, transferred, labeled]
  pull_request:
    types: [opened, reopened, labeled, ready_for_review]
jobs:
  add:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/add-to-project@v1
        with:
          project-url: ${PROJECT_URL}
          github-token: ${{ secrets.ADD_TO_PROJECT_PAT }}
"""

WORKFLOW_SET_FIELDS = """
name: Set Project fields
on:
  issues:
    types: [opened, labeled]
  pull_request:
    types: [opened, labeled, ready_for_review]
jobs:
  set-fields:
    runs-on: ubuntu-latest
    steps:
      - uses: leonsteinhaeuser/project-fields@v2
        with:
          github_token: ${{ secrets.PROJECT_PAT }}
          project_url: ${PROJECT_URL}
          fields: Status,Priority
          values: Todo,P2
"""

ISSUE_TEMPLATE_FEATURE = """
---
name: Feature request
a bout: Suggest an idea
labels: [enhancement, needs-triage]
---
**Problem**

**Proposed solution**

**Scope**

**References**
"""

ISSUE_TEMPLATE_BUG = """
---
name: Bug report
about: Report a bug
labels: [bug, needs-triage]
---
**Describe the bug**

**To Reproduce**

**Expected behavior**

**Logs**
"""

PR_TEMPLATE = """
## Summary

## Changes

## Testing

## Checklist
- [ ] Linked issue
- [ ] Added/updated docs
- [ ] Added tests (if applicable)
"""


def setup_project_automation(repo_dir: Path, project_url: str, apply: bool):
    items = []
    items.append(ensure_file(repo_dir/".github"/"workflows"/"add_to_project.yml",
                             WORKFLOW_ADD_TO_PROJECT.replace("${PROJECT_URL}", project_url), apply))
    items.append(ensure_file(repo_dir/".github"/"workflows"/"project_fields.yml",
                             WORKFLOW_SET_FIELDS.replace("${PROJECT_URL}", project_url), apply))
    items.append(ensure_file(repo_dir/".github"/"ISSUE_TEMPLATE"/"feature_request.md",
                             ISSUE_TEMPLATE_FEATURE, apply))
    items.append(ensure_file(repo_dir/".github"/"ISSUE_TEMPLATE"/"bug_report.md",
                             ISSUE_TEMPLATE_BUG, apply))
    items.append(ensure_file(repo_dir/".github"/"PULL_REQUEST_TEMPLATE.md",
                             PR_TEMPLATE, apply))
    return items

# --- Optional: run bundler and capture output -----------------------------------

def run_bundle_codebase(repo_dir: Path, apply: bool):
    script = repo_dir/"bundle_codebase.py"
    if not script.exists():
        return {"name": "bundle_codebase", "applied": False, "detail": "missing"}
    rc, out, err = run([sys.executable, str(script)], cwd=repo_dir)
    # Save output for later review
    (LOG_DIR/"bundle_output.txt").write_text(out + ("\n"+err if err else ""), encoding="utf-8")
    return {"name": "bundle_codebase", "applied": rc == 0, "detail": f"rc={rc}"}

# --- CHANGELOG helper ------------------------------------------------------------

def append_changelog(repo_dir: Path, entry: str, apply: bool):
    path = repo_dir/"CHANGELOG.md"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    line = f"- {ts} {entry}\n"
    if apply:
        with path.open("a", encoding="utf-8") as f:
            f.write(line)
        return {"name": "changelog", "applied": True, "detail": entry[:80]}
    else:
        return {"name": "changelog", "applied": False, "detail": "dry-run"}

@dataclass
class StepResult:
    name: str
    applied: bool
    detail: str = ""

def _connect(db_path: str) -> sqlite3.Connection:
    os.makedirs(os.path.dirname(db_path) or ".", exist_ok=True)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    # Pragmas
    conn.execute("PRAGMA foreign_keys=ON;")
    conn.execute("PRAGMA journal_mode=WAL;")
    return conn

def _table_exists(conn: sqlite3.Connection, table: str) -> bool:
    cur = conn.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table,))
    return cur.fetchone() is not None

def _column_exists(conn: sqlite3.Connection, table: str, column: str) -> bool:
    cur = conn.execute(f"PRAGMA table_info({table});")
    return any(row[1] == column for row in cur.fetchall())

def _fts5_available(conn: sqlite3.Connection) -> bool:
    try:
        conn.execute("CREATE VIRTUAL TABLE IF NOT EXISTS __fts5_probe USING fts5(x)")
        conn.execute("DROP TABLE IF EXISTS __fts5_probe")
        return True
    except Exception:
        return False

def _apply(conn: sqlite3.Connection, sql: str) -> None:
    conn.executescript(sql)

def ensure_baseline_v1(conn: sqlite3.Connection, apply: bool):
    name = "baseline v1 schema"
    # If core tables exist, assume baseline present and no-op
    if _table_exists(conn, "instruments") and _table_exists(conn, "fragments") and _table_exists(conn, "current_pages"):
        return dict(name=name, applied=False, detail="already present")

    ddl = """
CREATE TABLE IF NOT EXISTS instruments (
  id INTEGER PRIMARY KEY,
  name TEXT NOT NULL UNIQUE,
  source_url TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  metadata_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_instruments_source_url ON instruments(source_url);

CREATE TABLE IF NOT EXISTS fragments (
  id INTEGER PRIMARY KEY,
  instrument_id INTEGER NOT NULL,
  code TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  metadata_json TEXT,
  UNIQUE(instrument_id, code),
  FOREIGN KEY (instrument_id) REFERENCES instruments(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_fragments_instrument_code ON fragments(instrument_id, code);

CREATE TABLE IF NOT EXISTS current_pages (
  id INTEGER PRIMARY KEY,
  fragment_id INTEGER NOT NULL UNIQUE,
  url TEXT,
  content_text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  extracted_at TEXT NOT NULL,
  metadata_json TEXT,
  FOREIGN KEY (fragment_id) REFERENCES fragments(id) ON DELETE CASCADE ON UPDATE CASCADE
);
CREATE INDEX IF NOT EXISTS idx_current_pages_url ON current_pages(url);
CREATE INDEX IF NOT EXISTS idx_current_pages_hash ON current_pages(content_hash);

-- Housekeeping triggers, safe if they already exist
CREATE TRIGGER IF NOT EXISTS trg_instruments_updated_at
AFTER UPDATE ON instruments
FOR EACH ROW WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE instruments SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

CREATE TRIGGER IF NOT EXISTS trg_fragments_updated_at
AFTER UPDATE ON fragments
FOR EACH ROW WHEN NEW.updated_at = OLD.updated_at
BEGIN
  UPDATE fragments SET updated_at = strftime('%Y-%m-%dT%H:%M:%fZ','now') WHERE id = NEW.id;
END;

-- Historical scaffolding (v1-compatible; also created later in v4 migration)
CREATE TABLE IF NOT EXISTS historical_fragments (
  id INTEGER PRIMARY KEY,
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  content_text TEXT NOT NULL,
  content_hash TEXT NOT NULL,
  date TEXT NOT NULL,
  metadata_json TEXT
);
CREATE TABLE IF NOT EXISTS fragment_changes (
  id INTEGER PRIMARY KEY,
  historical_fragment_id INTEGER NOT NULL REFERENCES historical_fragments(id) ON DELETE CASCADE,
  change_type TEXT NOT NULL,
  old_value TEXT,
  new_value TEXT
);
"""
    if apply:
        _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: instruments, fragments, current_pages (+triggers)")

def ensure_topics_taxonomy(conn: sqlite3.Connection, apply: bool):
    name = "topics taxonomy"
    ddl = """
CREATE TABLE IF NOT EXISTS topics (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  parent_id INTEGER REFERENCES topics(id) ON DELETE SET NULL
);
CREATE INDEX IF NOT EXISTS idx_topics_parent ON topics(parent_id);

CREATE TABLE IF NOT EXISTS fragment_topics (
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  weight REAL,
  PRIMARY KEY(fragment_id, topic_id)
);

CREATE TABLE IF NOT EXISTS standard_clause_topics (
  standard_clause_id INTEGER NOT NULL REFERENCES standard_clauses(id) ON DELETE CASCADE,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  weight REAL,
  PRIMARY KEY(standard_clause_id, topic_id)
);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: topics, fragment_topics, standard_clause_topics")

def ensure_standards(conn: sqlite3.Connection, apply: bool):
    name = "standards corpus"
    ddl = """
CREATE TABLE IF NOT EXISTS standard_bodies (
  id INTEGER PRIMARY KEY,
  code TEXT UNIQUE NOT NULL,   -- e.g., CSA, ISO, ANSI, EN, BS, AS, JIS
  name TEXT NOT NULL,
  country TEXT
);

CREATE TABLE IF NOT EXISTS standards (
  id INTEGER PRIMARY KEY,
  body_id INTEGER NOT NULL REFERENCES standard_bodies(id) ON DELETE CASCADE,
  designation TEXT NOT NULL,  -- e.g., Z259.11-17
  title TEXT,
  edition TEXT,
  year INTEGER,
  status TEXT,                -- current/withdrawn/draft
  UNIQUE(body_id, designation)
);
CREATE INDEX IF NOT EXISTS idx_standards_body ON standards(body_id);

CREATE TABLE IF NOT EXISTS standard_clauses (
  id INTEGER PRIMARY KEY,
  standard_id INTEGER NOT NULL REFERENCES standards(id) ON DELETE CASCADE,
  code TEXT,                  -- e.g., 4.2.1
  title TEXT,
  text TEXT,
  lang TEXT,
  display_order INTEGER,
  UNIQUE(standard_id, code, lang)
);
CREATE INDEX IF NOT EXISTS idx_standard_clauses_std ON standard_clauses(standard_id);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: standard_bodies, standards, standard_clauses")

def ensure_citations(conn: sqlite3.Connection, apply: bool):
    name = "citations mapping"
    ddl = """
CREATE TABLE IF NOT EXISTS fragment_citations (
  id INTEGER PRIMARY KEY,
  fragment_id INTEGER NOT NULL REFERENCES fragments(id) ON DELETE CASCADE,
  target_type TEXT NOT NULL,   -- instrument_fragment | standard_clause
  target_id INTEGER NOT NULL,  -- FK depends on target_type
  citation_text TEXT,
  relevance REAL,
  note TEXT
);
CREATE INDEX IF NOT EXISTS idx_fragment_citations_fragment ON fragment_citations(fragment_id);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="table: fragment_citations")

def ensure_annotations(conn: sqlite3.Connection, apply: bool):
    name = "annotations & issues"
    ddl = """
CREATE TABLE IF NOT EXISTS notes (
  id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  author TEXT,
  body_md TEXT NOT NULL,
  visibility TEXT,          -- private, shared
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_notes_entity ON notes(entity_type, entity_id);

CREATE TABLE IF NOT EXISTS comments (
  id INTEGER PRIMARY KEY,
  note_id INTEGER NOT NULL REFERENCES notes(id) ON DELETE CASCADE,
  author TEXT,
  body_md TEXT NOT NULL,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);
CREATE INDEX IF NOT EXISTS idx_comments_note ON comments(note_id);

CREATE TABLE IF NOT EXISTS issues (
  id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  type TEXT NOT NULL,       -- Obsolescence, Conflict, Ambiguity, Missing reference, Inconsistency
  severity TEXT,            -- low, medium, high
  status TEXT,              -- open, closed
  summary TEXT,
  detail_md TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  resolved_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_issues_entity ON issues(entity_type, entity_id);
CREATE INDEX IF NOT EXISTS idx_issues_status ON issues(status);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: notes, comments, issues")

def ensure_orientations_and_knowledge(conn: sqlite3.Connection, apply: bool):
    name = "orientations, QA, guides, attachments"
    ddl = """
CREATE TABLE IF NOT EXISTS orientations (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
  stance TEXT,
  rationale_md TEXT,
  approved_by TEXT,
  status TEXT,                -- draft, approved, retired
  effective_date TEXT,
  review_date TEXT
);

CREATE TABLE IF NOT EXISTS qa (
  id INTEGER PRIMARY KEY,
  question_md TEXT NOT NULL,
  answer_md TEXT,
  topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL,
  citations_json TEXT,
  created_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  updated_at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now'))
);

CREATE TABLE IF NOT EXISTS guides (
  id INTEGER PRIMARY KEY,
  title TEXT NOT NULL,
  body_md TEXT NOT NULL,
  topic_id INTEGER REFERENCES topics(id) ON DELETE SET NULL
);

CREATE TABLE IF NOT EXISTS attachments (
  id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,
  entity_id INTEGER NOT NULL,
  path TEXT NOT NULL,
  sha256 TEXT,
  mime TEXT,
  title TEXT
);
CREATE INDEX IF NOT EXISTS idx_attachments_entity ON attachments(entity_type, entity_id);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: orientations, qa, guides, attachments")

def ensure_comparisons(conn: sqlite3.Connection, apply: bool):
    name = "comparisons & benchmarks"
    ddl = """
CREATE TABLE IF NOT EXISTS position_matrix (
  id INTEGER PRIMARY KEY,
  entity_type TEXT NOT NULL,     -- jurisdiction | standard | instrument
  entity_id INTEGER NOT NULL,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  position TEXT,
  strictness REAL,
  requirements_json TEXT,
  rationale_md TEXT,
  score REAL,
  UNIQUE(entity_type, entity_id, topic_id)
);
CREATE INDEX IF NOT EXISTS idx_position_matrix_topic ON position_matrix(topic_id);

CREATE TABLE IF NOT EXISTS benchmarks (
  id INTEGER PRIMARY KEY,
  topic_id INTEGER NOT NULL REFERENCES topics(id) ON DELETE CASCADE,
  scoring_json TEXT,
  last_calculated_at TEXT
);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: position_matrix, benchmarks")

def ensure_ops(conn: sqlite3.Connection, apply: bool):
    name = "users & events"
    ddl = """
CREATE TABLE IF NOT EXISTS users (
  id INTEGER PRIMARY KEY,
  name TEXT,
  email TEXT,
  role TEXT
);

CREATE TABLE IF NOT EXISTS events (
  id INTEGER PRIMARY KEY,
  actor TEXT,
  action TEXT,
  entity_type TEXT,
  entity_id INTEGER,
  at TEXT NOT NULL DEFAULT (strftime('%Y-%m-%dT%H:%M:%fZ','now')),
  payload_json TEXT
);
CREATE INDEX IF NOT EXISTS idx_events_entity ON events(entity_type, entity_id);
"""
    if apply: _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="tables: users, events")

def ensure_fts_current(conn: sqlite3.Connection, apply: bool):
    name = "FTS5 on current_pages"
    if not _table_exists(conn, "current_pages"):
        return dict(name=name, applied=False, detail="skipped: current_pages not found (baseline not initialized yet)")
    if not _fts5_available(conn):
        return dict(name=name, applied=False, detail="FTS5 not available in SQLite build")
    ddl = """
CREATE VIRTUAL TABLE IF NOT EXISTS fts_current USING fts5(fragment_id UNINDEXED, content);
CREATE INDEX IF NOT EXISTS idx_current_pages_fragment ON current_pages(fragment_id);

-- Upsert helpers via triggers
CREATE TRIGGER IF NOT EXISTS trg_fts_current_ai AFTER INSERT ON current_pages BEGIN
  INSERT INTO fts_current(rowid, fragment_id, content) VALUES (NEW.fragment_id, NEW.fragment_id, NEW.content_text)
  ON CONFLICT(rowid) DO UPDATE SET content=excluded.content;
END;
CREATE TRIGGER IF NOT EXISTS trg_fts_current_au AFTER UPDATE ON current_pages BEGIN
  INSERT INTO fts_current(rowid, fragment_id, content) VALUES (NEW.fragment_id, NEW.fragment_id, NEW.content_text)
  ON CONFLICT(rowid) DO UPDATE SET content=excluded.content;
END;
CREATE TRIGGER IF NOT EXISTS trg_fts_current_ad AFTER DELETE ON current_pages BEGIN
  DELETE FROM fts_current WHERE rowid = OLD.fragment_id;
END;
"""
    if apply:
        _apply(conn, ddl)
    return dict(name=name, applied=apply, detail="table: fts_current + triggers")

def seed_standard_bodies(conn: sqlite3.Connection, apply: bool):
    name = "seed standard bodies"
    if not apply:
        return dict(name=name, applied=False, detail="dry-run")
    bodies = [
        ("CSA", "Canadian Standards Association", "CA"),
        ("ISO", "International Organization for Standardization", "INTL"),
        ("ANSI", "American National Standards Institute", "US"),
        ("EN", "European Standards (CEN)", "EU"),
        ("BS", "British Standards Institution", "UK"),
        ("AS", "Standards Australia", "AU"),
        ("JIS", "Japanese Industrial Standards", "JP"),
    ]
    cur = conn.cursor()
    try:
        for code, name_, ctry in bodies:
            cur.execute(
                """
                INSERT INTO standard_bodies(code, name, country)
                VALUES(?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET name=excluded.name, country=excluded.country
                """,
                (code, name_, ctry),
            )
        conn.commit()
    finally:
        cur.close()
    return dict(name=name, applied=True, detail=f"seeded {len(bodies)} bodies")


def seed_topics(conn: sqlite3.Connection, apply: bool):
    name = "seed topics (fall protection subset)"
    if not apply:
        return dict(name=name, applied=False, detail="dry-run")
    topics = [
        ("FP", "Protection contre les chutes", None),
        ("FP.GUARDRAIL", "Garde-corps", "FP"),
        ("FP.GUARDRAIL.HEIGHT", "Hauteur minimale", "FP.GUARDRAIL"),
        ("FP.GUARDRAIL.LOAD", "Résistance/charges", "FP.GUARDRAIL"),
        ("FP.WARNING_LINE", "Lignes d'avertissement", "FP"),
        ("FP.WARNING_LINE.OFFSET", "Distance du bord", "FP.WARNING_LINE"),
        ("FP.ROPE_ACCESS", "Accès sur cordes", "FP"),
        ("FP.ROPE_ACCESS.ANCHORS", "Ancrages", "FP.ROPE_ACCESS"),
    ]
    cur = conn.cursor()
    try:
        for code, name_, parent_code in topics:
            parent_id = None
            if parent_code:
                cur.execute("SELECT id FROM topics WHERE code=?", (parent_code,))
                row = cur.fetchone()
                parent_id = row[0] if row else None
            cur.execute(
                """
                INSERT INTO topics(code, name, parent_id)
                VALUES(?, ?, ?)
                ON CONFLICT(code) DO UPDATE SET name=excluded.name, parent_id=COALESCE(excluded.parent_id, topics.parent_id)
                """,
                (code, name_, parent_id),
            )
        conn.commit()
    finally:
        cur.close()
    return dict(name=name, applied=True, detail=f"seeded {len(topics)} topics")


def bump_user_version(conn: sqlite3.Connection, target: int, apply: bool):
    name = f"set PRAGMA user_version={target}"
    cur = conn.execute("PRAGMA user_version;")
    current = int(cur.fetchone()[0])
    if current >= target:
        return dict(name=name, applied=False, detail=f"already {current}")
    if apply:
        conn.execute(f"PRAGMA user_version={target};")
    return dict(name=name, applied=apply, detail=f"{current} -> {target}")

def update_roadmap(roadmap_path: str, db_path: str, steps, apply: bool):
    name = f"update {roadmap_path}"
    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%SZ")
    applied = False

    plan = []
    plan.append(f"**Auto-generated on {ts} (UTC).**")
    plan.append("")
    plan.append("### What this run ensured")
    for s in steps:
        mark = "✅" if s['applied'] else "•"
        plan.append(f"- {mark} {s['name']} — {s['detail']}")
    plan.append("")
    plan.append("### How to run the pipeline (correct CLI usage)")
    plan.append("```bash")
    plan.append("python -m lrn.cli extract --db-path legislation.sqlite --out-dir output --preview")
    plan.append("python -m lrn.cli extract --db-path legislation.sqlite --out-dir output")
    plan.append("python -m lrn.cli db verify --db-path legislation.sqlite --strict")
    plan.append("python -m lrn.cli db query --db-path legislation.sqlite current-by-fragment > output/current.csv")
    plan.append("```")
    plan.append("")
    plan.append("### Notes")
    plan.append("- Roadmap section is maintained between markers. Edit around it, not inside.")
    plan.append("- FTS5 is required for search; if missing, install a SQLite build with FTS5 (conda provides it).")
    plan.append("")
    plan.append("### Conda quickstart")
    plan.append("```bash")
    plan.append("conda create -n legis python=3.11 -c conda-forge")
    plan.append("conda activate legis")
    plan.append("conda install -c conda-forge sqlite requests beautifulsoup4 lxml pytest")
    plan.append("# optional for API: fastapi uvicorn")
    plan.append("```")
    plan.append("")
    plan.append("### Seeding")
    plan.append("- The script seeds a minimal topic taxonomy and standard bodies on --apply (idempotent).")
    body = "\n".join(plan)
    log("[ROADMAP] updating auto-block")

    new_block = f"{BEGIN}\n{body}\n{END}\n"

    try:
        with open(roadmap_path, "r", encoding="utf-8") as f:
            txt = f.read()
    except FileNotFoundError:
        txt = ""

    if BEGIN in txt and END in txt:
        pre = txt.split(BEGIN)[0]
        post = txt.split(END)[1]
        updated = pre + new_block + post
    else:
        updated = (txt + "\n\n" if txt else "") + "# Roadmap\n\n" + new_block

    if apply:
        with open(roadmap_path, "w", encoding="utf-8") as f:
            f.write(updated)
        applied = True

    return dict(name=name, applied=applied, detail=f"markers: {BEGIN}..{END}")

def main(argv=None):
    p = argparse.ArgumentParser(description="Upgrade DB to v5 and update roadmap.md")
    p.add_argument("--db", required=True, help="Path to SQLite DB (e.g., legislation.sqlite)")
    p.add_argument("--roadmap", default="ROADMAP.md", help="Path to roadmap file to update")
    p.add_argument("--apply", action="store_true", help="Apply changes (default: dry-run)")
    p.add_argument("--git-pull", action="store_true", help="git pull --rebase before making changes")
    p.add_argument("--git-commit", action="store_true", help="git add/commit after changes")
    p.add_argument("--git-push", action="store_true", help="git push after commit (implies --git-commit)")
    p.add_argument("--repo", default="g0udurix/LRN", help="GitHub repo slug for label sync (owner/repo)")
    p.add_argument("--project-url", default="https://github.com/users/g0udurix/projects/3", help="GitHub Projects v2 URL")
    p.add_argument("--setup-automation", action="store_true", help="ensure workflows & templates for Projects v2")
    p.add_argument("--sync-labels", action="store_true", help="sync a standard label set via gh")
    p.add_argument("--bundle", action="store_true", help="run bundle_codebase.py and capture output")
    args = p.parse_args(argv)

    conn = _connect(args.db)
    steps = []

    # Update the script header timestamp for sanity check
    self_update_header_timestamp(args.apply, log_fn=log)

    repo_dir = Path.cwd()
    ext_steps = []
    if args.git_pull:
        ext_steps.append(ensure_git_pull(repo_dir, args.apply))

    try:
        conn.execute("BEGIN;")
        steps.append(ensure_baseline_v1(conn, args.apply))
        steps.append(ensure_topics_taxonomy(conn, args.apply))
        steps.append(ensure_standards(conn, args.apply))
        steps.append(ensure_citations(conn, args.apply))
        steps.append(ensure_annotations(conn, args.apply))
        steps.append(ensure_orientations_and_knowledge(conn, args.apply))
        steps.append(ensure_comparisons(conn, args.apply))
        steps.append(ensure_ops(conn, args.apply))
        # Seed after tables exist
        steps.append(seed_standard_bodies(conn, args.apply))
        steps.append(seed_topics(conn, args.apply))
        # FTS after baseline
        steps.append(ensure_fts_current(conn, args.apply))
        steps.append(bump_user_version(conn, 5, args.apply))

        if args.apply:
            conn.commit()
        else:
            conn.rollback()
    except Exception as e:
        conn.rollback()
        print(f"[ERROR] {e}", file=sys.stderr)
        sys.exit(1)
    finally:
        conn.close()

    # Update roadmap (outside DB txn)
    steps.append(update_roadmap(args.roadmap, args.db, steps, args.apply))

    # Optional repo housekeeping
    if args.setup_automation:
        for it in setup_project_automation(repo_dir, args.project_url, args.apply):
            ext_steps.append(it)
    if args.sync_labels:
        ext_steps.append(sync_labels_with_gh(args.repo, args.apply))
    if args.bundle:
        ext_steps.append(run_bundle_codebase(repo_dir, args.apply))

    # Append a short entry to CHANGELOG.md
    summary = ", ".join([s['name'] for s in steps if s['applied']]) or "no DB changes"
    ext_steps.append(append_changelog(repo_dir, f"upgrade_and_roadmap: {summary}", args.apply))

    # Git commit/push
    if args.git_push:
        args.git_commit = True
    if args.git_commit:
        ext_steps.append(ensure_git_commit_push(repo_dir, "chore: run upgrade_and_roadmap", args.git_push, args.apply))

    # Print summary of main steps
    for s in steps:
        sym = "APPLIED" if s['applied'] else "OK"
        print(f"[{sym}] {s['name']} — {s['detail']}")
    # Print summary of extra steps
    for s in ext_steps:
        sym = "APPLIED" if s['applied'] else "OK"
        print(f"[{sym}] {s['name']} — {s['detail']}")
    if not args.apply:
        print("\n(dry-run only; re-run with --apply to commit)")

if __name__ == "__main__":
    main()
