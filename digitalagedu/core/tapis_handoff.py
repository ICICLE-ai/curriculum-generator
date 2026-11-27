"""
Compute-node Phase 2 CPU handoff for Tapis batch jobs.

After Phase 1 completes on a GPU node (tapisGPUshared), this module uses the job's
TAPIS_REFRESH_TOKEN to query the parent job's metadata and submit a follow-up CPU
job (tapisShared) running Phase 2 on the staged Phase 1 outputs, releasing the GPU
node immediately.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, Optional

from digitalagedu.core.llm.rag.qdrant_client import DEFAULT_TAPIS_BASE_URL, exchange_tapis_refresh_token

CPU_QUEUE = "tapisShared"
CPU_MAX_MINUTES = 800


def detect_current_job_uuid(cwd: Optional[str] = None) -> Optional[str]:
    """Detects the active Tapis job UUID from environment variables or /jobs/<uuid> working directory."""
    for env_key in ("_tapisJobUUID", "TAPIS_JOB_UUID"):
        val = (os.getenv(env_key) or "").strip()
        if val:
            return val

    abs_cwd = os.path.abspath(cwd or os.getcwd())
    parent = os.path.dirname(abs_cwd)
    base = os.path.basename(abs_cwd)
    if os.path.basename(parent) == "jobs" and base and base != "jobs":
        return base
    return None


def _parse_parameter_set(raw: Any) -> Dict[str, Any]:
    if not raw:
        return {}
    if isinstance(raw, dict):
        return raw
    return json.loads(str(raw))


def build_phase2_cpu_payload(
    parent: Dict[str, Any],
    root_dir: str,
    refresh_token: str,
    nrp_api_key: Optional[str] = None,
) -> Dict[str, Any]:
    """Builds a Tapis CPU job submission payload mirroring `parent` with GPU flags excluded."""
    params = _parse_parameter_set(parent.get("parameterSet"))

    def pick(key: str, names: tuple[str, ...]) -> list[Dict[str, Any]]:
        return [
            {"name": o["name"], "arg": str(o["arg"])}
            for o in (params.get(key) or [])
            if o.get("name") in names
        ]

    exec_dir = str(parent.get("execSystemExecDir") or f"/jobs/{parent['uuid']}").lstrip("/")
    from_dir = f"{root_dir.rstrip('/')}/{exec_dir}"

    env_vars = [
        {"key": "RERUN_FROM_DIR", "value": from_dir},
        {"key": "RERUN_WEEKS", "value": "all"},
        {"key": "TAPIS_REFRESH_TOKEN", "value": refresh_token},
    ]
    if nrp_api_key and nrp_api_key.strip():
        env_vars.append({"key": "NRP_LLM_API", "value": nrp_api_key.strip()})

    parent_name = parent["name"]
    return {
        "name": f"{parent_name}-p2",
        "appId": parent["appId"],
        "appVersion": parent.get("appVersion") or "1.0.0",
        "description": f"Automatic Phase 2 CPU job for {parent_name}",
        "execSystemId": parent.get("execSystemId") or "expanse-tapis-static",
        "execSystemLogicalQueue": CPU_QUEUE,
        "nodeCount": parent.get("nodeCount") or 1,
        "coresPerNode": parent.get("coresPerNode") or 12,
        "memoryMB": parent.get("memoryMB") or 64000,
        "maxMinutes": CPU_MAX_MINUTES,
        "execSystemExecDir": "/jobs/${JobUUID}",
        "execSystemInputDir": "/jobs/${JobUUID}",
        "execSystemOutputDir": "/jobs/${JobUUID}",
        "parameterSet": {
            "appArgs": pick("appArgs", ("config_file",)),
            "schedulerOptions": [
                *pick("schedulerOptions", ("resource-allocation", "singularity-cache-export")),
                # Tapis requires `arg` even on an excluded INCLUDE_BY_DEFAULT option
                {"name": "gpu-request", "arg": "--gpus=1", "include": False},
            ],
            "containerArgs": [
                *pick("containerArgs", ("bind-expanse",)),
                {"name": "bind-gpu", "arg": "--nv", "include": False},
            ],
            "envVariables": env_vars,
        },
        "notes": {
            "parent_job": parent["uuid"],
            "parent_name": parent_name,
            "auto_phase2": True,
            "rerun": "phase2",
            "weeks": "all",
            "queue": "cpu",
        },
    }


def _tapis_request(
    access_token: str,
    path: str,
    body: Optional[Dict[str, Any]] = None,
    base_url: str = DEFAULT_TAPIS_BASE_URL,
) -> Dict[str, Any]:
    url = f"{base_url.rstrip('/')}{path}"
    data = json.dumps(body).encode("utf-8") if body is not None else None
    req = urllib.request.Request(
        url,
        data=data,
        method="POST" if body is not None else "GET",
        headers={
            "X-Tapis-Token": access_token.strip(),
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            payload = json.load(resp)
            return payload.get("result", payload)
    except urllib.error.HTTPError as e:
        err_body = e.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"Tapis request {path} failed (HTTP {e.code}): {err_body}") from e


def _record_handoff_in_progress(progress_output_dir: Optional[str], child: Dict[str, Any]) -> None:
    if not progress_output_dir:
        return
    progress_path = os.path.join(progress_output_dir, "progress.json")
    if not os.path.isfile(progress_path):
        return
    try:
        with open(progress_path, encoding="utf-8") as f:
            data = json.load(f)
        child_uuid = child.get("uuid", "")
        child_name = child.get("name", "")
        data["phase2_handoff"] = {
            "job_uuid": child_uuid,
            "job_name": child_name,
            "queue": CPU_QUEUE,
        }
        for stg in data.get("stages") or []:
            if stg.get("id") == "exercise_generation":
                stg["details"] = f"Handed off to CPU job {child_name} ({child_uuid})"
        data["current_message"] = f"Phase 1 complete; Phase 2 handed off to CPU job {child_name}"
        tmp_path = progress_path + ".tmp"
        with open(tmp_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
        os.replace(tmp_path, progress_path)
    except Exception as err:
        print(f"[WARN] Could not record Phase 2 handoff in progress.json: {err}")


def submit_phase2_cpu_job(
    job_uuid: Optional[str] = None,
    refresh_token: Optional[str] = None,
    base_url: Optional[str] = None,
    progress_output_dir: Optional[str] = None,
) -> Dict[str, Any]:
    """Submits the follow-up Phase 2 CPU job for `job_uuid` and records it in progress.json."""
    resolved_uuid = job_uuid or detect_current_job_uuid()
    if not resolved_uuid:
        raise RuntimeError("Cannot auto-submit Phase 2 CPU job: Tapis job UUID not found.")

    resolved_refresh = (refresh_token or os.getenv("TAPIS_REFRESH_TOKEN") or "").strip()
    if not resolved_refresh:
        raise RuntimeError("Cannot auto-submit Phase 2 CPU job: TAPIS_REFRESH_TOKEN is not set.")

    tapis_base = (base_url or os.getenv("TAPIS_BASE_URL") or DEFAULT_TAPIS_BASE_URL).rstrip("/")
    access_token = exchange_tapis_refresh_token(resolved_refresh, tapis_base_url=tapis_base)
    parent = _tapis_request(access_token, f"/v3/jobs/{resolved_uuid}", base_url=tapis_base)
    exec_system = parent.get("execSystemId") or "expanse-tapis-static"
    sys_info = _tapis_request(access_token, f"/v3/systems/{exec_system}?select=rootDir", base_url=tapis_base)
    root_dir = sys_info.get("rootDir") or ""

    payload = build_phase2_cpu_payload(
        parent=parent,
        root_dir=root_dir,
        refresh_token=resolved_refresh,
        nrp_api_key=os.getenv("NRP_LLM_API"),
    )
    child = _tapis_request(access_token, "/v3/jobs/submit", body=payload, base_url=tapis_base)
    _record_handoff_in_progress(progress_output_dir, child)
    return child


def can_handoff() -> bool:
    """True when running inside a Tapis job with a refresh token and handoff is not disabled."""
    if (os.getenv("DISABLE_AUTO_PHASE2_HANDOFF") or "").strip().lower() in ("1", "true", "yes"):
        return False
    return bool(detect_current_job_uuid() and (os.getenv("TAPIS_REFRESH_TOKEN") or "").strip())


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="Submit follow-up Phase 2 CPU job from a finished Phase 1 Tapis job.")
    parser.add_argument("--config", default=None, help="Path to YAML config (to locate output directory for progress.json)")
    parser.add_argument("--check-available", action="store_true", help="Exit 0 if Tapis handoff is available, else 1")
    args = parser.parse_args(argv)

    if args.check_available:
        return 0 if can_handoff() else 1

    output_dir = None
    if args.config and os.path.isfile(args.config):
        from digitalagedu.core.config import load_config
        output_dir = load_config(args.config).output.directory

    child = submit_phase2_cpu_job(progress_output_dir=output_dir)
    print(f"[HANDOFF] Submitted Phase 2 CPU job: {child.get('name')} ({child.get('uuid')})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
