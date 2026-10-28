import requests, os, sys

port = os.environ.get("port", 5000)
url = f"http://127.0.0.1:{port}"

request = requests.post(f"{url}/api/login", json={"username":"bob", "password": "password"})

request.raise_for_status()

token = request.json()["token"]

request = requests.get(f"{url}/api/admin/users", headers={"Authorization": f"Bearer {token}"})
if request.status_code == 200:
    users = request.json()["users"]
    print(users)
    for user in users:
        print(f"User: {user['username']}, Role: {user['role']}")
    sys.exit(0)
else:
    print(f"Failed to retrieve users: {request.status_code}")
    sys.exit(1)