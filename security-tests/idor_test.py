import requests, os, sys

port = os.environ.get("port", 5000)
url = f"http://127.0.0.1:{port}"

# Log in as alice, who owns no notes. bob owns notes 1 and 2, jake 3.
try:
    request = requests.post(f"{url}/api/login", json={"username": "alice", "password": "password"})
    request.raise_for_status()
    token = request.json()["token"]

except Exception as e:
    print(f"setup failed: could not log in as alice ({e})")
    sys.exit(2)

leaked = []
for i in range(1, 4):
    request = requests.get(f"{url}/api/notes/{i}", headers={"Authorization": f"Bearer {token}"})
    if request.status_code == 200:
        leaked.append(i)

if leaked:
    print(f"Alice accessed {len(leaked)}/3 note(s) she does not own")
    sys.exit(1)
else:
    print("Alice could not access any other user's notes")
    sys.exit(0)