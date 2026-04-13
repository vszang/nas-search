"""
API 테스트 스크립트
"""
import requests
import json

BASE_URL = "http://localhost:5000"

# 1. Health check
print("=" * 60)
print("1. Health Check")
print("=" * 60)
response = requests.get(f"{BASE_URL}/api/health")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2)}")

# 2. Get tools
print("\n" + "=" * 60)
print("2. Get Tools")
print("=" * 60)
response = requests.get(f"{BASE_URL}/api/tools")
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

# 3. Search files
print("\n" + "=" * 60)
print("3. Search Files")
print("=" * 60)
search_data = {
    "query": "python",
    "file_type": None,
    "max_results": 10
}
print(f"Request: {json.dumps(search_data, indent=2)}")
response = requests.post(f"{BASE_URL}/api/search", json=search_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")

# 4. List directory
print("\n" + "=" * 60)
print("4. List Directory")
print("=" * 60)
dir_data = {
    "path": "/",
    "recursive": False
}
print(f"Request: {json.dumps(dir_data, indent=2)}")
response = requests.post(f"{BASE_URL}/api/directory", json=dir_data)
print(f"Status: {response.status_code}")
print(f"Response: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
