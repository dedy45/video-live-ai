"""Authentic Test Flow (Real LLM + Real TTS)

This script bypasses Mock Mode to independently verify that the
LLM Provider (Groq/Gemini) and the TTS Engine (Edge-TTS)
are actually functional without faking data.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import os
import asyncio
import argparse

# Force Mock Mode OFF to test real APIs
os.environ["MOCK_MODE"] = "false"

def main():
    parser = argparse.ArgumentParser(description="Run authentic pipeline test.")
    parser.add_argument("--query", type=str, default="Halo, bisa perkenalkan dirimu secara singkat dengan semangat?")
    args = parser.parse_args()

    asyncio.run(run_authentic_test(args.query))

async def run_authentic_test(query: str):
    import time
    from src.utils.logging import get_logger
    from src.brain.router import BrainRouter
    from src.voice.engine import VoiceRouter
    from src.config.loader import get_env
    
    logger = get_logger("authentic_test")
    env = get_env()
    
    print("==========================================================")
    print("   AI Live Commerce — AUTENTIC TEST (NO FAKE DATA)        ")
    print("==========================================================")
    print(f"MOCK_MODE is currently: {os.environ.get('MOCK_MODE')}")
    print(f"Testing Query: '{query}'")
    print("----------------------------------------------------------")

    try:
        # Phase 1: Authentic LLM Generation
        print("\n[Layer 2 - Brain] Connecting to Real LLM Provider...")
        brain = BrainRouter()
        
        start_t = time.perf_counter()
        # We assume the user has Groq API Key set in .env or the system will fallback
        # If no keys, this will legitimately FAIL (which is correct behavior).
        response = await brain.generate_chat_reply(
            username="test_user",
            message=query,
            context={"product": "Sample Item", "price": "100k"}
        )
        llm_latency = (time.perf_counter() - start_t) * 1000
        
        print(f"✔ LLM Success! Latency: {llm_latency:.0f}ms")
        print(f"  Response Emotion: {response.emotion}")
        print(f"  Response Text   : {response.text_content}")
        
    except Exception as e:
        print(f"❌ LLM Authentication/Connection Failed: {e}")
        print("Note: Please check your .env file for GROQ_API_KEY or GEMINI_API_KEY.")
        sys.exit(1)

    try:
        # Phase 2: Authentic TTS Engine
        print("\n[Layer 3 - Voice] Synthesizing Real Audio using Edge-TTS...")
        voice = VoiceRouter()
        
        start_t = time.perf_counter()
        audio_result = await voice.synthesize(text=response.text_content, emotion=response.emotion)
        tts_latency = (time.perf_counter() - start_t) * 1000
        
        file_path = "authentic_test.wav"
        with open(file_path, "wb") as f:
            f.write(audio_result.audio_data)
        
        print(f"✔ TTS Success! Latency: {tts_latency:.0f}ms")
        print(f"  Audio Duration  : {audio_result.duration_ms:.0f}ms")
        print(f"  Saved File to   : {file_path}")
        
    except Exception as e:
        print(f"❌ TTS Failed: {e}")
        sys.exit(1)

    print("\n==========================================================")
    print("  TEST COMPLETED: System APIs are authentically working")
    print("==========================================================")

if __name__ == "__main__":
    main()
