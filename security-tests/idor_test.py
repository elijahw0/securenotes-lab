import requests, os, sys

port = os.environ.get("port", 5000)
url = f"http://127.0.0.1:{port}"

request = requests.post(f"{url}/api/login", json={"username":"bob", "password": "password"})

request.raise_for_status()

token = request.json()["token"]



for i in range(1,4):
    request = requests.get(f"{url}/api/notes/{i}", headers={"Authorization": f"Bearer {token}"})
    if request.status_code == 200:
        print(f"Note {i}: {request.json()}")
    else:
        print(f"Note {i}: {request.status_code}")
        

sys.exit(1)