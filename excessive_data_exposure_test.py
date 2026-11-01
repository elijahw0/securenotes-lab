import os, requests, sys

port = os.environ.get("PORT", 5000)
#logs in as admin to test leak of passwords
r = requests.post(f"http://127.0.0.1:{port}/api/login", json={"username": "jake", "password": "password"})

token = r.json()["token"]

r = requests.get(f"http://127.0.0.1:{port}/api/admin/users", headers={"Authorization": f"Bearer {token}"}, timeout=5)
r.raise_for_status()

leaked = [user["username"] for user in r.json()["users"] if "password_hash" in user]
print(leaked)
if leaked:
    print(f" password hashes exposed for {len(leaked)} users: {', '.join(leaked)}")
    sys.exit(1)

print("PASS: no password hashes in the admin users response")
sys.exit(0)