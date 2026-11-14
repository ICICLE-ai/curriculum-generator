"""Pure helpers of scripts/replay_plan_failures.py (no LLM calls)."""
import importlib.util
import os

_path = os.path.join(os.path.dirname(__file__), "..", "scripts", "replay_plan_failures.py")
_spec = importlib.util.spec_from_file_location("replay_plan_failures", _path)
replay = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(replay)


def test_fatal_weeks_only_picks_lesson_plan_deaths(tmp_path):
    for week, name, text in [(1, "a", "Lesson planning failed to generate a plan for 'A'."), (2, "b", "finished"),
                             (3, "c", "Sandbox verification failed")]:
        d = tmp_path / "exercises" / f"Week_0{week}" / name
        d.mkdir(parents=True)
        (d / f"{name}_phase2.log").write_text(text, encoding="utf-8")
    assert [os.path.basename(p) for p in replay.fatal_weeks(str(tmp_path))] == ["a"]


def test_helpers():
    assert replay.strip_docstring_header('"""\nSolution: X\n"""\n\nimport os\n') == "import os\n"
    err = ("1 validation error for LessonPlan\n  Value error, goal and application slides need at least one real number "
           "in `evidence`: ['x'] [type=value_error, input_value={...}]")
    assert replay.short_error(err) == "goal and application slides need at least one real number in `evidence`: ['x']"
    assert replay.identical_repeats(["a", "a", "b", "b", "b"]) == 3
