import os, sys, requests

PORT = os.environ.get("PORT", "5000")
BASE = f"http://127.0.0.1:{PORT}"

r = requests.post(f"{BASE}/api/login", json={"username": "alice", "password": "password"}, timeout=5)
r.raise_for_status()
token = r.json()["token"]
headers = {"Authorization": f"Bearer {token}"}

r = requests.post(f"{BASE}/api/logout", headers=headers, timeout=5)
print(f"Logout: {r.status_code}")

r = requests.get(f"{BASE}/api/profile", headers=headers, timeout=5)
print(f"Reuse token after logout: expected 401, got {r.status_code}")
sys.exit(0 if r.status_code == 401 else 1)