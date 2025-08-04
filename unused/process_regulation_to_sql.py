#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a fully decoded database from all historical versions of a Légis Québec page,
storing the results in a Microsoft SQL Server database.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
from typing import Dict, Iterable, List, Optional, Tuple

import lxml.html as LH
import lxml.etree as ET
import pandas as pd
import pyodbc

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"

# --- Database Functions ---
def get_db_connection(server, database, username, password):
    """Establishes a connection to the SQL Server database."""
    try:
        conn_str = f'DRIVER={{ODBC Driver 17 for SQL Server}};SERVER={server};DATABASE={database};UID={username};PWD={password}'
        conn = pyodbc.connect(conn_str)
        return conn
    except pyodbc.Error as ex:
        sqlstate = ex.args[0]
        print(f"Database connection error: {sqlstate}", file=sys.stderr)
        print(ex, file=sys.stderr)
        sys.exit(1)

def setup_database_table(conn):
    """Creates the regulations table if it doesn't exist."""
    cursor = conn.cursor()
    table_name = "Regulations"
    # Check if table exists
    cursor.execute(f"IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='{table_name}' and xtype='U') CREATE TABLE {table_name} (ID NVARCHAR(255) NOT NULL, VersionDate NVARCHAR(20) NOT NULL, Type NVARCHAR(50), Classes NVARCHAR(255), Article NVARCHAR(50), MainText NVARCHAR(MAX), HistoricalNote NVARCHAR(MAX), DecodedRef NVARCHAR(MAX), DecodedParts NVARCHAR(MAX), DecodedTerm NVARCHAR(MAX), Title NVARCHAR(MAX), ModificationDate NVARCHAR(20), SourceURL NVARCHAR(500), AbrogationNotice NVARCHAR(MAX), OfficialStatus NVARCHAR(MAX), PdfURL NVARCHAR(500), PRIMARY KEY (ID, VersionDate))")
    conn.commit()
    print(f"Database table '{table_name}' is set up.")

def insert_data_to_sql(conn, rows: List[Dict[str, str]]):
    """Inserts rows into the Regulations table, avoiding duplicates."""
    cursor = conn.cursor()
    table_name = "Regulations"
    insert_count = 0
    for row in rows:
        # Check for existing record
        cursor.execute(f"SELECT COUNT(1) FROM {table_name} WHERE ID = ? AND VersionDate = ?", (row['ID'], row['VersionDate']))
        if cursor.fetchone()[0] == 0:
            columns = ', '.join(row.keys())
            placeholders = ', '.join(['?' for _ in row])
            sql = f"INSERT INTO {table_name} ({columns}) VALUES ({placeholders})"
            cursor.execute(sql, list(row.values()))
            insert_count += 1
    conn.commit()
    print(f"Inserted {insert_count} new rows into the database.")
    
# --- Scraper Functions (mostly unchanged) ---
def download_file(url: str, out_path: str, accept: Optional[str] = None) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    headers = ["-H", f"User-Agent: {UA}"]
    if accept:
        headers += ["-H", f"Accept: {accept}"]
    curl = shutil.which("curl")
    if curl:
        cmd = [curl, "-L", "--compressed", *headers, "-o", out_path, url]
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0: return
    wget = shutil.which("wget")
    if wget:
        cmd = [wget, "-q", "--content-disposition", "--header", f"User-Agent: {UA}", "-O", out_path, url]
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0: return
    if requests is None: raise RuntimeError("'requests' not available.")
    resp = requests.get(url, headers={"User-Agent": UA, "Accept": accept or "*/*"}, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f: f.write(resp.content)

def download_html(url: str, out_html: str) -> None:
    download_file(url, out_html, accept="text/html,application/xhtml+xml")

def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()

def find_version_links(html_bytes: bytes, base_url: str) -> List[Dict[str, str]]:
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(base_url)
    versions = []
    for a_tag in doc.xpath('//div[@id="accordion"]//a[contains(@href, "/document/rc/")]'):
        href = a_tag.get('href')
        date_text = normspace(a_tag.text_content())
        if href and date_text and re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
            versions.append({"VersionDate": date_text, "URL": href})
    if not versions: return [{"VersionDate": "current", "URL": base_url}]
    seen_urls = set()
    unique_versions = [v for v in versions if v["URL"] not in seen_urls and not seen_urls.add(v["URL"])]
    unique_versions.sort(key=lambda x: x['VersionDate'], reverse=True)
    return unique_versions

def process_version_page(version_info: Dict[str, str], save_dir: str) -> List[Dict[str, str]]:
    url, version_date = version_info['URL'], version_info['VersionDate']
    print(f"[HTML] Processing Version: {version_date} from {url}")
    save_path = os.path.join(save_dir, f"version-{version_date}.html")
    download_html(url, save_path)
    with open(save_path, "rb") as f: html_bytes = f.read()
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(url)
    title = normspace(doc.xpath('//h3[@class="card-title"]')[0].text_content()) if doc.xpath('//h3[@class="card-title"]') else ""
    mod_date = doc.xpath('//meta[@name="dc.date.modified"]/@content')[0] if doc.xpath('//meta[@name="dc.date.modified"]/@content') else ""
    abrogation_text = normspace(doc.xpath('//div[contains(@class, "alert-danger")]/h4')[0].text_content()) if doc.xpath('//div[contains(@class, "alert-danger")]/h4') else ""
    official_status_text = normspace(doc.xpath('//div[contains(@class, "alert-info")]')[0].text_content()) if doc.xpath('//div[contains(@class, "alert-info")]') else ""
    pdf_url = doc.xpath('//a[contains(@href, ".pdf")]')[0].get('href') if doc.xpath('//a[contains(@href, ".pdf")]') else ""
    metadata = {"VersionDate": version_date, "Title": title, "ModificationDate": mod_date, "SourceURL": url, "AbrogationNotice": abrogation_text, "OfficialStatus": official_status_text, "PdfURL": pdf_url}
    container = doc.xpath("//div[@id='mainContent-document']")[0] if doc.xpath("//div[@id='mainContent-document']") else None
    if container is None:
        print(f"  [WARN] mainContent-document not found in {url}", file=sys.stderr)
        return []
    return rows_from_iter(iterate_ids_from_html_block(container), metadata)

def rows_from_iter(iterable: Iterable[Tuple[str,str, str]], metadata: Dict[str, str]) -> List[Dict[str,str]]:
    # This function and its helpers (split_main_and_history, etc.) are complex and self-contained.
    # For brevity, their direct implementation is omitted here, but they are the same as the previous script.
    # They perform the core parsing logic.
    rows = []
    for idv, txt, classes in iterable:
        main_text, history = split_main_and_history(txt)
        decoded_ref, parts_map = build_decoded_ref(idv)
        rows.append({
            "ID": idv, "Type": classify_id(idv), "Classes": classes, "Article": article_from_id(idv), "MainText": main_text, "HistoricalNote": history,
            "DecodedRef": decoded_ref, "DecodedParts": " | ".join([f"{k}={v}" for k,v in parts_map.items() if v]),
            "DecodedTerm": extract_df_term(main_text) if "-df:" in idv else "", **metadata
        })
    return rows

# --- Helper functions for parsing IDs, same as before ---
def split_main_and_history(txt: str) -> Tuple[str, str]:
    if not txt: return "", ""
    m = re.search(r"R\.R\.Q\.|D\.\s?\d|L\.Q\.", txt)
    return (txt[:m.start()].rstrip(), txt[m.start():].lstrip()) if m else (txt, "")
def build_decoded_ref(id_str: str) -> Tuple[str, Dict[str, str]]:
    parts = id_str.split("-"); decoded_parts = {"Article": "", "Alinéa": "", "Niveau2": "", "Niveau3": "", "Niveau4": ""}
    if not parts or not parts[0].startswith("se:"): return "", decoded_parts
    article_code = part_value(parts[0]).replace("_", "."); decoded_parts["Article"] = article_code; ref = article_code
    p1,p2,p3=None,None,None
    for s in parts[1:]:
        if s.startswith("p1:"): p1=part_value(s)
        elif s.startswith("p2:"): p2=part_value(s)
        elif s.startswith("p3:"): p3=part_value(s)
    had_al=False
    if p1:
        f1=token_to_human(p1,1)
        if f1.startswith("al. "): ref=f"{ref} {f1}"; had_al=True; decoded_parts["Alinéa"]=f1.replace("al. ","")
        else: ref=f"{ref} {f1}"; decoded_parts["Alinéa"]=f1
    if p2:
        f2=token_to_human(p2,2)
        if f2.startswith("("):
            if had_al or p1: ref=f"{ref} {f2}"
            else: ref=f"{ref}{f2}"
        else: ref=f"{ref} {f2}"
        decoded_parts["Niveau2"]=f2
    if p3: f3=token_to_human(p3,3); ref=f"{ref}{f3}"; decoded_parts["Niveau3"]=f3
    return ref, decoded_parts
def part_value(s:str)->str: return s.split(":",1)[1] if ":" in s else s
def is_numeric_token(t:str)->bool: return bool(re.fullmatch(r"^\d+(?:_\d+)*$",t))
def token_to_human(t:str,l:int)->str:
    if l==1: return f"al. {t.replace('_','.')}" if is_numeric_token(t) else f"{t})"
    return f"({t.replace('_','.')})" if is_numeric_token(t) else f"{t})"
def classify_id(i:str)->str: return "Provision" if i.startswith("se:") else "Heading" if i.startswith("ga:") else "Annexe" if i.startswith("sc-nb:") else "Technique"
def article_from_id(i:str)->str: return part_value(i.split("-",1)[0]).replace("_",".") if i.startswith("se:") else ""
def extract_df_term(t:str)->str: m=re.search(r'«\s*([^»]+?)\s*»',t) or re.search(r'"([^"]+)"',t); return m.group(1).strip() if m else ""
def iterate_ids_from_html_block(c: ET._Element) -> Iterable[Tuple[str,str,str]]:
    for el in c.xpath(".//*[@id]"): yield el.get("id"), normspace("".join(el.itertext())), el.get("class","")

def main():
    ap = argparse.ArgumentParser(description="Archive all historical versions of a Légis Québec regulation to SQL Server.")
    ap.add_argument("--url", "-u", required=True, help="Main Légis Québec URL for the regulation")
    ap.add_argument("--save-dir", default="html_versions", help="Directory to save downloaded HTML files")
    # DB Arguments
    ap.add_argument("--server", required=True, help="SQL Server name or IP address")
    ap.add_argument("--database", required=True, help="Database name")
    ap.add_argument("--user", required=True, help="Database username")
    ap.add_argument("--password", required=True, help="Database password")
    args = ap.parse_args()
    
    os.makedirs(args.save_dir, exist_ok=True)
    
    # Database Connection
    conn = get_db_connection(args.server, args.database, args.user, args.password)
    setup_database_table(conn)
    
    print(f"[INFO] Starting archival for: {args.url}")
    main_page_path = os.path.join(args.save_dir, "main_page.html")
    download_html(args.url, main_page_path)
    with open(main_page_path, "rb") as f: main_html_bytes = f.read()
        
    versions = find_version_links(main_html_bytes, args.url)
    print(f"[INFO] Found {len(versions)} historical versions to process.")

    all_rows = []
    for version_info in versions:
        try:
            version_rows = process_version_page(version_info, args.save_dir)
            all_rows.extend(version_rows)
        except Exception as e:
            print(f"  [ERROR] Failed to process version {version_info['VersionDate']}: {e}", file=sys.stderr)

    if not all_rows:
        print("[ERROR] No data was extracted from any version.", file=sys.stderr)
        conn.close()
        sys.exit(1)
        
    insert_data_to_sql(conn, all_rows)
    
    conn.close()
    print(f"\n[SUCCESS] Database archival complete.")

if __name__ == "__main__":
    main()
