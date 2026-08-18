import os
import sys
import argparse
import requests
from tapipy.tapis import Tapis

DEFAULT_JWT = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlBiZU5IU3lJVGtZRHctOWtnbjRZU21VSnk2ZVRYZTNEYWFMRDNBZnl0SDQiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiIyYjI3Njk2Yy1kZTU4LTQzYzQtYWVmNC0yOTM3YzY1NmM2YWUiLCJpc3MiOiJodHRwczovL2ljaWNsZWFpLnRhcGlzLmlvL3YzL3Rva2VucyIsInN1YiI6InNlaC4xQG9zdS5lZHVAaWNpY2xlYWkiLCJ0YXBpcy90ZW5hbnRfaWQiOiJpY2ljbGVhaSIsInRhcGlzL3Rva2VuX3R5cGUiOiJhY2Nlc3MiLCJ0YXBpcy9kZWxlZ2F0aW9uIjpmYWxzZSwidGFwaXMvZGVsZWdhdGlvbl9zdWIiOm51bGwsInRhcGlzL3VzZXJuYW1lIjoic2VoLjFAb3N1LmVkdSIsInRhcGlzL2FjY291bnRfdHlwZSI6InVzZXIiLCJleHAiOjE3ODcwMjQ3NzJ9.UHsxJjNlKJNkBFTZUWAaqPtGnQVwmfGoKonLQnFauWIt4Kohwe2qWiKVmXsdNHGv2qEWpTtrNiyUlkkxLiPzvecGRcEjYxpFOL1BEv6PYwl--cmgbHw01jJEvGnnXFK21tpu4VZjF8IY9fnEM-wxzDq16Ja-hZCwDIyC01w_qlR_4KmX57jeppvhE8s27TgB7ZRDBZ8PaUwAuRI4az_N_sKUL-2RbQN7BcYGHzf2JxzW3TEgNeD6Lk-TlsBqP55IEBuHyT7VkCLxcB8F9nV1tpQZRTu7547Fqr2677P-POv8PpYJ-ADXidvwo0PudfqqQrFQR6ZffH9axhFKfXSymw"
POD_ID = "digitalagedu"
DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "frontend", "dist"))
UPLOAD_URL = f"https://icicleai.tapis.io/v3/pods/{POD_ID}/upload_to_pod"

def upload_frontend(jwt_token=None):
    token = jwt_token or os.environ.get("TAPIS_JWT") or DEFAULT_JWT
    headers = {"X-Tapis-Token": token}
    t = Tapis(base_url="https://icicleai.tapis.io", jwt=token)

    if not os.path.exists(DIST_DIR):
        print(f"[ERROR] Frontend dist folder not found at {DIST_DIR}")
        return

    # Ensure assets directory exists in pod
    print("[INFO] Creating assets directory in pod...")
    t.pods.exec_pod_commands(pod_id=POD_ID, commands=["mkdir", "-p", "/usr/share/nginx/html/assets"])

    print(f"[INFO] Uploading build artifacts to pod '{POD_ID}' via {UPLOAD_URL}...")
    for root, _, files in os.walk(DIST_DIR):
        for filename in files:
            local_filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(local_filepath, DIST_DIR).replace("\\", "/")
            dest_pod_path = f"/usr/share/nginx/html/{rel_path}"

            print(f" -> Uploading {rel_path} to {dest_pod_path}...")
            with open(local_filepath, "rb") as f_in:
                files_payload = {"file": (filename, f_in, "application/octet-stream")}
                data_payload = {"dest_path": dest_pod_path}
                resp = requests.post(UPLOAD_URL, headers=headers, files=files_payload, data=data_payload)

                if resp.status_code == 200:
                    print(f"    [OK] {rel_path}")
                else:
                    print(f"    [FAILED] {rel_path} (Status {resp.status_code}): {resp.text}")

    # Set permissions
    t.pods.exec_pod_commands(pod_id=POD_ID, commands=["chmod", "-R", "755", "/usr/share/nginx/html"])

    # Configure Nginx reverse proxy for /v3/ to prevent CORS errors on pod
    print("[INFO] Updating Nginx configuration to proxy /v3/ endpoints...")
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

    # Verify assets listing
    res_assets = t.pods.exec_pod_commands(pod_id=POD_ID, commands=["ls", "/usr/share/nginx/html/assets"])
    print("\n[VERIFICATION] /usr/share/nginx/html/assets:")
    print(res_assets.execution_results[0].stdout)

    print(f"\n[SUCCESS] All assets & Nginx proxy deployed! Visit: https://{POD_ID}.pods.icicleai.tapis.io")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Upload frontend build artifacts to Tapis Pod")
    parser.add_argument("--jwt", help="Tapis JWT access token (optional, falls back to env or default)", default=None)
    args = parser.parse_args()
    upload_frontend(jwt_token=args.jwt)
