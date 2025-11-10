#!/usr/bin/env python
"""
Add SPDX license headers to Python files.

This script adds MIT license headers to all Python files in the project.
"""

import sys
from pathlib import Path
from typing import List

# SPDX License Header (MIT)
LICENSE_HEADER = '''"""
SPDX-License-Identifier: MIT
Copyright (c) 2025 KooCAD Team

KooCAD - Parametric Electronic Component CAD Automation System
"""

'''


def should_skip_file(file_path: Path) -> bool:
    """Check if file should be skipped."""
    # Skip if already has license header
    content = file_path.read_text()
    if "SPDX-License-Identifier" in content:
        return True

    # Skip __pycache__ and other build artifacts
    if "__pycache__" in str(file_path):
        return True

    return False


def add_header_to_file(file_path: Path, dry_run: bool = False) -> bool:
    """Add license header to a file.

    Args:
        file_path: Path to Python file.
        dry_run: If True, don't actually modify files.

    Returns:
        True if header was added.
    """
    if should_skip_file(file_path):
        return False

    content = file_path.read_text()

    # Handle shebang
    if content.startswith("#!"):
        lines = content.split("\n", 1)
        shebang = lines[0] + "\n"
        rest = lines[1] if len(lines) > 1 else ""
        new_content = shebang + LICENSE_HEADER + rest
    else:
        new_content = LICENSE_HEADER + content

    if not dry_run:
        file_path.write_text(new_content)

    return True


def process_directory(
    directory: Path,
    dry_run: bool = False,
) -> tuple[int, int]:
    """Process all Python files in directory.

    Args:
        directory: Root directory.
        dry_run: If True, don't actually modify files.

    Returns:
        Tuple of (files_processed, files_modified).
    """
    processed = 0
    modified = 0

    for py_file in directory.rglob("*.py"):
        processed += 1
        if add_header_to_file(py_file, dry_run=dry_run):
            modified += 1
            print(f"✓ {py_file.relative_to(directory)}")
        else:
            print(f"- {py_file.relative_to(directory)} (skipped)")

    return processed, modified


def main() -> int:
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Add SPDX license headers")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually modify files",
    )
    parser.add_argument(
        "directory",
        nargs="?",
        default="src",
        help="Directory to process (default: src)",
    )

    args = parser.parse_args()

    directory = Path(args.directory)
    if not directory.exists():
        print(f"Error: Directory '{directory}' does not exist")
        return 1

    print(f"Processing Python files in {directory}...")
    if args.dry_run:
        print("(DRY RUN - no files will be modified)")

    processed, modified = process_directory(directory, dry_run=args.dry_run)

    print(f"\nSummary:")
    print(f"  Files processed: {processed}")
    print(f"  Files modified: {modified}")
    print(f"  Files skipped: {processed - modified}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
