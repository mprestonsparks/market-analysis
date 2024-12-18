#!/usr/bin/env python3
"""
Cleanup script to remove Python cache files and other development artifacts.
"""

import os
import shutil
import glob
import argparse
from pathlib import Path
from typing import Set

def get_protected_files() -> Set[str]:
    """Get list of files that should never be removed."""
    return {
        ".env",
        ".env.example",
        ".gitignore",
        ".windsurfrules",
        "README.md",
        "pyproject.toml",
        "setup.py",
        "requirements.txt"
    }

def cleanup_project(dry_run: bool = False):
    """Remove Python cache files and other development artifacts.
    
    Args:
        dry_run: If True, only print what would be removed without actually removing
    """
    # Get the project root directory (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    protected_files = get_protected_files()
    
    # Patterns for files/directories to remove
    patterns = [
        "**/__pycache__",
        "**/*.pyc",
        "**/*.pyo",
        "**/*.pyd",
        "**/.pytest_cache",
        "**/.coverage",
        "**/htmlcov",
        "**/.tox",
        "**/*.egg-info",
        "**/*.egg",
        "**/dist",
        "**/build",
        "**/.eggs",
        "**/.mypy_cache",
        "**/.hypothesis",
    ]

    total_found = 0
    total_removed = 0
    
    print(f"{'[DRY RUN] ' if dry_run else ''}Cleaning up project at: {project_root}")
    print("-" * 50)

    for pattern in patterns:
        # Use glob to find all matching paths
        matches = glob.glob(str(project_root / pattern), recursive=True)
        
        for path in matches:
            total_found += 1
            relative_path = os.path.relpath(path, project_root)
            
            # Skip protected files
            if os.path.basename(path) in protected_files:
                print(f"Skipping protected file: {relative_path}")
                continue

            try:
                if dry_run:
                    print(f"Would remove: {relative_path}")
                    continue

                if os.path.isfile(path):
                    os.remove(path)
                    print(f"Removed file: {relative_path}")
                    total_removed += 1
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"Removed directory: {relative_path}")
                    total_removed += 1
            except Exception as e:
                print(f"Error processing {relative_path}: {e}")

    print("-" * 50)
    if dry_run:
        print(f"Dry run complete! Would remove {total_found} items")
    else:
        print(f"Cleanup complete! Removed {total_removed} of {total_found} items found")

def main():
    parser = argparse.ArgumentParser(description="Cleanup development artifacts")
    parser.add_argument("--dry-run", action="store_true", 
                      help="Show what would be removed without actually removing")
    args = parser.parse_args()
    
    cleanup_project(dry_run=args.dry_run)

if __name__ == "__main__":
    main()
