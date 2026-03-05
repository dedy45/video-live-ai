# VideoLiveAI — Quick Reference

**v0.3.1** | Python 3.10+ | UV | MIT

## What
AI live commerce platform: Multi-LLM + TTS + Avatar → RTMP streaming

## Commands
```bash
set MOCK_MODE=true && uv run python -m src.main  # No GPU
uv run python -m src.main                        # With GPU
uv run pytest tests/ -v                          # Test
curl http://localhost:8000/diagnostic/health     # Health
```

## Architecture
7-layer: Brain(LLM) Voice(TTS) Face(Avatar) Composition Stream Chat Commerce
Orchestrator: SELLING→REACTING→ENGAGING→IDLE

## Key Files
- `AGENTS.md` - Complete context
- `src/main.py` - Entry point
- `.env` + `config/config.yaml` - Config
- `BOTTLENECK_FIXES.md` - Performance

## Config
**API Keys:** GEMINI, ANTHROPIC, OPENAI, GROQ, TIKTOK_SESSION_ID, TIKTOK_STREAM_KEY
**LLM:** Gemini(chat) Claude(script) GPT4o(emotion) | Fallback: gemini→gpt4o→qwen

## Common Issues
- GPU OOM → `MOCK_MODE=true`
- LLM timeout → Check API keys
- Stream fail → Check RTMP credentials
- Chat fail → Refresh TikTok session

## Docs
- `AGENTS.md` - Main docs
- `BOTTLENECK_FIXES.md` - Performance
- `.kiro/steering/troubleshooting.md` - Debug
