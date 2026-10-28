"""Escalation ladder of the sandbox self-healing loop (real sandbox, scripted LLMs)."""
from types import SimpleNamespace

import pytest

from digitalagedu.core.llm.generation_trace import GenerationTrace
from digitalagedu.core.llm.schemas import ArbiterVerdictSchema, ProblemStatementSchema
from digitalagedu.core.llm.self_healing import ContractRevisionNeeded, verify_with_self_healing

TEST = "from adder_solution import *\nassert add(1, 1) == 2\n"
GOOD = "def add(a, b):\n    return a + b\n"
WRONG = "def add(a, b):\n    return a - b\n"
PROBLEM = ProblemStatementSchema(
    title="Adder", domain_context="d", problem_statement="Add two numbers",
    learning_objectives=["add"], suggested_focus="addition", markdown_overview="# Adder",
)


def fenced(code):
    message = SimpleNamespace(content=f"```python\n{code}```")
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason="stop")])


class CodeClient:
    def __init__(self, codes):
        self.replies, self.prompts = [fenced(c) for c in codes], []
        self.chat = self.completions = self

    def create(self, messages, **kwargs):
        self.prompts.append(messages[1]["content"])
        return self.replies.pop(0)


class Arbiter:
    def __init__(self, faults):
        self.verdicts = [ArbiterVerdictSchema(fault=f, rationale=f"why-{f}", fix_directive=f"do-{f}") for f in faults]
        self.calls = 0
        self.chat = self.completions = self

    def create_with_completion(self, response_model, **kwargs):
        self.calls += 1
        return self.verdicts.pop(0), SimpleNamespace(usage=SimpleNamespace(prompt_tokens=10, completion_tokens=5))


def run(tmp_path, solution, codes, faults=(), unit_test=TEST):
    fixtures = tmp_path / "fixtures_dir"
    fixtures.mkdir()
    (fixtures / "results.csv").write_text("a,b\n1,2\n", encoding="utf-8")
    trace = GenerationTrace(str(tmp_path / "module"), "adder", "qwen")
    trace.add_entity("unit_test", unit_test, ext="py", versioned=True)
    trace.add_entity("solution", solution, ext="py", versioned=True)
    code_client, arbiter = CodeClient(codes), Arbiter(faults)
    result = lambda: verify_with_self_healing(
        arbiter, code_client, "qwen", SimpleNamespace(id="adder"), PROBLEM, "QA PROMPT", "CODER PROMPT",
        unit_test, solution, [str(fixtures)], trace,
    )
    return result, code_client, arbiter, trace


def kinds(trace, prov_type):
    return [a for a in trace.doc["activity"].values() if a["prov:type"] == prov_type]


def test_missing_fixture_repair_gets_the_fixture_filenames(tmp_path):
    broken = "open('fixtures/results.csv').read()\n" + GOOD
    result, code_client, arbiter, _ = run(tmp_path, broken, [GOOD])
    success, _, _, escalations, _, solution = result()
    assert success and solution.strip() == GOOD.strip() and arbiter.calls == 0
    assert "[missing_fixture]" in code_client.prompts[0] and "results.csv" in code_client.prompts[0].split("FIX HINTS:")[1]
    assert [(e["level"], e["to_agent"]) for e in escalations] == [(1, "agent1_coder")]


def test_stuck_mismatch_goes_to_the_arbiter_whose_directive_drives_the_repair(tmp_path):
    result, code_client, arbiter, trace = run(tmp_path, WRONG, [WRONG, GOOD], faults=["solution"])
    success, _, _, escalations, _, _ = result()
    assert success and arbiter.calls == 1
    assert "do-solution" not in code_client.prompts[0] and "do-solution" in code_client.prompts[1]
    assert [(e["level"], e["to_agent"]) for e in escalations] == [(1, "agent1_coder"), (2, "arbiter"), (2, "agent1_coder")]
    assert kinds(trace, "dage:arbitration")[0]["dage:fault"] == "solution"
    assert any(e["prov:type"] == "dage:verdict" for e in trace.doc["entity"].values())


def test_contract_verdict_requests_a_revision(tmp_path):
    result, _, _, trace = run(tmp_path, WRONG, [WRONG], faults=["contract"])
    with pytest.raises(ContractRevisionNeeded) as caught:
        result()
    assert caught.value.verdict.fault == "contract" and "do-contract" in caught.value.feedback()
    assert [e["level"] for e in caught.value.escalations][-1] == 3


def test_fixed_failure_that_comes_back_restarts_at_level_one(tmp_path):
    # WRONG (mismatch) -> coder -> RAISES (new error) -> coder -> WRONG again (regression) -> coder -> GOOD
    raises = "def add(a, b):\n    raise ValueError('boom')\n"
    result, _, arbiter, _ = run(tmp_path, WRONG, [raises, WRONG, GOOD])
    success, _, _, escalations, _, _ = result()
    assert success and arbiter.calls == 0
    assert [e["level"] for e in escalations] == [1, 1, 1]


def test_sandbox_exposes_run_folders_and_hides_generated_exercises(tmp_path, monkeypatch):
    from digitalagedu.core.llm.sandbox import describe_sandbox_fixtures, run_in_sandbox
    monkeypatch.chdir(tmp_path)
    run_dir = tmp_path / "outputs" / "run"
    (run_dir / "images" / "dataset_sample" / "Apple___scab").mkdir(parents=True)
    (run_dir / "images" / "dataset_sample" / "Apple___scab" / "leaf 1.JPG").write_bytes(b"jpg")
    (run_dir / "images" / "masks").mkdir()
    (run_dir / "images" / "masks" / "m.png").write_bytes(b"png")
    (run_dir / "exercises").mkdir()
    (run_dir / "results.csv").write_text("image_path,mask\n/data/leaf.JPG,./outputs/run/images/masks/m.png\n", encoding="utf-8")

    test = (
        "import os\n"
        "assert os.path.exists('results.csv')\n"
        "assert os.path.exists('images/dataset_sample/Apple___scab/leaf 1.JPG')\n"
        "assert os.path.exists('./outputs/run/images/masks/m.png')  # CSV-relative path resolves as written\n"
        "assert not os.path.exists('exercises') and not os.path.exists('outputs/run/exercises')\n"
    )
    ok, log = run_in_sandbox("x = 1\n", test, module_id="m", artifact_sources=["outputs/run"])
    assert ok, log

    note = describe_sandbox_fixtures("outputs/run")
    assert "Folder images/dataset_sample/: 1 subfolders" in note and "leaf 1.JPG" in note
    assert "mask='./outputs/run/images/masks/m.png'" in note and "exercises" not in note
    assert "Paths starting with outputs/run/" in note


def test_missing_typing_name_is_an_import_fix_not_a_contract_symbol():
    from digitalagedu.core.llm.ai_setup import add_missing_typing_imports
    from digitalagedu.core.llm.generation_trace import attribute_failures
    log = ('Traceback (most recent call last):\n  File "/tmp/x/m_solution.py", line 84, in <module>\n'
           "NameError: name 'Any' is not defined. Did you mean: 'any'?")
    assert attribute_failures(log, ["run_pipeline"])[0]["kind"] == "missing_import"
    assert attribute_failures(log.replace("'Any'", "'run_pipeline'"), ["run_pipeline"])[0]["kind"] == "missing_symbol"

    code = "from typing import List\n\ndef f(x: Any) -> Union[int, List[str]]:\n    return x\n"
    assert add_missing_typing_imports(code).startswith("from typing import Any, Union\n")
    assert add_missing_typing_imports("from typing import Any\nx: Any = 1\n") == "from typing import Any\nx: Any = 1\n"
    assert add_missing_typing_imports("from collections import Counter\nc = Counter()\n").startswith("from collections")


def test_failure_surviving_an_arbiter_directed_repair_escalates_to_the_contract(tmp_path):
    # The Arbiter wrongly blames the test; the QA repair changes nothing, so the dispute goes up to Agent 0
    result, _, arbiter, _ = run(tmp_path, WRONG, [WRONG, TEST], faults=["test"])
    with pytest.raises(ContractRevisionNeeded) as caught:
        result()
    assert arbiter.calls == 1 and caught.value.escalations[-1]["to_agent"] == "agent0_director"
