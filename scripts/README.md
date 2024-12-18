# Development Scripts

This directory contains utility scripts for managing the development environment.

## Available Scripts

### cleanup.py
Removes Python cache files and other development artifacts while preserving important configuration files.

Usage:
```bash
# Preview what would be removed (recommended before actual cleanup)
python scripts/cleanup.py --dry-run

# Perform the actual cleanup
python scripts/cleanup.py
```

When to use:
- Before committing code to clean up unnecessary files
- When switching between branches to ensure a clean state
- If you encounter unexpected behavior that might be caused by stale cache files
- After running tests to clean up test artifacts

Protected Files:
The following files will never be removed by the cleanup script:
- `.env`
- `.env.example`
- `.gitignore`
- `.windsurfrules`
- `README.md`
- `pyproject.toml`
- `setup.py`
- `requirements.txt`

## Best Practices

1. Always run with `--dry-run` first to preview what will be removed
2. Run cleanup when switching between major feature branches
3. Run cleanup if you encounter any import or module-related issues
4. Run cleanup before running a fresh test suite
