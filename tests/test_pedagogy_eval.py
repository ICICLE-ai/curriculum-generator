"""Pedagogy-eval pilot: rule-based flags, scoring, loading, budget and the log-only hook (scripted LLM)."""
import csv
import itertools
import json
from types import SimpleNamespace

import pytest

from digitalagedu.core.eval import bloom, load, run, schemas, sim_learner
from digitalagedu.core.llm import main

LEVELS = ["remember", "apply", "analyze", "create"]
STRUCT = {"test_name": "test_shape", "quoted_assert": "assert x.shape == (2,)", "checks_only_structure": True}
VALUE = {"test_name": "test_value", "quoted_assert": "assert f(1) == 2", "checks_only_structure": False}


def test_bloom_flags_split_gaps_from_untestable_and_catch_structure_only_tests():
    mappings = [{**VALUE, "objective_index": 1}, {**STRUCT, "objective_index": 2}, {**STRUCT, "objective_index": None}]
    f = bloom.flags(LEVELS, mappings, "Grade 10")
    assert f["untested_objectives"] == [3]          # 'create', not tested
    assert f["untestable_by_unit_test"] == [0]      # 'remember' can't be unit-tested: reported apart
    assert f["low_level_tests_only"] == [2]         # 'analyze' checked only by a shape test
    assert f["level_mismatch"] == [3]               # 'create' above the high-school cap
    assert f["unmapped_tests"] == ["test_shape"]
    assert f["coverage"] == 0.5
    assert bloom.flags(LEVELS, mappings, "Undergraduate")["level_mismatch"] == []


def test_bloom_test_names_finds_functions_and_methods():
    code = "def test_a():\n    pass\nclass T:\n    def test_b(self):\n        pass\ndef helper():\n    pass\n"
    assert bloom.test_names(code) == ["test_a", "T.test_b"]
    assert bloom.test_names("def broken(:") == []


def _quiz(kinds=("run_data", "run_data", "concept", "concept", "run_data", "concept")):
    return schemas.Quiz(questions=[
        schemas.QuizQuestion(question=f"q{i}", options=["a", "b", "c", "d"], answer_index=0, kind=k, objective_index=i % 2)
        for i, k in enumerate(kinds)])


def test_sim_score_gain_by_kind_and_missing_answers_count_wrong():
    quiz = _quiz()
    s = sim_learner.score(quiz, pre=[1, 1, 0, 0, 1, 1], post=[0, 0, 0])  # post missing last 3 answers
    assert s["overall"] == {"n": 6, "pre": 2 / 6, "post": 3 / 6, "gain": pytest.approx(1 / 6)}
    assert s["by_kind"]["run_data"]["gain"] == pytest.approx(2 / 3)
    assert s["by_kind"]["concept"]["pre"] == pytest.approx(2 / 3)


def _week(root, week, name, verified=True, versions=(1,)):
    d = root / f"Week_{week:02d}" / name
    (d / "trace").mkdir(parents=True)
    (d / f"{name}_verification.json").write_text(json.dumps({"verified": verified}), encoding="utf-8")
    (d / f"{name}_presentation.pptx").write_bytes(b"")
    (d / f"{name}_test.py").write_text("def test_a():\n    assert 1 == 1\n", encoding="utf-8")
    for v in versions:
        (d / "trace" / f"problem_formulation_v{v}.json").write_text(
            json.dumps({"learning_objectives": [f"objective from v{v}"]}), encoding="utf-8")
    return d


def test_load_picks_newest_contract_and_skips_unverified_weeks(tmp_path):
    good = _week(tmp_path, 1, "leaf", versions=(2, 10))
    _week(tmp_path, 2, "broken", verified=False)
    assert load.list_finished_weeks(str(tmp_path)) == [str(good)]
    bundle = load.load_week(str(good))
    assert (bundle.week, bundle.objectives) == (1, ["objective from v10"])  # numeric, not lexical, version order


class ScriptedJudge:
    """Instructor-style client answering by response_model."""
    def __init__(self):
        self.chat = self.completions = self
        self.calls = []

    def create(self, model, response_model, messages, **kwargs):
        self.calls.append(response_model.__name__)
        if response_model is schemas.BloomLevels:
            return schemas.BloomLevels(objectives=[schemas.BloomObjective(objective="o", rationale="r", level="apply")])
        if response_model is schemas.TestMap:
            return schemas.TestMap(tests=[schemas.TestMapping(objective_index=0, **VALUE)])
        if response_model is schemas.Quiz:
            return _quiz()
        if response_model is schemas.QuizAnswers:
            return schemas.QuizAnswers(answers=[0] * 6)
        return schemas.RubricVerdict(scores=[schemas.RubricScore(dimension="level_fit", evidence="e", score=4)])


CONFIG = SimpleNamespace(curriculum=SimpleNamespace(level="Grade 10"))


def test_evaluate_run_writes_only_the_evaluation_dir(tmp_path, monkeypatch):
    week = _week(tmp_path, 1, "leaf")
    before = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*"))
    monkeypatch.setattr(run, "render_slides", lambda deck, out: ([], ["Slide one text"]))
    client = ScriptedJudge()
    out = run.evaluate_run(str(tmp_path), None, CONFIG, client, "judge-model", repeat=2)

    after = sorted(p.relative_to(tmp_path) for p in tmp_path.rglob("*") if "evaluation" not in p.parts)
    assert after == before  # nothing outside evaluation/ was touched
    rec = json.loads((tmp_path / "evaluation" / "Week_01_leaf_evaluation.json").read_text(encoding="utf-8"))
    assert rec["status"] == "ok" and rec["judged_without_images"] is True
    assert rec["bloom"]["flags"]["coverage"] == 1.0
    assert len(rec["judge"]) == len(rec["sim_learner"]) == 2
    assert rec["judge"][0]["missing_dimensions"]  # only level_fit was scored: the rest are listed, not invented
    assert client.calls.count("Quiz") == 1        # one quiz per week, retaken per repeat
    with open(f"{out}/evaluation_summary.csv", encoding="utf-8") as f:
        metrics = {r["metric"] for r in csv.DictReader(f)}
    assert {"rubric.level_fit", "bloom.coverage", "sim.run_data.gain", "text_chars"} <= metrics


def test_budget_skips_remaining_weeks(tmp_path, monkeypatch):
    _week(tmp_path, 1, "a")
    _week(tmp_path, 2, "b")
    clock = itertools.chain([0, 0], itertools.repeat(7200))  # start, week 1 check, then 2 h later
    monkeypatch.setattr(run, "time", SimpleNamespace(monotonic=lambda: next(clock)))  # run's clock only
    monkeypatch.setattr(run, "evaluate_week", lambda d, *a: {"module_id": "a", "week": 1})
    run.evaluate_run(str(tmp_path), None, CONFIG, None, "m", budget_minutes=60)
    status = json.loads((tmp_path / "evaluation" / "Week_02_b_evaluation.json").read_text(encoding="utf-8"))["status"]
    assert status == "skipped_budget"


def test_hook_is_off_by_default_and_swallows_errors(monkeypatch):
    def boom(*a, **k):
        raise RuntimeError("judge endpoint down")
    monkeypatch.setattr(run, "evaluate_run", boom)
    execution = SimpleNamespace(pedagogy_eval=False, pedagogy_eval_minutes=60, llm_models=SimpleNamespace(judge="m"))
    config = SimpleNamespace(execution=execution)
    main._pedagogy_eval(config, "out", None, None)  # off: never calls evaluate_run
    execution.pedagogy_eval = True
    main._pedagogy_eval(config, "out", None, None)  # on: the error is printed, not raised
