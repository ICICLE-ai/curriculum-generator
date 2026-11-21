"""Quality gates (core/llm/gates.py), Agent 0's contract validator and the telemetry recall fix."""
from types import SimpleNamespace

import pytest
from pydantic import ValidationError

from digitalagedu.core.llm import gates
from digitalagedu.core.llm.schemas.generation_types import AgentZeroContract, ComponentSpec, MilestoneSubsystem
from digitalagedu.core.llm.telemetry import _format_per_class_metrics_summary


def _milestone(num, names, indices):
    comps = [ComponentSpec(name=n, kind="function", signature=f"def {n}():", description="x") for n in names]
    return MilestoneSubsystem(milestone_num=num, title=f"M{num}", objective="o", objective_indices=indices, components=comps)


def _contract(milestones, objectives=("classify leaves", "explain errors")):
    return dict(title="t", domain_context="d", problem_statement="p", learning_objectives=list(objectives),
                milestone_subsystems=milestones, suggested_focus="f", markdown_overview="m")


GOOD = [_milestone(1, ["load"], [0]), _milestone(2, ["train"], [0]), _milestone(3, ["explain"], [1])]


def test_contract_validator_accepts_complete_and_rejects_gaps():
    AgentZeroContract(**_contract(GOOD))
    with pytest.raises(ValidationError, match="write 3"):
        AgentZeroContract(**_contract([]))
    with pytest.raises(ValidationError, match="not 0..1"):
        AgentZeroContract(**_contract(GOOD[:2] + [_milestone(3, ["explain"], [5])]))
    with pytest.raises(ValidationError, match="no objective_indices"):
        AgentZeroContract(**_contract(GOOD[:2] + [_milestone(3, ["explain"], [])]))


def test_contract_gate_flags_untaught_objectives():
    good = SimpleNamespace(**_contract(GOOD))
    assert gates.contract_gate(good) == []
    partial = SimpleNamespace(**_contract([_milestone(1, ["load"], [0])]))
    checks = {f["check"] for f in gates.contract_gate(partial)}
    assert checks == {"milestones", "untaught_objectives"}


TESTS = '''
def test_load():
    """Objective 0: rows load from the real CSV"""
    rows = load()
    assert len(rows) == 500

def test_train():
    """Objective 0: accuracy beats chance"""
    assert train()["accuracy"] > 0.5
    assert result["seed"] == 6767
'''


def test_tests_gate_findings():
    found = {f["check"]: f["message"] for f in gates.tests_gate(TESTS, SimpleNamespace(**_contract(GOOD)))}
    assert "explain" in found["untested_components"]
    assert "1" in found["unassessed_objectives"]
    assert "seed" in found["bookkeeping_assert"]
    assert "test_load" in found["structure_only"]  # len(...) == 500 is its only assert
    assert gates.tests_gate("def (", None)[0]["check"] == "syntax"


def _plan(*slides):
    return SimpleNamespace(slides=[SimpleNamespace(title=t, explanation=x, on_slide_text=[], evidence=[
        SimpleNamespace(label="Recall", value=v, context="") for v in values]) for t, x, values in slides])


def test_numbers_gate():
    telemetry = {"run_summary": {"recall": 0.8123, "f1": 0.75}}
    assert gates.numbers_gate(_plan(("ok", "", ["81.2%", "0.75"])), telemetry) == []
    checks = [f["check"] for f in gates.numbers_gate(_plan(
        ("made up", "", ["0.42"]), ("bad", "recall = 0 but F1 = 0.75, accuracy 120%", [])), telemetry)]
    assert checks == ["unknown_number", "impossible_metric", "impossible_metric"]


def test_run_gate_records_and_off_mode():
    gates.configure("log")
    gates.run_gate("G9", lambda: 1 / 0)
    assert gates.RECORDS[0]["findings"][0]["check"] == "gate_error"
    gates.configure("off")
    assert gates.run_gate("G9", lambda: [{"check": "x"}]) == [] and gates.RECORDS == []
    gates.configure("log")


def test_telemetry_summary_reads_sensitivity_recall():
    mpc = {f"c{i}": {"sensitivity_recall": 0.6, "f1": 0.1 * i} for i in range(6)}
    text = "\n".join(_format_per_class_metrics_summary(mpc, {"c0": 12}))
    assert "Recall=0.6" in text and "Recall=0.0" not in text
    assert "Support=12" in text
