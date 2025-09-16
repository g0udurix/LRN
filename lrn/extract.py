"""Core extraction utilities for LegisQuébec XHTML fragments."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import re
from typing import Optional

from bs4 import BeautifulSoup


@dataclass
class Fragment:
    """Structured representation of an extracted XHTML fragment."""

    source_path: Path
    instrument_id: str
    xhtml: str
    soup: BeautifulSoup
    raw_html: str


class FragmentExtractionError(RuntimeError):
    """Raised when the extractor cannot locate the inner XHTML fragment."""


def read_html(path: Path) -> str:
    """Read an HTML file with lenient error handling."""
    return path.read_text(encoding="utf-8", errors="ignore")


def find_inner_xhtml(html: str) -> str:
    """Extract the inner XHTML fragment from a LegisQuébec HTML page."""
    m2 = re.search(
        r'id="mainContent-document"[\s\S]*?(<\?xml[^>]*\?>\s*<!DOCTYPE\s+div[^>]*>\s*<div\b[\s\S]*?</div>\s*)',
        html,
        re.IGNORECASE,
    )
    if m2:
        return m2.group(1)

    m2b = re.search(
        r'id="mainContent-document"[\s\S]*?(<div\b[^>]*xmlns="http://www.w3.org/1999/xhtml"[\s\S]*?</div>\s*)',
        html,
        re.IGNORECASE,
    )
    if m2b:
        return m2b.group(1)

    m = re.search(
        r'(?:<\?xml[^>]*\?>\s*)?<!DOCTYPE\s+div[^>]*>\s*<div\b[\s\S]*?</div>\s*',
        html,
        re.IGNORECASE,
    )
    if m:
        return m.group(0)

    soup = BeautifulSoup(html, "lxml")
    section = soup.find(id=re.compile(r"^se:")) or soup.find("div", id=True)
    if section:
        inner = str(section)
        return (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            '<!DOCTYPE div PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN" "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">\n'
            f'<div xmlns="http://www.w3.org/1999/xhtml">{inner}</div>'
        )

    raise FragmentExtractionError("Unable to locate XHTML fragment in input HTML")


def detect_instrument(source_path: Path, fragment_soup: BeautifulSoup) -> str:
    """Infer the instrument identifier for the fragment."""
    ident = fragment_soup.find(class_=re.compile(r"Identification-Id"))
    if ident:
        txt = ident.get_text(" ", strip=True)
        match = re.search(r"[A-Z]-[0-9]+(?:\.[0-9]+)?,\s*r\.\s*[^\s]+", txt)
        if match:
            return (
                match.group(0)
                .replace(" ", "")
                .replace(",", "_")
                .replace(".", "_")
                .replace("/", "-")
            )

    heading = fragment_soup.find(["h1", "h2", "h3"])
    if heading:
        text = heading.get_text(" ", strip=True)
        if text:
            return (
                text.replace(" ", "_")
                .replace(",", "_")
                .replace(".", "_")
                .replace("/", "-")
            )[:80]

    normalized = str(source_path).replace("\\", "/")
    if "/document/rc/" in normalized:
        leaf = source_path.parent.name
        if leaf:
            cleaned = leaf.strip().replace(" ", "%20").replace(",", "%2C")
            return cleaned

    return source_path.stem


def load_fragment(path: Path) -> Fragment:
    """Load and parse a fragment from disk."""
    raw_html = read_html(path)
    xhtml = find_inner_xhtml(raw_html)
    soup = BeautifulSoup(xhtml, "lxml")
    instrument_id = detect_instrument(path, soup)
    return Fragment(
        source_path=path,
        instrument_id=instrument_id,
        xhtml=xhtml,
        soup=soup,
        raw_html=raw_html,
    )


__all__ = [
    "Fragment",
    "FragmentExtractionError",
    "find_inner_xhtml",
    "detect_instrument",
    "load_fragment",
]
