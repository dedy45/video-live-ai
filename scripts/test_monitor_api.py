#!/usr/bin/env python3
"""Test monitor API endpoints to identify bottleneck."""
import time
import requests

BASE_URL = "http://localhost:8001"

def test_endpoint(name, url):
    """Test single endpoint and measure time."""
    print(f"\n{'='*60}")
    print(f"Testing: {name}")
    print(f"URL: {url}")
    print(f"{'='*60}")
    
    try:
        start = time.time()
        response = requests.get(url, timeout=30)
        elapsed = time.time() - start
        
        print(f"✓ Status: {response.status_code}")
        print(f"✓ Time: {elapsed:.2f}s ({elapsed*1000:.0f}ms)")
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, dict):
                print(f"✓ Keys: {list(data.keys())[:10]}")
                if 'error' in data:
                    print(f"⚠ Error in response: {data['error']}")
            elif isinstance(data, list):
                print(f"✓ Items: {len(data)}")
        else:
            print(f"✗ Error: {response.text[:200]}")
            
        return elapsed
        
    except requests.Timeout:
        print(f"✗ TIMEOUT after 30s")
        return 30.0
    except Exception as e:
        print(f"✗ Exception: {e}")
        return -1

def main():
    """Test all monitor endpoints."""
    print("\n" + "="*60)
    print("MONITOR API PERFORMANCE TEST")
    print("="*60)
    
    endpoints = [
        ("Recent Chats", f"{BASE_URL}/api/chat/recent"),
        ("Health Summary", f"{BASE_URL}/api/health/summary"),
        ("Resources", f"{BASE_URL}/api/resources"),
        ("Incidents", f"{BASE_URL}/api/incidents"),
        ("Brain Health", f"{BASE_URL}/api/brain/health"),
        ("Brain Stats", f"{BASE_URL}/api/brain/stats"),
    ]
    
    results = {}
    total_time = 0
    
    for name, url in endpoints:
        elapsed = test_endpoint(name, url)
        if elapsed > 0:
            results[name] = elapsed
            total_time += elapsed
    
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    
    for name, elapsed in sorted(results.items(), key=lambda x: x[1], reverse=True):
        print(f"{name:20s}: {elapsed:6.2f}s ({elapsed*1000:7.0f}ms)")
    
    print(f"\n{'Total Time':20s}: {total_time:6.2f}s")
    print(f"{'Parallel Time':20s}: {max(results.values()):6.2f}s (if parallel)")
    
    # Identify bottleneck
    slowest = max(results.items(), key=lambda x: x[1])
    print(f"\n⚠ BOTTLENECK: {slowest[0]} ({slowest[1]:.2f}s)")

if __name__ == "__main__":
    main()
