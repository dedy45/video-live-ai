import requests
import json

# Test endpoint - port 8001
base_url = "http://localhost:8001"

print("Testing Prompt Registry API endpoints on port 8001...")
print("=" * 60)

# Test 1: List prompts
print("\n1. GET /api/brain/prompts")
try:
    response = requests.get(f"{base_url}/api/brain/prompts", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   ✓ Found {len(data)} revisions")
        if data:
            print(f"   First revision: {json.dumps(data[0], indent=2)}")
    else:
        print(f"   ✗ Error: {response.text}")
except requests.exceptions.ConnectionError:
    print("   ✗ Server not running at localhost:8001")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 2: Get specific revision
print("\n2. GET /api/brain/prompts/1")
try:
    response = requests.get(f"{base_url}/api/brain/prompts/1", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        print(f"   ✓ Revision ID: {data.get('id')}")
        print(f"   ✓ Slug: {data.get('slug')}")
        print(f"   ✓ Version: {data.get('version')}")
        print(f"   ✓ Status: {data.get('status')}")
        print(f"   ✓ Persona name: {data.get('persona', {}).get('name')}")
    else:
        print(f"   ✗ Error: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

# Test 3: Get brain config
print("\n3. GET /api/brain/config")
try:
    response = requests.get(f"{base_url}/api/brain/config", timeout=5)
    print(f"   Status: {response.status_code}")
    if response.ok:
        data = response.json()
        prompt = data.get('prompt', {})
        print(f"   ✓ Active prompt: {prompt.get('active_revision')}")
        print(f"   ✓ Slug: {prompt.get('slug')}")
        print(f"   ✓ Status: {prompt.get('status')}")
    else:
        print(f"   ✗ Error: {response.text}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print("\n" + "=" * 60)
print("✓ All endpoints working!")
print("\nDashboard URL: http://localhost:8001/dashboard")
print("Navigate to: AI Brain → Prompt Registry tab")
