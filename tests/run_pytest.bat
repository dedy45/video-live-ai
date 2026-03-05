@echo off
set "MOCK_MODE=true"
uv run pytest tests/ -v > debug_output.txt 2>&1
echo Done.
