"""Runs the pilot evaluators over every finished week and writes exercises/evaluation/. Never raises per week."""
import csv
import json
import os
import time
import traceback
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from digitalagedu.core.eval import bloom, judge, sim_learner
from digitalagedu.core.eval.load import list_finished_weeks, load_week, render_slides
from digitalagedu.core.llm.telemetry import build_telemetry_prompt_summary, load_phase1_telemetry
from digitalagedu.core.writer import write_file


class _Log:
    """Prints and appends to evaluation.log."""
    def __init__(self, path: str):
        self.path = path

    def __call__(self, msg: str) -> None:
        line = f"[Pedagogy Eval {datetime.now(timezone.utc).strftime('%H:%M:%S')}] {msg}"
        print(line, flush=True)
        with open(self.path, "a", encoding="utf-8") as f:
            f.write(line + "\n")


def _timed(record: Dict[str, Any], key: str, fn, log):
    """record[key] = fn(), or {'error': ...}; the time each part took goes in record['seconds']."""
    started = time.monotonic()
    try:
        record[key] = fn()
    except Exception as err:
        log(f"{key} failed: {err!r}")
        record[key] = {"error": repr(err), "traceback": traceback.format_exc()[-2000:]}
    record.setdefault("seconds", {})[key] = round(time.monotonic() - started, 1)


def _csv_rows(rec: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Flat week x metric rows for evaluation_summary.csv."""
    base = {"week": rec["week"], "module_id": rec["module_id"]}
    rows = []
    add = lambda metric, value, repeat=0: rows.append({**base, "metric": metric, "value": value, "repeat": repeat})
    for r, j in enumerate(rec.get("judge") or []):
        for dim, s in (j.get("scores") or {}).items():
            add(f"rubric.{dim}", s["score"], r)
    flags = (rec.get("bloom") or {}).get("flags") or {}
    if flags:
        add("bloom.coverage", flags["coverage"])
        for k in ("untested_objectives", "untestable_by_unit_test", "low_level_tests_only", "level_mismatch"):
            add(f"bloom.{k}", len(flags[k]))
    for r, s in enumerate(rec.get("sim_learner") or []):
        if "overall" in s:
            for kind, summ in [("overall", s["overall"])] + list(s["by_kind"].items()):
                add(f"sim.{kind}.pre", summ["pre"], r)
                add(f"sim.{kind}.post", summ["post"], r)
                add(f"sim.{kind}.gain", summ["gain"], r)
    add("text_chars", rec.get("text_chars"))  # guard: do scores just track length?
    return rows


def evaluate_week(module_dir: str, out_dir: str, client, model: str, run_facts: str, student_level: str,
                  rubric, repeat: int, log) -> Dict[str, Any]:
    bundle = load_week(module_dir)
    rec: Dict[str, Any] = {"module_id": bundle.module_id, "week": bundle.week, "model": model,
                           "student_level": student_level, "objectives": bundle.objectives}
    slide_dir = os.path.join(out_dir, f"Week_{bundle.week:02d}_{bundle.module_id}_slides")
    _timed(rec, "slides", lambda: dict(zip(("pngs", "texts"), render_slides(bundle.deck_path, slide_dir))), log)
    pngs = (rec["slides"] or {}).get("pngs") or []
    texts = (rec["slides"] or {}).get("texts") or []
    rec["judged_without_images"] = not pngs
    rec["text_chars"] = len(bundle.overview) + len(bundle.exercise) + sum(len(t) for t in texts)
    log(f"Week {bundle.week} {bundle.module_id}: {len(pngs)} slide images, {len(bundle.objectives)} objectives")

    _timed(rec, "bloom", lambda: bloom.evaluate(client, model, bundle.objectives, bundle.tests, student_level), log)
    rec["judge"] = []
    rec["sim_learner"] = []
    quiz: Optional[Any] = None
    try:
        quiz = sim_learner.write_quiz(client, model, bundle, run_facts, student_level)
        rec["quiz"] = quiz.model_dump()
    except Exception as err:
        log(f"quiz writing failed: {err!r}")
        rec["quiz"] = {"error": repr(err)}
    for r in range(repeat):
        holder: Dict[str, Any] = {}
        _timed(holder, "judge", lambda: judge.score_week(client, model, bundle, pngs, texts, run_facts,
                                                          student_level, rubric), log)
        rec["judge"].append(holder["judge"])
        if quiz is not None:
            def sim():
                pre = sim_learner.take_quiz(client, model, quiz, student_level)
                post = sim_learner.take_quiz(client, model, quiz, student_level, pngs, None if pngs else texts)
                return {**sim_learner.score(quiz, pre, post), "pre_answers": pre, "post_answers": post}
            _timed(holder, "sim_learner", sim, log)
            rec["sim_learner"].append(holder["sim_learner"])
        rec.setdefault("seconds", {})[f"repeat_{r}"] = holder.get("seconds")
    return rec


def evaluate_run(exercises_dir: str, telemetry_dir: Optional[str], root_config: Any, client, model: str,
                 budget_minutes: Optional[float] = None, repeat: int = 1) -> str:
    """Scores every finished week; returns the evaluation dir. Writes only under <exercises_dir>/evaluation/."""
    out_dir = os.path.join(exercises_dir, "evaluation")
    os.makedirs(out_dir, exist_ok=True)
    log = _Log(os.path.join(out_dir, "evaluation.log"))
    run_facts = build_telemetry_prompt_summary(load_phase1_telemetry(telemetry_dir) if telemetry_dir else {})
    student_level = root_config.curriculum.level
    rubric = judge.load_rubric()
    weeks = list_finished_weeks(exercises_dir)
    log(f"Scoring {len(weeks)} finished week(s) with {model}, repeat={repeat}, budget={budget_minutes or 'none'} min")

    started, rows = time.monotonic(), []
    for module_dir in weeks:
        name = os.path.basename(module_dir)
        week_tag = os.path.basename(os.path.dirname(module_dir))
        path = os.path.join(out_dir, f"{week_tag}_{name}_evaluation.json")
        if budget_minutes and (time.monotonic() - started) / 60 > budget_minutes:
            rec = {"module_id": name, "status": "skipped_budget"}
            log(f"{name}: skipped, {budget_minutes} min budget used up")
        else:
            try:
                rec = {"status": "ok", **evaluate_week(module_dir, out_dir, client, model, run_facts, student_level,
                                                        rubric, repeat, log)}
                rows += _csv_rows(rec)
            except Exception as err:  # one bad week never stops the others
                log(f"{name}: failed: {err!r}")
                rec = {"module_id": name, "status": "error", "error": repr(err), "traceback": traceback.format_exc()[-2000:]}
        write_file(path, lambda f: json.dump(rec, f, indent=2))

    def fill(f):
        writer = csv.DictWriter(f, fieldnames=["week", "module_id", "metric", "value", "repeat"])
        writer.writeheader()
        writer.writerows(rows)
    write_file(os.path.join(out_dir, "evaluation_summary.csv"), fill, newline="")
    log(f"Done in {(time.monotonic() - started) / 60:.1f} min -> {out_dir}")
    return out_dir
