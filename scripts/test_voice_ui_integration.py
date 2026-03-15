#!/usr/bin/env python3
"""
Test Voice UI Integration - Comprehensive E2E Test

Tests the complete flow from UI → API → Fish-Speech → Response
"""

import asyncio
import httpx
import json
from pathlib import Path

BASE_URL = "http://127.0.0.1:8001"
FISH_SPEECH_URL = "http://127.0.0.1:8080"


async def test_fish_speech_health():
    """Test 1: Fish-Speech health endpoint"""
    print("\n=== Test 1: Fish-Speech Health ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{FISH_SPEECH_URL}/v1/health", timeout=5.0)
            print(f"✅ Fish-Speech Health: {response.status_code}")
            print(f"   Response: {response.json()}")
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Fish-Speech Health Failed: {e}")
            return False


async def test_runtime_truth():
    """Test 2: Runtime truth voice_engine status"""
    print("\n=== Test 2: Runtime Truth ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/runtime/truth", timeout=5.0)
            data = response.json()
            voice_engine = data.get("voice_engine", {})
            
            print(f"✅ Runtime Truth: {response.status_code}")
            print(f"   requested_engine: {voice_engine.get('requested_engine')}")
            print(f"   resolved_engine: {voice_engine.get('resolved_engine')}")
            
            server_reachable = voice_engine.get("server_reachable", {})
            if isinstance(server_reachable, dict):
                reachable = server_reachable.get("reachable", False)
            else:
                reachable = server_reachable
            
            print(f"   server_reachable: {reachable}")
            print(f"   reference_ready: {voice_engine.get('reference_ready')}")
            
            return reachable is True
        except Exception as e:
            print(f"❌ Runtime Truth Failed: {e}")
            return False


async def test_voice_warmup():
    """Test 3: Voice warmup endpoint"""
    print("\n=== Test 3: Voice Warmup ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(f"{BASE_URL}/api/voice/warmup", timeout=90.0)
            data = response.json()
            
            print(f"✅ Voice Warmup: {response.status_code}")
            print(f"   status: {data.get('status')}")
            print(f"   message: {data.get('message')}")
            
            return data.get("status") == "success"
        except Exception as e:
            print(f"❌ Voice Warmup Failed: {e}")
            return False


async def test_voice_profiles():
    """Test 4: List voice profiles"""
    print("\n=== Test 4: Voice Profiles ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/voice/profiles", timeout=5.0)
            data = response.json()
            
            print(f"✅ Voice Profiles: {response.status_code}")
            print(f"   Total profiles: {len(data)}")
            
            if data:
                active_profile = next((p for p in data if p.get("is_active")), None)
                if active_profile:
                    print(f"   Active profile: {active_profile.get('name')}")
                else:
                    print(f"   No active profile")
            
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Voice Profiles Failed: {e}")
            return False


async def test_voice_test():
    """Test 5: Voice test (quick synthesis)"""
    print("\n=== Test 5: Voice Test ===")
    async with httpx.AsyncClient() as client:
        try:
            payload = {"text": "Halo, ini test suara Indonesia."}
            response = await client.post(
                f"{BASE_URL}/api/voice/test",
                json=payload,
                timeout=60.0
            )
            data = response.json()
            
            print(f"✅ Voice Test: {response.status_code}")
            print(f"   audio_url: {data.get('audio_url')}")
            print(f"   latency_ms: {data.get('latency_ms')}")
            
            if data.get("error"):
                print(f"   ⚠️  error: {data.get('error')}")
                return False
            
            return response.status_code == 200 and data.get("audio_url") is not None
        except Exception as e:
            print(f"❌ Voice Test Failed: {e}")
            return False


async def test_voice_generate():
    """Test 6: Voice generate (full synthesis with profile)"""
    print("\n=== Test 6: Voice Generate ===")
    async with httpx.AsyncClient() as client:
        try:
            # First get active profile
            profiles_response = await client.get(f"{BASE_URL}/api/voice/profiles", timeout=5.0)
            profiles = profiles_response.json()
            active_profile = next((p for p in profiles if p.get("is_active")), None)
            
            if not active_profile:
                print("   ⚠️  No active profile, skipping generate test")
                return True
            
            payload = {
                "text": "Selamat datang di live streaming kami. Hari ini kami punya penawaran spesial untuk Anda.",
                "profile_id": active_profile.get("id"),
                "language": "id",
                "style_preset": "natural"
            }
            
            response = await client.post(
                f"{BASE_URL}/api/voice/generate",
                json=payload,
                timeout=90.0
            )
            data = response.json()
            
            print(f"✅ Voice Generate: {response.status_code}")
            print(f"   generation_id: {data.get('generation_id')}")
            print(f"   audio_url: {data.get('audio_url')}")
            print(f"   latency_ms: {data.get('latency_ms')}")
            
            if data.get("error"):
                print(f"   ⚠️  error: {data.get('error')}")
                return False
            
            return response.status_code == 200 and data.get("audio_url") is not None
        except Exception as e:
            print(f"❌ Voice Generate Failed: {e}")
            return False


async def test_voice_generations_list():
    """Test 7: List voice generations"""
    print("\n=== Test 7: Voice Generations List ===")
    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(f"{BASE_URL}/api/voice/generations", timeout=5.0)
            data = response.json()
            
            print(f"✅ Voice Generations: {response.status_code}")
            print(f"   Total generations: {len(data)}")
            
            if data:
                latest = data[0]
                print(f"   Latest: {latest.get('text', '')[:50]}...")
                print(f"   Audio URL: {latest.get('audio_url')}")
            
            return response.status_code == 200
        except Exception as e:
            print(f"❌ Voice Generations List Failed: {e}")
            return False


async def main():
    """Run all tests"""
    print("=" * 60)
    print("Voice UI Integration Test Suite")
    print("=" * 60)
    
    tests = [
        ("Fish-Speech Health", test_fish_speech_health),
        ("Runtime Truth", test_runtime_truth),
        ("Voice Warmup", test_voice_warmup),
        ("Voice Profiles", test_voice_profiles),
        ("Voice Test", test_voice_test),
        ("Voice Generate", test_voice_generate),
        ("Voice Generations List", test_voice_generations_list),
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = await test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} crashed: {e}")
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Voice UI integration is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check logs above for details.")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
