# VideoLiveAI — Agent Context

**v0.3.1** | Python 3.10+ | UV package manager | MIT License

## What
AI live commerce: Multi-LLM + TTS + Avatar → RTMP streaming ke TikTok/Shopee

## Architecture
```
L1:Brain(LLM) L2:Voice(TTS) L3:Face(Avatar) L4:Composition L5:Stream L6:Chat L7:Commerce
Orchestrator: SELLING→REACTING→ENGAGING→IDLE (10Hz)
Priority: P1(purchase)→P2(question)→P3(comment)→P4(reaction)→P5(spam)
```

## Key Files
- `src/main.py` - Entry point
- `src/orchestrator/state_machine.py` - State machine
- `src/brain/router.py` - LLM routing
- `.env` + `config/config.yaml` - Config
- `data/logs/app.log` - Logs

## Config
**API Keys (.env):** GEMINI, ANTHROPIC, OPENAI, GROQ, TIKTOK_SESSION_ID, TIKTOK_STREAM_KEY
**LLM:** Gemini(chat,500ms) Claude(script,5s) GPT4o(emotion,1s) | Fallback: gemini→gpt4o→qwen
**Mock Mode:** `MOCK_MODE=true` untuk run tanpa GPU

## Commands
```bash
# Run (no GPU)
set MOCK_MODE=true && uv run python -m src.main

# Run (GPU)
uv run python -m src.main

# Test
uv run pytest tests/ -v

# Health
curl http://localhost:8000/diagnostic/health
```

## Coding Standards
- ✅ Type hints required
- ✅ Async/await for I/O
- ✅ Structured logging (no print!)
- ✅ Mock mode support
- ✅ Trace ID propagation

## Performance Targets
E2E: <2s | Chat:<50ms | LLM:<200ms | TTS:<500ms | Avatar:<800ms | Comp:<100ms

## Bottlenecks (see BOTTLENECK_FIXES.md)
1. Sequential LLM → Batch
2. Sequential TTS → Parallel
3. Sequential GFPGAN → Batch

## Common Issues
**GPU OOM:** Reduce `GPU_VRAM_BUDGET_MB` or use `MOCK_MODE=true`
**LLM timeout:** Check API keys, increase timeout
**Stream disconnect:** Verify RTMP credentials
**Chat not working:** Refresh TikTok session ID

## Docs
- `BOTTLENECK_FIXES.md` - Performance fixes
- `.kiro/steering/troubleshooting.md` - Debug guide
- `.kiro/steering/coding-standards.md` - Code guidelines
