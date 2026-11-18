#!/usr/bin/env python3
"""Replays the lesson plans that killed weeks (Week_XX/<module>/<module>_phase2.log says "Lesson planning failed")
under several repair strategies, to tell thinking budget, model weakness and bad specs apart. Read-only on the run
dirs: results go to --out (JSONL) and a summary table is printed.

    python scripts/replay_plan_failures.py --config <the job's yaml> --run-dir <job>/outputs/<name> [--run-dir ...]
        [--arms low_reask,high,fresh_low,other_model] [--other-model kimi] [--repeats 1] [--workers 4]

Arms (attempts = max_retries + 1 in instructor):
  low_reask   production before the fix: default effort, re-asked with the validator error, 4 attempts
  high        production fallback after the fix: reasoning_effort=high, 2 attempts
  fresh_low   restart policy: 4 independent single attempts at default effort, no re-ask
  other_model a different family (--other-model) at its default settings, 4 attempts
"""
import argparse
import glob
import json
import os
import re
import sys
import time
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.config import load_config
from digitalagedu.core.llm.ai_setup import configure_model_slots, get_instructor_client, llm_kwargs
from digitalagedu.core.llm.main import _build_modules
from digitalagedu.core.llm.week_builder import collect_deck_artifacts
from digitalagedu.core.llm.presentation_prompts import LESSON_PLANNER_SYSTEM, LessonPlan, build_lesson_plan_prompt
from digitalagedu.core.llm.schemas import ProblemStatementSchema
from digitalagedu.core.llm.telemetry import load_phase1_telemetry

ARMS = {  # name: (model override or None, effort, max_retries, independent tries)
    "low_reask": (None, None, 3, 1),
    "high": (None, "high", 1, 1),
    "fresh_low": (None, None, 0, 4),
    "other_model": ("OTHER", None, 3, 1),
}


def fatal_weeks(run_dir):
    """Module dirs whose week died in lesson planning."""
    found = []
    for log in sorted(glob.glob(os.path.join(run_dir, "exercises", "Week_*", "*", "*_phase2.log"))):
        with open(log, encoding="utf-8", errors="replace") as f:
            if "Lesson planning failed" in f.read():
                found.append(os.path.dirname(log))
    return found


def strip_docstring_header(text):
    """week_builder._write_code_file prepends a docstring; the planner saw the bare solution."""
    return re.sub(r'\A"""[\s\S]*?"""\s*', "", text, count=1)


def short_error(err):
    """The first validator message, without the pydantic input dump."""
    m = re.search(r"Value error, (.*?)(?: \[type=|$)", str(err), re.S)
    return (m.group(1) if m else str(err)).strip().splitlines()[0][:300]


def identical_repeats(errors):
    """How many attempts repeated the previous attempt's exact violation."""
    return sum(1 for a, b in zip(errors, errors[1:]) if a == b)


def load_inputs(module_dir, modules, telemetry, telemetry_dir):
    clean_id = os.path.basename(module_dir)
    versions = glob.glob(os.path.join(module_dir, "trace", "problem_formulation_v*.json"))
    newest = max(versions, key=lambda p: int(re.search(r"_v(\d+)\.json$", p).group(1)))
    with open(newest, encoding="utf-8") as f:
        formulation = ProblemStatementSchema.model_validate(json.load(f))
    with open(os.path.join(module_dir, f"{clean_id}_solution.py"), encoding="utf-8") as f:
        solution = strip_docstring_header(f.read())
    module = next(m for m in modules if m.id.replace("-", "_") == clean_id)
    return build_lesson_plan_prompt(module, formulation, solution, telemetry, collect_deck_artifacts(telemetry_dir, telemetry))


def run_arm(base_url, model, effort, max_retries, tries, prompt):
    """One arm on one week: success, attempts, per-attempt violations, time and tokens."""
    client = get_instructor_client(base_url=base_url)
    errors, usage = [], {"prompt": 0, "completion": 0}
    attempts = [0]
    client.on("completion:kwargs", lambda *a, **k: attempts.__setitem__(0, attempts[0] + 1))
    client.on("parse:error", lambda err: errors.append(short_error(err)))

    def count(resp):
        u = getattr(resp, "usage", None)
        usage["prompt"] += getattr(u, "prompt_tokens", 0) or 0
        usage["completion"] += getattr(u, "completion_tokens", 0) or 0
    client.on("completion:response", count)

    started, success, first_success = time.monotonic(), False, None
    for _ in range(tries):
        try:
            client.chat.completions.create(
                model=model, response_model=LessonPlan, max_retries=max_retries, max_tokens=65536,
                messages=[{"role": "system", "content": LESSON_PLANNER_SYSTEM}, {"role": "user", "content": prompt}],
                **llm_kwargs(model, effort))
            success, first_success = True, attempts[0]
            break
        except Exception as err:  # a validator that never passed, or a transport error
            if not errors or "Value error" not in str(err):
                errors.append(f"[{type(err).__name__}] {short_error(err)}")
    return {"success": success, "attempts": attempts[0], "first_success_attempt": first_success, "errors": errors,
            "identical_repeats": identical_repeats(errors), "seconds": round(time.monotonic() - started),
            "prompt_tokens": usage["prompt"], "completion_tokens": usage["completion"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", required=True)
    ap.add_argument("--run-dir", action="append", required=True, help="a job's output dir (holds exercises/); repeatable")
    ap.add_argument("--arms", default=",".join(ARMS))
    ap.add_argument("--other-model", default="kimi")
    ap.add_argument("--repeats", type=int, default=1)
    ap.add_argument("--workers", type=int, default=4)
    ap.add_argument("--out", default="replay_plan_failures.jsonl")
    ap.add_argument("--base-url", help="override execution.llm_base_url, e.g. https://ellm.nrp-nautilus.io/v1 "
                                       "(with NRP_LLM_API exported) to skip the Tapis-token proxy")
    args = ap.parse_args()

    cfg = load_config(args.config)
    ex = cfg.execution
    planner, base_url = ex.llm_models.planner, args.base_url or ex.llm_base_url
    if not (cfg.curriculum.modules or cfg.curriculum.topics):
        sys.exit("shortcut: only configs with explicit modules or topics are supported (syllabus-architect runs are not)")
    configure_model_slots(dict(ex.llm_concurrency or {}))

    tasks = []
    for run_dir in args.run_dir:
        telemetry = load_phase1_telemetry(run_dir)
        modules = _build_modules(cfg, telemetry, None, None, os.path.join(run_dir, "exercises"))
        for module_dir in fatal_weeks(run_dir):
            prompt = load_inputs(module_dir, modules, telemetry, run_dir)
            for arm in args.arms.split(","):
                model, effort, retries, tries = ARMS[arm]
                model = args.other_model if model == "OTHER" else planner
                for rep in range(args.repeats):
                    tasks.append(({"run_dir": run_dir, "module": os.path.basename(module_dir), "arm": arm, "model": model,
                                   "effort": effort or "default", "repeat": rep}, (base_url, model, effort, retries, tries, prompt)))
    print(f"{len(tasks)} replays ({len({(t[0]['run_dir'], t[0]['module']) for t in tasks})} fatal weeks) -> {args.out}")

    def work(task):
        meta, call = task
        result = {**meta, **run_arm(*call)}
        with open(args.out, "a", encoding="utf-8") as f:
            f.write(json.dumps(result) + "\n")
        print(f"{meta['module'][:28]:28} {meta['arm']:11} ok={result['success']!s:5} attempts={result['attempts']} "
              f"repeats={result['identical_repeats']} {result['seconds']}s", flush=True)
        return result

    with ThreadPoolExecutor(args.workers) as pool:
        results = list(pool.map(work, tasks))

    print("\narm          success  mean attempts  mean s  identical repeats")
    for arm in args.arms.split(","):
        rs = [r for r in results if r["arm"] == arm]
        if rs:
            print(f"{arm:12} {sum(r['success'] for r in rs):3}/{len(rs):<3}  {sum(r['attempts'] for r in rs) / len(rs):13.1f}"
                  f"  {sum(r['seconds'] for r in rs) / len(rs):6.0f}  {sum(r['identical_repeats'] for r in rs):17}")


if __name__ == "__main__":
    main()
