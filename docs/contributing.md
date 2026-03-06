# Contributing Guide

> **Version**: 0.3.7
> **Last Updated**: 2026-03-06 14:00
> Standar penulisan kode untuk Agent AI dan developer manusia.

## Code Standards

- **Language**: Python 3.10+
- **Type Hints**: Wajib untuk semua fungsi publik
- **Formatter**: Ruff (`ruff format`)
- **Linter**: Ruff (`ruff check`)
- **Type Checker**: Mypy (`mypy --strict`)
- **Testing**: pytest + hypothesis + pytest-asyncio
- **Package Manager**: UV (NOT conda)
- **Virtual Environment**: `.venv/` (created by UV, NOT conda env)

## Commit Convention

```
<type>: <description>

Types: feat, fix, refactor, test, docs, chore
```

## File Naming

- Python: `snake_case.py`
- Classes: `PascalCase`
- Constants: `UPPER_SNAKE_CASE`
- Test files: `test_<module>.py`
- Config files: `config.yaml`, `.env`

## Agent-Specific Rules (MANDATORY)

> ⚠️ These rules are enforced by `.agent/workflows/update-docs.md`

### Documentation Protocol

1. **Setiap Phase selesai** → Update `docs/task_status.md` (mark ✅, update file count)
2. **Setiap code change** → Append ke `docs/changelogs.md` (version, date, details)
3. **Setiap new module/endpoint** → Update `docs/architecture.md` (diagram, API table)
4. **Setiap new command/script** → Update `docs/workflow.md` (commands, URLs)
5. **Setiap new API key/auth** → Update `docs/security.md` (keys table, auth)
6. **Setiap new convention** → Update `docs/contributing.md` (this file)

### Code Quality Rules

7. **Error Handling** → Setiap function publik WAJIB punya try/except
8. **Empty Input Validation** → Semua adapter WAJIB validate input kosong
9. **Timeout Protection** → Setiap async call ke external API WAJIB pakai `asyncio.wait_for` atau `Retry/CircuitBreaker`
10. **Health Checks** → Setiap component HARUS register ke `HealthManager`
11. **Mock Mode** → Setiap GPU component WAJIB punya mock fallback
12. **Logging & Tracing** → Gunakan `structlog` dengan `trace_id` dan `Sentry` jika tersedia.
13. **Metrics** → Track interaksi penting menggunakan `AnalyticsEngine` untuk Prometheus.

### Testing Rules

14. **Unit tests** → Jalankan dalam `MOCK_MODE=true`
15. **Integration tests** → Harus tes integrasi di GPU server
16. **Authentic tests** → Gunakan `test_authentic_flow.py` (MOCK_MODE=false) untuk memvalidasi interaksi LLM/TTS secara nyata.
17. **New feature** → WAJIB punya minimal 1 test
18. **Bug fix** → WAJIB punya regression test

### Pre-Completion Checklist

Before reporting to user, verify:

- [ ] All 6 docs files updated
- [ ] Tests pass (`pytest tests/ -v`)
- [ ] Linting passes (`ruff check src/`)
- [ ] `changelogs.md` has new entry
- [ ] `task_status.md` reflects current state

## UV Package Manager Rules

### Setup Commands

```bash
# Create virtual environment (ALWAYS in project root)
uv venv

# Install dependencies
uv pip install -e .                    # Core only
uv pip install -e ".[livetalking]"    # With LiveTalking
uv pip install -e ".[dev]"            # With dev tools

# Run scripts (ALWAYS use uv run)
uv run python -m src.main
uv run pytest tests/
uv run ruff check src/
```

### UV Best Practices

1. **NEVER mix UV and conda** — Don't activate conda env when using UV
2. **Always use `uv run`** — Ensures correct Python interpreter from `.venv`
3. **Check Python path** — Verify using `.venv/Scripts/python.exe`:
   ```bash
   uv run python -c "import sys; print(sys.executable)"
   # Should output: videoliveai\.venv\Scripts\python.exe
   ```
4. **Clean install if corrupt** — Delete `.venv` + clean cache:
   ```bash
   rm -rf .venv
   uv cache clean
   uv venv
   uv pip install -e ".[livetalking]"
   ```

### Common UV Errors

| Error | Cause | Solution |
|-------|-------|----------|
| Using miniconda Python | `.venv` not created | Run `uv venv` first |
| Module not found | Dependencies not installed | Run `uv pip install -e .` |
| Websockets corruption | Corrupt cache/venv | Delete `.venv`, clean cache, reinstall |
| Path not found | Wrong directory | `cd videoliveai/` first |

## Project Structure Convention

```
videoliveai/
├── .venv/                   # UV virtual environment (NEVER commit!)
├── src/<layer>/
│   ├── __init__.py          # Package exports
│   ├── <main_module>.py     # Core logic
│   └── <sub_module>.py      # Supporting modules
├── tests/
│   ├── test_<layer>.py      # Layer-specific tests
│   └── conftest.py          # Shared fixtures
├── scripts/
│   ├── setup_livetalking.py # LiveTalking setup automation
│   ├── quick_setup.bat      # Fast setup (no LiveTalking)
│   └── setup_livetalking_uv.bat  # Full setup with LiveTalking
├── external/                # Git submodules
│   └── livetalking/         # LiveTalking repository
├── docs/
│   ├── architecture.md      # System design (KEEP CURRENT!)
│   ├── workflow.md          # Dev & deploy commands
│   ├── changelogs.md        # Version history
│   ├── task_status.md       # Phase completion tracker
│   ├── security.md          # Auth & keys
│   └── contributing.md      # This file
├── SETUP_GUIDE.md           # Setup options guide
├── LIVETALKING_QUICKSTART.md  # LiveTalking integration guide
├── UV_VS_CONDA_GUIDE.md     # UV vs Conda explained
└── pyproject.toml           # UV dependencies
```
