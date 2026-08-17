import os
from tapipy.tapis import Tapis

JWT_TOKEN = "eyJhbGciOiJSUzI1NiIsImtpZCI6IlBiZU5IU3lJVGtZRHctOWtnbjRZU21VSnk2ZVRYZTNEYWFMRDNBZnl0SDQiLCJ0eXAiOiJKV1QifQ.eyJqdGkiOiJiMTVhYTc0Ni04ZmI4LTRmZmEtODFiMi05OGU3NDI1OTk0YzQiLCJpc3MiOiJodHRwczovL2ljaWNsZWFpLnRhcGlzLmlvL3YzL3Rva2VucyIsInN1YiI6InNlaC4xQG9zdS5lZHVAaWNpY2xlYWkiLCJ0YXBpcy90ZW5hbnRfaWQiOiJpY2ljbGVhaSIsInRhcGlzL3Rva2VuX3R5cGUiOiJhY2Nlc3MiLCJ0YXBpcy9kZWxlZ2F0aW9uIjpmYWxzZSwidGFwaXMvZGVsZWdhdGlvbl9zdWIiOm51bGwsInRhcGlzL3VzZXJuYW1lIjoic2VoLjFAb3N1LmVkdSIsInRhcGlzL2FjY291bnRfdHlwZSI6InVzZXIiLCJleHAiOjE3ODY5MzQ4MjUsInRhcGlzL2NsaWVudF9pZCI6InRhcGlzdWktaW1wbGljaXQtY2xpZW50IiwidGFwaXMvZ3JhbnRfdHlwZSI6ImltcGxpY2l0IiwidGFwaXMvaWRwX2lkIjoiZ2xvYnVzIn0.L_su4ssd92c00ilVTkfuaRwSTa9RnMVFtOSru3KzWMVKvgChd8siSzNiRgrYh00XxVOp3RcEiI3aXkkK-yKCgvxqLzfVKGPy5OMjISyAmyVsHdW41IYNbrKWqcGOyDQtQj323QvCnzwQx57xCsUqll6_QdPX90ozZQm49O1TffV7B9cWEP3BlBUimSlzOKPA-tqtfVSPhGr85kSPaOFDb6Qe8C8MjJ6s4OYRZsydkMW6TESOCJa6tIbXvadpyQe3zcN8h8xtYCSLl0MhpYOmJe-tM3N0DbA5vIfbMaTJ1W19HHxuWkTvbEs_qdd01xB4zpWckS7fgNDuteWLeNnjmA"
VOLUME_ID = "digitalagedustorage"
DIST_DIR = os.path.join(os.path.dirname(__file__), "frontend", "dist")

def upload_all():
    print(f"[INFO] Connecting to Tapis Volume '{VOLUME_ID}'...")
    t = Tapis(base_url="https://icicleai.tapis.io", jwt=JWT_TOKEN)

    if not os.path.exists(DIST_DIR):
        print(f"[ERROR] Frontend dist folder not found at {DIST_DIR}")
        return

    print(f"[INFO] Uploading build artifacts to volume '{VOLUME_ID}'...")
    for root, _, files in os.walk(DIST_DIR):
        for filename in files:
            local_filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(local_filepath, DIST_DIR).replace("\\", "/")
            dest_volume_path = f"dist/{rel_path}"

            print(f" -> Uploading {rel_path} to {dest_volume_path}...")
            with open(local_filepath, "rb") as f_in:
                try:
                    res = t.pods.upload_to_volume(
                        volume_id=VOLUME_ID,
                        path=dest_volume_path,
                        file=f_in
                    )
                    print(f"    [OK] {rel_path}")
                except Exception as e:
                    print(f"    [FAILED] {rel_path}: {e}")

    print("\n[VERIFICATION] Listing volume contents:")
    try:
        files = t.pods.list_volume_files(volume_id=VOLUME_ID, path="dist")
        for f in files:
            print(f"  - {f.name} ({f.size} bytes)")
    except Exception as e:
        print(f"List error: {e}")

if __name__ == "__main__":
    upload_all()
