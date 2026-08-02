import requests

BASE = "http://127.0.0.1:5000"
users = ["bob", "alice", "jake", "joey", "bill"]

for username in users:
    resp = requests.post(f"{BASE}/api/login", json={"username": username, "password": "password"})
    if resp.status_code != 200:
        print(f"{username}: login failed ({resp.status_code})")
        continue
    token = resp.json()["token"]
    # second call to get the id from profile
    profile = requests.get(f"{BASE}/api/profile", headers={"Authorization": f"Bearer {token}"})
    user_id = profile.json()["id"]
    print(f"{username} (id {user_id}): {token}")