# 🎯 ACTION ITEMS - PRIORITIZED & ACTIONABLE

**Created**: 6 Maret 2026  
**Status**: Ready for Execution  
**Timeline**: 8 minggu (realistic)

---

## 🔥 IMMEDIATE ACTIONS (Hari Ini)

### 1. Verify Current State
```bash
cd videoliveai

# Test 1: Config loading
uv run python -c "from src.config import load_config; c=load_config(); print(f'Config OK: {c.app.name}')"

# Test 2: Database
uv run python -c "from src.data.database import init_database, check_database_health; init_database(); print(check_database_health())"

# Test 3: LLM Router
uv run python -c "from src.brain.router import LLMRouter; r=LLMRouter(); print(f'Adapters: {list(r.adapters.keys())}')"

# Test 4: Face Pipeline (akan fail)
set MOCK_MODE=true
uv run python -c "from src.face.livetalking_adapter import LiveTalkingPipeline; p=LiveTalkingPipeline(); print('Pipeline OK')"

# Test 5: Start server
set MOCK_MODE=true
set LOG_LEVEL=DEBUG
uv run python -m src.main
# Buka: http://localhost:8000/diagnostic/health
```

**Expected Results**:
- ✅ Config, Database, LLM Router: OK
- ⚠️ Face Pipeline: OK tapi tidak functional
- ✅ Server: Starts tapi face rendering tidak jalan

### 2. Document Current Failures
**File**: `CURRENT_FAILURES.md` (create)

```markdown
# Current Failures

## 1. Face Pipeline
- Status: Loads but NotImplementedError on generate_frames()
- Impact: No video generation
- Fix: Implement LiveTalking integration

## 2. Streaming
- Status: RTMPStreamer exists but not connected
- Impact: No output to TikTok/Shopee
- Fix: Connect orchestrator → streamer

## 3. Tests
- Status: No test files
- Impact: Can't verify anything works
- Fix: Create test suite
```

### 3. Update README with Honest Status
**File**: `README.md`

Add section:
```markdown
## ⚠️ CURRENT STATUS (HONEST)

### What Works
- ✅ Configuration loading
- ✅ Database initialization
- ✅ LLM routing (multi-provider)
- ✅ Voice synthesis (EdgeTTS)
- ✅ Mock mode for development

### What Doesn't Work
- ❌ Face rendering (NotImplementedError)
- ❌ LiveTalking integration (skeleton only)
- ❌ RTMP streaming (not connected)
- ❌ End-to-end flow (incomplete)

### Timeline to Production
- MVP (basic flow): 2 weeks
- LiveTalking integration: 4-6 weeks
- Production ready: 8 weeks
```

---

## 📅 WEEK 1: Foundation & Testing

### Day 1: Dependency Management
**Goal**: Resolve all dependency conflicts

**Tasks**:
1. Create unified requirements
```bash
# Merge livetalking requirements ke pyproject.toml
cd videoliveai
# Edit pyproject.toml, add livetalking deps
```

2. Test installation
```bash
# Clean environment
uv venv --python 3.10
uv pip install -e ".[livetalking,dev]"
```

3. Document conflicts
```bash
# Create DEPENDENCIES.md
# List all conflicts and resolutions
```

**Deliverable**: Clean installation tanpa conflicts

### Day 2: Test Infrastructure
**Goal**: Create pytest setup

**Tasks**:
1. Create test directory structure
```bash
mkdir -p tests/{unit,integration,e2e}
touch tests/__init__.py
touch tests/conftest.py
```

2. Create fixtures (`tests/conftest.py`)
```python
import pytest
import os

@pytest.fixture(autouse=True)
def mock_mode():
    """Enable mock mode for all tests."""
    os.environ["MOCK_MODE"] = "true"
    yield
    os.environ.pop("MOCK_MODE", None)

@pytest.fixture
def config():
    """Load test config."""
    from src.config import load_config
    return load_config()

@pytest.fixture
async def llm_router():
    """Create LLM router."""
    from src.brain.router import LLMRouter
    return LLMRouter()
```

3. Create first test (`tests/unit/test_config.py`)
```python
import pytest
from src.config import load_config, is_mock_mode

def test_config_loads():
    config = load_config()
    assert config.app.name == "AI Live Commerce"

def test_mock_mode():
    assert is_mock_mode() == True
```

**Deliverable**: Working pytest setup

### Day 3: Unit Tests - Config & Database
**Goal**: Test core components

**Files to Create**:
1. `tests/unit/test_config.py`
2. `tests/unit/test_database.py`
3. `tests/unit/test_logging.py`

**Example** (`tests/unit/test_database.py`):
```python
import pytest
from src.data.database import init_database, check_database_health

def test_database_init():
    init_database()
    health = check_database_health()
    assert health["healthy"] == True

def test_database_schema():
    from src.data.database import get_db
    db = get_db()
    # Test tables exist
    assert db is not None
```

**Run**:
```bash
pytest tests/unit/ -v
```

**Deliverable**: 10+ passing unit tests

### Day 4: Unit Tests - Brain & Voice
**Goal**: Test LLM and TTS

**Files to Create**:
1. `tests/unit/test_brain_router.py`
2. `tests/unit/test_voice_engine.py`

**Example** (`tests/unit/test_brain_router.py`):
```python
import pytest
from src.brain.router import LLMRouter
from src.brain.adapters.base import TaskType

@pytest.mark.asyncio
async def test_llm_router_init():
    router = LLMRouter()
    assert len(router.adapters) > 0

@pytest.mark.asyncio
async def test_llm_route_mock():
    router = LLMRouter()
    # Mock response
    response = await router.route(
        system_prompt="You are helpful",
        user_prompt="Hello",
        task_type=TaskType.CHAT_REPLY
    )
    # In mock mode, should get response from local
    assert response.success or response.error
```

**Run**:
```bash
pytest tests/unit/test_brain_router.py -v
```

**Deliverable**: Brain & Voice tests passing

### Day 5: Integration Test - Mock Flow
**Goal**: Test end-to-end dengan mock mode

**File**: `tests/integration/test_mock_flow.py`

```python
import pytest
from src.brain.router import LLMRouter
from src.voice.engine import VoiceRouter
from src.face.livetalking_adapter import LiveTalkingPipeline

@pytest.mark.asyncio
async def test_text_to_speech_flow():
    """Test: Text → TTS → Audio"""
    voice = VoiceRouter()
    result = await voice.synthesize("Hello world")
    assert result.audio_data is not None
    assert result.duration_ms > 0

@pytest.mark.asyncio
async def test_speech_to_video_flow():
    """Test: Audio → Face → Video"""
    pipeline = LiveTalkingPipeline()
    audio_data = b"fake audio data"
    
    frames = []
    async for frame in pipeline.render(audio_data, 1000.0):
        frames.append(frame)
        if len(frames) >= 5:  # Test 5 frames
            break
    
    assert len(frames) == 5
    assert frames[0].pixels is not None

@pytest.mark.asyncio
async def test_full_mock_flow():
    """Test: Text → TTS → Face → Video"""
    llm = LLMRouter()
    voice = VoiceRouter()
    face = LiveTalkingPipeline()
    
    # 1. Generate text
    from src.brain.adapters.base import TaskType
    text_response = await llm.route(
        system_prompt="You are a seller",
        user_prompt="Describe this product",
        task_type=TaskType.SELLING_SCRIPT
    )
    
    # 2. Text to speech
    audio = await voice.synthesize(text_response.text)
    
    # 3. Speech to video
    frames = []
    async for frame in face.render(audio.audio_data, audio.duration_ms):
        frames.append(frame)
        if len(frames) >= 3:
            break
    
    assert len(frames) == 3
```

**Run**:
```bash
pytest tests/integration/test_mock_flow.py -v
```

**Deliverable**: Mock flow working end-to-end

### Day 6-7: Documentation
**Goal**: Document everything

**Files to Create/Update**:
1. `TESTING.md` - How to run tests
2. `DEVELOPMENT.md` - Development guide
3. `TROUBLESHOOTING.md` - Common issues
4. `API.md` - API documentation

**Example** (`TESTING.md`):
```markdown
# Testing Guide

## Setup
```bash
uv pip install -e ".[dev]"
```

## Run Tests
```bash
# All tests
pytest

# Unit tests only
pytest tests/unit/ -v

# Integration tests
pytest tests/integration/ -v

# With coverage
pytest --cov=src --cov-report=html
```

## Mock Mode
All tests run in mock mode by default (no GPU needed).

## Integration Tests (GPU)
```bash
# Requires GPU
set MOCK_MODE=false
pytest tests/integration/ -v -m integration
```
```

**Deliverable**: Complete documentation

---

## 📅 WEEK 2-3: LiveTalking Integration

### Day 8-10: HTTP Client Implementation
**Goal**: Create working LiveTalking client

**File**: `src/face/livetalking_client.py` (NEW)

**Implementation**:
```python
import httpx
import asyncio
from typing import AsyncIterator

class LiveTalkingClient:
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.session_id = None
        self.client = httpx.AsyncClient(timeout=30.0)
    
    async def health_check(self) -> bool:
        """Check if LiveTalking server is running."""
        try:
            response = await self.client.get(f"{self.base_url}/")
            return response.status_code == 200
        except:
            return False
    
    async def create_session(self) -> str:
        """Create WebRTC session."""
        # TODO: Implement WebRTC offer/answer
        pass
    
    async def send_text(self, text: str) -> None:
        """Send text for TTS + lip-sync."""
        if not self.session_id:
            raise RuntimeError("No active session")
        
        response = await self.client.post(
            f"{self.base_url}/human",
            json={
                "sessionid": self.session_id,
                "type": "echo",
                "text": text
            }
        )
        response.raise_for_status()
    
    async def close(self):
        await self.client.aclose()
```

**Test**: `tests/unit/test_livetalking_client.py`

**Deliverable**: Working HTTP client

### Day 11-13: WebRTC Integration
**Goal**: Read video stream dari LiveTalking

**File**: `src/face/webrtc_reader.py` (NEW)

**Implementation**:
```python
from aiortc import RTCPeerConnection, RTCSessionDescription
from av import VideoFrame as AVVideoFrame
from src.face.pipeline import VideoFrame
import asyncio

class WebRTCStreamReader:
    def __init__(self, base_url: str = "http://localhost:8010"):
        self.base_url = base_url
        self.pc = None
        self.video_track = None
    
    async def connect(self) -> bool:
        """Establish WebRTC connection."""
        self.pc = RTCPeerConnection()
        
        # Create offer
        offer = await self.pc.createOffer()
        await self.pc.setLocalDescription(offer)
        
        # Send to LiveTalking
        import httpx
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/offer",
                json={
                    "sdp": self.pc.localDescription.sdp,
                    "type": self.pc.localDescription.type
                }
            )
            data = response.json()
        
        # Set remote description
        answer = RTCSessionDescription(
            sdp=data["sdp"],
            type=data["type"]
        )
        await self.pc.setRemoteDescription(answer)
        
        # Get video track
        @self.pc.on("track")
        def on_track(track):
            if track.kind == "video":
                self.video_track = track
        
        return True
    
    async def read_frame(self) -> VideoFrame:
        """Read single frame."""
        if not self.video_track:
            raise RuntimeError("No video track")
        
        av_frame = await self.video_track.recv()
        
        # Convert av.VideoFrame → VideoFrame
        import numpy as np
        img = av_frame.to_ndarray(format="bgr24")
        
        return VideoFrame(
            pixels=img,
            timestamp_ms=av_frame.pts * 1000.0 / 90000,
            width=img.shape[1],
            height=img.shape[0]
        )
    
    async def close(self):
        if self.pc:
            await self.pc.close()
```

**Test**: `tests/integration/test_webrtc_reader.py`

**Deliverable**: Working WebRTC reader

### Day 14: Update LiveTalking Adapter
**Goal**: Connect client + reader ke adapter

**File**: `src/face/livetalking_adapter.py` (UPDATE)

**Changes**:
```python
from src.face.livetalking_client import LiveTalkingClient
from src.face.webrtc_reader import WebRTCStreamReader

class LiveTalkingEngine(BaseAvatarEngine):
    def __init__(self, ...):
        # ... existing code ...
        self.client = LiveTalkingClient()
        self.reader = WebRTCStreamReader()
    
    async def initialize(self) -> bool:
        # Check server
        if not await self.client.health_check():
            logger.error("LiveTalking server not running")
            return False
        
        # Connect WebRTC
        if not await self.reader.connect():
            logger.error("WebRTC connection failed")
            return False
        
        self._initialized = True
        return True
    
    async def generate_frames(
        self,
        audio_data: bytes,
        duration_ms: float,
        trace_id: str = "",
    ) -> AsyncIterator[VideoFrame]:
        if not self._initialized:
            await self.initialize()
        
        # Send audio to LiveTalking
        # (Implementation depends on LiveTalking API)
        
        # Read frames from WebRTC
        start_time = time.time()
        while (time.time() - start_time) * 1000 < duration_ms:
            frame = await self.reader.read_frame()
            frame.trace_id = trace_id
            yield frame
```

**Test**: `tests/integration/test_livetalking_adapter.py`

**Deliverable**: Working adapter

---

## 📅 WEEK 4: Process Management & Orchestrator

### Day 15-17: Process Manager
**Goal**: Manage LiveTalking server lifecycle

**File**: `src/face/livetalking_process.py` (NEW)

**Implementation**: (See detailed spec in INTEGRASI_LIVETALKING_SUMMARY.md)

**Test**: `tests/unit/test_livetalking_process.py`

**Deliverable**: Reliable process management

### Day 18-21: Orchestrator Integration
**Goal**: Connect everything together

**File**: `src/orchestrator/state_machine.py` (UPDATE)

**Changes**:
1. Add face pipeline to orchestrator
2. Implement frame buffering
3. Connect to RTMPStreamer
4. Test state transitions

**Test**: `tests/integration/test_orchestrator_flow.py`

**Deliverable**: Working end-to-end flow

---

## 📅 WEEK 5-6: Production Testing

### Day 22-28: GPU Testing
**Goal**: Test dengan actual GPU dan models

**Prerequisites**:
- GPU dengan CUDA
- LiveTalking models downloaded
- Reference video/audio prepared

**Tasks**:
1. Download models (~5GB)
2. Train ER-NeRF (2-4 hours)
3. Test inference
4. Measure latency
5. Optimize performance

**Deliverable**: Working on GPU

### Day 29-35: Streaming Testing
**Goal**: Test RTMP streaming ke platforms

**Tasks**:
1. Setup TikTok RTMP
2. Test streaming
3. Monitor quality
4. Fix issues
5. Load testing

**Deliverable**: Stable streaming

---

## 📅 WEEK 7-8: Deployment & Monitoring

### Day 36-42: Production Deployment
**Goal**: Deploy to production environment

**Tasks**:
1. Create Dockerfile
2. Setup GPU passthrough
3. Configure monitoring
4. Deploy
5. Smoke tests

**Deliverable**: Deployed system

### Day 43-49: Monitoring & Documentation
**Goal**: Ensure system is maintainable

**Tasks**:
1. Setup Prometheus + Grafana
2. Create dashboards
3. Write runbooks
4. Final documentation
5. Handover

**Deliverable**: Production-ready system dengan monitoring

---

## 🎯 SUCCESS CRITERIA

### Week 1
- [ ] All dependencies installed cleanly
- [ ] 20+ unit tests passing
- [ ] Mock flow working end-to-end
- [ ] Documentation complete

### Week 2-3
- [ ] LiveTalking HTTP client working
- [ ] WebRTC stream reader working
- [ ] Adapter updated dan tested
- [ ] Integration tests passing

### Week 4
- [ ] Process manager working
- [ ] Orchestrator integrated
- [ ] End-to-end flow working
- [ ] Performance acceptable

### Week 5-6
- [ ] GPU inference working
- [ ] Streaming to TikTok/Shopee working
- [ ] Latency < 3 seconds
- [ ] Stable under load

### Week 7-8
- [ ] Deployed to production
- [ ] Monitoring working
- [ ] Documentation complete
- [ ] Team trained

---

## 📊 TRACKING

### Daily Standup Questions
1. What did I complete yesterday?
2. What will I work on today?
3. Any blockers?

### Weekly Review
1. What % of week's goals completed?
2. What went well?
3. What needs improvement?
4. Adjust next week's plan

### Metrics to Track
- Tests passing: X / Y
- Code coverage: X%
- Latency: X ms
- Uptime: X%
- Bugs found: X
- Bugs fixed: X

---

## 🚨 ESCALATION

### When to Escalate
- Blocked > 1 day
- Critical bug found
- Timeline at risk
- Resource constraints

### Who to Escalate To
- Technical: Tech Lead
- Timeline: Project Manager
- Resources: Engineering Manager

---

## 💡 TIPS FOR SUCCESS

1. **Start small** - Get one thing working perfectly before moving on
2. **Test everything** - Write tests as you go, not after
3. **Document as you go** - Don't wait until the end
4. **Ask for help** - Don't struggle alone for > 2 hours
5. **Celebrate wins** - Acknowledge progress, even small wins
6. **Be realistic** - Better to under-promise and over-deliver
7. **Communicate** - Keep stakeholders updated on progress
8. **Take breaks** - Burnout helps nobody

---

## 📝 CONCLUSION

This is a realistic, actionable plan for 8 weeks of work. It's not glamorous, it's not fast, but it's achievable and will result in a production-ready system.

**Key Principles**:
- Incremental progress
- Test everything
- Document everything
- Communicate constantly
- Be honest about status

**Remember**: Quality > Speed. A working system in 8 weeks is better than a broken system in 2 weeks.

