#!/usr/bin/env python3
"""Pedagogy-eval pilot on a finished run (e.g. re-score runs 6319/2000). Log-only: writes <exercises>/evaluation/.

    python scripts/evaluate_curriculum.py --config configs/x.yaml --run-dir <output dir> [--repeat 2]
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.config import load_config
from digitalagedu.core.eval.run import evaluate_run
from digitalagedu.core.llm.ai_setup import configure_model_slots, get_instructor_client


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="The run's YAML config (student level, models, endpoint)")
    parser.add_argument("--run-dir", help="The run's output directory (default: output.directory from the config)")
    parser.add_argument("--repeat", type=int, default=1, help="Judge and learner runs per week, for stability")
    parser.add_argument("--budget-minutes", type=float, default=None, help="Stop starting new weeks after this")
    parser.add_argument("--model", help="Override execution.llm_models.judge")
    parser.add_argument("--from-run", help="A finished job's directory: its Phase 1 outputs and finished weeks are "
                                           "copied into the current directory first (the Tapis evaluation job)")
    args = parser.parse_args()

    config = load_config(args.config)
    run_dir = args.run_dir or config.output.directory
    if args.from_run:
        from run_pipeline import _check_refresh_token, stage_phase2_rerun
        _check_refresh_token()
        stage_phase2_rerun(args.from_run, run_dir, args.config, weeks="failed")  # "failed" keeps the finished weeks
    execution = config.execution
    configure_model_slots(dict(execution.llm_concurrency or {}))
    client = get_instructor_client(base_url=execution.llm_base_url)
    evaluate_run(os.path.join(run_dir, "exercises"), run_dir, config, client, args.model or execution.llm_models.judge,
                 budget_minutes=args.budget_minutes, repeat=args.repeat)


if __name__ == "__main__":
    main()
