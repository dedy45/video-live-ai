import requests

try:
    url = "http://localhost:8001/api/brain/test"
    payload = {
        "task_type": "selling_script",
        "system_prompt": "You are a helpful assistant.",
        "user_prompt": "Test hello message",
        "provider": "chutes"
    }
    response = requests.post(url, json=payload)
    print("Status:", response.status_code)
    print("Response JSON:")
    print(response.json())
except Exception as e:
    print(f"Error: {e}")
