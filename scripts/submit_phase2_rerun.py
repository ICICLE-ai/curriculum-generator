"""Submits a Phase 2 rerun of a finished job to the CPU queue: what the web app's "Run Phase 2 again" will do.

    python scripts/submit_phase2_rerun.py <parent job uuid> [--weeks failed|all] [--app digital-age-edu-test]
        [--version 1.0.0-dev] [--gpu] [--dry-run]

Reads TAPIS_JWT from .env and TAPIS_REFRESH_TOKEN from the environment (the job's LLM proxy credential).
The config is locked to the parent's: the same config_file argument, checked against its provenance hash on start.
"""
import argparse
import json
import os
import sys
import urllib.request

BASE = "https://icicleai.tapis.io/v3"
ENV = os.path.join(os.path.dirname(__file__), "..", ".env")


def tapis(token, path, body=None):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode() if body else None,
                                 method="POST" if body else "GET",
                                 headers={"X-Tapis-Token": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["result"]


def rerun_payload(parent, root_dir, weeks, app_id, app_version, refresh_token, gpu=False):
    """Job request for a Phase 2 rerun of `parent` (a Tapis job record); CPU queue unless gpu."""
    params = json.loads(parent["parameterSet"]) if isinstance(parent["parameterSet"], str) else parent["parameterSet"]
    payload = {
        "name": f"{parent['name']}-p2",
        "appId": app_id,
        "appVersion": app_version,
        "notes": {"parent_job": parent["uuid"], "rerun": "phase2", "weeks": weeks},
        "parameterSet": {
            "appArgs": [{"name": a["name"], "arg": a["arg"]} for a in params.get("appArgs", [])
                        if a.get("name") == "config_file"],
            "envVariables": [
                {"key": "RERUN_FROM_DIR", "value": root_dir.rstrip("/") + "/" + parent["execSystemExecDir"].lstrip("/")},
                {"key": "RERUN_WEEKS", "value": weeks},
                {"key": "TAPIS_REFRESH_TOKEN", "value": refresh_token},
            ],
        },
    }
    if not gpu:  # no Phase 1, so no GPU: the CPU queue at its 800-minute cap
        payload.update(execSystemLogicalQueue="tapisShared", maxMinutes=800)
        # Tapis requires `arg` even on an excluded option
        payload["parameterSet"]["schedulerOptions"] = [{"name": "gpu-request", "arg": "--gpus=1", "include": False}]
        payload["parameterSet"]["containerArgs"] = [{"name": "bind-gpu", "arg": "--nv", "include": False}]
    return payload


def main():
    p = argparse.ArgumentParser()
    p.add_argument("parent")
    p.add_argument("--weeks", choices=["failed", "all"], default="failed")
    p.add_argument("--app", default="digital-age-edu-test")
    p.add_argument("--version", default="1.0.0-dev")
    p.add_argument("--gpu", action="store_true", help="GPU queue instead of CPU")
    p.add_argument("--dry-run", action="store_true", help="print the request (token hidden) without submitting")
    args = p.parse_args()

    token = next(line.split("=", 1)[1].strip().strip("\"'") for line in open(ENV) if line.startswith("TAPIS_JWT="))
    refresh = os.getenv("TAPIS_REFRESH_TOKEN", "").strip()
    if not refresh and not args.dry_run:
        sys.exit("Export TAPIS_REFRESH_TOKEN first: the rerun's Phase 2 needs it for the LLM proxy.")
    parent = tapis(token, f"/jobs/{args.parent}")
    root_dir = tapis(token, f"/systems/{parent['execSystemId']}?select=rootDir")["rootDir"]
    payload = rerun_payload(parent, root_dir, args.weeks, args.app, args.version, refresh, args.gpu)
    if args.dry_run:
        for env in payload["parameterSet"]["envVariables"]:
            if env["key"] == "TAPIS_REFRESH_TOKEN":
                env["value"] = "<hidden>"
        print(json.dumps(payload, indent=2))
        return
    job = tapis(token, "/jobs/submit", payload)
    print(f"Submitted {job['name']}: {job['uuid']}")


if __name__ == "__main__":
    main()
