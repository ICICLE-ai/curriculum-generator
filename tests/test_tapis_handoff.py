"""Unit tests for compute-node Phase 2 CPU handoff (no network)."""
import json

import pytest

from digitalagedu.core import tapis_handoff

PARENT_JOB = {
    "uuid": "job-phase1-uuid",
    "name": "curriculum-run-1234",
    "appId": "digital-age-edu-test",
    "appVersion": "1.0.0-dev",
    "execSystemId": "expanse-tapis-static",
    "execSystemExecDir": "/jobs/job-phase1-uuid",
    "nodeCount": 1,
    "coresPerNode": 12,
    "memoryMB": 64000,
    "maxMinutes": 480,
    "parameterSet": json.dumps({
        "appArgs": [{"name": "config_file", "arg": "/scratch/cfg.yaml"}],
        "schedulerOptions": [
            {"name": "resource-allocation", "arg": "-A uot260"},
            {"name": "singularity-cache-export", "arg": "--export=ALL"},
            {"name": "gpu-request", "arg": "--gpus=1"},
        ],
        "containerArgs": [
            {"name": "bind-expanse", "arg": "--bind /expanse:/expanse"},
            {"name": "bind-gpu", "arg": "--nv"},
        ],
    }),
}


def test_detect_current_job_uuid_prefers_env_and_falls_back_to_jobs_dir(monkeypatch, tmp_path):
    monkeypatch.delenv("_tapisJobUUID", raising=False)
    monkeypatch.delenv("TAPIS_JOB_UUID", raising=False)
    jobs_cwd = tmp_path / "jobs" / "abc-123-uuid"
    jobs_cwd.mkdir(parents=True)
    assert tapis_handoff.detect_current_job_uuid(str(jobs_cwd)) == "abc-123-uuid"

    local_cwd = tmp_path / "workspace"
    local_cwd.mkdir()
    assert tapis_handoff.detect_current_job_uuid(str(local_cwd)) is None

    monkeypatch.setenv("_tapisJobUUID", "env-job-uuid")
    assert tapis_handoff.detect_current_job_uuid(str(local_cwd)) == "env-job-uuid"


def test_build_phase2_cpu_payload_excludes_gpu_and_targets_cpu_queue():
    payload = tapis_handoff.build_phase2_cpu_payload(
        parent=PARENT_JOB,
        root_dir="/expanse/lustre/scratch/harvest/temp_project/",
        refresh_token="refresh-tok",
        nrp_api_key="nrp-secret",
    )
    assert payload["name"] == "curriculum-run-1234-p2"
    assert payload["execSystemLogicalQueue"] == "tapisShared"
    assert payload["maxMinutes"] == 800

    sched = payload["parameterSet"]["schedulerOptions"]
    assert {"name": "resource-allocation", "arg": "-A uot260"} in sched
    assert {"name": "gpu-request", "arg": "--gpus=1", "include": False} in sched

    cargs = payload["parameterSet"]["containerArgs"]
    assert {"name": "bind-expanse", "arg": "--bind /expanse:/expanse"} in cargs
    assert {"name": "bind-gpu", "arg": "--nv", "include": False} in cargs

    env = {e["key"]: e["value"] for e in payload["parameterSet"]["envVariables"]}
    assert env == {
        "RERUN_FROM_DIR": "/expanse/lustre/scratch/harvest/temp_project/jobs/job-phase1-uuid",
        "RERUN_WEEKS": "all",
        "TAPIS_REFRESH_TOKEN": "refresh-tok",
        "NRP_LLM_API": "nrp-secret",
    }
    assert payload["notes"] == {
        "parent_job": "job-phase1-uuid",
        "parent_name": "curriculum-run-1234",
        "auto_phase2": True,
        "rerun": "phase2",
        "weeks": "all",
        "queue": "cpu",
    }


def test_submit_phase2_cpu_job_updates_progress_json(monkeypatch, tmp_path):
    out_dir = tmp_path / "outputs"
    out_dir.mkdir()
    progress_file = out_dir / "progress.json"
    progress_file.write_text(json.dumps({
        "status": "FINISHED",
        "current_message": "done",
        "stages": [{"id": "exercise_generation", "status": "SKIPPED", "details": "Deferred"}],
    }), encoding="utf-8")

    monkeypatch.setattr(tapis_handoff, "exchange_tapis_refresh_token", lambda tok, tapis_base_url=None: "access-jwt")

    calls = []

    def fake_request(access_token, path, body=None, base_url=None):
        calls.append((path, body))
        if path == "/v3/jobs/job-phase1-uuid":
            return PARENT_JOB
        if path.startswith("/v3/systems/"):
            return {"rootDir": "/expanse/scratch"}
        if path == "/v3/jobs/submit":
            return {"uuid": "child-p2-uuid", "name": "curriculum-run-1234-p2", "status": "PENDING"}
        raise AssertionError(f"Unexpected path: {path}")

    monkeypatch.setattr(tapis_handoff, "_tapis_request", fake_request)

    child = tapis_handoff.submit_phase2_cpu_job(
        job_uuid="job-phase1-uuid",
        refresh_token="refresh-tok",
        progress_output_dir=str(out_dir),
    )
    assert child["uuid"] == "child-p2-uuid"
    assert calls[-1][0] == "/v3/jobs/submit"
    assert calls[-1][1]["execSystemLogicalQueue"] == "tapisShared"

    updated = json.loads(progress_file.read_text(encoding="utf-8"))
    assert updated["phase2_handoff"] == {
        "job_uuid": "child-p2-uuid",
        "job_name": "curriculum-run-1234-p2",
        "queue": "tapisShared",
    }
    assert "child-p2-uuid" in updated["stages"][0]["details"]
