"""End-to-end check of generate_llm_curriculum with a scripted LLM client and the real sandbox."""
import hashlib
import json
from types import SimpleNamespace

import pytest

from digitalagedu.core.llm import main as phase2
from digitalagedu.core.llm.schemas import ArbiterVerdictSchema, ProblemStatementSchema

CONFIG = """
project: {{domain: "Generic", context_statement: "c"}}
dataset: {{root_path: "{root}"}}
output: {{directory: "{root}"}}
pipeline: {{stages: [{{name: "Classification", active: true, task_type: "classification"}}]}}
execution: {{device: "cpu", batch_size: 1, image_size: 32, seed: 7, parallel_weeks: 1}}
curriculum:
  subject: "Testing"
  modules: [{{id: "adder", week: 1, title: "Adder"}}]
"""


def fenced(code, finish_reason="stop"):
    """A streamed chat completion (content, finish and usage chunks) whose reply is one ```python block."""
    return stream(f"Here you go:\n```python\n{code}```\n", finish_reason)


def stream(content, finish_reason="stop"):
    return [SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=content), finish_reason=None)], usage=None),
            SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content=None), finish_reason=finish_reason)], usage=None),
            SimpleNamespace(choices=[], usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5))]


SOLUTION = fenced("def add(a, b):\n    return a + b\n")
WRONG_SOLUTION = fenced("def add(a, b):\n    return a - b\n")
BROKEN_TEST = fenced("assert add(1, 1) == expected_sum\n")  # NameError inside the test file -> blamed on the test
GOOD_TEST = fenced('assert add(1, 1) == 2, f"got {add(1, 1)}"\n')  # double quotes, unescaped: no JSON in the way
STARTER = fenced("def add(a, b):\n    # TODO: return the sum of a and b\n    pass\n")


class ScriptedArbiter:
    """Instructor-style client returning one queued ArbiterVerdictSchema per arbitration."""
    def __init__(self, faults):
        self.verdicts = [ArbiterVerdictSchema(fault=f, rationale=f"why-{f}", fix_directive=f"do-{f}") for f in faults]
        self.chat = self.completions = self

    def create_with_completion(self, response_model, **kwargs):
        return self.verdicts.pop(0), SimpleNamespace(usage=None)


def load_trace(module_dir):
    return json.loads((module_dir / "adder_generation_trace.json").read_text())


class ScriptedCodeClient:
    """Plain OpenAI-style client returning queued completions in call order; records each request's messages."""
    def __init__(self, replies):
        self.replies = list(replies)
        self.requests = []
        self.chat = self
        self.completions = self

    def create(self, messages, **kwargs):
        self.requests.append(list(messages))  # snapshot: _ask_code keeps appending to one list
        return self.replies.pop(0)


@pytest.fixture
def phase2_env(tmp_path, monkeypatch):
    config_path = tmp_path / "config.yaml"
    config_path.write_text(CONFIG.format(root=tmp_path.as_posix()), encoding="utf-8")
    (tmp_path / "run_summary.json").write_text(json.dumps({"overall_accuracy_percent": 90.0}), encoding="utf-8")
    (tmp_path / "provenance.json").write_text(json.dumps({"workflow_run_id": "run_7", "artifact_manifest": []}), encoding="utf-8")

    problem = ProblemStatementSchema(
        title="Adder", domain_context="d", problem_statement="Add two numbers",
        learning_objectives=["add"], suggested_focus="addition", markdown_overview="# Adder",
    )
    agent0_feedback, agent0_history = [], []  # revision_feedback and curriculum_history of each Agent 0 call

    def fake_agent0(**kw):
        agent0_feedback.append(kw.get("revision_feedback"))
        agent0_history.append([h["week"] for h in kw.get("curriculum_history") or []])
        return problem
    monkeypatch.setattr(phase2, "formulate_problem_statement", fake_agent0)
    monkeypatch.setattr("digitalagedu.core.llm.context.get_rag_context", lambda *a, **kw: "")

    def fake_deck(self, output_path, **kw):
        open(output_path, "wb").close()
        return output_path
    monkeypatch.setattr(phase2.PresentationDesigner, "generate_presentation_deck", fake_deck)

    def run(replies, faults=()):
        client = ScriptedCodeClient(replies)
        monkeypatch.setattr(phase2, "get_openai_client", lambda base_url=None: client)
        monkeypatch.setattr(phase2, "get_instructor_client", lambda base_url=None: ScriptedArbiter(faults))
        phase2.generate_llm_curriculum(str(config_path), output_dir=str(tmp_path / "exercises"), telemetry_dir=str(tmp_path))
        return client
    run.agent0_feedback = agent0_feedback
    run.agent0_history = agent0_history
    return tmp_path, run


def test_self_heals_failing_tests_and_writes_all_module_assets(phase2_env):
    tmp_path, run = phase2_env
    # Call order: QA tests -> solution -> QA repair after the sandbox fails -> starter code
    client = run([BROKEN_TEST, SOLUTION, GOOD_TEST, STARTER])
    module_dir = tmp_path / "exercises" / "Week_01" / "adder"
    assert json.loads((module_dir / "adder_verification.json").read_text())["verified"] is True
    assert json.loads((module_dir / "adder_generated.json").read_text())["unit_test"] == 'assert add(1, 1) == 2, f"got {add(1, 1)}"'
    assert "TODO" in (module_dir / "adder_exercise.py").read_text()
    for suffix in ("overview.md", "manifest.json", "solution.py", "test.py", "slides_payload.json", "presentation.pptx"):
        assert (module_dir / f"adder_{suffix}").exists(), suffix
    assert (tmp_path / "exercises" / "requirements.txt").exists()
    assert not client.replies  # QA retry was used exactly once
    assert "FAILURES ATTRIBUTED TO YOUR TEST FILE" in client.requests[2][1]["content"]

    trace = load_trace(module_dir)
    entities, derived = trace["entity"], trace["wasDerivedFrom"].values()
    assert {"dage:unit_test_v1", "dage:unit_test_v2", "dage:solution_v1", "dage:starter_code_v1"} <= set(entities)
    assert {"prov:generatedEntity": "dage:unit_test_v2", "prov:usedEntity": "dage:unit_test_v1"} in derived
    failure = next(e for e in entities.values() if e["prov:type"] == "dage:failure")
    assert (failure["dage:blame"], failure["dage:file"]) == ("test", "test_runner.py")
    runs = [a for a in trace["activity"].values() if a["prov:type"] == "dage:sandbox_run"]
    assert [r["dage:verified"] for r in runs] == [False, True]
    for entity in entities.values():  # every stored text is on disk and matches its checksum
        if "dage:path" in entity:
            assert hashlib.sha256((module_dir / entity["dage:path"]).read_bytes()).hexdigest() == entity["dage:sha256"]

    listed = json.loads((tmp_path / "provenance.json").read_text())["generation_traces"]
    assert listed[0]["module_id"] == "adder" and listed[0]["path"].endswith("adder_generation_trace.json")


def test_contract_mismatch_routes_repair_to_the_coder(phase2_env):
    tmp_path, run = phase2_env
    client = run([GOOD_TEST, WRONG_SOLUTION, SOLUTION, STARTER])
    assert "FAILURES ATTRIBUTED TO YOUR SOLUTION" in client.requests[2][1]["content"]
    trace = load_trace(tmp_path / "exercises" / "Week_01" / "adder")
    assert {"prov:generatedEntity": "dage:solution_v2", "prov:usedEntity": "dage:solution_v1"} in trace["wasDerivedFrom"].values()
    assert any(r["prov:informant"].startswith("dage:sandbox_run") for r in trace["wasInformedBy"].values())


def test_contract_fault_revises_the_contract_and_regenerates(phase2_env):
    tmp_path, run = phase2_env
    # Pass 1: broken test survives its QA repair -> Arbiter blames the contract. Pass 2 (revised contract) passes.
    run([BROKEN_TEST, SOLUTION, BROKEN_TEST, GOOD_TEST, SOLUTION, STARTER], faults=["contract"])
    assert run.agent0_feedback[0] is None and "why-contract" in run.agent0_feedback[1]
    module_dir = tmp_path / "exercises" / "Week_01" / "adder"
    verification = json.loads((module_dir / "adder_verification.json").read_text())
    assert verification["verified"] is True
    assert [(e["level"], e["to_agent"]) for e in verification["escalations"]] == [
        (1, "agent2_qa"), (2, "arbiter"), (3, "agent0_director")
    ]
    derived = load_trace(module_dir)["wasDerivedFrom"].values()
    assert {"prov:generatedEntity": "dage:problem_formulation_v2", "prov:usedEntity": "dage:problem_formulation_v1"} in derived
    assert any(r["prov:generatedEntity"] == "dage:problem_formulation_v2" and r["prov:usedEntity"].startswith("dage:verdict")
               for r in derived)
    # The regenerated test is fresh from the revised contract, not a repair of the old one
    assert {"prov:generatedEntity": "dage:unit_test_v3", "prov:usedEntity": "dage:unit_test_v2"} not in derived


def test_second_contract_fault_fails_fast_and_keeps_the_trace(phase2_env):
    tmp_path, run = phase2_env
    with pytest.raises(RuntimeError, match=r"Sandbox verification failed.*Unresolved after 1 contract revision.*verdict \(contract\)"):
        run([BROKEN_TEST, SOLUTION, BROKEN_TEST] * 2, faults=["contract", "contract"])
    assert len(run.agent0_feedback) == 1 + phase2.MAX_CONTRACT_REVISIONS
    module_dir = tmp_path / "exercises" / "Week_01" / "adder"
    verification = json.loads((module_dir / "adder_verification.json").read_text())
    assert verification["verified"] is False and verification["failures"][0]["blame"] == "test"
    assert not (module_dir / "adder_presentation.pptx").exists()
    # The crashed module still leaves its trace, linked from provenance.json
    activities = load_trace(module_dir)["activity"].values()
    assert len([a for a in activities if a["prov:type"] == "dage:arbitration"]) == 2
    assert json.loads((tmp_path / "provenance.json").read_text())["generation_traces"][0]["module_id"] == "adder"


def test_ask_code_reasks_with_compile_error_and_cut_off_notice():
    truncated = fenced("print(f'Greenness: {results[")
    client = ScriptedCodeClient([truncated, fenced("x = 1\n", finish_reason="length"), fenced("x = {'a': 1}\n")])
    assert phase2._ask_code(client, "m", "write code", "reference solution") == "x = {'a': 1}"
    assert "does not compile" in client.requests[1][-1]["content"]
    assert "cut off" in client.requests[2][-1]["content"]

    with pytest.raises(RuntimeError, match="compilable reference solution after 2 attempts"):
        phase2._ask_code(ScriptedCodeClient([truncated, truncated]), "m", "p", "reference solution", max_retries=1)


def test_extract_code_block_handles_prose_and_missing_fences():
    from digitalagedu.core.llm.ai_setup import extract_code_block
    assert extract_code_block("intro\n```python\nshort = 1\n```\nand\n```python\nlonger = [1, 2]\n```") == "longer = [1, 2]"
    assert extract_code_block("x = 1") == "x = 1"
    assert extract_code_block("```python\nx = 1") == "x = 1"  # unclosed fence (cut-off reply)


def test_failed_week_does_not_stop_later_weeks(phase2_env):
    tmp_path, run = phase2_env
    config = tmp_path / "config.yaml"
    config.write_text(config.read_text().replace(
        '{id: "adder", week: 1, title: "Adder"}', '{id: "adder", week: 1, title: "Adder"}, {id: "adder2", week: 2, title: "Adder 2"}'
    ), encoding="utf-8")
    # Week 1 stays broken through its contract revision; Week 2 passes first time
    with pytest.raises(RuntimeError, match=r"1 of 2 module\(s\) failed:\nadder \(Week 1\): Sandbox verification failed"):
        run([BROKEN_TEST, SOLUTION, BROKEN_TEST] * 2 + [GOOD_TEST, SOLUTION, STARTER], faults=["contract", "contract"])
    week2 = tmp_path / "exercises" / "Week_02" / "adder2"
    assert json.loads((week2 / "adder2_verification.json").read_text())["verified"] is True
    assert (week2 / "adder2_presentation.pptx").exists()
    assert not (tmp_path / "exercises" / "Week_01" / "adder" / "adder_presentation.pptx").exists()
    traces = json.loads((tmp_path / "provenance.json").read_text())["generation_traces"]
    assert [t["module_id"] for t in traces] == ["adder", "adder2"]
    # Stage A writes every week's problem statement first, in order; Week 1's contract revision comes later
    assert run.agent0_history[:2] == [[], [1]] and run.agent0_feedback[:2] == [None, None]
    # Each week logs to its own file; the failed week's log holds its error
    log1 = (tmp_path / "exercises" / "Week_01" / "adder" / "adder_phase2.log").read_text(encoding="utf-8")
    log2 = (week2 / "adder2_phase2.log").read_text(encoding="utf-8")
    assert "Processing LLM Module: Adder (Week 1)" in log1 and "[ERROR] Failed processing module adder" in log1
    assert "Processing LLM Module: Adder 2 (Week 2)" in log2 and "Adder (Week 1)" not in log2


def test_ask_code_retries_a_stream_that_drops_mid_reply(monkeypatch):
    """Run 49088b7e: NRP closed a glm-5 stream mid-reply and the SDK, which only retries before streaming starts,
    let the error fail the whole week."""
    import httpx
    from digitalagedu.core.llm import ai_setup
    monkeypatch.setattr(ai_setup.time, "sleep", lambda s: None)

    def dropping():
        yield stream("```python\nx = ")[0]
        raise httpx.RemoteProtocolError("peer closed connection without sending complete message body")

    client = ScriptedCodeClient([dropping(), fenced("x = 1\n")])
    assert phase2._ask_code(client, "m", "write code", "reference solution") == "x = 1"
    assert len(client.requests) == 2 and client.requests[1] == client.requests[0]  # same request, no partial reply kept

    always = ScriptedCodeClient([dropping() for _ in range(3)])
    with pytest.raises(httpx.RemoteProtocolError):
        phase2._ask_code(always, "m", "write code", "reference solution")


def test_model_slots_cap_concurrent_streams_across_threads():
    """Week workers and slide prefetch threads share one per-model cap (NRP's per-user concurrency limit)."""
    import threading
    from digitalagedu.core.llm import ai_setup
    gate, running, peak, lock = threading.Event(), [0], [0], threading.Lock()

    class SlowClient:
        def __init__(self):
            self.chat = self.completions = self

        def create(self, **kwargs):
            with lock:
                running[0] += 1
                peak[0] = max(peak[0], running[0])
            gate.wait(5)
            with lock:
                running[0] -= 1
            return stream("```python\nx = 1\n```")

    ai_setup.configure_model_slots({"m": 2})
    try:
        threads = [threading.Thread(target=ai_setup._stream_reply, args=(SlowClient(), "m", [{"role": "user", "content": "x"}], 10, "t"))
                   for _ in range(5)]
        for t in threads:
            t.start()
        threading.Timer(0.5, gate.set).start()
        for t in threads:
            t.join(10)
        assert peak[0] == 2
    finally:
        ai_setup.configure_model_slots({})


def test_generation_trace_ids_stay_unique_across_threads(tmp_path):
    import threading
    from digitalagedu.core.llm.generation_trace import GenerationTrace
    trace = GenerationTrace(str(tmp_path), "m", "glm-5")
    threads = [threading.Thread(target=lambda: [trace.add_activity("llm_call", "slide_builder") for _ in range(50)]) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert len([a for a in trace.doc["activity"].values() if a["prov:type"] == "dage:llm_call"]) == 400


def _worker_view(_):
    from digitalagedu.core.llm import ai_setup, main
    ctx = main._WEEK_CTX
    return (type(ctx["code_client"]).__name__, ctx["models"].coder, ctx["telemetry"]["run_summary"]["overall_accuracy_percent"],
            sorted(ai_setup.MODEL_SLOTS), "NRP_LLM_API" in __import__("os").environ)


def test_spawned_week_workers_get_the_run_context_caps_and_their_own_clients():
    import multiprocessing
    from concurrent.futures import ProcessPoolExecutor
    from digitalagedu.core.config import LLMModels
    from digitalagedu.core.llm import ai_setup
    ctx = multiprocessing.get_context("spawn")
    ai_setup.configure_model_slots({"glm-5": 2}, ctx)
    try:
        run_ctx = {"base_url": None, "api_key": "test-key", "models": LLMModels(), "telemetry": {"run_summary": {"overall_accuracy_percent": 90.0}}}
        with ProcessPoolExecutor(max_workers=2, mp_context=ctx, initializer=phase2._init_week_worker,
                                 initargs=(run_ctx, dict(ai_setup.MODEL_SLOTS))) as pool:
            views = list(pool.map(_worker_view, range(2)))
    finally:
        ai_setup.configure_model_slots({})
    assert views == [("OpenAI", "glm-5", 90.0, ["glm-5"], False)] * 2
