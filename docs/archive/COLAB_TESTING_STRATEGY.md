# 🚀 Google Colab Testing Strategy

**Purpose**: Test LiveTalking + videoliveai integration dengan FREE GPU  
**Timeline**: 1-2 hari untuk setup + testing  
**Cost**: $0 (menggunakan Colab free tier)

---

## 🎯 WHY GOOGLE COLAB?

### Advantages
- ✅ FREE GPU (Tesla T4, 15GB VRAM)
- ✅ Pre-installed CUDA & PyTorch
- ✅ Easy sharing & collaboration
- ✅ No local setup needed
- ✅ Perfect untuk prototyping

### Limitations
- ⚠️ Session timeout (12 hours max)
- ⚠️ Disk space limited (~100GB)
- ⚠️ Network restrictions (no RTMP streaming)
- ⚠️ Can't run 24/7

### Best Use Cases
1. Test LiveTalking standalone
2. Test model inference
3. Benchmark performance
4. Debug GPU issues
5. Prototype integration

---

## 📋 COLAB NOTEBOOK STRUCTURE

### Notebook 1: LiveTalking Standalone Test
**File**: `notebooks/01_livetalking_standalone.ipynb`


**Sections**:
```python
# 1. Setup Environment
!nvidia-smi  # Check GPU
!git clone https://github.com/lipku/LiveTalking.git
%cd LiveTalking
!pip install -r requirements.txt

# 2. Download Models
!mkdir -p models
# Download MuseTalk, ER-NeRF, GFPGAN models
# (Provide download links)

# 3. Prepare Avatar
!mkdir -p data/avatars/test_avatar
# Upload reference video & audio

# 4. Run LiveTalking
!python app.py --model musetalk --avatar_id test_avatar --tts edgetts

# 5. Test API
import requests
response = requests.post("http://localhost:8010/human", json={
    "sessionid": 0,
    "type": "echo",
    "text": "Hello world"
})
print(response.json())
```

**Expected Output**: LiveTalking server running, dapat generate video

---

### Notebook 2: videoliveai Integration Test
**File**: `notebooks/02_videoliveai_integration.ipynb`

**Sections**:
```python
# 1. Clone videoliveai
!git clone <your-repo-url> videoliveai
%cd videoliveai

# 2. Install dependencies
!pip install -e ".[livetalking]"

# 3. Setup config
!cp .env.example .env
# Edit .env dengan Colab-specific settings

# 4. Test components
from src.config import load_config
from src.brain.router import LLMRouter
from src.face.livetalking_adapter import LiveTalkingPipeline

config = load_config()
router = LLMRouter()
pipeline = LiveTalkingPipeline()

# 5. Test integration
import asyncio
async def test_flow():
    # LLM → TTS → Face
    pass

asyncio.run(test_flow())
```

**Expected Output**: All components load, integration works

---

### Notebook 3: Performance Benchmark
**File**: `notebooks/03_performance_benchmark.ipynb`

**Sections**:
```python
# 1. Benchmark LLM latency
# 2. Benchmark TTS latency
# 3. Benchmark Face rendering latency
# 4. Benchmark end-to-end latency
# 5. Generate report
```

**Expected Output**: Latency metrics, bottleneck identification

---

## 🛠️ SETUP INSTRUCTIONS

### Step 1: Create Colab Notebooks
1. Go to https://colab.research.google.com
2. Create new notebook
3. Enable GPU: Runtime → Change runtime type → GPU → T4

### Step 2: Upload Reference Files
```python
from google.colab import files
uploaded = files.upload()
# Upload reference video & audio
```

### Step 3: Mount Google Drive (Optional)
```python
from google.colab import drive
drive.mount('/content/drive')
# Save models to Drive untuk reuse
```

---

## 🧪 TEST SCENARIOS

### Scenario 1: LiveTalking Standalone
**Goal**: Verify LiveTalking works on Colab GPU

**Steps**:
1. Install LiveTalking
2. Download models
3. Start server
4. Send test request
5. Verify video generation

**Success Criteria**:
- Server starts without errors
- API responds
- Video frames generated
- Latency < 1 second per frame

### Scenario 2: HTTP Client Test
**Goal**: Test videoliveai can communicate dengan LiveTalking

**Steps**:
1. Start LiveTalking server (background)
2. Run videoliveai HTTP client
3. Send text request
4. Receive video frames
5. Verify frame quality

**Success Criteria**:
- HTTP connection established
- Frames received
- No dropped frames
- Proper error handling

### Scenario 3: End-to-End Flow
**Goal**: Test full pipeline

**Steps**:
1. Input text
2. LLM generates response
3. TTS converts to audio
4. LiveTalking generates video
5. Output video frames

**Success Criteria**:
- All steps complete
- Total latency < 3 seconds
- Video quality acceptable
- No memory leaks

---

## 📊 METRICS TO COLLECT

### Performance Metrics
```python
metrics = {
    "llm_latency_ms": [],
    "tts_latency_ms": [],
    "face_latency_ms": [],
    "e2e_latency_ms": [],
    "gpu_memory_mb": [],
    "fps": []
}
```

### Quality Metrics
- Video resolution
- Frame rate
- Lip-sync accuracy (subjective)
- Face quality (subjective)

### Resource Metrics
- GPU utilization %
- VRAM usage MB
- CPU usage %
- Network bandwidth

---

## 🚨 COMMON ISSUES & SOLUTIONS

### Issue 1: CUDA Out of Memory
**Symptom**: RuntimeError: CUDA out of memory

**Solutions**:
```python
# 1. Reduce batch size
opt.batch_size = 8  # Default 16

# 2. Clear cache
import torch
torch.cuda.empty_cache()

# 3. Use smaller models
# Use Wav2Lip instead of MuseTalk
```

### Issue 2: Model Download Fails
**Symptom**: Connection timeout, slow download

**Solutions**:
```python
# 1. Use Google Drive mirror
!gdown <google-drive-link>

# 2. Use Hugging Face mirror
from huggingface_hub import hf_hub_download
model = hf_hub_download(repo_id="...", filename="...")

# 3. Split large files
# Download in chunks
```

### Issue 3: Port Already in Use
**Symptom**: Address already in use

**Solutions**:
```python
# 1. Kill existing process
!kill $(lsof -t -i:8010)

# 2. Use different port
!python app.py --listenport 8011
```

### Issue 4: Session Timeout
**Symptom**: Colab disconnects after 12 hours

**Solutions**:
```python
# 1. Save checkpoints frequently
import pickle
with open('checkpoint.pkl', 'wb') as f:
    pickle.dump(state, f)

# 2. Use Colab Pro ($10/month)
# - 24 hour sessions
# - Better GPUs (V100, A100)

# 3. Auto-reconnect script
from IPython.display import Javascript
Javascript('function KeepClicking(){console.log("Clicking");document.querySelector("colab-connect-button").click()}setInterval(KeepClicking,60000)')
```

---

## 📦 DELIVERABLES

### After Colab Testing
1. **Performance Report**
   - Latency metrics
   - GPU utilization
   - Bottleneck analysis

2. **Working Notebooks**
   - Standalone test
   - Integration test
   - Benchmark test

3. **Issue List**
   - Bugs found
   - Performance issues
   - Integration problems

4. **Recommendations**
   - Model optimizations
   - Architecture changes
   - Deployment strategy

---

## 🎯 SUCCESS CRITERIA

### Minimum Viable Test
- [ ] LiveTalking runs on Colab
- [ ] Can generate video from text
- [ ] Latency measured
- [ ] Issues documented

### Complete Test
- [ ] All notebooks working
- [ ] Integration tested
- [ ] Performance benchmarked
- [ ] Report generated
- [ ] Recommendations documented

---

## 📝 NEXT STEPS AFTER COLAB

### If Tests Pass
1. Implement fixes in local code
2. Create production deployment plan
3. Setup GPU server (RunPod, Vast.ai)
4. Deploy to staging

### If Tests Fail
1. Document failures
2. Identify root causes
3. Create fix plan
4. Re-test on Colab

---

## 💡 TIPS FOR COLAB SUCCESS

1. **Save work frequently** - Sessions can disconnect
2. **Use Google Drive** - Persist models & data
3. **Monitor GPU usage** - Don't waste resources
4. **Test incrementally** - One component at a time
5. **Document everything** - Screenshots, logs, metrics
6. **Share notebooks** - Collaborate with team
7. **Use Colab Pro** - If serious about testing ($10/month worth it)

---

## 🔗 USEFUL RESOURCES

### Colab Guides
- [Colab FAQ](https://research.google.com/colaboratory/faq.html)
- [GPU Best Practices](https://colab.research.google.com/notebooks/gpu.ipynb)
- [External Data](https://colab.research.google.com/notebooks/io.ipynb)

### LiveTalking Resources
- [LiveTalking GitHub](https://github.com/lipku/LiveTalking)
- [MuseTalk Paper](https://arxiv.org/abs/2410.10122)
- [Model Downloads](https://github.com/lipku/LiveTalking#models)

### Alternative GPU Platforms
- [Kaggle Notebooks](https://www.kaggle.com/code) - Free GPU, 30h/week
- [Paperspace Gradient](https://gradient.run/) - Free tier available
- [RunPod](https://runpod.io/) - Pay-per-use, cheap
- [Vast.ai](https://vast.ai/) - Cheapest GPU rental

---

## 🎉 CONCLUSION

Google Colab adalah cara TERBAIK untuk:
- Test LiveTalking tanpa GPU lokal
- Prototype integration
- Benchmark performance
- Debug issues

Tapi BUKAN untuk:
- Production deployment
- 24/7 streaming
- RTMP output
- Long-running processes

**Recommendation**: Use Colab untuk development & testing, deploy to dedicated GPU server untuk production.

