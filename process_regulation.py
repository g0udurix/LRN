#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Build a fully decoded CSV from a Légis Québec page,
with EPUB fallback and a local test mode that can run without internet.
"""

import argparse
import os
import re
import shutil
import subprocess
import sys
import zipfile
from typing import Dict, Iterable, List, Optional, Tuple

import lxml.html as LH
import lxml.etree as ET
import pandas as pd

try:
    import requests
except Exception:  # pragma: no cover
    requests = None

UA = "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 " \
     "(KHTML, like Gecko) Chrome/123.0 Safari/537.36"


# -------------------------
# Download helpers (HTML/EPUB)
# -------------------------
def download_file(url: str, out_path: str, accept: Optional[str] = None) -> None:
    """Download URL to out_path using curl, else wget, else requests."""
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
    resp = requests.get(url, headers={"User-Agent": UA, "Accept": accept or "*/*"}, timeout=60)
    resp.raise_for_status()
    with open(out_path, "wb") as f:
        f.write(resp.content)


def download_html(url: str, out_html: str) -> None:
    download_file(url, out_html, accept="text/html,application/xhtml+xml")


def download_epub(url: str, out_epub: str) -> None:
    download_file(url, out_epub, accept="application/epub+zip,application/octet-stream,*/*")


# -------------------------
# Text & decode helpers
# -------------------------
def normspace(s: str) -> str:
    return re.sub(r"\s+", " ", s or "").strip()


def split_main_and_history(txt: str) -> Tuple[str, str]:
    """
    Split legislative text into main and trailing historical note.
    Heuristic: first occurrence of 'R.R.Q.' or 'D.' or 'L.Q.' and onward.
    """
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


_ROMAN_RE = re.compile(r"^(i|ii|iii|iv|v|vi|vii|viii|ix|x)$")
_LETTER_RE = re.compile(r"^[a-z]$")
_NUMERIC_RE = re.compile(r"^\d+(?:_\d+)*$")


def is_numeric_token(tok: str) -> bool:
    return bool(_NUMERIC_RE.fullmatch(tok))


def is_letter_token(tok: str) -> bool:
    return bool(_LETTER_RE.fullmatch(tok))


def is_roman_token(tok: str) -> bool:
    return bool(_ROMAN_RE.fullmatch(tok))


def part_value(seg: str) -> str:
    if ":" in seg:
        return seg.split(":", 1)[1]
    return seg


def token_to_human(tok: str, level: int) -> str:
    if level == 1:
        if is_numeric_token(tok):
            n = tok.replace("_", ".")
            return f"al. {n}"
        elif is_letter_token(tok) or is_roman_token(tok):
            return f"{tok})"
        return tok

    if is_numeric_token(tok):
        n = tok.replace("_", ".")
        return f"({n})"
    elif is_letter_token(tok) or is_roman_token(tok):
        return f"{tok})"
    return tok


def build_decoded_ref(id_str: str) -> Tuple[str, Dict[str, str]]:
    parts = id_str.split("-")
    decoded_parts = {"Article": "", "Alinéa": "", "Niveau2": "", "Niveau3": "", "Niveau4": ""}

    if not parts or not parts[0].startswith("se:"):
        return "", decoded_parts

    article_code = part_value(parts[0]).replace("_", ".")
    decoded_parts["Article"] = article_code
    ref = article_code

    p1 = p2 = p3 = None
    for seg in parts[1:]:
        if seg.startswith("p1:"):
            p1 = part_value(seg)
        elif seg.startswith("p2:"):
            p2 = part_value(seg)
        elif seg.startswith("p3:"):
            p3 = part_value(seg)

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
            if had_al:
                ref = f"{ref} {frag2}"
            else:
                if p1:
                    ref = f"{ref} {frag2}"
                else:
                    ref = f"{ref}{frag2}"  # e.g., 29(3)
        else:
            ref = f"{ref} {frag2}"
        decoded_parts["Niveau2"] = frag2

    if p3:
        frag3 = token_to_human(p3, 3)
        ref = f"{ref}{frag3}"          # no extra space, e.g., ...a)ii
        decoded_parts["Niveau3"] = frag3

    return ref, decoded_parts


def extract_df_term(text: str) -> str:
    if not text:
        return ""
    m = re.search(r"«\s*([^»]+?)\s*»", text)
    if m:
        return m.group(1).strip()
    m2 = re.search(r'"([^"]+)"', text)
    if m2:
        return m2.group(1).strip()
    return ""


def classify_id(idv: str) -> str:
    if idv.startswith("se:"):
        return "Provision"
    if idv.startswith("ga:"):
        return "Heading"
    if idv.startswith("sc-nb:"):
        return "Annexe"
    return "Technique"


def article_from_id(idv: str) -> str:
    if not idv.startswith("se:"):
        return ""
    first = idv.split("-", 1)[0]
    return part_value(first).replace("_", ".")


# -------------------------
# HTML parsing
# -------------------------
def parse_legis_block_from_html(html_bytes: bytes) -> ET._Element:
    doc = LH.fromstring(html_bytes)
    nodes = doc.xpath("//div[@id='mainContent-document']")
    if not nodes:
        raise RuntimeError("mainContent-document not found in HTML.")
    return nodes[0]


def iterate_ids_from_html_block(container: ET._Element) -> Iterable[Tuple[str, str, str]]:
    for el in container.xpath(".//*[@id]"):
        idv = el.get("id")
        txt = normspace("".join(el.itertext()))
        classes = el.get("class", "")
        yield idv, txt, classes


def find_epub_link_in_html(html_bytes: bytes) -> Optional[str]:
    try:
        doc = LH.fromstring(html_bytes)
    except Exception:
        return None
    for a in doc.xpath("//a[@href]"):
        href = a.get("href") or ""
        if ".epub" in href.lower():
            if href.startswith("http"):
                return href
            from urllib.parse import urljoin
            return urljoin(doc.base_url or "", href)
        text = normspace("".join(a.itertext())).lower()
        if "epub" in text and a.get("href"):
            href = a.get("href")
            if href.startswith("http"):
                return href
            from urllib.parse import urljoin
            return urljoin(doc.base_url or "", href)
    return None


# -------------------------
# EPUB parsing
# -------------------------
def iterate_ids_from_epub(epub_path: str) -> Iterable[Tuple[str, str, str]]:
    with zipfile.ZipFile(epub_path, "r") as z:
        names = [n for n in z.namelist() if n.lower().endswith((".xhtml", ".html"))]
        def page_order(n: str) -> Tuple[int, str]:
            m = re.search(r"page(\d+)\.xhtml$", n)
            return (int(m.group(1)) if m else 10**9, n)
        names.sort(key=page_order)
        for name in names:
            content = z.read(name)
            try:
                tree = LH.fromstring(content)
            except Exception:
                try:
                    tree = ET.fromstring(content)
                except Exception:
                    continue
            for el in tree.xpath(".//*[@id]"):
                idv = el.get("id")
                if not idv:
                    continue
                txt = normspace("".join(el.itertext()))
                classes = el.get("class", "")
                yield idv, txt, classes


# -------------------------
# Orchestration
# -------------------------
def rows_from_iter(iterable: Iterable[Tuple[str,str, str]]) -> List[Dict[str,str]]:
    rows: List[Dict[str,str]] = []
    for idv, txt, classes in iterable:
        typ = classify_id(idv)
        main_text, history = split_main_and_history(txt)
        decoded_ref = ""
        decoded_parts_str = ""
        decoded_term = ""
        if idv.startswith("se:"):
            decoded_ref, parts_map = build_decoded_ref(idv)
            decoded_parts_str = " | ".join([f"{k}={v}" for k,v in parts_map.items() if v])
            if "-df:" in idv:
                decoded_term = extract_df_term(main_text)
        elif idv.startswith("ga:") or idv.startswith("sc-nb:"):
            decoded_ref = main_text
        else:
            decoded_ref = main_text
        rows.append({
            "ID": idv,
            "Type": typ,
            "Classes": classes,
            "Article": article_from_id(idv),
            "MainText": main_text,
            "HistoricalNote": history,
            "DecodedRef": decoded_ref,
            "DecodedParts": decoded_parts_str,
            "DecodedTerm": decoded_term,
        })
    return rows


def run_from_html(url: str, save_html: str) -> List[Dict[str, str]]:
    print(f"[HTML] Downloading: {url}")
    download_html(url, save_html)
    with open(save_html, "rb") as f:
        html_bytes = f.read()

    doc = LH.fromstring(html_bytes)
    title_nodes = doc.xpath("//div[@id='title-and-update-container']//h1")
    if title_nodes:
        print(f"[HTML] Title: {normspace(title_nodes[0].text_content())}")

    print("[HTML] Extracting #mainContent-document …")
    container_nodes = doc.xpath("//div[@id='mainContent-document']")
    if not container_nodes:
        raise RuntimeError("Could not find div with id='mainContent-document'")
    container = container_nodes[0]
    
    print("[HTML] Collecting ids …")
    return rows_from_iter(iterate_ids_from_html_block(container))


def run_from_epub(url: Optional[str], epub_url: Optional[str], save_html: str, save_epub: str) -> List[Dict[str, str]]:
    final_epub_url = epub_url
    if not final_epub_url:
        if url and not os.path.exists(save_html):
            print(f"[EPUB] Downloading page to discover EPUB link: {url}")
            download_html(url, save_html)
        
        if os.path.exists(save_html):
            with open(save_html, "rb") as f:
                html_bytes = f.read()
            final_epub_url = find_epub_link_in_html(html_bytes)
        
        if not final_epub_url:
            raise RuntimeError("EPUB link not found on the page; use --epub-url explicitly.")

    print(f"[EPUB] Downloading EPUB: {final_epub_url}")
    download_epub(final_epub_url, save_epub)
    print("[EPUB] Parsing ids from EPUB …")
    return rows_from_iter(iterate_ids_from_epub(save_epub))


# -------------------------
# Local test (offline) fixture
# -------------------------
TEST_HTML = b"""
<!DOCTYPE html>
<html lang=fr>
  <head>
    <meta charset="utf-8">
  </head>
  <body>
    <div id=mainContent-document>
      <div id="ga:l_ii-gb:l_2_11-h1">\xc2\xa7 2.11 \xe2\x80\x94 \xc3\x89lectricit\xc3\xa9</div>
      <div id="se:29-ss:1-p1:3-p2:a">Utilisations prohib\xc3\xa9es \xe2\x80\x94 exemple a) R.R.Q., 1981, c. S-2.1, r. 4, a. 29</div>
      <div id="se:312_46-ss:2-p1:2-p2:3-p3:ii">Composition du syst\xc3\xa8me \xe2\x80\x94 ligne ii. \xc2\xab v\xc3\xaatement de protection \xc2\xbb D. 502-2018, a. 6</div>
      <div id="se:62_2-ss:1-p1:1">Texte pour 62.2 al. 1</div>
      <div id="se:62_2-ss:1-p1:2">Texte pour 62.2 al. 2</div>
      <div id="sc-nb:5_3">ANNEXE 5.3</div>
    </div>
  </body>
</html>
"""


def run_test_local() -> List[Dict[str,str]]:
    container = parse_legis_block_from_html(TEST_HTML)
    return rows_from_iter(iterate_ids_from_html_block(container))


# -------------------------
# Main CLI
# -------------------------

def main():
    ap = argparse.ArgumentParser(description="Build a CSV from a Légis Québec page.")
    ap.add_argument("--url", "-u", required=True,
                    help="Légis Québec URL")
    ap.add_argument("--out", "-o", default="regulation.csv",
                    help="Output CSV path")
    ap.add_argument("--save-html", default="page.html", help="Where to save the downloaded HTML")
    ap.add_argument("--save-epub", default="doc.epub", help="Where to save the downloaded EPUB")
    ap.add_argument("--from-epub", action="store_true", help="Force EPUB mode (skip HTML parse)")
    ap.add_argument("--epub-url", default=None, help="EPUB URL to use explicitly")
    ap.add_argument("--test-local", action="store_true", help="Run using an embedded local HTML fixture (offline)")

    args = ap.parse_args()

    if args.test_local:
        rows = run_test_local()
    else:
        if args.from_epub:
            rows = run_from_epub(args.url, args.epub_url, args.save_html, args.save_epub)
        else:
            try:
                rows = run_from_html(args.url, args.save_html)
            except Exception as e:
                print(f"[HTML] Failed: {e}", file=sys.stderr)
                print("[Fallback] Trying EPUB …", file=sys.stderr)
                try:
                    rows = run_from_epub(args.url, args.epub_url, args.save_html, args.save_epub)
                except Exception as e_epub:
                    print(f"[EPUB] Also failed: {e_epub}", file=sys.stderr)
                    sys.exit(1)

    # Deduplicate & sort
    if rows:
        seen = set()
        uniq = []
        for r in rows:
            rid = r.get("ID")
            if rid in seen:
                continue
            seen.add(rid)
            uniq.append(r)

        type_order = {"Provision": 0, "Heading": 1, "Annexe": 2, "Technique": 3}
        df = pd.DataFrame(uniq)
        if "Type" in df.columns:
            df["__ord__"] = df["Type"].map(type_order).fillna(9)
            df = df.sort_values(["__ord__", "Article", "ID"]).drop(columns="__ord__")

        out_path = os.path.abspath(args.out)
        df.to_csv(out_path, index=False, encoding="utf-8-sig")
        print(f"[OK] Wrote: {out_path}")
    else:
        print("[WARN] No data was extracted.")


if __name__ == "__main__":
    main()
