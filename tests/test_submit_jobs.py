"""Job requests built by scripts/submit_phase2_rerun.py (no network)."""
import json

from scripts.submit_phase2_rerun import job_payload

PARENT = {
    "uuid": "p-1", "name": "curriculum-run-2736", "appId": "digital-age-edu-test", "appVersion": "1.0.0-dev",
    "execSystemId": "expanse-tapis-static", "execSystemExecDir": "/jobs/p-1", "maxMinutes": 480,
    "parameterSet": json.dumps({
        "appArgs": [{"name": "config_file", "arg": "/cfg.yaml"}, {"name": "other", "arg": "x"}],
        "schedulerOptions": [{"name": "resource-allocation", "arg": "-A uot260"}, {"name": "gpu-request", "arg": "--gpus=1"}],
        "containerArgs": [{"name": "bind-expanse", "arg": "--bind /expanse"}, {"name": "bind-gpu", "arg": "--nv"}],
    }),
}


def env(payload):
    return {e["key"]: e["value"] for e in payload["parameterSet"]["envVariables"]}


def test_evaluation_job_runs_the_script_on_the_cpu_queue_from_the_parent_dir():
    p = job_payload(PARENT, "/root/", "damage", "failed", " --repeat 2 ", "tok")
    assert env(p) == {"EVAL_FROM_DIR": "/root/jobs/p-1", "EVAL_SCRIPT": "damage_test", "EVAL_ARGS": "--repeat 2",
                      "TAPIS_REFRESH_TOKEN": "tok"}
    assert (p["name"], p["execSystemLogicalQueue"], p["maxMinutes"]) == ("curriculum-run-2736-damage", "tapisShared", 800)
    assert p["parameterSet"]["appArgs"] == [{"name": "config_file", "arg": "/cfg.yaml"}]
    assert {"name": "gpu-request", "arg": "--gpus=1", "include": False} in p["parameterSet"]["schedulerOptions"]
    assert {"name": "bind-expanse", "arg": "--bind /expanse"} in p["parameterSet"]["containerArgs"]
    assert "rerun" not in p["notes"]


def test_rerun_job_keeps_the_rerun_variables_and_empty_eval_args_are_left_out():
    assert set(env(job_payload(PARENT, "/root", "rerun", "all", "", "tok"))) == {
        "RERUN_FROM_DIR", "RERUN_WEEKS", "TAPIS_REFRESH_TOKEN"}
    assert "EVAL_ARGS" not in env(job_payload(PARENT, "/root", "evaluate", "failed", "", "tok"))
    gpu = job_payload(PARENT, "/root", "evaluate", "failed", "", "tok", gpu=True)
    assert (gpu["execSystemLogicalQueue"], gpu["maxMinutes"]) == ("tapisGPUshared", 480)


def test_vlm_test_always_gets_the_gpu_and_reads_the_parents_screenshots():
    p = job_payload(PARENT, "/root", "vlm_test", "failed", "", "tok", vlm_env={"VLM_MODEL": "m", "VLLM_SPEC": None})
    assert env(p) == {"VLM_TEST": "1", "VLM_SHOTS_DIR": "/root/jobs/p-1", "VLM_MODEL": "m", "TAPIS_REFRESH_TOKEN": "tok"}
    assert p["execSystemLogicalQueue"] == "tapisGPUshared"
    assert {"name": "gpu-request", "arg": "--gpus=1"} in p["parameterSet"]["schedulerOptions"]
    assert {"name": "bind-gpu", "arg": "--nv"} in p["parameterSet"]["containerArgs"]


def test_allocation_override_replaces_the_parents_account():
    opts = job_payload(PARENT, "/root", "vlm_test", "failed", "", "tok", allocation="ohs120")["parameterSet"]["schedulerOptions"]
    assert [o for o in opts if o["name"] == "resource-allocation"] == [{"name": "resource-allocation", "arg": "-A ohs120"}]
    default = job_payload(PARENT, "/root", "vlm_test", "failed", "", "tok")["parameterSet"]["schedulerOptions"]
    assert {"name": "resource-allocation", "arg": "-A uot260"} in default
