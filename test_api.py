import requests
import json

print("Testing Brain Health API...")
print("=" * 60)

try:
    r = requests.get("http://localhost:8001/api/brain/health", timeout=15)
    data = r.json()
    
    print("\nProviders loaded:")
    for name, healthy in data["providers"].items():
        status = "✓" if healthy else "✗"
        print(f"  {status} {name}")
    
    print(f"\nTotal: {data['healthy_count']}/{data['total_count']}")
    print(f"Current: {data['current_provider']}")
    print(f"Mock mode: {data['mock_mode']}")
    
    print("\n" + "=" * 60)
    print("SUCCESS!")
    
except Exception as e:
    print(f"\nERROR: {e}")
