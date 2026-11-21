"""Submits a job on a finished job's outputs, built like the web app's "Run Phase 2 again" request
(frontend/src/services/tapis/jobs.ts, submitPhase2Rerun): a Phase 2 rerun, or a pedagogy evaluation of its finished
weeks (scripts/evaluate_curriculum.py, or damage_test.py). CPU queue unless --gpu.

    python scripts/submit_phase2_rerun.py <parent job uuid> [--task rerun|evaluate|damage] [--weeks failed|all]
        [--eval-args "--repeat 2 --weeks Week_01"] [--app digital-age-edu-test] [--version 1.0.0-dev] [--gpu] [--dry-run]

Reads TAPIS_JWT from .env. The job's LLM credential is TAPIS_REFRESH_TOKEN from the environment, else a 30-day
refresh token minted from TAPIS_JWT, as the web app does. The config is locked to the parent's: the same config_file
argument, checked against its provenance hash on start. Evaluation tasks need an image built after
scripts/evaluate_curriculum.py was added to the Dockerfile (the test app runs :latest).
"""
import argparse
import base64
import json
import os
import urllib.request

BASE = "https://icicleai.tapis.io/v3"
ENV = os.path.join(os.path.dirname(__file__), "..", ".env")
# task -> (job name suffix, script the entrypoint runs; None for the Phase 2 rerun)
TASKS = {"rerun": ("-p2", None), "evaluate": ("-eval", "evaluate_curriculum"), "damage": ("-damage", "damage_test")}


def tapis(token, path, body=None):
    req = urllib.request.Request(f"{BASE}{path}", data=json.dumps(body).encode() if body else None,
                                 method="POST" if body else "GET",
                                 headers={"X-Tapis-Token": token, "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)["result"]


def refresh_token(token):
    """TAPIS_REFRESH_TOKEN, else a new 30-day one from the Tokens API (what the web app sends with every job)."""
    existing = os.getenv("TAPIS_REFRESH_TOKEN", "").strip()
    if existing:
        return existing
    part = token.split(".")[1]
    claims = json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))
    result = tapis(token, "/tokens", {
        "token_tenant_id": claims.get("tapis/tenant_id", "icicleai"),
        "token_username": claims.get("tapis/username") or claims["sub"],
        "account_type": "user", "access_token_ttl": 14400, "refresh_token_ttl": 2592000,
        "generate_refresh_token": True,
    })
    return result["refresh_token"]["refresh_token"]


def job_payload(parent, root_dir, task, weeks, eval_args, refresh, app_id=None, app_version=None, gpu=False):
    """Job request for `task` on `parent` (a Tapis job record): a new job directory, the parent's config, allocation
    and Expanse bind, and its job directory as the source the entrypoint copies from."""
    params = json.loads(parent["parameterSet"]) if isinstance(parent["parameterSet"], str) else parent["parameterSet"]
    pick = lambda key, names: [{"name": o["name"], "arg": o["arg"]} for o in params.get(key, []) if o.get("name") in names]
    suffix, script = TASKS[task]
    from_dir = root_dir.rstrip("/") + "/" + parent["execSystemExecDir"].lstrip("/")
    if script is None:
        env = [{"key": "RERUN_FROM_DIR", "value": from_dir}, {"key": "RERUN_WEEKS", "value": weeks}]
    else:
        env = [{"key": "EVAL_FROM_DIR", "value": from_dir}, {"key": "EVAL_SCRIPT", "value": script}]
        if eval_args.strip():
            env.append({"key": "EVAL_ARGS", "value": eval_args.strip()})
    return {
        "name": f"{parent['name']}{suffix}",
        "appId": app_id or parent["appId"],
        "appVersion": app_version or parent.get("appVersion") or "1.0.0",
        "description": f"{task} of {parent['name']}" + (f" ({weeks} weeks)" if script is None else f" {eval_args}".rstrip()),
        "execSystemId": parent.get("execSystemId") or "expanse-tapis-static",
        "execSystemLogicalQueue": "tapisGPUshared" if gpu else "tapisShared",
        "nodeCount": parent.get("nodeCount") or 1,
        "coresPerNode": parent.get("coresPerNode") or 12,
        "memoryMB": parent.get("memoryMB") or 64000,
        "maxMinutes": (parent.get("maxMinutes") or 480) if gpu else 800,  # 800: the CPU queue's cap
        # A new job directory: the parent's outputs are copied from it, never written to
        "execSystemExecDir": "/jobs/${JobUUID}",
        "execSystemInputDir": "/jobs/${JobUUID}",
        "execSystemOutputDir": "/jobs/${JobUUID}",
        "parameterSet": {
            "appArgs": [{"name": a["name"], "arg": str(a["arg"])} for a in pick("appArgs", ["config_file"])],
            "schedulerOptions": pick("schedulerOptions", ["resource-allocation", "singularity-cache-export"])
            # Tapis requires `arg` even on an excluded option
            + (pick("schedulerOptions", ["gpu-request"]) if gpu else [{"name": "gpu-request", "arg": "--gpus=1", "include": False}]),
            "containerArgs": pick("containerArgs", ["bind-expanse"])
            + (pick("containerArgs", ["bind-gpu"]) if gpu else [{"name": "bind-gpu", "arg": "--nv", "include": False}]),
            "envVariables": env + [{"key": "TAPIS_REFRESH_TOKEN", "value": refresh}],
        },
        "notes": {"parent_job": parent["uuid"], "parent_name": parent["name"], "task": task,
                  "queue": "gpu" if gpu else "cpu", **({"rerun": "phase2", "weeks": weeks} if script is None else {})},
    }


def main():
    p = argparse.ArgumentParser()
    p.add_argument("parent", help="The finished job's UUID")
    p.add_argument("--task", choices=list(TASKS), default="rerun")
    p.add_argument("--weeks", choices=["failed", "all"], default="failed", help="rerun only")
    p.add_argument("--eval-args", default="", help='evaluate/damage only: extra script flags, e.g. "--repeat 2"')
    p.add_argument("--app", help="App id (default: the parent's)")
    p.add_argument("--version", help="App version (default: the parent's)")
    p.add_argument("--gpu", action="store_true", help="GPU queue instead of CPU")
    p.add_argument("--dry-run", action="store_true", help="print the request (token hidden) without submitting")
    args = p.parse_args()

    token = next(line.split("=", 1)[1].strip().strip("\"'") for line in open(ENV) if line.startswith("TAPIS_JWT="))
    parent = tapis(token, f"/jobs/{args.parent}")
    root_dir = tapis(token, f"/systems/{parent['execSystemId']}?select=rootDir")["rootDir"]
    refresh = "<hidden>" if args.dry_run else refresh_token(token)
    payload = job_payload(parent, root_dir, args.task, args.weeks, args.eval_args, refresh, args.app, args.version,
                          args.gpu)
    if args.dry_run:
        print(json.dumps(payload, indent=2))
        return
    job = tapis(token, "/jobs/submit", payload)
    print(f"Submitted {job['name']}: {job['uuid']}")


if __name__ == "__main__":
    main()
