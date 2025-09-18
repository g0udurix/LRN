#!/usr/bin/env python3
"""Governance helper CLI for syncing repository templates and performing self-checks."""
from __future__ import annotations

import argparse
import filecmp
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable, List


DEFAULT_TEMPLATE_DIR = Path(__file__).parent / "governance" / "templates"
DEFAULT_REPO_ROOT = Path(__file__).parent


@dataclass
class TemplateEntry:
    """Represents a governance template and its target destination."""

    source: Path
    destination: Path
    template_root: Path

    @property
    def relative_path(self) -> Path:
        return self.source.relative_to(self.template_root)


def discover_templates(template_dir: Path, repo_root: Path) -> List[TemplateEntry]:
    """Return all template files under template_dir mapped to repo_root."""
    if not template_dir.exists():
        raise FileNotFoundError(f"Template directory not found: {template_dir}")

    entries: List[TemplateEntry] = []
    for path in sorted(template_dir.rglob("*")):
        if path.is_file():
            relative = path.relative_to(template_dir)
            entries.append(TemplateEntry(source=path, destination=repo_root / relative, template_root=template_dir))
    return entries


def find_mismatches(entries: Iterable[TemplateEntry]) -> List[TemplateEntry]:
    """Return templates whose destinations are missing or content-mismatched."""
    mismatches: List[TemplateEntry] = []
    for entry in entries:
        dest = entry.destination
        if not dest.exists():
            mismatches.append(entry)
            continue
        try:
            if not filecmp.cmp(entry.source, dest, shallow=False):
                mismatches.append(entry)
        except OSError:
            mismatches.append(entry)
    return mismatches


def apply_templates(entries: Iterable[TemplateEntry]) -> None:
    """Copy templates to their destinations, creating parent directories as needed."""
    for entry in entries:
        entry.destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(entry.source, entry.destination)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Governance helper CLI")
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Copy templates into the repository",
    )
    parser.add_argument(
        "--self-test",
        action="store_true",
        help="Validate that repository files match governance templates",
    )
    parser.add_argument(
        "--template-dir",
        type=Path,
        default=None,
        help="Override template directory (for testing)",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Override repository root (for testing)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without copying files (when used with --apply)",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    template_dir = args.template_dir or DEFAULT_TEMPLATE_DIR
    repo_root = args.repo_root or DEFAULT_REPO_ROOT

    entries = discover_templates(template_dir, repo_root)

    exit_code = 0

    if args.self_test:
        mismatches = find_mismatches(entries)
        if mismatches:
            exit_code = 1
            print("[SELF-TEST] Mismatches detected:")
            for entry in mismatches:
                status = "missing" if not entry.destination.exists() else "differs"
                print(f" - {entry.destination} ({status})")
        else:
            print("[SELF-TEST] All templates match repository files.")

    if args.apply:
        mismatches = find_mismatches(entries)
        if not mismatches:
            print("[APPLY] No changes required.")
        else:
            print("[APPLY] Updating files:")
            for entry in mismatches:
                print(f" - {entry.destination}")
            if not args.dry_run:
                apply_templates(mismatches)
                print("[APPLY] Copy complete.")
            else:
                print("[DRY-RUN] No files were written.")

    if not args.self_test and not args.apply:
        parser.print_help()

    return exit_code


if __name__ == "__main__":  # pragma: no cover - entry point
    raise SystemExit(main())
