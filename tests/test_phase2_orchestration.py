"""End-to-end check of generate_llm_curriculum with a scripted LLM client and the real sandbox."""
import json
from types import SimpleNamespace

import pytest

from digitalagedu.core.llm import main as phase2
from digitalagedu.core.llm.schemas import ProblemStatementSchema

CONFIG = """
project: {{domain: "Generic", context_statement: "c"}}
dataset: {{root_path: "{root}"}}
output: {{directory: "{root}"}}
pipeline: {{stages: [{{name: "Classification", active: true, task_type: "classification"}}]}}
execution: {{device: "cpu", batch_size: 1, image_size: 32, seed: 7}}
curriculum:
  subject: "Testing"
  modules: [{{id: "adder", week: 1, title: "Adder"}}]
"""


def fenced(code, finish_reason="stop"):
    """A plain chat completion whose reply is one ```python block."""
    message = SimpleNamespace(content=f"Here you go:\n```python\n{code}```\n")
    return SimpleNamespace(choices=[SimpleNamespace(message=message, finish_reason=finish_reason)])


SOLUTION = fenced("def add(a, b):\n    return a + b\n")
BROKEN_TEST = fenced("assert add(1, 1) == 3\n")
GOOD_TEST = fenced('assert add(1, 1) == 2, f"got {add(1, 1)}"\n')  # double quotes, unescaped: no JSON in the way
STARTER = fenced("def add(a, b):\n    # TODO: return the sum of a and b\n    pass\n")


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

    problem = ProblemStatementSchema(
        title="Adder", domain_context="d", problem_statement="Add two numbers",
        learning_objectives=["add"], suggested_focus="addition", markdown_overview="# Adder",
    )
    monkeypatch.setattr(phase2, "formulate_problem_statement", lambda **kw: problem)
    monkeypatch.setattr("digitalagedu.core.llm.context.get_rag_context", lambda *a, **kw: "")
    monkeypatch.setattr(phase2, "get_instructor_client", lambda base_url=None: None)

    def fake_deck(self, output_path, **kw):
        open(output_path, "wb").close()
        return output_path
    monkeypatch.setattr(phase2.PresentationDesigner, "generate_presentation_deck", fake_deck)

    def run(replies):
        client = ScriptedCodeClient(replies)
        monkeypatch.setattr(phase2, "get_openai_client", lambda base_url=None: client)
        phase2.generate_llm_curriculum(str(config_path), output_dir=str(tmp_path / "exercises"), telemetry_dir=str(tmp_path))
        return client
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


def test_unverifiable_solution_crashes_before_slides(phase2_env):
    tmp_path, run = phase2_env
    with pytest.raises(RuntimeError, match="Sandbox verification failed"):
        run([BROKEN_TEST, SOLUTION] + [BROKEN_TEST] * phase2.MAX_SELF_HEAL_ROUNDS)
    module_dir = tmp_path / "exercises" / "Week_01" / "adder"
    assert json.loads((module_dir / "adder_verification.json").read_text())["verified"] is False
    assert not (module_dir / "adder_presentation.pptx").exists()


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
