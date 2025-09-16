"""History sidecar discovery, snapshotting, and HTML injection."""
from __future__ import annotations

import json
import os
import re
import time
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, Iterable, List, Optional
from urllib.parse import parse_qs, urljoin, urlparse

import requests
from bs4 import BeautifulSoup

DEFAULT_TIMEOUT = 20


class HistoryStatus(str, Enum):
    SNAPSHOT = "snapshot"
    FAILED = "failed"


@dataclass
class HistorySnapshot:
    fragment: str
    date: str
    url: str
    path: Optional[Path]
    status: HistoryStatus
    message: Optional[str] = None


@dataclass
class HistoryOptions:
    base_url: str = ""
    timeout: int = DEFAULT_TIMEOUT
    user_agent: str = "LRN/HistoryCrawler"
    cache_dir: Optional[str] = None
    max_dates: Optional[int] = None
    delay_seconds: float = 0.0
    session: Optional[requests.Session] = None


@dataclass
class HistoryResult:
    html: str
    index: Dict[str, List[Dict[str, str]]]
    snapshots: List[HistorySnapshot]


class HistoryCrawler:
    def __init__(self, instrument_dir: Path, options: HistoryOptions):
        self.instrument_dir = Path(instrument_dir)
        self.options = options
        self.base_url = options.base_url.rstrip('/') if options.base_url else ''
        self.session = options.session or requests.Session()
        self.session.headers.setdefault('User-Agent', options.user_agent)

    # Cache helpers -----------------------------------------------------
    def _cache_key(self, url: str) -> Optional[Path]:
        if not self.options.cache_dir:
            return None
        cache_dir = Path(self.options.cache_dir)
        cache_dir.mkdir(parents=True, exist_ok=True)
        key = re.sub(r'[^A-Za-z0-9._-]+', '_', url)
        return cache_dir / f"{key}.html"

    def _cached_fetch(self, url: str) -> str:
        ck = self._cache_key(url)
        if ck and ck.exists():
            return ck.read_text(encoding='utf-8', errors='ignore')
        response = self.session.get(url, timeout=self.options.timeout)
        response.raise_for_status()
        text = response.text
        if ck:
            ck.write_text(text, encoding='utf-8')
        return text

    # Discovery ---------------------------------------------------------
    def discover_fragment_links(self, fragment_html: str) -> List[str]:
        soup = BeautifulSoup(fragment_html, 'lxml')
        links: List[str] = []
        for img in soup.find_all('img', src=True):
            if 'history' in img['src']:
                anchor = img.find_parent('a')
                if anchor and anchor.get('href'):
                    links.append(anchor['href'])
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            if 'historique' in href or (anchor.get('class') and any('HistoryLink' in c for c in anchor['class'])):
                links.append(href)
        seen: List[str] = []
        for href in links:
            if href not in seen:
                seen.append(href)
        return seen

    def _resolve(self, href: str) -> str:
        if self.base_url and not re.match(r'^https?://', href):
            return urljoin(self.base_url + '/', href)
        return href

    def enumerate_versions(self, link: str) -> List[Dict[str, str]]:
        url = self._resolve(link)
        try:
            html = self._cached_fetch(url)
        except Exception:
            return []
        soup = BeautifulSoup(html, 'lxml')
        items: List[Dict[str, str]] = []
        for anchor in soup.find_all('a', href=True):
            href = anchor['href']
            match = re.search(r'(?:#|/)(\d{8})(?:$|\b|_)', href)
            if match:
                items.append({'date': match.group(1), 'href': href})
        if not items:
            for anchor in soup.find_all('a', href=True):
                if 'historique=' in anchor['href']:
                    items.append({'date': 'unknown', 'href': anchor['href']})
        if not items:
            parsed = urlparse(link)
            guess = None
            if parsed.fragment and re.match(r'^\d{8}$', parsed.fragment):
                guess = parsed.fragment
            else:
                for val in parse_qs(parsed.query).values():
                    for candidate in val:
                        m = re.search(r'(\d{8})', candidate)
                        if m:
                            guess = m.group(1)
                            break
                    if guess:
                        break
            if guess:
                items.append({'date': guess, 'href': link})
        seen = set()
        uniq: List[Dict[str, str]] = []
        for item in items:
            key = (item['date'], item['href'])
            if key not in seen:
                uniq.append(item)
                seen.add(key)
        if self.options.max_dates is not None and self.options.max_dates >= 0:
            uniq = uniq[: self.options.max_dates]
        return uniq

    def _fragment_code(self, href: str) -> str:
        try:
            code = parse_qs(urlparse(href).query).get('code', ['fragment'])[0]
            return re.sub(r'[^A-Za-z0-9:_-]+', '_', code)
        except Exception:
            return 'fragment'

    # Snapshot ----------------------------------------------------------
    def _extract_fragment_html(self, html: str, fragment_code: str) -> str:
        soup = BeautifulSoup(html, 'lxml')
        node = soup.find(id=fragment_code)
        if node:
            return str(node)
        return html

    def snapshot(self, fragment_code: str, date: str, href: str) -> HistorySnapshot:
        url = self._resolve(href)
        try:
            html = self._cached_fetch(url)
        except Exception as exc:
            return HistorySnapshot(
                fragment=fragment_code,
                date=date,
                url=url,
                path=None,
                status=HistoryStatus.FAILED,
                message=str(exc),
            )

        fragment_html = self._extract_fragment_html(html, fragment_code)
        history_dir = self.instrument_dir / 'history' / fragment_code
        history_dir.mkdir(parents=True, exist_ok=True)
        safe_date = date if re.match(r'^\d{8}$', date) else time.strftime('%Y%m%d')
        path = history_dir / f'{safe_date}.html'
        path.write_text(fragment_html, encoding='utf-8')
        return HistorySnapshot(
            fragment=fragment_code,
            date=safe_date,
            url=url,
            path=path,
            status=HistoryStatus.SNAPSHOT,
        )

    def crawl(self, fragment_html: str) -> HistoryResult:
        links = self.discover_fragment_links(fragment_html)
        index: Dict[str, List[Dict[str, str]]] = {}
        snapshots: List[HistorySnapshot] = []

        for link in links:
            fragment_code = self._fragment_code(link)
            versions = self.enumerate_versions(link)
            entries: List[Dict[str, str]] = []
            for item in versions:
                snap = self.snapshot(fragment_code, item['date'], item['href'])
                snapshots.append(snap)
                if snap.status is HistoryStatus.SNAPSHOT and snap.path is not None:
                    entries.append(
                        {
                            'date': snap.date,
                            'path': snap.path.relative_to(self.instrument_dir).as_posix(),
                            'url': snap.url,
                        }
                    )
                if self.options.delay_seconds:
                    time.sleep(self.options.delay_seconds)
            if entries:
                index[fragment_code] = entries

        html_with_versions = _inject_versions(fragment_html, index)
        return HistoryResult(html=html_with_versions, index=index, snapshots=snapshots)


def build_history_sidecars(
    fragment_html: str,
    *,
    instrument_dir: Path,
    options: HistoryOptions,
) -> HistoryResult:
    crawler = HistoryCrawler(instrument_dir=instrument_dir, options=options)
    result = crawler.crawl(fragment_html)
    history_dir = instrument_dir / 'history'
    history_dir.mkdir(parents=True, exist_ok=True)
    (history_dir / 'index.json').write_text(
        json.dumps(result.index, ensure_ascii=False, indent=2),
        encoding='utf-8',
    )
    return result


def _inject_versions(fragment_html: str, index: Dict[str, List[Dict[str, str]]]) -> str:
    soup = BeautifulSoup(fragment_html, 'lxml')
    if not index:
        target = soup.find(id=re.compile(r'^se:')) or soup
        container = soup.new_tag('div')
        container['class'] = ['LRN-Versions']
        container['data-fragment'] = 'se:placeholder'
        container.append(soup.new_tag('ul'))
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
            a = soup.new_tag('a', href=item['path'])
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
    'DEFAULT_TIMEOUT',
    'HistoryCrawler',
    'HistoryOptions',
    'HistoryResult',
    'HistorySnapshot',
    'HistoryStatus',
    'build_history_sidecars',
]
