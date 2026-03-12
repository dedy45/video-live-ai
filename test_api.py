import requests
import json

# Test endpoint
base_url = "http://localhost:8000"

print("Testing Prompt Registry API endpoints...")
print("=" * 60)

# Test 1: List prompts
print("\n1. GET /api/brain/prompts")
try:
    response = requests.get(f"{base_url}/api/brain/prompts", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Found {len(data)} revisions")
        if data:
            print(f"   First revision: {data[0]}")
    else:
        print(f"   Error: {response.text}")
except requests.exceptions.ConnectionError:
    print("   ✗ Server not running at localhost:8000")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Get brain config
print("\n2. GET /api/brain/config")
try:
    response = requests.get(f"{base_url}/api/brain/config", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   Prompt: {data.get('prompt', {})}")
    else:
        print(f"   Error: {response.text}")
except requests.exceptions.ConnectionError:
    print("   ✗ Server not running")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("If server is not running, start it with:")
print("  uv run python scripts/manage.py serve --mock")
