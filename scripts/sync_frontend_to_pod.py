import os
import sys
import base64
import argparse
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
POD_ID = "smartcurriculumdesigner"
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))

def main():
    parser = argparse.ArgumentParser(description="Sync frontend build artifacts to Tapis Pod")
    parser.add_argument("--jwt", default=None, help="Tapis JWT token")
    parser.add_argument("--pod", default=POD_ID, help="Tapis Pod ID")
    args = parser.parse_args()

    jwt_token = args.jwt or os.environ.get("TAPIS_JWT")
    if not jwt_token:
        print("[ERROR] Missing TAPIS_JWT. Set TAPIS_JWT in your .env or pass --jwt <TOKEN>.")
        sys.exit(1)
    pod_id = args.pod

    print(f"[INFO] Connecting to Tapis Pods for '{pod_id}'...")
    print(f"[INFO] Using build directory: {DIST_DIR}")
    if not os.path.isdir(DIST_DIR):
        print(f"[ERROR] Directory does not exist: {DIST_DIR}")
        sys.exit(1)

    t = Tapis(base_url="https://icicleai.tapis.io", jwt=jwt_token)

    # 1. Ensure directory structure
    print("[INFO] Creating target directories inside pod...")
    t.pods.exec_pod_commands(
        pod_id=pod_id,
        commands=["mkdir", "-p", "/usr/share/nginx/html/assets"]
    )

    # 2. Upload each file directly via base64 in chunks
    for root, _, files in os.walk(DIST_DIR):
        for filename in files:
            local_path = os.path.join(root, filename)
            rel_path = os.path.relpath(local_path, DIST_DIR).replace("\\", "/")
            dest_path = f"/usr/share/nginx/html/{rel_path}"

            print(f" -> Syncing {rel_path} -> {dest_path}...")
            with open(local_path, "rb") as f:
                content = f.read()

            # Truncate / create destination file
            t.pods.exec_pod_commands(
                pod_id=pod_id,
                commands=["sh", "-c", f"> {dest_path}"]
            )

            # Write in 40KB base64 chunks
            chunk_size = 40000
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                b64 = base64.b64encode(chunk).decode("ascii")
                cmd = f"echo '{b64}' | base64 -d >> {dest_path}"
                t.pods.exec_pod_commands(
                    pod_id=pod_id,
                    commands=["sh", "-c", cmd]
                )

            # Fix permissions
            t.pods.exec_pod_commands(
                pod_id=pod_id,
                commands=["chmod", "644", dest_path]
            )
            print(f"    [SUCCESS] {rel_path} ({len(content)} bytes)")

    # 3. Fix directory traversal permissions
    t.pods.exec_pod_commands(
        pod_id=pod_id,
        commands=["chmod", "-R", "755", "/usr/share/nginx/html"]
    )

    # 4. Ensure Nginx reverse proxy configuration for /v3/
    print("[INFO] Verifying/Updating Nginx reverse proxy for /v3/...")
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
        pod_id=pod_id,
        commands=["sh", "-c", f"cat << 'EOF' > /etc/nginx/conf.d/default.conf\n{nginx_conf}\nEOF"]
    )
    t.pods.exec_pod_commands(pod_id=POD_ID, commands=["nginx", "-s", "reload"])

    # 5. Verify directory contents
    res = t.pods.exec_pod_commands(
        pod_id=pod_id,
        commands=["ls", "-la", "/usr/share/nginx/html"]
    )
    print("\n[VERIFICATION] /usr/share/nginx/html contents:")
    for result in getattr(res, "execution_results", []):
        print(getattr(result, "stdout", result))

    res_assets = t.pods.exec_pod_commands(
        pod_id=pod_id,
        commands=["ls", "-la", "/usr/share/nginx/html/assets"]
    )
    print("[VERIFICATION] /usr/share/nginx/html/assets contents:")
    for result in getattr(res_assets, "execution_results", []):
        print(getattr(result, "stdout", result))

    print("\n[DONE] All frontend assets synchronized successfully!")
    print(f"URL: https://{pod_id}.pods.icicleai.tapis.io")

if __name__ == "__main__":
    main()
