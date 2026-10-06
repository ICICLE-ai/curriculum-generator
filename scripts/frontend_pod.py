import os
import sys
import requests

def load_env():
    env_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".env"))
    if os.path.isfile(env_path):
        with open(env_path, "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#") and "=" in line:
                    k, v = line.split("=", 1)
                    os.environ.setdefault(k.strip(), v.strip())

load_env()
jwt_token = os.environ.get("TAPIS_JWT")
if not jwt_token:
    print("[ERROR] Missing TAPIS_JWT. Set TAPIS_JWT in your .env file.")
    sys.exit(1)

url = "https://icicleai.tapis.io/v3/pods"
headers = {
    "X-Tapis-Token": jwt_token,
    "Content-Type": "application/json"
}

payload = {
    "pod_id": "smartcurriculumdesigner",
    "image": "nginx",
    "description": "Smart Curriculum Designer Web Portal",
    "volume_mounts": {
        "/usr/share/nginx/html": {
            "type": "tapisvolume",
            "source_id": "digitalagedustorage",
            "sub_path": "dist",
            "read_only": False
        }
    },
    "networking": {
        "default": {
            "protocol": "http",
            "port": 80
        }
    },
    "resources": {
        "cpu_request": 250,
        "cpu_limit": 1000,
        "mem_request": 256,
        "mem_limit": 1024
    },
    "time_to_stop_default": -1,
    "time_to_stop_instance": -1
}

response = requests.post(url, json=payload, headers=headers)
print("Status Code:", response.status_code)
print("Response:", response.json())