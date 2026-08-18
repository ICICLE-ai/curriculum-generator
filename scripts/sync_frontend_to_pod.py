import os
import base64
from tapipy.tapis import Tapis

JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlBiZU5IU3lJVGtZRHctOWtnbjRZU21VSnk2ZVRYZTNEYWFMRDNBZnl0SDQiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiIyYjI3Njk2Yy1kZTU4LTQzYzQtYWVmNC0yOTM3YzY1NmM2YWUiLCJpc3MiOiJodHRwczovL2ljaWNsZWFpLnRhcGlzLmlvL3YzL3Rva2VucyIsInN1YiI6InNlaC4xQG9zdS5lZHVAaWNpY2xlYWkiLCJ0YXBpcy90ZW5hbnRfaWQiOiJpY2ljbGVhaSIsInRhcGlzL3Rva2VuX3R5cGUiOiJhY2Nlc3MiLCJ0YXBpcy9kZWxlZ2F0aW9uIjpmYWxzZSwidGFwaXMvZGVsZWdhdGlvbl9zdWIiOm51bGwsInRhcGlzL3VzZXJuYW1lIjoic2VoLjFAb3N1LmVkdSIsInRhcGlzL2FjY291bnRfdHlwZSI6InVzZXIiLCJleHAiOjE3ODcwMjQ3NzJ9.UHsxJjNlKJNkBFTZUWAaqPtGnQVwmfGoKonLQnFauWIt4Kohwe2qWiKVmXsdNHGv2qEWpTtrNiyUlkkxLiPzvecGRcEjYxpFOL1BEv6PYwl--cmgbHw01jJEvGnnXFK21tpu4VZjF8IY9fnEM-wxzDq16Ja-hZCwDIyC01w_qlR_4KmX57jeppvhE8s27TgB7ZRDBZ8PaUwAuRI4az_N_sKUL-2RbQN7BcYGHzf2JxzW3TEgNeD6Lk-TlsBqP55IEBuHyT7VkCLxcB8F9nV1tpQZRTu7547Fqr2677P-POv8PpYJ-ADXidvwo0PudfqqQrFQR6ZffH9axhFKfXSymw"
POD_ID = "digitalagedu"
DIST_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

def main():
    print(f"[INFO] Connecting to Tapis Pods for '{POD_ID}'...")
    t = Tapis(base_url="https://icicleai.tapis.io", jwt=JWT_TOKEN)

    # 1. Ensure directory structure
    t.pods.exec_pod_commands(
        pod_id=POD_ID,
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
                pod_id=POD_ID,
                commands=["sh", "-c", f"> {dest_path}"]
            )

            # Write in 40KB base64 chunks
            chunk_size = 40000
            for i in range(0, len(content), chunk_size):
                chunk = content[i:i + chunk_size]
                b64 = base64.b64encode(chunk).decode("ascii")
                cmd = f"echo '{b64}' | base64 -d >> {dest_path}"
                t.pods.exec_pod_commands(
                    pod_id=POD_ID,
                    commands=["sh", "-c", cmd]
                )

            # Fix permissions
            t.pods.exec_pod_commands(
                pod_id=POD_ID,
                commands=["chmod", "644", dest_path]
            )
            print(f"    [SUCCESS] {rel_path} ({len(content)} bytes)")

    # 3. Fix directory traversal permissions
    t.pods.exec_pod_commands(
        pod_id=POD_ID,
        commands=["chmod", "-R", "755", "/usr/share/nginx/html"]
    )

    # 4. Verify directory contents
    res = t.pods.exec_pod_commands(
        pod_id=POD_ID,
        commands=["ls", "-la", "/usr/share/nginx/html"]
    )
    print("\n[VERIFICATION] /usr/share/nginx/html contents:")
    print(res.execution_results[0].stdout)

    res_assets = t.pods.exec_pod_commands(
        pod_id=POD_ID,
        commands=["ls", "-la", "/usr/share/nginx/html/assets"]
    )
    print("[VERIFICATION] /usr/share/nginx/html/assets contents:")
    print(res_assets.execution_results[0].stdout)

    print("\nAll frontend assets synchronized successfully!")
    print(f"URL: https://{POD_ID}.pods.icicleai.tapis.io")

if __name__ == "__main__":
    main()
