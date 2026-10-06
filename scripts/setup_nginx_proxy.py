import os
import sys
from tapipy.tapis import Tapis

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
JWT_TOKEN = os.environ.get("TAPIS_JWT")
if not JWT_TOKEN:
    print("[ERROR] Missing TAPIS_JWT in environment or .env file.")
    sys.exit(1)

POD_ID = "smartcurriculumdesigner"

t = Tapis(base_url="https://icicleai.tapis.io", jwt=JWT_TOKEN)

nginx_conf = """server {
    listen 80;
    server_name localhost;

    location / {
        root /usr/share/nginx/html;
        index index.html index.htm;
        try_files $uri $uri/ /index.html;
    }

    location /v3/ {
        proxy_pass https://icicleai.tapis.io;
        proxy_set_header Host icicleai.tapis.io;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_ssl_server_name on;
    }
}"""

t.pods.exec_pod_commands(
    pod_id=POD_ID,
    commands=["sh", "-c", f"cat << 'EOF' > /etc/nginx/conf.d/default.conf\n{nginx_conf}\nEOF"]
)
t.pods.exec_pod_commands(pod_id=POD_ID, commands=["nginx", "-s", "reload"])
print(f"[SUCCESS] Nginx configured and reloaded on '{POD_ID}' pod!")
