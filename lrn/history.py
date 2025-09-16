#!/usr/bin/env python3
import os
import re
import json
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse, parse_qs

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20


@dataclass
class HistoryOptions:
    base_url: str = ""
    timeout: int = DEFAULT_TIMEOUT
    user_agent: str = "LRN/HistoryCrawler"
    cache_dir: Optional[str] = None
    max_dates: Optional[int] = None


@dataclass
class HistoryResult:
    index: Dict[str, List[Dict[str, str]]]
    html: str

class HistoryCrawler:
    def __init__(
        self,
        base_url: str,
        out_dir: str,
        session: Optional[requests.Session] = None,
        *,
        timeout: int = DEFAULT_TIMEOUT,
        user_agent: str = "LRN/HistoryCrawler",
        cache_dir: Optional[str] = None,
        max_dates: Optional[int] = None,
    ):
        self.base_url = base_url.rstrip('/') if base_url else ''
        self.out_dir = out_dir
        self.session = session or requests.Session()
        self.timeout = timeout or DEFAULT_TIMEOUT
        self.max_dates = max_dates
        self.cache_dir = cache_dir
        self.session.headers.update({"User-Agent": user_agent or "LRN/HistoryCrawler"})

    def _cache_key(self, url: str) -> Optional[str]:
        if not self.cache_dir:
            return None
        os.makedirs(self.cache_dir, exist_ok=True)
        # simple filesystem-safe key
        key = re.sub(r'[^A-Za-z0-9._-]+', '_', url)
        return os.path.join(self.cache_dir, key + '.html')

    def fetch(self, url: str) -> str:
        ck = self._cache_key(url)
        if ck and os.path.exists(ck):
            with open(ck, 'r', encoding='utf-8', errors='ignore') as f:
                return f.read()
        r = self.session.get(url, timeout=self.timeout)
        r.raise_for_status()
        text = r.text
        if ck:
            with open(ck, 'w', encoding='utf-8') as f:
                f.write(text)
        return text

    def discover_fragment_history_links(self, xhtml_html: str) -> List[str]:
        soup = BeautifulSoup(xhtml_html, 'lxml')
        links = []
        for img in soup.find_all('img', src=True):
            if 'history' in img['src']:
                a = img.find_parent('a')
                if a and a.get('href'):
                    links.append(a['href'])
        # Also check explicit HistoryLink anchors (class/alt patterns)
        for a in soup.find_all('a', href=True):
            if 'historique=' in a['href'] or 'historique' in a['href'] or (a.get('class') and any('HistoryLink' in c for c in a.get('class'))):
                links.append(a['href'])
        # Deduplicate preserving order
        seen = set(); out = []
        for href in links:
            if href not in seen:
                out.append(href); seen.add(href)
        return out

    def _resolve_url(self, href: str) -> str:
        if self.base_url and not re.match(r'^https?://', href):
            return urljoin(self.base_url + '/', href)
        return href

    def enumerate_versions(self, history_link_url: str) -> List[Dict[str, str]]:
        # Fetch the version page and scrape available historique dates from anchors
        url = self._resolve_url(history_link_url)
        try:
            html = self.fetch(url)
        except Exception:
            return []
        soup = BeautifulSoup(html, 'lxml')
        items = []
        for a in soup.find_all('a', href=True):
            href = a['href']
            m = re.search(r'(?:#|/)(\d{8})(?:$|\b|_)', href)
            if m:
                ymd = m.group(1)
                items.append({'date': ymd, 'href': href})
        # Fallback: any anchor with historique parameter
        if not items:
            for a in soup.find_all('a', href=True):
                if 'historique=' in a['href']:
                    items.append({'date': 'unknown', 'href': a['href']})
        # Final fallback: derive at least one entry from the history_link_url itself so offline fixtures
        # that stub snapshots directly (without intermediate listing pages) still crawl
        if not items:
            parsed = urlparse(history_link_url)
            date_guess = None
            if parsed.fragment and re.match(r'^\d{8}$', parsed.fragment):
                date_guess = parsed.fragment
            else:
                q = parse_qs(parsed.query)
                cand = q.get('historique') or q.get('date') or []
                for val in cand:
                    m = re.search(r'(\d{8})', val)
                    if m:
                        date_guess = m.group(1)
                        break
            if date_guess:
                items.append({'date': date_guess, 'href': history_link_url})
        # Dedup by date+href
        uniq = []
        seen = set()
        for it in items:
            k = (it['date'], it['href'])
            if k not in seen:
                uniq.append(it); seen.add(k)
        if self.max_dates is not None and self.max_dates >= 0:
            uniq = uniq[: self.max_dates]
        return uniq

    def _fragment_code_from_history_href(self, href: str) -> str:
        # Try to extract ?code=se:1 style
        try:
            q = parse_qs(urlparse(href).query)
            c = q.get('code', ['fragment'])[0]
            # sanitize
            return re.sub(r'[^A-Za-z0-9:_-]+', '_', c)
        except Exception:
            return 'fragment'

    def _extract_fragment_html(self, html: str, fragment_code: str) -> Optional[str]:
        """
        Given a full HTML page for a historical version, try to extract only the section for the fragment_code.
        This targets id="se:1" style sections and their descendant content. If not found, fall back to the full page.
        """
        try:
            soup = BeautifulSoup(html, 'lxml')
            node = soup.find(id=fragment_code)
            if node:
                # Wrap in a minimal container to keep valid XHTML fragment
                return str(node)
        except Exception:
            pass
        return html  # fallback

    def snapshot(self, instrument_dir: str, fragment_code: str, date: str, href: str) -> Optional[str]:
        url = self._resolve_url(href)
        try:
            html = self.fetch(url)
        except Exception:
            return None
        # Extract only the associated section if possible
        frag_html = self._extract_fragment_html(html, fragment_code)
        d = os.path.join(instrument_dir, 'history', fragment_code)
        os.makedirs(d, exist_ok=True)
        safe_date = date if re.match(r'^\d{8}$', date) else time.strftime('%Y%m%d')
        path = os.path.join(d, f'{safe_date}.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(frag_html)
        return path

    def build_index(self, instrument_dir: str, entries: Dict[str, List[Dict[str, str]]]):
        # entries: { fragment_code: [ {date, path} ] }
        hist_dir = os.path.join(instrument_dir, 'history')
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir, 'index.json'), 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)

    def crawl_from_fragment(self, instrument_dir: str, fragment_html: str) -> Dict[str, List[Dict[str, str]]]:
        # Discover all history links in fragment and capture snapshots
        links = self.discover_fragment_history_links(fragment_html)
        print(f"[INFO] Fragment discovery: {len(links)} history link(s) found", flush=True)
        index: Dict[str, List[Dict[str, str]]] = {}
        for link in links:
            frag_code = self._fragment_code_from_history_href(link)
            versions = self.enumerate_versions(link)
            print(f"[INFO] {frag_code}: {len(versions)} version(s) enumerated", flush=True)
            out_items: List[Dict[str, str]] = []
            for it in versions:
                p = self.snapshot(instrument_dir, frag_code, it['date'], it['href'])
                if p:
                    out_items.append({'date': it['date'], 'path': os.path.relpath(p, instrument_dir).replace(os.sep, '/')})
            if out_items:
                index[frag_code] = out_items
        # Persist consolidated index
        self.build_index(instrument_dir, index)
        print(f"[INFO] Wrote history index with {len(index)} fragment(s)", flush=True)
        return index


def build_history_sidecars(
    fragment_html: str,
    *,
    instrument_dir: Path,
    options: HistoryOptions,
) -> HistoryResult:
    crawler = HistoryCrawler(
        base_url=options.base_url,
        out_dir=str(instrument_dir),
        timeout=options.timeout,
        user_agent=options.user_agent,
        cache_dir=options.cache_dir,
        max_dates=options.max_dates,
    )
    index = crawler.crawl_from_fragment(str(instrument_dir), fragment_html)
    updated_html = _inject_versions(fragment_html, index)
    return HistoryResult(index=index, html=updated_html)


def _inject_versions(fragment_html: str, index: Dict[str, List[Dict[str, str]]]) -> str:
    soup = BeautifulSoup(fragment_html, 'lxml')
    if not index:
        target = soup.find(id=re.compile(r'^se:')) or soup
        container = soup.new_tag('div')
        container['class'] = ['LRN-Versions']
        container['data-fragment'] = 'se:placeholder'
        ul = soup.new_tag('ul')
        container.append(ul)
        if target:
            target.append(container)
        return str(soup)

    for frag_code, versions in index.items():
        target = soup.find(id=frag_code) or soup.find(attrs={'data-fragment': frag_code})
        container = soup.new_tag('div')
        container['class'] = ['LRN-Versions']
        container['data-fragment'] = frag_code
        ul = soup.new_tag('ul')
        for item in versions:
            li = soup.new_tag('li')
            a = soup.new_tag('a', href=f"history/{frag_code}/{item['date']}.html")
            a.string = item['date']
            li.append(a)
            ul.append(li)
        container.append(ul)
        if target:
            target.append(container)
        else:
            soup.append(container)
    return str(soup)


__all__ = [
    'HistoryCrawler',
    'HistoryOptions',
    'HistoryResult',
    'build_history_sidecars',
]
