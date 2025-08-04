#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a fully decoded CSV from all historical versions of a Légis Québec page.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from typing import Dict, Iterable, List, Optional, Tuple
from urllib.parse import urljoin

import lxml.html as LH
import lxml.etree as ET
import pandas as pd

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"


def download_file(url: str, out_path: str, accept: Optional[str] = None) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)
    headers = ["-H", f"User-Agent: {UA}"]
    if accept:
        headers += ["-H", f"Accept: {accept}"]

    curl = shutil.which("curl")
    if curl:
        cmd = [curl, "-L", "--compressed", *headers, "-o", out_path, url]
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return

    wget = shutil.which("wget")
    if wget:
        cmd = [wget, "-q", "--content-disposition", "--header", f"User-Agent: {UA}", "-O", out_path, url]
        subprocess.run(cmd, check=True, capture_output=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return

    if requests is None:
        raise RuntimeError("curl/wget failed and 'requests' not available.")
    resp = requests.get(url, headers={"User-Agent": UA, "Accept": accept or "*/*"}, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)


def download_html(url: str, out_html: str) -> None:
    download_file(url, out_html, accept="text/html,application/xhtml+xml")


def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def find_version_links(html_bytes: bytes, base_url: str) -> List[Dict[str, str]]:
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(base_url)
    versions = []
    
    # Find links in the main historical versions accordion
    for a_tag in doc.xpath('//div[@id="accordion"]//a[contains(@href, "/document/rc/")]'):
        href = a_tag.get('href')
        date_text = normspace(a_tag.text_content())
        if href and date_text and re.match(r'^\d{4}-\d{2}-\d{2}$', date_text):
            versions.append({"VersionDate": date_text, "URL": href})

    # Also include the current version if it's not in the list
    current_version_link = doc.xpath('//a[contains(text(), "Afficher le texte complet à cette date")]')
    if current_version_link:
        href = current_version_link[0].get('href')
        # The date for the current version is not always clearly marked in the same way.
        # We will extract it from the URL if possible, or use the modification date as a fallback.
        date_match = re.search(r'/(\d{8})', href)
        if date_match:
            date_str = date_match.group(1)
            version_date = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:]}"
            if not any(v['VersionDate'] == version_date for v in versions):
                 versions.append({"VersionDate": version_date, "URL": href})

    # Deduplicate and sort
    if not versions:
         # If no historical versions are found, use the base URL as the single version
        return [{"VersionDate": "current", "URL": base_url}]

    seen_urls = set()
    unique_versions = []
    for v in versions:
        if v["URL"] not in seen_urls:
            unique_versions.append(v)
            seen_urls.add(v["URL"])
            
    unique_versions.sort(key=lambda x: x['VersionDate'], reverse=True)
    return unique_versions


def split_main_and_history(txt: str) -> Tuple[str, str]:
    if not txt:
        return "", ""
    markers = []
    for pat in [r"R\.R\.Q\.", r"\bD\.\s?\d", r"\bL\.Q\."]:
        m = re.search(pat, txt)
        if m:
            markers.append(m.start())
    if not markers:
        return txt, ""
    cut = min(markers)
    return txt[:cut].rstrip(), txt[cut:].lstrip()

def build_decoded_ref(id_str: str) -> Tuple[str, Dict[str, str]]:
    parts = id_str.split("-")
    decoded_parts = {"Article": "", "Alinéa": "", "Niveau2": "", "Niveau3": "", "Niveau4": ""}

    if not parts or not parts[0].startswith("se:"):
        return "", decoded_parts

    article_code = part_value(parts[0]).replace("_", ".")
    decoded_parts["Article"] = article_code
    ref = article_code
    
    # ... (rest of the decoding logic is the same as before)
    p1 = p2 = p3 = None
    for seg in parts[1:]:
        if seg.startswith("p1:"): p1 = part_value(seg)
        elif seg.startswith("p2:"): p2 = part_value(seg)
        elif seg.startswith("p3:"): p3 = part_value(seg)

    had_al = False
    if p1:
        frag1 = token_to_human(p1, 1)
        if frag1.startswith("al. "):
            ref = f"{ref} {frag1}"
            had_al = True
            decoded_parts["Alinéa"] = frag1.replace("al. ", "")
        else:
            ref = f"{ref} {frag1}"
            decoded_parts["Alinéa"] = frag1
    if p2:
        frag2 = token_to_human(p2, 2)
        if frag2.startswith("("):
            if had_al or p1: ref = f"{ref} {frag2}"
            else: ref = f"{ref}{frag2}"
        else: ref = f"{ref} {frag2}"
        decoded_parts["Niveau2"] = frag2
    if p3:
        frag3 = token_to_human(p3, 3)
        ref = f"{ref}{frag3}"
        decoded_parts["Niveau3"] = frag3

    return ref, decoded_parts

def part_value(seg: str) -> str:
    return seg.split(":", 1)[1] if ":" in seg else seg

def is_numeric_token(tok: str) -> bool: return bool(re.fullmatch(r"^\d+(?:_\d+)*$", tok))
def is_letter_token(tok: str) -> bool: return bool(re.fullmatch(r"^[a-z]$", tok))
def is_roman_token(tok: str) -> bool: return bool(re.fullmatch(r"^(i|ii|iii|iv|v|vi|vii|viii|ix|x)$", tok))

def token_to_human(tok: str, level: int) -> str:
    if level == 1:
        if is_numeric_token(tok): return f"al. {tok.replace('_', '.')}"
        elif is_letter_token(tok) or is_roman_token(tok): return f"{tok})"
        return tok
    if is_numeric_token(tok): return f"({tok.replace('_', '.')})"
    elif is_letter_token(tok) or is_roman_token(tok): return f"{tok})"
    return tok

def extract_df_term(text: str) -> str:
    m = re.search(r"«\s*([^»]+?)\s*»", text) or re.search(r'"([^"]+)"', text)
    return m.group(1).strip() if m else ""

def classify_id(idv: str) -> str:
    if idv.startswith("se:"): return "Provision"
    if idv.startswith("ga:"): return "Heading"
    if idv.startswith("sc-nb:"): return "Annexe"
    return "Technique"

def article_from_id(idv: str) -> str:
    if not idv.startswith("se:"): return ""
    return part_value(idv.split("-", 1)[0]).replace("_", ".")


def rows_from_iter(iterable: Iterable[Tuple[str,str, str]], metadata: Dict[str, str]) -> List[Dict[str,str]]:
    rows = []
    for idv, txt, classes in iterable:
        main_text, history = split_main_and_history(txt)
        decoded_ref, parts_map = build_decoded_ref(idv)
        rows.append({
            "ID": idv,
            "Type": classify_id(idv),
            "Classes": classes,
            "Article": article_from_id(idv),
            "MainText": main_text,
            "HistoricalNote": history,
            "DecodedRef": decoded_ref,
            "DecodedParts": " | ".join([f"{k}={v}" for k,v in parts_map.items() if v]),
            "DecodedTerm": extract_df_term(main_text) if "-df:" in idv else "",
            **metadata
        })
    return rows

def process_version_page(version_info: Dict[str, str], save_dir: str) -> List[Dict[str, str]]:
    url = version_info['URL']
    version_date = version_info['VersionDate']
    
    print(f"[HTML] Processing Version: {version_date} from {url}")
    
    file_name = f"version-{version_date}.html"
    save_path = os.path.join(save_dir, file_name)
    download_html(url, save_path)
    
    with open(save_path, "rb") as f:
        html_bytes = f.read()

    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(url)
    
    # Extract metadata
    title = normspace(doc.xpath('//h3[@class="card-title"]')[0].text_content()) if doc.xpath('//h3[@class="card-title"]') else ""
    mod_date_meta = doc.xpath('//meta[@name="dc.date.modified"]/@content')
    mod_date = mod_date_meta[0] if mod_date_meta else ""
    
    abrogation_node = doc.xpath('//div[contains(@class, "alert-danger")]/h4')
    abrogation_text = normspace(abrogation_node[0].text_content()) if abrogation_node else ""

    official_status_node = doc.xpath('//div[contains(@class, "alert-info")]')
    official_status_text = normspace(official_status_node[0].text_content()) if official_status_node else ""

    pdf_link_node = doc.xpath('//a[contains(@href, ".pdf")]')
    pdf_url = pdf_link_node[0].get('href') if pdf_link_node else ""


    metadata = {
        "VersionDate": version_date,
        "Title": title,
        "ModificationDate": mod_date,
        "SourceURL": url,
        "AbrogationNotice": abrogation_text,
        "OfficialStatus": official_status_text,
        "PdfURL": pdf_url
    }

    container_nodes = doc.xpath("//div[@id='mainContent-document']")
    if not container_nodes:
        print(f"  [WARN] mainContent-document not found in {url}", file=sys.stderr)
        return []
        
    container = container_nodes[0]
    
    def iterate_ids_from_html_block(container_el: ET._Element) -> Iterable[Tuple[str, str, str]]:
        for el in container_el.xpath(".//*[@id]"):
            idv = el.get("id")
            txt = normspace("".join(el.itertext()))
            classes = el.get("class", "")
            yield idv, txt, classes
            
    return rows_from_iter(iterate_ids_from_html_block(container), metadata)


def main():
    ap = argparse.ArgumentParser(description="Archive all historical versions of a Légis Québec regulation.")
    ap.add_argument("--url", "-u", required=True, help="Main Légis Québec URL for the regulation")
    ap.add_argument("--out", "-o", default="regulation_archive.csv", help="Output CSV path")
    ap.add_argument("--save-dir", default="html_versions", help="Directory to save downloaded HTML files")

    args = ap.parse_args()
    
    os.makedirs(args.save_dir, exist_ok=True)
    
    print(f"[INFO] Starting archival for: {args.url}")
    
    # Download the main page to find all versions
    main_page_path = os.path.join(args.save_dir, "main_page.html")
    download_html(args.url, main_page_path)
    with open(main_page_path, "rb") as f:
        main_html_bytes = f.read()
        
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
        sys.exit(1)
        
    # Deduplicate & sort
    df = pd.DataFrame(all_rows)
    df = df.drop_duplicates(subset=["ID", "VersionDate"])

    type_order = {"Provision": 0, "Heading": 1, "Annexe": 2, "Technique": 3}
    df["__ord__"] = df["Type"].map(type_order).fillna(9)
    df = df.sort_values(["VersionDate", "__ord__", "Article", "ID"], ascending=[False, True, True, True]).drop(columns="__ord__")

    out_path = os.path.abspath(args.out)
    df.to_csv(out_path, index=False, encoding="utf-8-sig")
    print(f"\n[SUCCESS] Wrote {len(df)} rows to: {out_path}")


if __name__ == "__main__":
    main()
