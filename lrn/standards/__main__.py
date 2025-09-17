from __future__ import annotations

import argparse
from pathlib import Path

from .models import load_mappings, validate_mapping_file


def main() -> None:
    parser = argparse.ArgumentParser(description='Standards mapping utilities')
    sub = parser.add_subparsers(dest='command', required=True)

    validate_cmd = sub.add_parser('validate', help='Validate a mapping JSON file')
    validate_cmd.add_argument('path', help='Path to mapping JSON/YAML (JSON supported currently)')

    args = parser.parse_args()

    if args.command == 'validate':
        validate_mapping_file(Path(args.path))
        mappings = load_mappings(Path(args.path))
        print(f"Validated {len(mappings)} mappings in {args.path}")


if __name__ == '__main__':
    main()
