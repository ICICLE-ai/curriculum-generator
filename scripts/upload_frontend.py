import os
import requests
from tapipy.tapis import Tapis

JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlBiZU5IU3lJVGtZRHctOWtnbjRZU21VSnk2ZVRYZTNEYWFMRDNBZnl0SDQiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiJiMTVhYTc0Ni04ZmI4LTRmZmEtODFiMi05OGU3NDI1OTk0YzQiLCJpc3MiOiJodHRwczovL2ljaWNsZWFpLnRhcGlzLmlvL3YzL3Rva2VucyIsInN1YiI6InNlaC4xQG9zdS5lZHVAaWNpY2xlYWkiLCJ0YXBpcy90ZW5hbnRfaWQiOiJpY2ljbGVhaSIsInRhcGlzL3Rva2VuX3R5cGUiOiJhY2Nlc3MiLCJ0YXBpcy9kZWxlZ2F0aW9uIjpmYWxzZSwidGFwaXMvZGVsZWdhdGlvbl9zdWIiOm51bGwsInRhcGlzL3VzZXJuYW1lIjoic2VoLjFAb3N1LmVkdSIsInRhcGlzL2FjY291bnRfdHlwZSI6InVzZXIiLCJleHAiOjE3ODY5MzQ4MjUsInRhcGlzL2NsaWVudF9pZCI6InRhcGlzdWktaW1wbGljaXQtY2xpZW50IiwidGFwaXMvZ3JhbnRfdHlwZSI6ImltcGxpY2l0IiwidGFwaXMvaWRwX2lkIjoiZ2xvYnVzIn0.L_su4ssd92c00ilVTkfuaRwSTa9RnMVFtOSru3KzWMVKvgChd8siSzNiRgrYh00XxVOp3RcEiI3aXkkK-yKCgvxqLzfVKGPy5OMjISyAmyVsHdW41IYNbrKWqcGOyDQtQj323QvCnzwQx57xCsUqll6_QdPX90ozZQm49O1TffV7B9cWEP3BlBUimSlzOKPA-tqtfVSPhGr85kSPaOFDb6Qe8C8MjJ6s4OYRZsydkMW6TESOCJa6tIbXvadpyQe3zcN8h8xtYCSLl0MhpYOmJe-tM3N0DbA5vIfbMaTJ1W19HHxuWkTvbEs_qdd01xB4zpWckS7fgNDuteWLeNnjmA"
POD_ID = "digitalagedu"
DIST_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")
UPLOAD_URL = f"https://icicleai.tapis.io/v3/pods/{POD_ID}/upload_to_pod"

def upload_frontend():
    headers = {"X-Tapis-Token": JWT_TOKEN}
    t = Tapis(base_url="https://icicleai.tapis.io", jwt=JWT_TOKEN)

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

    # Verify assets listing
    res_assets = t.pods.exec_pod_commands(pod_id=POD_ID, commands=["ls", "/usr/share/nginx/html/assets"])
    print("\n[VERIFICATION] /usr/share/nginx/html/assets:")
    print(res_assets.execution_results[0].stdout)

    print(f"\n[SUCCESS] All assets deployed! Visit: https://{POD_ID}.pods.icicleai.tapis.io")

if __name__ == "__main__":
    upload_frontend()
