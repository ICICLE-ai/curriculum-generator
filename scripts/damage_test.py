#!/usr/bin/env python3
"""Damage test of the pedagogy evaluators on a finished run: scores damaged copies of its weeks next to unchanged
copies and reports which metrics caught which damage. Writes only <exercises>/evaluation/damage/.

    python scripts/damage_test.py --config configs/x.yaml --run-dir <output dir> [--weeks Week_01 Week_03]
        [--variants shuffle_slides wrong_numbers] [--repeat 2]

Cost: (variants + 1) full pedagogy evaluations per week, plus the TODO check (one sandbox run per stub) on the
original and give_away_solution copies. --repeat 2 or more is needed to tell damage from the judge's own noise.
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.config import load_config
from digitalagedu.core.eval.damage import VARIANTS, damage_run
from digitalagedu.core.llm.ai_setup import configure_model_slots, get_instructor_client


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--config", required=True, help="The run's YAML config (student level, models, endpoint)")
    parser.add_argument("--run-dir", help="The run's output directory (default: output.directory from the config)")
    parser.add_argument("--weeks", nargs="*", default=[], help="Only weeks whose folder path contains one of these")
    parser.add_argument("--variants", nargs="*", default=[], choices=[v for v in VARIANTS if v != "original"],
                        help="Damage to apply (default: all); the unchanged original is always scored")
    parser.add_argument("--repeat", type=int, default=2, help="Judge and learner runs per copy, for the noise estimate")
    parser.add_argument("--seed", type=int, default=0)
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
    damage_run(os.path.join(run_dir, "exercises"), run_dir, config, client, args.model or execution.llm_models.judge,
               weeks=args.weeks, variants=args.variants, repeat=args.repeat, seed=args.seed)


if __name__ == "__main__":
    main()
