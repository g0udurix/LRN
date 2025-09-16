"""Annex (PDF) discovery, download, and conversion helpers."""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path
import subprocess
from typing import Iterable, List, Optional, Set
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from lrn.extract import Fragment


class AnnexStatus(str, Enum):
    CONVERTED = "converted"
    DOWNLOADED = "downloaded"
    SKIPPED = "skipped"
    FAILED = "failed"


@dataclass
class AnnexOptions:
    engine: str = "marker"
    base_url: Optional[str] = None
    timeout: int = 60
    retries: int = 2
    max_bytes: Optional[int] = None
    skip_existing: bool = True
    session: Optional[requests.Session] = None


@dataclass
class AnnexRecord:
    pdf_url: str
    pdf_path: Optional[Path]
    markdown_path: Optional[Path]
    sha256: Optional[str]
    status: AnnexStatus
    message: Optional[str] = None


def _sha256(data: bytes) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _normalize_url(href: str, base_url: Optional[str]) -> str:
    href = href.strip()
    if base_url and not urlparse(href).scheme:
        return urljoin(base_url if base_url.endswith(('/', ':')) else base_url + '/', href)
    return href


def _iter_pdf_links(soup: BeautifulSoup) -> Iterable[str]:
    seen: Set[str] = set()
    for anchor in soup.find_all('a', href=True):
        href = anchor['href']
        if not href or '.pdf' not in href.lower():
            continue
        if href in seen:
            continue
        seen.add(href)
        yield href


def _download_with_limit(session: requests.Session, url: str, *, timeout: int, max_bytes: Optional[int], retries: int) -> bytes:
    attempt = 0
    last_error: Optional[Exception] = None
    while attempt <= retries:
        try:
            with session.get(url, timeout=timeout, stream=True) as resp:
                resp.raise_for_status()
                data = bytearray()
                for chunk in resp.iter_content(8192):
                    if not chunk:
                        continue
                    data.extend(chunk)
                    if max_bytes and len(data) > max_bytes:
                        raise ValueError(f"download exceeded {max_bytes} bytes")
                return bytes(data)
        except Exception as exc:
            last_error = exc
            attempt += 1
    assert last_error is not None
    raise last_error


def _convert_pdf(pdf_path: Path, markdown_path: Path, engine: str) -> Optional[str]:
    try:
        result = subprocess.run(
            [engine, "--input", str(pdf_path), "--output", str(markdown_path), "--format", "gfm"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        stdout = result.stdout.decode('utf-8', errors='ignore').strip()
        stderr = result.stderr.decode('utf-8', errors='ignore').strip()
        if stdout or stderr:
            return (stdout + '\n' + stderr).strip() or None
        return None
    except Exception as exc:  # pragma: no cover - subprocess behaviour varies
        return str(exc)


def process_annexes(
    fragment: Fragment,
    instrument_dir: Path,
    *,
    options: AnnexOptions,
) -> List[AnnexRecord]:
    """Download and convert annex PDFs referenced in ``fragment``."""
    session = options.session or requests.Session()
    session.headers.setdefault('User-Agent', 'LRN/AnnexDownloader')

    records: List[AnnexRecord] = []
    soup = fragment.soup

    for href in _iter_pdf_links(soup):
        abs_url = _normalize_url(href, options.base_url)
        parsed = urlparse(abs_url)
        pdf_name = Path(parsed.path).name or 'annex.pdf'
        pdf_dir = instrument_dir / 'annexes'
        pdf_path = pdf_dir / pdf_name

        if options.skip_existing and pdf_path.exists():
            records.append(
                AnnexRecord(
                    pdf_url=abs_url,
                    pdf_path=pdf_path,
                    markdown_path=pdf_path.with_suffix('.md') if pdf_path.with_suffix('.md').exists() else None,
                    sha256=None,
                    status=AnnexStatus.SKIPPED,
                    message='existing file reused',
                )
            )
            continue

        try:
            pdf_bytes = _download_with_limit(
                session,
                abs_url,
                timeout=options.timeout,
                max_bytes=options.max_bytes,
                retries=options.retries,
            )
        except Exception as exc:
            records.append(
                AnnexRecord(
                    pdf_url=abs_url,
                    pdf_path=None,
                    markdown_path=None,
                    sha256=None,
                    status=AnnexStatus.FAILED,
                    message=f'download failed: {exc}',
                )
            )
            continue

        sha = _sha256(pdf_bytes)
        pdf_dir.mkdir(parents=True, exist_ok=True)
        pdf_path.write_bytes(pdf_bytes)

        markdown_path = pdf_path.with_suffix('.md')
        conversion_message = _convert_pdf(pdf_path, markdown_path, options.engine)
        if conversion_message is None:
            front_matter = f"---\nsource_url: {abs_url}\nsha256: {sha}\n---\n\n"
            existing = markdown_path.read_text(encoding='utf-8', errors='ignore')
            markdown_path.write_text(front_matter + existing, encoding='utf-8')
            rel_md = markdown_path.relative_to(instrument_dir).as_posix()
            anchor = soup.find('a', href=href)
            if anchor:
                anchor.insert_after(f" [Version Markdown]({rel_md})")
            status = AnnexStatus.CONVERTED
            message = None
        else:
            markdown_path = None
            status = AnnexStatus.DOWNLOADED
            message = conversion_message

        records.append(
            AnnexRecord(
                pdf_url=abs_url,
                pdf_path=pdf_path,
                markdown_path=markdown_path,
                sha256=sha,
                status=status,
                message=message,
            )
        )

    fragment.soup = soup
    fragment.xhtml = str(soup)
    return records


__all__ = [
    'AnnexOptions',
    'AnnexRecord',
    'AnnexStatus',
    'process_annexes',
]
