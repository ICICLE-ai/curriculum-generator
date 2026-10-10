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

VOLUME_ID = "digitalagedustorage"
DIST_DIR = os.path.join(os.path.dirname(__file__), "..", "frontend", "dist")

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
