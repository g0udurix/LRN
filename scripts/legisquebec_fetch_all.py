#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Auto-discover and download current HTML pages for:
- S-2.1 main law (FR and EN)
- All bylaws under S-2.1 (FR and EN)

Saves the raw HTML into a new folder: "Legisquebec originals"
Skips PDFs and historical versions per user request.

Discovery strategy:
- Start from S-2.1 main pages (FR and EN)
- Parse the "Règlements" / "Regulations" sections to find linked bylaws
- Normalize and download current HTML for each FR/EN instrument

Robust download:
- Try curl, then wget, then requests
- Set a modern User-Agent
- Create deterministic filenames

Output layout:
Legisquebec originals/
  S-2.1/
    law/
      S-2.1.fr.html
      S-2.1.en.html
    bylaws/
      S-2.1_r_3.fr.html
      S-2.1_r_3.en.html
      S-2.1_r_4.fr.html
      ...
  index.csv  (optional: not created in this first pass)

Usage:
  python scripts/legisquebec_fetch_all.py
"""

import os
import re
import sys
import shutil
import subprocess
from typing import List, Dict, Tuple, Optional
from urllib.parse import urljoin, quote

import lxml.html as LH

try:
    import requests  # fallback
except Exception:
    requests = None

UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 14_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/123.0 Safari/537.36"

FR_LAW_URL = "https://www.legisquebec.gouv.qc.ca/fr/document/lc/S-2.1"
EN_LAW_URL = "https://www.legisquebec.gouv.qc.ca/en/document/lc/S-2.1"

OUT_ROOT = os.path.join("Legisquebec originals")
OUT_LAW_DIR = os.path.join(OUT_ROOT, "S-2.1", "law")
OUT_BYLAW_DIR = os.path.join(OUT_ROOT, "S-2.1", "bylaws")


def ensure_dirs() -> None:
    os.makedirs(OUT_LAW_DIR, exist_ok=True)
    os.makedirs(OUT_BYLAW_DIR, exist_ok=True)


def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").replace("\xa0", " ")).strip()


def download_file(url: str, out_path: str, accept: Optional[str] = None) -> None:
    """
    Download URL to out_path using curl, else wget, else requests.
    """
    os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

    headers = ["-H", f"User-Agent: {UA}"]
    if accept:
        headers += ["-H", f"Accept: {accept}"]

    curl = shutil.which("curl")
    if curl:
        cmd = [curl, "-L", "--compressed", *headers, "-o", out_path, url]
        subprocess.run(cmd, check=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return

    wget = shutil.which("wget")
    if wget:
        cmd = [wget, "-q", "--content-disposition", "--header", f"User-Agent: {UA}", "-O", out_path, url]
        subprocess.run(cmd, check=True)
        if os.path.exists(out_path) and os.path.getsize(out_path) > 0:
            return

    if requests is None:
        raise RuntimeError("curl/wget failed and 'requests' not available.")
    resp = requests.get(url, headers={"User-Agent": UA, "Accept": accept or "text/html,application/xhtml+xml"}, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)


def fetch_html(url: str) -> bytes:
    tmp_path = os.path.join(".tmp_legis", re.sub(r"[^a-zA-Z0-9_.-]", "_", url) + ".html")
    os.makedirs(os.path.dirname(tmp_path), exist_ok=True)
    download_file(url, tmp_path, accept="text/html,application/xhtml+xml")
    with open(tmp_path, "rb") as f:
        return f.read()


def find_bylaw_links_from_law_page(html_bytes: bytes, base_url: str) -> List[Dict[str, str]]:
    """
    Parse the S-2.1 law page to find "Règlements"/"Regulations" links.
    Returns a list of dicts with keys: title, href, lang ('fr' or 'en'), official_number (if parseable).
    """
    doc = LH.fromstring(html_bytes)
    doc.make_links_absolute(base_url)

    # Heuristic: bylaw links are under sections that contain /document/rc/S-2.1, r. X (FR)
    # and /en/document/rc/S-2.1, r. X (EN). Also capture main law links.
    anchors = doc.xpath("//a[@href]")
    results: List[Dict[str, str]] = []

    for a in anchors:
        href = a.get("href", "")
        text = normspace("".join(a.itertext()))
        if not href:
            continue

        is_bylaw = False
        lang = None

        # Identify bylaw links: contain '/document/rc/' and 'S-2.1'
        if "/document/rc/" in href and "S-2.1" in href:
            is_bylaw = True

        if href.startswith("https://www.legisquebec.gouv.qc.ca/en/") or "/en/document/" in href:
            lang = "en"
        elif href.startswith("https://www.legisquebec.gouv.qc.ca/fr/") or "/fr/document/" in href:
            lang = "fr"

        if is_bylaw and lang in ("fr", "en"):
            results.append({
                "title": text or "",
                "href": href,
                "lang": lang,
                "official_number": extract_official_number_from_href(href) or ""
            })

    # Deduplicate by URL+lang
    seen = set()
    uniq: List[Dict[str, str]] = []
    for r in results:
        key = (r["href"], r["lang"])
        if key in seen:
            continue
        seen.add(key)
        uniq.append(r)

    return uniq


def extract_official_number_from_href(href: str) -> Optional[str]:
    """
    Attempt to extract 'S-2.1, r. X' from the URL string.
    """
    # decode %20 and similar for matching
    try:
        from urllib.parse import unquote
        u = unquote(href)
    except Exception:
        u = href

    m = re.search(r"(S-2\.1,\s*r\.\s*\d+)", u, flags=re.IGNORECASE)
    if m:
        # Normalize spacing/case: "S-2.1, r. 3"
        raw = m.group(1)
        # Collapse spaces properly
        norm = re.sub(r"\s+", " ", raw)
        norm = norm.replace("R.", "r.")
        return norm.strip()
    return None


def make_filename_for_law(lang: str) -> str:
    return f"S-2.1.{lang}.html"


def make_filename_for_bylaw(official_number: str, lang: str) -> str:
    # Normalize "S-2.1, r. 3" -> "S-2.1_r_3"
    safe = official_number
    safe = safe.replace(", ", "_").replace(". ", "_").replace(".", "_").replace(",", "_").replace(" ", "_")
    # Make cleaner: collapse multiple underscores
    safe = re.sub(r"_+", "_", safe)
    return f"{safe}.{lang}.html"


def save_html(out_dir: str, filename: str, content: bytes) -> str:
    path = os.path.join(out_dir, filename)
    with open(path, "wb") as f:
        f.write(content)
    return path


def discover_and_download_main_law() -> List[Tuple[str, str]]:
    saved: List[Tuple[str, str]] = []
    # FR
    try:
        fr_html = fetch_html(FR_LAW_URL)
        fr_name = make_filename_for_law("fr")
        fr_path = save_html(OUT_LAW_DIR, fr_name, fr_html)
        saved.append((FR_LAW_URL, fr_path))
        print(f"[LAW] Saved FR: {fr_path}")
    except Exception as e:
        print(f"[LAW][FR] ERROR: {e}", file=sys.stderr)

    # EN
    try:
        en_html = fetch_html(EN_LAW_URL)
        en_name = make_filename_for_law("en")
        en_path = save_html(OUT_LAW_DIR, en_name, en_html)
        saved.append((EN_LAW_URL, en_path))
        print(f"[LAW] Saved EN: {en_path}")
    except Exception as e:
        print(f"[LAW][EN] ERROR: {e}", file=sys.stderr)

    return saved


def discover_and_download_bylaws() -> List[Tuple[str, str]]:
    """
    Discover bylaws by parsing both FR and EN law pages for links.
    Download each discovered bylaw page for both languages if link is present.
    """
    discovered: Dict[Tuple[str, str], Dict[str, str]] = {}

    # Parse FR page
    try:
        fr_html = fetch_html(FR_LAW_URL)
        fr_links = find_bylaw_links_from_law_page(fr_html, FR_LAW_URL)
        for l in fr_links:
            key = (l["official_number"] or l["href"], l["lang"])
            discovered[key] = l
    except Exception as e:
        print(f"[DISCOVER][FR] ERROR: {e}", file=sys.stderr)

    # Parse EN page
    try:
        en_html = fetch_html(EN_LAW_URL)
        en_links = find_bylaw_links_from_law_page(en_html, EN_LAW_URL)
        for l in en_links:
            key = (l["official_number"] or l["href"], l["lang"])
            # Prefer official number key if available; store/merge
            discovered[key] = l
    except Exception as e:
        print(f"[DISCOVER][EN] ERROR: {e}", file=sys.stderr)

    # Group by official number so we attempt to get both FR and EN for same instrument if present
    grouped: Dict[str, Dict[str, str]] = {}  # official_number -> { lang: href }
    for (_, lang), info in discovered.items():
        off = info["official_number"] or info["href"]
        grouped.setdefault(off, {})
        grouped[off][lang] = info["href"]

    saved: List[Tuple[str, str]] = []
    total = len(grouped)
    print(f"[DISCOVER] Found approximately {total} bylaws (grouped by official number or URL).")

    for off, d in sorted(grouped.items()):
        for lang in ("fr", "en"):
            if lang not in d:
                # if one lang missing, skip silently; we only save what exists
                continue
            url = d[lang]
            try:
                html = fetch_html(url)
                fname = make_filename_for_bylaw(off if "S-2.1" in off else extract_official_number_from_href(url) or off, lang)
                fpath = save_html(OUT_BYLAW_DIR, fname, html)
                saved.append((url, fpath))
                print(f"[BYLAW] Saved {off} ({lang.upper()}): {fpath}")
            except Exception as e:
                print(f"[BYLAW][{off}][{lang}] ERROR fetching {url}: {e}", file=sys.stderr)

    return saved


def main():
    print("[START] Discover and download current HTML for S-2.1 law and bylaws (FR/EN). PDFs/historical versions skipped.")
    ensure_dirs()
    law_saved = discover_and_download_main_law()
    bylaws_saved = discover_and_download_bylaws()

    total = len(law_saved) + len(bylaws_saved)
    print(f"[DONE] Saved {total} HTML files into '{OUT_ROOT}'.")
    print("Next step: identify the smallest file to start manual analysis as requested.")


if __name__ == "__main__":
    main()