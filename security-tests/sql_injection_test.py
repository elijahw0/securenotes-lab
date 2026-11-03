import requests, os, sys


port = os.environ.get("port", 5001)
url = f"http://127.0.0.1:{port}"

req = requests.post(f"{url}/api/login", json={"username":"alice", "password": "password"})

req.raise_for_status()

token = req.json()["token"]


req = requests.get(f"{url}/api/notes/search", headers={"Authorization": f"Bearer {token}"}, params={"q": "' ) or 1=1 --"})

output = req.json().get('notes', [])
if not output:
    print("test passed, sql injection failed", output)
    sys.exit(0)
else:
    print("test failed", output)
    sys.exit(1)