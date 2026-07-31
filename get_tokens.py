import requests

BASE = "http://127.0.0.1:5000"
users = ["bob", "alice", "jake"]

for username in users:
    resp = requests.post(f"{BASE}/api/login", json={"username": username, "password": "password"})
    if resp.status_code == 200:
        token = resp.json()["token"]
        print(f"{username}: {token}")
    else:
        print(f"{username}: login failed ({resp.status_code})")