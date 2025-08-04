#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Ingestion Script for the Knowledge Base.

This script scrapes a given legislative document URL, parses it, and populates
the normalized SQLite knowledge base created by 'setup_knowledge_base.py'.
"""

import argparse
import os
import re
import sqlite3
import subprocess
import sys
import time
from typing import Dict, List, Optional, Tuple
from urllib.parse import urljoin

import lxml.html as LH

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"

# --- Database Interaction ---
def get_db_connection(db_path: str) -> sqlite3.Connection:
    """Establishes a connection to the SQLite database and enables foreign keys."""
    if not os.path.exists(db_path):
        print(f"Error: Database file not found at '{db_path}'. Please run 'setup_knowledge_base.py' first.", flush=True)
        raise FileNotFoundError
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def get_or_create_jurisdiction(conn: sqlite3.Connection, name: str, j_type: str, parent_id: Optional[int] = None) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Jurisdictions WHERE name = ?", (name,))
    row = cursor.fetchone()
    if row:
        return row['id']
    else:
        cursor.execute(
            "INSERT INTO Jurisdictions (name, type, parent_id) VALUES (?, ?, ?)",
            (name, j_type, parent_id)
        )
        conn.commit()
        return cursor.lastrowid

def insert_asset(conn: sqlite3.Connection, data: Dict) -> int:
    cursor = conn.cursor()
    # Check if a similar asset already exists to avoid simple duplicates
    cursor.execute("SELECT id FROM InformationAssets WHERE official_number = ? AND jurisdiction_id = ?", (data['official_number'], data['jurisdiction_id']))
    row = cursor.fetchone()
    if row:
        print(f"  - Asset '{data['title']}' already exists with ID: {row['id']}.")
        return row['id']
    
    cursor.execute("""
        INSERT INTO InformationAssets (asset_type, title, official_number, jurisdiction_id, publication_date, source_url, consultation_date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (data['asset_type'], data['title'], data['official_number'], data['jurisdiction_id'], data['publication_date'], data['source_url'], data['consultation_date']))
    conn.commit()
    asset_id = cursor.lastrowid
    print(f"  - Created new InformationAsset with ID: {asset_id}.")
    return asset_id

def _infer_parent_oid(oid: str) -> Optional[str]:
    if not oid:
        return None
    # Example: 'se:2-ss:1-pp:3' -> parent 'se:2-ss:1'; 'se:2' -> None
    if '-' in oid:
        return oid.rsplit('-', 1)[0]
    return None


def insert_content_blocks(conn: sqlite3.Connection, asset_id: int, blocks: List[Dict]):
    cursor = conn.cursor()
    # Preload a map: original_id_str -> id (for this asset) as we insert
    oid_to_id: Dict[str, int] = {}

    # First pass: determine parent relationships by original_id_str
    to_insert = []
    for idx, block in enumerate(blocks):
        oid = block.get('content_id_str') or block.get('original_id_str')
        parent_oid = _infer_parent_oid(oid or '')
        # Derive semantic block_type from oid
        btype = 'Texte'
        if oid:
            if oid.startswith('se:'):
                btype = 'Article'
            if '-ss:' in oid or oid.startswith('ss:'):
                btype = 'Alinéa'
            if oid.startswith('sc-nb:'):
                btype = 'Annexe'
        to_insert.append({
            'asset_id': asset_id,
            'parent_oid': parent_oid,
            'display_order': idx,  # sequential if not provided
            'block_type': block.get('type') or block.get('block_type') or btype,
            'text_content': block.get('main_text') or block.get('text_content') or '',
            'file_path': block.get('file_path'),
            'original_id_str': oid,
        })

    # Insert all blocks with parent_id temporarily null; then update parent_ids
    cursor.executemany(
        """
        INSERT INTO ContentBlocks (asset_id, parent_id, display_order, block_type, text_content, file_path, original_id_str)
        VALUES (?, NULL, ?, ?, ?, ?, ?)
        """,
        [
            (
                asset_id,
                row['display_order'],
                row['block_type'],
                row['text_content'],
                row['file_path'],
                row['original_id_str'],
            ) for row in to_insert
        ]
    )
    conn.commit()

    # Build oid -> id map for inserted rows
    cursor.execute(
        "SELECT id, original_id_str FROM ContentBlocks WHERE asset_id = ? ORDER BY id",
        (asset_id,)
    )
    for r in cursor.fetchall():
        oid_to_id[r['original_id_str']] = r['id']

    # Update parent_id using the parent_oid mapping
    updates = []
    for row in to_insert:
        po = row['parent_oid']
        if po and po in oid_to_id:
            updates.append((oid_to_id[po], asset_id, row['original_id_str']))
    if updates:
        cursor.executemany(
            "UPDATE ContentBlocks SET parent_id = ? WHERE asset_id = ? AND original_id_str = ?",
            updates,
        )
        conn.commit()

    print(f"  - Inserted {len(to_insert)} new content blocks for asset ID {asset_id} and linked parents where possible.")

# --- Scraper & Parser ---
def download_file(url: str, out_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    # Using curl for robustness
    try:
        subprocess.run(['curl', '-L', '-A', UA, '-o', out_path, url], check=True, capture_output=True, timeout=120)
        return True
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
        print(f"  [WARN] curl failed for {url}: {e}", file=sys.stderr)
        return False

def normspace(s: str) -> str: return re.sub(r"\s+", " ", s or "").strip()

def find_version_links(html_bytes: bytes, base_url: str) -> List[Dict[str, str]]:
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(base_url)
    versions = []
    # Find links in the main historical versions accordion
    for a_tag in doc.xpath('//div[@id="accordion"]//a[contains(@href, "/document/rc/") or contains(@href, "/document/lq/")]'):
        href = a_tag.get('href')
        date_text = normspace(a_tag.text_content())
        if href and date_text and re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
            versions.append({"version_date": date_text, "source_url": href})
    
    if not versions: versions.append({"version_date": "current", "source_url": base_url})
    
    seen_urls = set()
    unique_versions = [v for v in versions if v["source_url"] not in seen_urls and not seen_urls.add(v["source_url"])]
    unique_versions.sort(key=lambda x: x['version_date'], reverse=True)
    return unique_versions

def parse_legisquebec_page(html_bytes: bytes, url: str) -> Tuple[Dict, List[Dict]]:
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(url)
    
    # --- Metadata Extraction ---
    title_nodes = doc.xpath('//div[@class="card-header"]//h3 | //header//h3')
    full_title = "Titre non trouvé"
    regulation_number = "Numéro inconnu"
    
    if title_nodes:
        raw_title = title_nodes[0].text_content()
        # Normalize spaces incl. non-breaking spaces
        raw_title = (raw_title or "").replace('\xa0', ' ')
        full_title = normspace(raw_title)
        # Prefer explicit LQ pattern like "S-2.1, r. 3 – Titre"
        m = re.match(r"^\s*(S-\d+(?:\.\d+)?\s*,\s*r\.\s*\d+)\s*[–-]\s*(.+)$", full_title, flags=re.IGNORECASE)
        if m:
            regulation_number = m.group(1).strip()
            full_title = m.group(2).strip()
        else:
            # Fallback: split on first dash (hyphen or en dash)
            m2 = re.match(r"^\s*([^–-]+?)\s*[–-]\s*(.+)$", full_title)
            if m2:
                candidate_num = normspace(m2.group(1))
                title_rest = normspace(m2.group(2))
                # Validate candidate looks like official number (allow letters/digits, dots, commas, spaces, r., hyphens)
                if re.match(r"^[A-Za-z0-9\-.,\s]+$", candidate_num):
                    regulation_number = candidate_num
                    full_title = title_rest
            # Else leave defaults

    # Ensure not empty
    if not full_title:
        full_title = "Titre non trouvé"

    mod_date_meta = doc.xpath('//meta[@name="dc.date.modified"]/@content')
    mod_date = mod_date_meta[0] if mod_date_meta else ""
    
    abrogation_node = doc.xpath('//div[contains(@class, "alert-danger")]/h4')
    abrogation_text = normspace(abrogation_node[0].text_content()) if abrogation_node else ""

    official_status_node = doc.xpath('//div[contains(@class, "alert-info")]')
    official_status_text = normspace(official_status_node[0].text_content()) if official_status_node else ""

    pdf_link_node = doc.xpath('//a[contains(@href, ".pdf")]')
    pdf_url = pdf_link_node[0].get('href') if pdf_link_node else ""
    pdf_path = ""
    if pdf_url:
        safe_reg_num = re.sub(r'[^a-zA-Z0-9_]', '_', regulation_number)
        pdf_filename = f"{safe_reg_num}-{os.path.basename(pdf_url)}"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        print(f"  -> Downloading PDF from {pdf_url}...")
        if not download_file(pdf_url, pdf_path):
            pdf_path = ""

    version_metadata = {
        "title": full_title,
        "official_number": regulation_number,
        "modification_date": mod_date,
        "abrogation_notice": abrogation_text,
        "official_status": official_status_text,
        "pdf_path": pdf_path,
    }

    # --- Content Parsing ---
    content_rows = []
    container = doc.xpath("//div[@id='mainContent-document']")
    if container:
        for i, el in enumerate(container[0].xpath(".//*[@id]")):
            content_rows.append({
                "content_id_str": el.get("id"),
                "type": "Provision",
                "classes": el.get("class", ""),
                "article_number": (el.get("id") or "").split('-')[0],
                "main_text": normspace("".join(el.itertext())),
                "historical_note": "",
                "decoded_ref": "", "decoded_parts": "", "decoded_term": ""
            })

    return version_metadata, content_rows


def _decode_oid(oid: Optional[str]) -> str:
    if not oid:
        return ""
    try:
        parts = oid.split('-')
        art = None
        al = None
        annexe = None
        others = []
        for p in parts:
            if p.startswith('se:'):
                art = p.split(':',1)[1]
            elif p.startswith('ss:'):
                al = p.split(':',1)[1]
            elif p.startswith('sc-nb:'):
                annexe = p.split(':',1)[1]
            else:
                others.append(p.replace(':', ' '))
        ref = []
        if art:
            ref.append(f"Art. {art}")
        if al:
            ref.append(f"al. {al}")
        if annexe:
            ref.append(f"Annexe {annexe}")
        if others:
            ref.append(' '.join(others))
        return ', '.join(ref) if ref else oid
    except Exception:
        return oid


def _print_block_tree(blocks_by_parent: Dict[Optional[int], List[sqlite3.Row]], parent_id: Optional[int], prefix: str = ""):
    children = blocks_by_parent.get(parent_id, [])
    for idx, row in enumerate(children):
        is_last = (idx == len(children) - 1)
        branch = "└─" if is_last else "├─"
        nxt_prefix = ("  " if is_last else "│ ")
        text = (row["text_content"] or "").strip().replace("\n", " ")
        if len(text) > 80:
            text = text[:77] + "..."
        oid = row['original_id_str'] or ''
        decoded = _decode_oid(oid)
        print(f"{prefix}{branch} Block[{row['id']}] ({row['block_type'] or '-'}) oid='{oid}' [{decoded}] ord={row['display_order']}: {text}")
        _print_block_tree(blocks_by_parent, row["id"], prefix + nxt_prefix)


def print_asset_tree(conn: sqlite3.Connection, asset_id: int, root_block_id: Optional[int] = None):
    cur = conn.cursor()
    cur.execute("SELECT id, asset_type, title, official_number FROM InformationAssets WHERE id = ?", (asset_id,))
    asset = cur.fetchone()
    if not asset:
        print(f"[WARN] Asset id {asset_id} not found.")
        return

    print(f"Asset[{asset['id']}] {asset['official_number'] or '-'} — {asset['title'] or ''} ({asset['asset_type'] or ''})")

    params = [asset_id]
    where = "asset_id = ?"
    if root_block_id is not None:
        where += " AND (id = ? OR parent_id = ?)"
        params.extend([root_block_id, root_block_id])

    cur.execute(f"""
        SELECT id, parent_id, display_order, block_type, text_content, file_path, original_id_str
        FROM ContentBlocks
        WHERE {where}
        ORDER BY COALESCE(parent_id, -1), COALESCE(display_order, 0), id
    """, params)
    rows = cur.fetchall()

    # Build index parent -> children
    blocks_by_parent: Dict[Optional[int], List[sqlite3.Row]] = {}
    for r in rows:
        blocks_by_parent.setdefault(r["parent_id"], []).append(r)

    # Start from root (None) or from a specific root_block_id
    start_parent = None if root_block_id is None else root_block_id
    _print_block_tree(blocks_by_parent, start_parent)


def print_trees_entrypoint(args):
    # DB connection
    try:
        conn = get_db_connection(args.db_path)
    except FileNotFoundError:
        sys.exit(1)

    cur = conn.cursor()

    asset_ids: List[int] = []
    if getattr(args, "all", False):
        cur.execute("SELECT id FROM InformationAssets ORDER BY id")
        asset_ids = [r[0] for r in cur.fetchall()]
    elif getattr(args, "asset_id", None) is not None:
        asset_ids = [args.asset_id]
    elif getattr(args, "official_number", None):
        cur.execute("SELECT id FROM InformationAssets WHERE official_number = ?", (args.official_number,))
        row = cur.fetchone()
        if not row:
            print(f"[WARN] No asset found with official_number='{args.official_number}'.")
            conn.close()
            return
        asset_ids = [row[0]]
    else:
        print("[ERROR] You must specify one of --official-number, --asset-id, or --all.")
        conn.close()
        return

    for aid in asset_ids:
        print_asset_tree(conn, aid, args.root_block_id)
        if aid != asset_ids[-1]:
            print()

    conn.close()


def main():
    parser = argparse.ArgumentParser(description="Knowledge base ingestion and inspection tool.")

    subparsers = parser.add_subparsers(dest="command")

    # Ingest subcommand
    ingest_p = subparsers.add_parser("ingest", help="Ingest a legislative document URL.")
    ingest_p.add_argument("--url", required=True, help="URL of the document to ingest.")
    ingest_p.add_argument("--category", default="Règlement", help="Category of the document (e.g., Loi, Norme).")
    ingest_p.add_argument("--db-path", default="knowledge_base.db", help="Path to the SQLite database file.")
    ingest_p.add_argument("--save-dir", default="archive", help="Directory to save downloaded files.")
    ingest_p.add_argument("--jurisdiction-name", default="Québec", help="Name of the jurisdiction.")
    ingest_p.add_argument("--jurisdiction-type", default="Province", help="Type of the jurisdiction (e.g., Province, Pays, Ville, Organisme).")

    # Print-tree subcommand
    tree_p = subparsers.add_parser("print-tree", help="Print an ASCII tree of assets and their content blocks.")
    tree_p.add_argument("--db-path", default="knowledge_base.db", help="Path to the SQLite database file.")
    sel = tree_p.add_mutually_exclusive_group(required=True)
    sel.add_argument("--official-number", dest="official_number", help="Official number of the asset, e.g., 'S-2.1, r. 3'.")
    sel.add_argument("--asset-id", type=int, help="ID of the asset.")
    sel.add_argument("--all", action="store_true", help="Print trees for all assets.")
    tree_p.add_argument("--root-block-id", type=int, default=None, help="Start the tree from a specific ContentBlocks.id (branch view).")

    # Rebuild-links subcommand
    rebuild_p = subparsers.add_parser("rebuild-links", help="Rebuild parent_id links for ContentBlocks using original_id_str within an asset or all.")
    rebuild_p.add_argument("--db-path", default="knowledge_base.db", help="Path to the SQLite database file.")
    rs = rebuild_p.add_mutually_exclusive_group(required=True)
    rs.add_argument("--asset-id", type=int, help="Asset ID to rebuild.")
    rs.add_argument("--all", action="store_true", help="Rebuild links for all assets.")

    args = parser.parse_args()

    if args.command == "print-tree":
        print_trees_entrypoint(args)
        return

    if args.command == "rebuild-links":
        try:
            conn = get_db_connection(args.db_path)
        except FileNotFoundError:
            sys.exit(1)
        cur = conn.cursor()
        asset_ids: List[int] = []
        if getattr(args, "all", False):
            cur.execute("SELECT id FROM InformationAssets")
            asset_ids = [r[0] for r in cur.fetchall()]
        else:
            asset_ids = [args.asset_id]

        for aid in asset_ids:
            # Build map of oid->id
            cur.execute("SELECT id, original_id_str FROM ContentBlocks WHERE asset_id = ?", (aid,))
            rows = cur.fetchall()
            oid_to_id = {r['original_id_str']: r['id'] for r in rows if r['original_id_str']}
            updates = []
            for r in rows:
                oid = r['original_id_str'] or ''
                parent_oid = _infer_parent_oid(oid)
                if parent_oid and parent_oid in oid_to_id:
                    updates.append((oid_to_id[parent_oid], r['id']))
            if updates:
                cur.executemany("UPDATE ContentBlocks SET parent_id = ? WHERE id = ?", updates)
                conn.commit()
                print(f"[rebuild] Asset {aid}: updated {len(updates)} links.")
            else:
                print(f"[rebuild] Asset {aid}: no updates.")
        conn.close()
        return

    if args.command == "ingest":
        # Setup directories
        html_dir = os.path.join(args.save_dir, "html")
        pdf_dir = os.path.join(args.save_dir, "pdfs")
        os.makedirs(html_dir, exist_ok=True)
        os.makedirs(pdf_dir, exist_ok=True)

        # Setup database connection
        try:
            conn = get_db_connection(args.db_path)
        except FileNotFoundError:
            sys.exit(1)

        print(f"--- Starting ingestion for: {args.url} ---")
        
        # 1. Get or create Jurisdiction
        jurisdiction_id = get_or_create_jurisdiction(conn, args.jurisdiction_name, args.jurisdiction_type)

        # 2. Download and parse the document
        page_path = os.path.join(html_dir, f"ingest_{re.sub('[^a-zA-Z0-9]', '_', args.url)}.html")
        if not download_file(args.url, page_path):
            print(f"[FATAL] Could not download the page. Aborting.", file=sys.stderr)
            conn.close()
            sys.exit(1)

        with open(page_path, "rb") as f:
            asset_metadata, content_blocks = parse_legisquebec_page(f.read(), args.url)
        
        asset_metadata['jurisdiction_id'] = jurisdiction_id
        asset_metadata['asset_type'] = args.category
        
        # 3. Insert data into the database
        if not content_blocks:
            print("[ERROR] No content was extracted from the page. Aborting ingestion.", file=sys.stderr)
            conn.close()
            sys.exit(1)
            
        asset_id = insert_asset(conn, asset_metadata)
        insert_content_blocks(conn, asset_id, content_blocks)
        
        conn.close()
        print(f"\n--- Ingestion complete for {args.url} ---")
        return

    # Default: show help
    parser.print_help()

if __name__ == "__main__":
    main()
