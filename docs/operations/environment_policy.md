# Environment Policy

> **Status**: Active
> **Date**: 2026-03-07

## UV-Only Policy

This project uses **UV** as the sole package/environment manager.

### Rules

1. **DO** use `uv venv`, `uv sync`, `uv run`, and `uv pip` for all operations
2. **DO NOT** use `conda create`, `conda activate`, or `pip install` directly to system Python
3. **DO NOT** introduce poetry, pipenv, or any other package manager
4. **DO** ensure all scripts work on both Windows and Ubuntu

### Standard Commands

| Action | Command |
|--------|---------|
| Create venv | `uv venv` |
| Install deps | `uv sync --extra dev` |
| Install package | `uv pip install <package>` |
| Run Python | `uv run python -m src.main` |
| Run tests | `uv run pytest tests -v` |
| Run script | `uv run python scripts/<script>.py` |

### Windows Batch Scripts

All `.bat` files must:
- Use `uv run` for Python execution
- Not assume conda is available
- Work from the project root directory
- Set `PYTHONUTF8=1` when producing Unicode output

### Ubuntu Server Equivalents

All commands should work identically on Ubuntu with:
```bash
uv sync --extra dev
uv run pytest tests -q -p no:cacheprovider
uv run python -m src.main
```

### What NOT to Do

```bash
# WRONG - conda
conda create -n videoliveai python=3.12
conda activate videoliveai

# WRONG - direct pip to system
pip install fastapi

# WRONG - poetry
poetry install

# CORRECT - UV
uv sync --extra dev
uv run python -m src.main
```
