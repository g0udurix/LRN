#!/usr/bin/env python3
"""Headless fetch helper using Playwright to retrieve HTML/PDF content."""
from __future__ import annotations

import argparse
from pathlib import Path

from playwright.sync_api import sync_playwright


def fetch(url: str, out_path: Path, wait_until: str = 'domcontentloaded', timeout: int = 30000) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        context = browser.new_context()
        page = context.new_page()
        page.goto(url, wait_until=wait_until, timeout=timeout)
        page.wait_for_timeout(2000)
        if url.lower().endswith('.pdf'):
            content = page.content().encode('utf-8')
        else:
            content = page.content().encode('utf-8')
        out_path.write_bytes(content)
        browser.close()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('url', help='URL to fetch')
    parser.add_argument('--out', required=True, help='Output file path')
    parser.add_argument('--timeout', type=int, default=30000, help='Timeout in ms (default: 30000)')
    parser.add_argument('--wait-until', default='domcontentloaded', help='Playwright wait_until mode (default: domcontentloaded)')
    args = parser.parse_args()

    fetch(args.url, Path(args.out), wait_until=args.wait_until, timeout=args.timeout)


if __name__ == '__main__':
    main()
