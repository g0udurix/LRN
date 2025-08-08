#!/usr/bin/env python3
"""
bundle_codebase.py – Flatten a codebase into a single file.

Usage:
  python bundle_codebase.py                # bundle current directory
  python bundle_codebase.py /path/to/project

Output:
  Always writes to `codebase.md` in the working directory and automatically
  skips itself and that file.

Why:
  • Feed an entire repo to an LLM in one shot.
  • Deterministic, reproducible context snapshots.
"""

import argparse
import os
import sys
from pathlib import Path

# --- sensible defaults ------------------------------------------------------ #
DEFAULT_EXTS = (
    ".py .ipynb .js .ts .jsx .tsx .java .kt .c .h .cpp .hpp "
    ".go .rb .rs .swift .m .mm .sh .ps1 .bat .psm1 .pl .php "
    ".html .css .scss .json .yaml .yml .toml .ini .cfg .txt"
).split()

SKIP_DIRS = {
    ".git", ".hg", ".svn", "__pycache__", "node_modules", "build",
    "dist", "venv", ".venv", ".mypy_cache", ".pytest_cache",
}

MAX_FILE_SIZE = 2 * 1024 * 1024       # 2 MB – tweak if needed
ENCODING_FALLBACKS = ("utf-8", "latin-1", "cp1252")  # best-effort
# Files we always skip (besides size/binary filters)
EXCLUDE_FILES = {"codebase.md", "bundle_codebase.py"}


# --- helpers ---------------------------------------------------------------- #
def is_binary(path: Path) -> bool:
    """Rudimentary heuristic: file contains NUL byte in first 1024 bytes."""
    try:
        with open(path, "rb") as f:
            chunk = f.read(1024)
            return b"\0" in chunk
    except Exception:
        return True  # treat unreadable as binary


def read_text(path: Path) -> str | None:
    """Try several encodings; return None on failure."""
    for enc in ENCODING_FALLBACKS:
        try:
            return path.read_text(encoding=enc)
        except Exception:
            continue
    return None


def iter_source_files(root: Path, exts: set[str]):
    """Yield Path objects for candidate files in depth-first order."""
    for dirpath, dirnames, filenames in os.walk(root):
        # prune unwanted dirs in-place for efficiency
        dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
        for fn in filenames:
            p = Path(dirpath) / fn
            # skip bundler script and output regardless of extension filters
            if fn in EXCLUDE_FILES or fn == Path(__file__).name:
                continue
            if p.suffix.lower() in exts or (not exts and not is_binary(p)):
                yield p


# --- main ------------------------------------------------------------------- #
def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        description="Flatten a codebase into a single file for LLM ingestion."
    )
    parser.add_argument(
        "base_dir",
        type=Path,
        nargs="?",
        default=Path("."),
        help="Root of the project (default: current working directory)"
    )
    parser.add_argument(
        "-e", "--extensions", default=",".join(DEFAULT_EXTS),
        help=(
            "Comma-separated list of file extensions to include. "
            "Use '*' to disable filtering. Output is always written to codebase.md."
        ),
    )
    parser.add_argument(
        "--max-bytes", type=int, default=MAX_FILE_SIZE,
        help=f"Skip files bigger than this many bytes (default: {MAX_FILE_SIZE})",
    )
    args = parser.parse_args(argv)

    exts = set() if args.extensions.strip() == "*" else {
        e.lower() if e.startswith(".") else f".{e.lower()}"
        for e in args.extensions.split(",") if e.strip()
    }

    output_path = Path("codebase.md").resolve()
    sink = open(output_path, "w", encoding="utf-8")

    root = args.base_dir.resolve()
    if not root.is_dir():
        sys.exit(f"Error: {root} is not a directory")
    script_basename = Path(__file__).name

    written = 0
    for path in sorted(iter_source_files(root, exts), key=str):
        # Skip the bundler itself and the output file
        if path.resolve() == output_path:
            continue
        if path.name == script_basename or path.name in EXCLUDE_FILES:
            continue
        if path.stat().st_size > args.max_bytes:
            continue
        if is_binary(path):
            continue

        text = read_text(path)
        if text is None:
            continue

        separator = f"\n\n{'='*80}\n# FILE: {path.relative_to(root)}\n{'='*80}\n"
        sink.write(separator)
        sink.write(text.rstrip() + "\n")   #  ensure trailing newline
        written += 1

    sink.close()
    print(f"Bundled {written} files from {root} -> {output_path}", file=sys.stderr)


if __name__ == "__main__":
    main()
