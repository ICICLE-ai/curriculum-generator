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


def test_failure_surviving_an_arbiter_directed_repair_escalates_to_the_contract(tmp_path):
    # The Arbiter wrongly blames the test; the QA repair changes nothing, so the dispute goes up to Agent 0
    result, _, arbiter, _ = run(tmp_path, WRONG, [WRONG, TEST], faults=["test"])
    with pytest.raises(ContractRevisionNeeded) as caught:
        result()
    assert arbiter.calls == 1 and caught.value.escalations[-1]["to_agent"] == "agent0_director"
