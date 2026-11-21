"""Step-by-step TODO check (real sandbox, tiny module) and the damage test's transforms and verdicts (no LLM)."""
import random

from digitalagedu.core.eval import bloom, damage, scaffold

SOLUTION = (
    "def add(a, b):\n    return a + b\n\n"
    "def _twice(x):\n    return add(x, x)\n\n"
    "def double(x):\n    return _twice(x)\n"
)
# The scaffolder left out the _twice helper: the check supplies it, so each stub is measured on its own
STARTER = (
    "def add(a, b):\n    # TODO: return the sum\n    raise NotImplementedError('TODO')\n\n"
    "def double(x):\n    # TODO: double x using add\n    raise NotImplementedError('TODO')\n"
)
TESTS = (
    "from adder_exercise import *\n"
    "def test_free():\n    assert 1 + 1 == 2\n"
    "def test_add():\n    assert add(2, 3) == 5\n"
    "def test_double():\n    assert double(4) == 8\n"
)


def test_each_stub_unlocks_its_tests_in_order():
    result = scaffold.check(STARTER, SOLUTION, TESTS, "adder", timeout=60)
    assert result["stubs"] == ["add", "double"] and result["solution_only_defs"] == ["_twice"]
    assert [s["newly_passing"] for s in result["steps"]] == [None, ["test_add"], ["test_double"]]
    f = result["flags"]
    assert f["pass_without_student_work"] == ["test_free"]  # a test that assesses nothing the student writes
    assert f["starter_pass_share"] == 1 / 3 and f["all_filled_pass_share"] == 1.0
    assert f["steps_unlocking_nothing"] == [] and f["largest_unlock_share"] == 1 / 3 and f["regressions"] == []


def test_a_starter_that_is_the_solution_passes_everything():
    f = scaffold.check(SOLUTION, SOLUTION, TESTS, "adder", timeout=60)["flags"]
    assert f["no_stubs"] and f["starter_pass_share"] == 1.0


def test_fill_replaces_only_the_named_stubs():
    code = scaffold.fill(STARTER, SOLUTION, ["add"])
    assert "return a + b" in code and code.count("NotImplementedError") == 1


def test_change_numbers_keeps_decimals_and_words():
    text = "Accuracy 87.5% on 2000 images with DINOv2, Week 3."
    changed = damage.change_numbers(text, random.Random(0))
    assert "DINOv2" in changed and changed != text
    acc = float(changed.split()[1].rstrip("%"))
    assert acc < 87.5 and changed.split()[1].count(".") == 1  # lower, one decimal kept


def test_hollow_tests_keep_every_test_but_check_nothing():
    source = (
        "import unittest\n"
        "def test_a():\n    x = 1\n    assert x == 2\n"
        "def test_b():\n    try:\n        f()\n        raise AssertionError('should raise')\n    except ValueError:\n        pass\n"
        "class T(unittest.TestCase):\n    def test_c(self):\n        self.assertEqual(1, 2)\n"
    )
    hollow = damage.hollow_tests(source)
    assert bloom.test_names(hollow) == bloom.test_names(source)
    assert "x == 2" not in hollow and "AssertionError" not in hollow and "assertEqual" not in hollow
    assert "x = 1" in hollow  # the code the test runs stays


def _deck(path, n):
    from pptx import Presentation
    prs = Presentation()
    for i in range(n):
        prs.slides.add_slide(prs.slide_layouts[5]).shapes.title.text = f"S{i}"
    prs.save(path)


def _titles(path):
    from pptx import Presentation
    return [s.shapes.title.text for s in Presentation(path).slides]


def test_slide_damage_keeps_title_and_takeaways(tmp_path):
    week = tmp_path / "Week_01" / "leaf"
    week.mkdir(parents=True)
    deck = str(week / "leaf_presentation.pptx")
    _deck(deck, 6)
    damage.shuffle_slides(str(week), random.Random(0))
    shuffled = _titles(deck)
    assert shuffled[0] == "S0" and shuffled[-1] == "S5" and sorted(shuffled) == _titles_sorted(6)
    assert shuffled != [f"S{i}" for i in range(6)]
    _deck(deck, 6)
    damage.drop_middle_half(str(week), random.Random(0))
    assert _titles(deck) == ["S0", "S1", "S4", "S5"]  # S2, S3: the central half of S1-S4


def _titles_sorted(n):
    return sorted(f"S{i}" for i in range(n))


def test_verdict_needs_a_move_beyond_the_original_noise():
    assert damage.verdict([4, 4], [3, 3], "down")["verdict"] == "caught"
    assert damage.verdict([3, 5], [3.5, 3.5], "down")["verdict"] == "missed"  # within the judge's own spread
    assert damage.verdict([4], [4], "not_up")["verdict"] == "caught"
    assert damage.verdict([4], [5], "not_up")["verdict"] == "missed"  # filler raised the score
    assert damage.verdict([], [3], "down")["verdict"] == "no data"
    report = [{"variant": "wrong_numbers", "metric": "m", "direction": "down", "verdict": v}
              for v in ("caught", "missed", "no data")]
    assert "| wrong_numbers | m | down | 1/2 (1 no data) |" in damage.summary_markdown(report)
