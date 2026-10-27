"""End-to-end check of generate_llm_curriculum with a scripted LLM client and the real sandbox."""
import json
import os

import pytest

from digitalagedu.core.llm import main as phase2
from digitalagedu.core.llm.schemas import (
    ExerciseSolutionSchema, ProblemStatementSchema, StarterCodeSchema, UnitTestSchema,
)

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

SOLUTION = ExerciseSolutionSchema(title="t", instructions="i", solution_code="def add(a, b):\n    return a + b\n")
BROKEN_TEST = UnitTestSchema(unit_test="assert add(1, 1) == 3\n")
GOOD_TEST = UnitTestSchema(unit_test="assert add(1, 1) == 2\n")
STARTER = StarterCodeSchema(starter_code="def add(a, b):\n    # TODO: return the sum of a and b\n    pass\n")


class ScriptedClient:
    """Returns queued responses per response_model, mimicking instructor's client.chat.completions.create."""
    def __init__(self, responses):
        self.responses = {k: list(v) for k, v in responses.items()}
        self.chat = self
        self.completions = self

    def create(self, response_model, **kwargs):
        return self.responses[response_model].pop(0)


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

    def fake_deck(self, output_path, **kw):
        open(output_path, "wb").close()
        return output_path
    monkeypatch.setattr(phase2.PresentationDesigner, "generate_presentation_deck", fake_deck)

    def run(responses):
        client = ScriptedClient(responses)
        monkeypatch.setattr(phase2, "get_instructor_client", lambda base_url=None: client)
        phase2.generate_llm_curriculum(str(config_path), output_dir=str(tmp_path / "exercises"), telemetry_dir=str(tmp_path))
        return client
    return tmp_path, run


def test_self_heals_failing_tests_and_writes_all_module_assets(phase2_env):
    tmp_path, run = phase2_env
    client = run({
        UnitTestSchema: [BROKEN_TEST, GOOD_TEST],
        ExerciseSolutionSchema: [SOLUTION],
        StarterCodeSchema: [STARTER],
    })
    module_dir = tmp_path / "exercises" / "Week_01" / "adder"
    assert json.loads((module_dir / "adder_verification.json").read_text())["verified"] is True
    assert json.loads((module_dir / "adder_generated.json").read_text())["unit_test"] == GOOD_TEST.unit_test
    assert "TODO" in (module_dir / "adder_exercise.py").read_text()
    for suffix in ("overview.md", "manifest.json", "solution.py", "test.py", "slides_payload.json", "presentation.pptx"):
        assert (module_dir / f"adder_{suffix}").exists(), suffix
    assert (tmp_path / "exercises" / "requirements.txt").exists()
    assert all(not queue for queue in client.responses.values())  # QA retry was used exactly once


def test_unverifiable_solution_crashes_before_slides(phase2_env):
    tmp_path, run = phase2_env
    with pytest.raises(RuntimeError, match="Sandbox verification failed"):
        run({UnitTestSchema: [BROKEN_TEST] * (1 + phase2.MAX_SELF_HEAL_ROUNDS), ExerciseSolutionSchema: [SOLUTION]})
    module_dir = tmp_path / "exercises" / "Week_01" / "adder"
    assert json.loads((module_dir / "adder_verification.json").read_text())["verified"] is False
    assert not (module_dir / "adder_presentation.pptx").exists()
