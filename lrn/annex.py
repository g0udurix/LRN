"""Annex (PDF) discovery and conversion helpers."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import subprocess
from typing import List, Optional
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

from lrn.extract import Fragment


@dataclass
class AnnexConversion:
    """Record of a converted annex."""

    pdf_url: str
    pdf_path: Path
    markdown_path: Optional[Path]
    sha256: str
    warning: Optional[str] = None


def _sha256(data: bytes) -> str:
    import hashlib

    digest = hashlib.sha256()
    digest.update(data)
    return digest.hexdigest()


def _ensure_dir(path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)


def _convert_pdf_to_markdown(pdf_path: Path, markdown_path: Path, engine: str) -> Optional[str]:
    try:
        subprocess.run(
            [engine, "--input", str(pdf_path), "--output", str(markdown_path), "--format", "gfm"],
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        return None
    except Exception as exc:  # pragma: no cover - subprocess errors depend on environment
        return str(exc)


def process_annexes(
    fragment: Fragment,
    *,
    base_url: Optional[str],
    instrument_dir: Path,
    engine: str = "marker",
) -> List[AnnexConversion]:
    """Download and convert annex PDFs referenced in the fragment."""
    conversions: List[AnnexConversion] = []
    soup = fragment.soup

    for anchor in soup.find_all("a", href=True):
        href = anchor["href"]
        if not href.lower().endswith(".pdf"):
            continue

        abs_url = urljoin(base_url + "/", href) if base_url and not bool(urlparse(href).scheme) else href
        try:
            response = requests.get(abs_url, timeout=60)
            response.raise_for_status()
            pdf_bytes = response.content
        except Exception as exc:  # pragma: no cover - network behaviour hard to replicate
            conversions.append(
                AnnexConversion(
                    pdf_url=abs_url,
                    pdf_path=Path(),
                    markdown_path=None,
                    sha256="",
                    warning=f"download failed: {exc}",
                )
            )
            continue

        sha = _sha256(pdf_bytes)
        pdf_dir = instrument_dir / "annexes"
        pdf_dir.mkdir(parents=True, exist_ok=True)
        parsed = urlparse(abs_url)
        pdf_name = Path(parsed.path).name or "annex.pdf"
        pdf_path = pdf_dir / pdf_name
        _ensure_dir(pdf_path)
        pdf_path.write_bytes(pdf_bytes)

        markdown_path = pdf_path.with_suffix(".md")
        warning = _convert_pdf_to_markdown(pdf_path, markdown_path, engine)
        if warning is None:
            front_matter = f"---\nsource_url: {abs_url}\nsha256: {sha}\n---\n\n"
            existing = markdown_path.read_text(encoding="utf-8")
            markdown_path.write_text(front_matter + existing, encoding="utf-8")
            rel_md = markdown_path.relative_to(instrument_dir).as_posix()
            anchor.insert_after(f" [Version Markdown]({rel_md})")
        else:
            markdown_path = None

        conversions.append(
            AnnexConversion(
                pdf_url=abs_url,
                pdf_path=pdf_path,
                markdown_path=markdown_path,
                sha256=sha,
                warning=warning,
            )
        )

    fragment.soup = soup
    fragment.xhtml = str(soup)
    return conversions


__all__ = ["AnnexConversion", "process_annexes"]
