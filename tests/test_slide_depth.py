"""Checks for the slide-depth fixes: no invented telemetry, compile-checked code, fail-fast decks."""
import re
from types import SimpleNamespace

import pytest

from digitalagedu.core.llm.sandbox import clean_code_snippet
from digitalagedu.core.llm.schemas import ExerciseSolutionSchema, UnitTestSchema

TELEMETRY = {
    "class_mapping": {"0": "Leaf_A", "1": "Leaf_B", "2": "Leaf_C"},
    "run_summary": {
        "total_rows_processed": 90,
        "overall_accuracy_percent": 94.5,
        "auc_roc": 0.9989,
        "class_balance": {"Leaf_A": 30, "Leaf_B": 30, "Leaf_C": 30},
        "error_counts": {"Leaf_A_predicted_as_Leaf_B": 3, "Leaf_C_predicted_as_Leaf_A": 2},
        "metrics_per_class": {
            c: {"precision": p, "sensitivity_recall": r, "f1_score": f}
            for c, p, r, f in [("Leaf_A", 0.93, 0.9, 0.91), ("Leaf_B", 0.9, 1.0, 0.95), ("Leaf_C", 1.0, 0.93, 0.96)]
        },
    },
}


def test_clean_code_snippet_keeps_newline_escapes_in_strings():
    code = 'msg = "a\\nb"\nprint(msg)'
    assert clean_code_snippet(code) == code
    # A fully escaped one-line snippet is still unescaped
    assert clean_code_snippet("x = 1\\ny = 2") == "x = 1\ny = 2"


@pytest.mark.parametrize("schema, field", [(ExerciseSolutionSchema, "solution_code"), (UnitTestSchema, "unit_test")])
def test_truncated_code_is_rejected(schema, field):
    base = {"title": "t", "instructions": "i"} if schema is ExerciseSolutionSchema else {}
    with pytest.raises(ValueError, match="does not compile"):
        schema(**base, **{field: "image_paths = [f'{config["})
    assert getattr(schema(**base, **{field: "x = 1"}), field) == "x = 1"


def test_planner_prompt_uses_real_accuracy():
    from digitalagedu.core.llm.presentation_prompts import build_concept_discretizer_prompt
    from digitalagedu.core.llm.schemas import Module

    module = Module(id="m", title="M", week=1, context="ctx", difficulty="intermediate")
    comps = [SimpleNamespace(kind="function", name=f"f{i}", signature=f"def f{i}()") for i in range(3)]
    pf = SimpleNamespace(
        title="M", domain_context="ctx", problem_statement="p", learning_objectives=["o"], suggested_focus="f",
        milestone_subsystems=[SimpleNamespace(milestone_num=1, title="S", objective="o", components=comps)],
    )
    prompt = build_concept_discretizer_prompt(module, pf, "\n".join(f"line_{i} = {i}" for i in range(60)), TELEMETRY)
    assert "94.5" in prompt and "90.57" not in prompt and "0.9709" not in prompt
    assert "def f2()" in prompt  # every component, not just the first two
    assert "line_59" in prompt  # whole solution, not the first 45 lines


@pytest.mark.parametrize("recipe_id", [
    "recipe_confusion_matrix", "recipe_metric_comparison", "recipe_class_distribution", "recipe_metric_kpi_badges",
])
def test_telemetry_recipes_run_on_real_keys(recipe_id, tmp_path):
    from digitalagedu.core.llm.slide_deck_repl import SlideDeckRepl
    from digitalagedu.core.llm.visuals.visual_recipes import VISUAL_RECIPES

    text = next(r["text"] for r in VISUAL_RECIPES if r["id"] == recipe_id)
    code = re.search(r"```python\n(.*?)```", text, re.S).group(1)
    repl = SlideDeckRepl(output_path=str(tmp_path / "d.pptx"), telemetry=TELEMETRY, solution_code="", temp_dir=str(tmp_path))
    ok, msg = repl.execute_snippet(code)
    assert ok, msg
    assert len(repl.prs.slides) == 1
