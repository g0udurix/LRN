#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Archives multiple legislative documents, including their full version history and PDFs,
into a normalized SQLite database.
"""

import argparse
import os
import re
import shutil
import sqlite3
import subprocess
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import lxml.html as LH
import pandas as pd

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"

# --- Database Functions ---
def get_db_connection(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def setup_database(conn: sqlite3.Connection):
    cursor = conn.cursor()
    # Main regulations table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS Regulations (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        number TEXT UNIQUE NOT NULL,
        title TEXT NOT NULL,
        main_url TEXT,
        category TEXT
    )""")
    # Versions table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS RegulationVersions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        regulation_id INTEGER NOT NULL,
        version_date TEXT NOT NULL,
        modification_date TEXT,
        source_url TEXT UNIQUE NOT NULL,
        abrogation_notice TEXT,
        official_status TEXT,
        pdf_path TEXT,
        FOREIGN KEY (regulation_id) REFERENCES Regulations(id)
    )""")
    # Content table
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS VersionContent (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        version_id INTEGER NOT NULL,
        content_id_str TEXT NOT NULL,
        type TEXT,
        classes TEXT,
        article_number TEXT,
        main_text TEXT,
        historical_note TEXT,
        decoded_ref TEXT,
        decoded_parts TEXT,
        decoded_term TEXT,
        FOREIGN KEY (version_id) REFERENCES RegulationVersions(id)
    )""")
    conn.commit()
    print("Database and tables are set up.")

def get_or_create_regulation(conn: sqlite3.Connection, number: str, title: str, main_url: str, category: str) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM Regulations WHERE number = ?", (number,))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        cursor.execute(
            "INSERT INTO Regulations (number, title, main_url, category) VALUES (?, ?, ?, ?)",
            (number, title, main_url, category)
        )
        conn.commit()
        return cursor.lastrowid

def insert_version(conn: sqlite3.Connection, regulation_id: int, data: Dict) -> int:
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM RegulationVersions WHERE source_url = ?", (data['source_url'],))
    row = cursor.fetchone()
    if row:
        return row[0]
    else:
        cursor.execute("""
            INSERT INTO RegulationVersions (regulation_id, version_date, modification_date, source_url, abrogation_notice, official_status, pdf_path)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (regulation_id, data['version_date'], data['modification_date'], data['source_url'], data['abrogation_notice'], data['official_status'], data['pdf_path']))
        conn.commit()
        return cursor.lastrowid

def insert_content_bulk(conn: sqlite3.Connection, version_id: int, content_rows: List[Dict]):
    cursor = conn.cursor()
    to_insert = []
    for row in content_rows:
        # Check if this specific content for this version already exists
        cursor.execute("SELECT id FROM VersionContent WHERE version_id = ? AND content_id_str = ?", (version_id, row['content_id_str']))
        if not cursor.fetchone():
            to_insert.append((version_id, row['content_id_str'], row['type'], row['classes'], row['article_number'], row['main_text'], row['historical_note'], row['decoded_ref'], row['decoded_parts'], row['decoded_term']))
    
    if to_insert:
        cursor.executemany("""
            INSERT INTO VersionContent (version_id, content_id_str, type, classes, article_number, main_text, historical_note, decoded_ref, decoded_parts, decoded_term)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, to_insert)
        conn.commit()
        print(f"  -> Inserted {len(to_insert)} new content rows for version_id {version_id}.")

# --- Scraper & Parser Functions ---
def download_file(url: str, out_path: str, accept: Optional[str] = None):
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    headers = ["-H", f"User-Agent: {UA}"]
    if accept: headers += ["-H", f"Accept: {accept}"]
    
    curl = shutil.which("curl")
    if curl:
        cmd = [curl, "-L", "--compressed", *headers, "-o", out_path, url]
        try:
            subprocess.run(cmd, check=True, capture_output=True, timeout=120)
            if os.path.exists(out_path) and os.path.getsize(out_path) > 0: return True
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            print(f"  [WARN] curl failed for {url}: {e}", file=sys.stderr)
    
    # Fallback to requests if curl fails or is not available
    try:
        import requests
        resp = requests.get(url, headers={"User-Agent": UA, "Accept": accept or "*/*"}, timeout=60)
        resp.raise_for_status()
        with open(out_path, "wb") as f: f.write(resp.content)
        return True
    except Exception as e:
        print(f"  [ERROR] requests failed for {url}: {e}", file=sys.stderr)
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

def parse_version_page(html_bytes: bytes, base_url: str, pdf_dir: str) -> Tuple[Dict, List[Dict]]:
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(base_url)

    # --- Metadata Extraction ---
    title_node = doc.xpath('//div[@class="card-header"]//h3')
    full_title = normspace(title_node[0].text_content()) if title_node else "Titre non trouvé"
    
    # Extract number like 'S-2.1, r. 3' from title
    num_match = re.search(r'^[A-Z0-9.\-,]+\s*-', full_title)
    regulation_number = num_match.group(1) if num_match else "Numéro inconnu"

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
        pdf_filename = f"{regulation_number.replace(', ', '_').replace('.', '-')}-{os.path.basename(pdf_url)}"
        pdf_path = os.path.join(pdf_dir, pdf_filename)
        print(f"  -> Downloading PDF from {pdf_url}...")
        if not download_file(pdf_url, pdf_path, "application/pdf"):
            pdf_path = "" # Download failed

    version_metadata = {
        "title": full_title,
        "number": regulation_number,
        "modification_date": mod_date,
        "abrogation_notice": abrogation_text,
        "official_status": official_status_text,
        "pdf_path": pdf_path,
    }

    # --- Content Parsing ---
    content_rows = []
    container = doc.xpath("//div[@id='mainContent-document']")
    if container:
        # Simplified content parsing logic for brevity
        for el in container[0].xpath(".//*[@id]"):
            content_rows.append({
                "content_id_str": el.get("id"),
                "type": "Provision", # Simplified
                "classes": el.get("class", ""),
                "article_number": el.get("id").split('-')[0], # Simplified
                "main_text": normspace("".join(el.itertext())),
                "historical_note": "", # Simplified
                "decoded_ref": "", "decoded_parts": "", "decoded_term": ""
            })

    return version_metadata, content_rows


def main():
    ap = argparse.ArgumentParser(description="Archive legislative documents to a normalized SQLite database.")
    ap.add_argument("--url", "-u", required=True, help="Main URL of the legislative document to archive.")
    ap.add_argument("--category", default="Règlement", help="Category of the document (e.g., Loi, Norme).")
    ap.add_argument("--db-path", default="legislation_archive.db", help="Path to the SQLite database file.")
    ap.add_argument("--save-dir", default="archive", help="Directory to save downloaded HTML and PDFs.")
    args = ap.parse_args()

    # Setup directories
    html_dir = os.path.join(args.save_dir, "html")
    pdf_dir = os.path.join(args.save_dir, "pdfs")
    os.makedirs(html_dir, exist_ok=True)
    os.makedirs(pdf_dir, exist_ok=True)

    # Setup database
    conn = get_db_connection(args.db_path)
    setup_database(conn)

    print(f"--- Starting archival for: {args.url} ---")
    
    # 1. Download main page to find versions
    main_page_path = os.path.join(html_dir, f"main_{re.sub('[^a-zA-Z0-9]', '_', args.url)}.html")
    if not download_file(args.url, main_page_path, "text/html"):
        print(f"[FATAL] Could not download the main page. Aborting.", file=sys.stderr)
        conn.close()
        sys.exit(1)

    with open(main_page_path, "rb") as f:
        versions = find_version_links(f.read(), args.url)
    print(f"Found {len(versions)} historical version(s) to process.")

    # 2. Process each version
    for v_info in versions:
        version_url = v_info['source_url']
        print(f"\nProcessing Version: {v_info['version_date']} from {version_url}")
        
        version_page_path = os.path.join(html_dir, f"version_{re.sub('[^a-zA-Z0-9]', '_', version_url)}.html")
        if not download_file(version_url, version_page_path, "text/html"):
            print(f"  [ERROR] Skipping version due to download failure.", file=sys.stderr)
            continue
            
        with open(version_page_path, "rb") as f:
            v_metadata, v_content = parse_version_page(f.read(), version_url, pdf_dir)
        
        # 3. Insert into DB
        # Get or create the main regulation entry
        regulation_id = get_or_create_regulation(conn, v_metadata['number'], v_metadata['title'], args.url, args.category)
        
        # Insert the version entry
        v_info.update(v_metadata) # Add metadata to version info
        version_id = insert_version(conn, regulation_id, v_info)
        
        # Insert the content entries
        if v_content:
            insert_content_bulk(conn, version_id, v_content)
        else:
            print(f"  -> No content found for version_id {version_id}.")

    conn.close()
    print(f"\n--- Archival complete. Database is at: {os.path.abspath(args.db_path)} ---")

if __name__ == "__main__":
    main()
