#!/usr/bin/env python3
import os, re, json, time
from typing import List, Dict, Optional
from urllib.parse import urljoin
import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20

class HistoryCrawler:
    def __init__(self, base_url: str, out_dir: str, session: Optional[requests.Session]=None):
        self.base_url = base_url.rstrip('/') if base_url else ''
        self.out_dir = out_dir
        self.session = session or requests.Session()
        self.session.headers.update({"User-Agent": "LRN/HistoryCrawler"})

    def fetch(self, url: str) -> str:
        r = self.session.get(url, timeout=DEFAULT_TIMEOUT)
        r.raise_for_status()
        return r.text

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
            if 'historique=' in a['href'] or 'historique' in a['href']:
                links.append(a['href'])
        # Deduplicate preserving order
        seen = set(); out = []
        for href in links:
            if href not in seen:
                out.append(href); seen.add(href)
        return out

    def enumerate_versions(self, history_link_url: str) -> List[Dict[str, str]]:
        # Fetch the version page and scrape available historique dates from anchors
        url = urljoin(self.base_url + '/', history_link_url) if self.base_url and not re.match(r'^https?://', history_link_url) else history_link_url
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
        # Dedup by date+href
        uniq = []
        seen = set()
        for it in items:
            k = (it['date'], it['href'])
            if k not in seen:
                uniq.append(it); seen.add(k)
        return uniq

    def snapshot(self, instrument_dir: str, fragment_code: str, date: str, href: str) -> Optional[str]:
        url = urljoin(self.base_url + '/', href) if self.base_url and not re.match(r'^https?://', href) else href
        try:
            html = self.fetch(url)
        except Exception:
            return None
        d = os.path.join(instrument_dir, 'history', fragment_code)
        os.makedirs(d, exist_ok=True)
        safe_date = date if re.match(r'^\d{8}$', date) else time.strftime('%Y%m%d')
        path = os.path.join(d, f'{safe_date}.html')
        with open(path, 'w', encoding='utf-8') as f:
            f.write(html)
        return path

    def build_index(self, instrument_dir: str, entries: Dict[str, List[Dict[str, str]]]):
        # entries: { fragment_code: [ {date, path} ] }
        hist_dir = os.path.join(instrument_dir, 'history')
        os.makedirs(hist_dir, exist_ok=True)
        with open(os.path.join(hist_dir, 'index.json'), 'w', encoding='utf-8') as f:
            json.dump(entries, f, ensure_ascii=False, indent=2)
