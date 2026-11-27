"""Damage test: do the pedagogy evaluators measure what they claim? Makes damaged copies of finished weeks, scores
each next to an unchanged copy of the same week (same quiz), and reports whether each metric moved the way it should.
A metric that doesn't drop when a week is made worse can't be trusted to rank real weeks.

Writes only under <exercises>/evaluation/damage/: the damaged copies, their scores, damage_report.csv and .md."""
import ast
import csv
import glob
import json
import os
import random
import re
import shutil
from collections import defaultdict
from typing import Any, Dict, List, Optional, Sequence

from digitalagedu.core.eval import judge, sim_learner
from digitalagedu.core.eval.load import _read, list_finished_weeks, load_week, module_file
from digitalagedu.core.eval.run import _Log, _csv_rows, evaluate_week
from digitalagedu.core.llm.telemetry import build_telemetry_prompt_summary, load_phase1_telemetry
from digitalagedu.core.writer import write_file

RUBRIC_DIMS = [d["id"] for d in judge.load_rubric()]


# ---- the damage --------------------------------------------------------------------------------------------------


def shuffle_slides(module_dir: str, rng: random.Random) -> None:
    """Shuffles every slide between the title and the takeaways (a different order guaranteed when there are 2+)."""
    from pptx import Presentation
    deck = module_file(module_dir, "presentation.pptx")
    prs = Presentation(deck)
    ids = prs.slides._sldIdLst
    items = list(ids)
    middle = items[1:-1]
    order = middle[:]
    while len(middle) > 1 and order == middle:
        rng.shuffle(order)
    for sid in middle:
        ids.remove(sid)
    for sid in order:
        ids.insert(len(ids) - 1, sid)  # before the takeaways slide, which is still last
    prs.save(deck)


def drop_middle_half(module_dir: str, rng: random.Random) -> None:
    """Deletes the central half of the slides between the title and the takeaways: the method, in a lesson-plan deck."""
    from pptx import Presentation
    deck = module_file(module_dir, "presentation.pptx")
    prs = Presentation(deck)
    ids = prs.slides._sldIdLst
    middle = list(ids)[1:-1]
    k = len(middle) // 2
    start = (len(middle) - k) // 2
    for sid in middle[start:start + k]:
        ids.remove(sid)
        prs.part.drop_rel(sid.rId)
    prs.save(deck)


_NUMBER = re.compile(r"(?<![\w.])(\d+(?:\.\d+)?)(?![\w])")


def change_numbers(text: str, rng: random.Random) -> str:
    """Every standalone number scaled down by 20-50%, keeping its decimals (so percentages stay under 100);
    digits inside words (DINOv2, ViT-B16) are left alone."""
    def swap(match):
        old = match.group(1)
        decimals = len(old.split(".")[1]) if "." in old else 0
        new = round(float(old) * rng.uniform(0.5, 0.8), decimals)
        if new == float(old):
            new = float(old) + 1
        return f"{new:.{decimals}f}"
    return _NUMBER.sub(swap, text)


def _text_frames(shapes):
    for shape in shapes:
        if getattr(shape, "shapes", None) is not None:  # group
            yield from _text_frames(shape.shapes)
        if getattr(shape, "has_text_frame", False) and shape.has_text_frame:
            yield shape.text_frame
        if getattr(shape, "has_table", False) and shape.has_table:
            yield from (cell.text_frame for row in shape.table.rows for cell in row.cells)


def wrong_numbers(module_dir: str, rng: random.Random) -> None:
    """Changes the numbers in the slides' text and the overview, so they no longer match the run.
    shortcut: numbers drawn inside chart images stay right; a judge reading only the charts won't see the damage."""
    from pptx import Presentation
    deck = module_file(module_dir, "presentation.pptx")
    prs = Presentation(deck)
    for slide in prs.slides:
        for frame in _text_frames(slide.shapes):
            for paragraph in frame.paragraphs:
                for run in paragraph.runs:
                    run.text = change_numbers(run.text, rng)
    prs.save(deck)
    overview = module_file(module_dir, "overview.md")
    text = _read(overview)
    write_file(overview, lambda f: f.write(change_numbers(text, rng)))


class _Hollow(ast.NodeTransformer):
    """Keeps every test and the code it runs, but removes what it checks."""

    def visit_Assert(self, node):
        return ast.copy_location(ast.Assert(test=ast.Constant(True)), node)

    def visit_Expr(self, node):  # self.assertEqual(...), np.testing.assert_allclose(...)
        call = node.value
        if isinstance(call, ast.Call) and isinstance(call.func, ast.Attribute) and call.func.attr.startswith("assert"):
            return ast.copy_location(ast.Pass(), node)
        return node

    def visit_Raise(self, node):  # raise AssertionError(...) in try/except checks
        exc = node.exc.func if isinstance(node.exc, ast.Call) else node.exc
        return ast.copy_location(ast.Pass(), node) if getattr(exc, "id", None) == "AssertionError" else node


def hollow_tests(source: str) -> str:
    return ast.unparse(ast.fix_missing_locations(_Hollow().visit(ast.parse(source))))


def hollow_test_file(module_dir: str, rng: random.Random) -> None:
    path = module_file(module_dir, "test.py")
    source = _read(path)
    write_file(path, lambda f: f.write(hollow_tests(source)))


def give_away_solution(module_dir: str, rng: random.Random) -> None:
    """The starter becomes the full solution: no student work left."""
    shutil.copyfile(module_file(module_dir, "solution.py"), module_file(module_dir, "exercise.py"))


_FILLER = [
    "Artificial intelligence is an important and rapidly growing field with many applications.",
    "Working carefully and checking your results is always a good habit in any project.",
    "Data can come in many forms, and understanding it is an essential first step.",
    "Many professionals use these techniques every day to solve real-world problems.",
    "Learning new skills takes practice, patience and a willingness to make mistakes.",
]


def filler_overview(module_dir: str, rng: random.Random) -> None:
    """Doubles the overview's length with content-free sentences: scores should not rise."""
    path = module_file(module_dir, "overview.md")
    text = _read(path)
    padding, i = [], 0
    while sum(len(s) + 1 for s in padding) < len(text):
        padding.append(_FILLER[i % len(_FILLER)])
        i += 1
    write_file(path, lambda f: f.write(text + "\n\n## Additional Context\n\n" + " ".join(padding) + "\n"))


# What each damage should do: "down" must fall, "up" must rise, "not_up" must not rise
VARIANTS: Dict[str, tuple] = {
    "original": (None, []),  # unchanged copy: the baseline, scored the same way
    "shuffle_slides": (shuffle_slides, [("rubric.revision_effort", "down")]),
    "drop_middle_half": (drop_middle_half, [("rubric.revision_effort", "down"), ("sim.overall.post", "down"),
                                            ("sim.run_data.post", "down")]),
    "wrong_numbers": (wrong_numbers, [("rubric.real_data_use", "down"), ("rubric.technical_accuracy", "down"),
                                      ("sim.run_data.post", "down")]),
    # Hollow tests still call the stubs, which raise NotImplementedError, so the TODO check can't see this one
    "hollow_tests": (hollow_test_file, [("rubric.objective_assessment_alignment", "down"), ("bloom.coverage", "down")]),
    "give_away_solution": (give_away_solution, [("scaffold.starter_pass_share", "up"), ("scaffold.stubs", "down")]),
    "filler_overview": (filler_overview, [("text_chars", "up")] + [(f"rubric.{d}", "not_up") for d in RUBRIC_DIMS]),
}
SCAFFOLD_VARIANTS = {"original", "give_away_solution"}  # the TODO check is slow, and the other damage leaves the code alone


# ---- scoring and comparison --------------------------------------------------------------------------------------

def damaged_copy(module_dir: str, dest_root: str, variant: str, seed: int = 0) -> str:
    """A copy of the week as the evaluators read it (Agent 0's contracts kept, other trace files left out), damaged."""
    rel = os.path.join(os.path.basename(os.path.dirname(module_dir)), os.path.basename(module_dir))
    dest = os.path.join(dest_root, variant, rel)
    shutil.rmtree(dest, ignore_errors=True)
    shutil.copytree(module_dir, dest, ignore=shutil.ignore_patterns("trace", "*_phase2.log"))
    os.makedirs(os.path.join(dest, "trace"), exist_ok=True)
    for contract in glob.glob(os.path.join(module_dir, "trace", "problem_formulation_v*.json")):
        shutil.copy2(contract, os.path.join(dest, "trace"))
    damage = VARIANTS[variant][0]
    if damage:
        damage(dest, random.Random(f"{seed}:{variant}:{os.path.basename(module_dir)}"))
    return dest


def metric_values(rows: List[Dict[str, Any]]) -> Dict[str, List[float]]:
    values: Dict[str, List[float]] = defaultdict(list)
    for row in rows:
        if isinstance(row["value"], (int, float)):
            values[row["metric"]].append(float(row["value"]))
    return values


def verdict(original: List[float], damaged: List[float], direction: str) -> Dict[str, Any]:
    """Whether the metric moved as `direction` says. With repeats, a move must exceed the spread of the original's
    own repeats (its noise); with one run, any move in the right direction counts."""
    if not original or not damaged:
        return {"verdict": "no data"}
    before, after = sum(original) / len(original), sum(damaged) / len(damaged)
    noise = max(original) - min(original)
    delta = after - before
    caught = {"down": delta < -noise, "up": delta > noise, "not_up": delta <= noise}[direction]
    return {"original": round(before, 3), "damaged": round(after, 3), "delta": round(delta, 3),
            "noise": round(noise, 3), "verdict": "caught" if caught else "missed"}


def damage_run(exercises_dir: str, telemetry_dir: Optional[str], root_config: Any, client, model: str,
               weeks: Sequence[str] = (), variants: Sequence[str] = (), repeat: int = 1, seed: int = 0) -> str:
    """Scores the original and damaged copies of each finished week (all, or those whose folder path contains one of
    `weeks`); returns the damage dir."""
    out = os.path.join(exercises_dir, "evaluation", "damage")
    os.makedirs(out, exist_ok=True)
    log = _Log(os.path.join(out, "damage.log"))
    variants = ["original"] + [v for v in (variants or VARIANTS) if v != "original"]
    unknown = [v for v in variants if v not in VARIANTS]
    if unknown:
        raise ValueError(f"Unknown damage variant(s) {unknown}; choose from {list(VARIANTS)}")
    run_facts = build_telemetry_prompt_summary(load_phase1_telemetry(telemetry_dir) if telemetry_dir else {})
    level, rubric = root_config.curriculum.level, judge.load_rubric()
    fixtures = [telemetry_dir] if telemetry_dir else []
    chosen = [d for d in list_finished_weeks(exercises_dir) if not weeks or any(w in d for w in weeks)]
    log(f"Damage test on {len(chosen)} week(s), variants {variants}, repeat={repeat}, judge {model}")

    report: List[Dict[str, Any]] = []
    for module_dir in chosen:
        name = os.path.basename(module_dir)
        try:
            quiz = sim_learner.write_quiz(client, model, load_week(module_dir), run_facts, level)
        except Exception as err:  # each copy then writes its own quiz: noisier, but still comparable
            log(f"{name}: shared quiz failed ({err!r}); each copy writes its own")
            quiz = None
        scores: Dict[str, Dict[str, List[float]]] = {}
        for variant in variants:
            try:
                copy = damaged_copy(module_dir, out, variant, seed)
                rec = evaluate_week(copy, os.path.join(out, variant), client, model, run_facts, level, rubric, repeat,
                                    log, fixtures, quiz=quiz, run_scaffold=variant in SCAFFOLD_VARIANTS)
                write_file(os.path.join(out, variant, f"{name}_evaluation.json"), lambda f: json.dump(rec, f, indent=2))
                scores[variant] = metric_values(_csv_rows(rec))
            except Exception as err:  # one failed copy never stops the others
                log(f"{name} {variant}: failed: {err!r}")
        for variant in variants[1:]:
            for metric, direction in VARIANTS[variant][1]:
                v = verdict(scores.get("original", {}).get(metric, []), scores.get(variant, {}).get(metric, []),
                            direction)
                report.append({"week": name, "variant": variant, "metric": metric, "direction": direction, **v})
                log(f"{name} {variant} {metric} ({direction}): {v['verdict']}"
                    + (f", {v['original']} -> {v['damaged']} (noise {v['noise']})" if "delta" in v else ""))

    def fill(f):
        writer = csv.DictWriter(f, fieldnames=["week", "variant", "metric", "direction", "original", "damaged",
                                               "delta", "noise", "verdict"])
        writer.writeheader()
        writer.writerows(report)
    write_file(os.path.join(out, "damage_report.csv"), fill, newline="")
    write_file(os.path.join(out, "damage_report.md"), lambda f: f.write(summary_markdown(report)))
    log(f"Done -> {out}")
    return out


def summary_markdown(report: List[Dict[str, Any]]) -> str:
    """Caught / weeks with data, per damage and metric."""
    tally: Dict[tuple, List[str]] = defaultdict(list)
    for row in report:
        tally[(row["variant"], row["metric"], row["direction"])].append(row["verdict"])
    lines = ["# Damage test", "", "A metric should catch each damage aimed at it. `noise` in the CSV is the spread of "
             "the original's own repeats; run with --repeat 2 or more for it to mean anything.", "",
             "| Damage | Metric | Should | Caught |", "|---|---|---|---|"]
    for (variant, metric, direction), verdicts in sorted(tally.items()):
        judged = [v for v in verdicts if v != "no data"]
        lines.append(f"| {variant} | {metric} | {direction.replace('_', ' ')} | "
                     f"{sum(v == 'caught' for v in judged)}/{len(judged)}"
                     + (f" ({len(verdicts) - len(judged)} no data)" if len(judged) < len(verdicts) else "") + " |")
    return "\n".join(lines) + "\n"
