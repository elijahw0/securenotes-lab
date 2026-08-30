import requests

BASE = "http://127.0.0.1:5000"
users = ["bob", "alice", "jake", "joey", "bill"]

for username in users:
    resp = requests.post(f"{BASE}/api/login", json={"username": username, "password": "password"}, timeout=10) # nosec B105 # seeded lab credential, matches seed.py; not a production secret
    if resp.status_code != 200:
        print(f"{username}: login failed ({resp.status_code})")
        continue
    token = resp.json()["token"]
    # second call to get the id from profile
    profile = requests.get(f"{BASE}/api/profile", headers={"Authorization": f"Bearer {token}"}, timeout=10)
    user_id = profile.json()["id"]
    print(f"{username} (id {user_id}): {token}")