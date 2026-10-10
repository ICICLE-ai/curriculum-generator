#!/usr/bin/env python3
"""
Tapis Dataset Transfer Utility
------------------------------
Copies datasets from one Tapis system to another asynchronously using
the Tapis v3 Background Transfer Service (POST /v3/files/transfers).

Non-destructive: Source files remain completely intact on the source system.
"""

import os
import sys
import time
import json
import argparse
import urllib.request
import urllib.error
from typing import Optional, Dict, Any

# ==============================================================================
# Configuration Defaults (Fill these in or pass via CLI / Environment variables)
# ==============================================================================
DEFAULT_TAPIS_BASE_URL = "https://icicleai.tapis.io"

# Example: source system and path
DEFAULT_SOURCE_SYSTEM = "source_system_id"
DEFAULT_SOURCE_PATH = "/path/to/source/dataset"

# Example: destination system and path
DEFAULT_DEST_SYSTEM = "digitalagedustorage"
DEFAULT_DEST_PATH = "/datasets/skin_cancer"

# Tapis JWT Token (Can also be provided via export TAPIS_JWT="...")
DEFAULT_TAPIS_JWT = os.getenv("TAPIS_JWT", os.getenv("TAPIS_TOKEN", ""))


def create_transfer_task(
    source_system: str,
    source_path: str,
    dest_system: str,
    dest_path: str,
    jwt_token: str,
    base_url: str = DEFAULT_TAPIS_BASE_URL,
    tag: str = "dataset-transfer"
) -> Dict[str, Any]:
    """
    Submits a background transfer task to copy files from sourceURI to destinationURI.
    """
    source_uri = f"tapis://{source_system.strip()}/{source_path.strip().lstrip('/')}"
    dest_uri = f"tapis://{dest_system.strip()}/{dest_path.strip().lstrip('/')}"

    url = f"{base_url.rstrip('/')}/v3/files/transfers"
    payload = {
        "tag": tag,
        "elements": [
            {
                "sourceURI": source_uri,
                "destinationURI": dest_uri
            }
        ]
    }

    headers = {
        "X-Tapis-Token": jwt_token.strip(),
        "Content-Type": "application/json"
    }

    print(f"\n[INFO] Initiating Tapis transfer task...")
    print(f"       Source:      {source_uri}")
    print(f"       Destination: {dest_uri}")

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST"
    )

    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            if data.get("status") == "success" and "result" in data:
                return data["result"]
            raise ValueError(f"Unexpected response from Tapis: {data}")
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise ConnectionError(f"Transfer creation failed (HTTP {e.code}): {err_body}") from e
    except Exception as e:
        raise ConnectionError(f"Transfer request failed: {e}") from e


def get_transfer_status(
    task_id: str,
    jwt_token: str,
    base_url: str = DEFAULT_TAPIS_BASE_URL
) -> Dict[str, Any]:
    """Retrieves the status of an ongoing transfer task."""
    url = f"{base_url.rstrip('/')}/v3/files/transfers/{task_id}"
    headers = {
        "X-Tapis-Token": jwt_token.strip(),
        "Content-Type": "application/json"
    }
    req = urllib.request.Request(url, headers=headers, method="GET")
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        return data.get("result", {})


def monitor_transfer(
    task_id: str,
    jwt_token: str,
    base_url: str = DEFAULT_TAPIS_BASE_URL,
    poll_interval_sec: int = 5,
    timeout_sec: int = 3600
):
    """Polls transfer status until COMPLETED, FAILED, or CANCELLED."""
    start_time = time.time()
    print(f"\n[INFO] Monitoring transfer task ID: {task_id}")

    while True:
        elapsed = int(time.time() - start_time)
        if elapsed > timeout_sec:
            print(f"\n[WARNING] Monitoring timed out after {timeout_sec}s. Transfer may still be running in background.")
            break

        try:
            res = get_transfer_status(task_id, jwt_token, base_url)
            status = res.get("status", "UNKNOWN")
            bytes_transferred = res.get("bytesTransferred", 0)
            total_bytes = res.get("totalBytes", 0)

            progress_str = ""
            if total_bytes > 0:
                pct = (bytes_transferred / total_bytes) * 100
                progress_str = f" | {bytes_transferred}/{total_bytes} bytes ({pct:.1f}%)"

            print(f"[{elapsed}s] Status: {status}{progress_str}", flush=True)

            if status in ("COMPLETED", "FINISHED"):
                print("\n[SUCCESS] Dataset transfer completed successfully!")
                break
            elif status in ("FAILED", "CANCELLED", "ERROR"):
                error_msg = res.get("errorMessage", "Unknown error")
                print(f"\n[ERROR] Transfer finished with status '{status}': {error_msg}")
                sys.exit(1)

        except Exception as e:
            print(f"[{elapsed}s] Polling error: {e}")

        time.sleep(poll_interval_sec)


def main():
    parser = argparse.ArgumentParser(description="Copy datasets between Tapis systems.")
    parser.add_argument("--source-system", default=DEFAULT_SOURCE_SYSTEM, help="Source Tapis system ID")
    parser.add_argument("--source-path", default=DEFAULT_SOURCE_PATH, help="Path to source dataset")
    parser.add_argument("--dest-system", default=DEFAULT_DEST_SYSTEM, help="Destination Tapis system ID")
    parser.add_argument("--dest-path", default=DEFAULT_DEST_PATH, help="Path on destination system")
    parser.add_argument("--token", default=DEFAULT_TAPIS_JWT, help="Tapis JWT Token (or set TAPIS_JWT env)")
    parser.add_argument("--base-url", default=DEFAULT_TAPIS_BASE_URL, help="Tapis tenant base URL")
    parser.add_argument("--no-wait", action="store_true", help="Do not wait for transfer completion")

    args = parser.parse_args()

    token = args.token.strip()
    if not token or token == "YOUR_JWT_HERE":
        print("[ERROR] Please provide a valid Tapis JWT token via --token, TAPIS_JWT environment variable, or in DEFAULT_TAPIS_JWT.", file=sys.stderr)
        sys.exit(1)

    result = create_transfer_task(
        source_system=args.source_system,
        source_path=args.source_path,
        dest_system=args.dest_system,
        dest_path=args.dest_path,
        jwt_token=token,
        base_url=args.base_url
    )

    task_id = result.get("uuid") or result.get("id")
    print(f"[SUCCESS] Transfer task created successfully with UUID: {task_id}")

    if not args.no_wait and task_id:
        monitor_transfer(task_id, token, base_url=args.base_url)


if __name__ == "__main__":
    main()
