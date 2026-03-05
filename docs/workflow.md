# Development & Deployment Workflow

> **Version**: 0.4.3
> **Last Updated**: 2026-03-03 19:35

## Quick Start — CLI Scripts

```bash
# Interactive Controller Menu (recommended)
scripts\menu.bat

# Full Validation Pipeline (automated, no prompts)
scripts\validate.bat
```

| Environment  | Purpose                                       | GPU              | Location     |
| ------------ | --------------------------------------------- | ---------------- | ------------ |
| Local (Dev)  | Code editing, unit tests, Mock Mode           | ❌               | Windows/Mac  |
| Remote (GPU) | Model inference, integration tests, streaming | ✅ RTX 4090/A100 | RunPod/Cloud |

## Local Development

```bash
# 1. Clone & Setup
cd videoliveai
uv sync

# 2. Run in Mock Mode (no GPU needed)
MOCK_MODE=true uv run python -m src.main

# 3. Access endpoints
#    Dashboard UI:   http://localhost:8000/dashboard
#    API Docs:       http://localhost:8000/docs
#    Diagnostic:     http://localhost:8000/diagnostic/
#    Metrics:        http://localhost:8000/metrics

# 4. Dashboard login:  admin / changeme (set in .env)
```

## Verification & Testing

```bash
# Verify all layers via Mock Architecture
MOCK_MODE=true python scripts/verify_pipeline.py --verbose

# Run Authentic Integration (Bypasses Mock, hits Real LLM/TTS APIs)
# WARNING: Will consume API credits (Groq/Gemini).
python scripts/test_authentic_flow.py

# Run all unit / property tests
uv run pytest tests/ -v
```

## Remote GPU Deployment (RunPod/EC2)

Ensure you have a Linux machine with an NVIDIA GPU and SSH access.

```bash
# 1. Sync local workspace to remote
REMOTE_HOST=IP_ADDRESS REMOTE_PORT=22 REMOTE_USER=root scripts/remote_sync.sh

# 2. Execute and run detatched in tmux
REMOTE_HOST=IP_ADDRESS REMOTE_PORT=22 REMOTE_USER=root scripts/remote_run.sh
```

# Run specific test file

uv run pytest tests/test_brain.py -v
uv run pytest tests/test_dashboard.py -v
uv run pytest tests/test_hardening.py -v

# Run linting

uv run ruff check src/
uv run mypy src/

````

## Remote Deployment

```bash
# 1. Sync code to remote server
./scripts/remote_sync.sh

# 2. SSH into server
ssh user@gpu-server

# 3. Run with GPU
cd /workspace/videoliveai
uv sync --extra gpu
MOCK_MODE=false uv run python -m src.main

# 4. Run integration tests (requires GPU)
uv run pytest tests/ -v -m integration
````

## Testing Pyramid

| Level          | Mode              | Location   | Command                             |
| -------------- | ----------------- | ---------- | ----------------------------------- |
| Unit Tests     | `MOCK_MODE=true`  | Local      | `pytest tests/`                     |
| Property Tests | `MOCK_MODE=true`  | Local      | `pytest tests/ -k hypothesis`       |
| Integration    | `MOCK_MODE=false` | GPU Server | `pytest tests/ -m integration`      |
| Verification   | `MOCK_MODE=true`  | Local      | `python scripts/verify_pipeline.py` |

## Test Files

| File                  | Tests  | Focus                                 |
| --------------------- | ------ | ------------------------------------- |
| `test_config.py`      | 5      | Config loading                        |
| `test_mock_mode.py`   | 6      | Mock voice/avatar                     |
| `test_brain.py`       | 16     | LLM adapters, router, persona, safety |
| `test_layers.py`      | 14     | Voice, face, stream, chat, commerce   |
| `test_hardening.py`   | 12     | Timeout, exceptions, edge cases       |
| `test_dashboard.py`   | 10     | Analytics, dashboard API              |
| `test_property.py`    | 2      | Hypothesis config round-trip          |
| `test_performance.py` | 2      | GPU benchmark placeholders            |
| **Total**             | **67** | **All passing in MOCK_MODE**          |
