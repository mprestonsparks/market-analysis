#!/usr/bin/env python3
"""
Cleanup script to remove Python cache files and other development artifacts.
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_project():
    """Remove Python cache files and other development artifacts."""
    # Get the project root directory (parent of scripts directory)
    project_root = Path(__file__).parent.parent
    
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

    total_removed = 0
    
    print(f"Cleaning up project at: {project_root}")
    print("-" * 50)

    for pattern in patterns:
        # Use glob to find all matching paths
        matches = glob.glob(str(project_root / pattern), recursive=True)
        
        for path in matches:
            try:
                if os.path.isfile(path):
                    os.remove(path)
                    print(f"Removed file: {path}")
                    total_removed += 1
                elif os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"Removed directory: {path}")
                    total_removed += 1
            except Exception as e:
                print(f"Error removing {path}: {e}")

    print("-" * 50)
    print(f"Cleanup complete! Removed {total_removed} items.")

if __name__ == "__main__":
    cleanup_project()
