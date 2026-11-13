#!/usr/bin/env python3
"""Expert-panel tooling for the pedagogy-eval pilot (for later, once humans rate).

    export: blank rating sheet (CSV) + rubric (markdown) for every finished week of a run
        python scripts/rating_packet.py export --run-dir <output dir> --out <dir>
    agree: judge vs expert agreement per rubric dimension, from a filled sheet
        python scripts/rating_packet.py agree --run-dir <output dir> --human <filled sheet.csv>
"""
import argparse
import csv
import json
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from digitalagedu.core.eval.judge import load_rubric
from digitalagedu.core.eval.load import list_finished_weeks

SHEET_FIELDS = ["rater", "week_dir", "module_id", "dimension", "score", "evidence"]


def export(run_dir: str, out: str) -> None:
    rubric = load_rubric()
    os.makedirs(out, exist_ok=True)
    with open(os.path.join(out, "rubric.md"), "w", encoding="utf-8") as f:
        f.write("# Rating rubric (score 1-5 on each dimension)\n\n")
        for d in rubric:
            f.write(f"## {d['id']}\n{d['question']}\n\n" + "".join(f"- **{k}**: {v}\n" for k, v in d["anchors"].items()) + "\n")
    with open(os.path.join(out, "rating_sheet.csv"), "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=SHEET_FIELDS)
        writer.writeheader()
        for module_dir in list_finished_weeks(os.path.join(run_dir, "exercises")):
            for d in rubric:
                writer.writerow({"week_dir": os.path.basename(os.path.dirname(module_dir)),
                                 "module_id": os.path.basename(module_dir), "dimension": d["id"]})
    print(f"Wrote {out}/rubric.md and {out}/rating_sheet.csv")


def agreement(pairs):
    """{dimension: {n, kappa_quadratic, spearman}} from {dimension: [(human, judge), ...]}."""
    from scipy.stats import spearmanr
    from sklearn.metrics import cohen_kappa_score
    result = {}
    for dim, xs in pairs.items():
        human, model = [h for h, _ in xs], [m for _, m in xs]
        enough = len(xs) >= 2 and len(set(human)) > 1 and len(set(model)) > 1
        result[dim] = {"n": len(xs),
                       "kappa_quadratic": cohen_kappa_score(human, model, weights="quadratic", labels=[1, 2, 3, 4, 5]) if enough else None,
                       "spearman": spearmanr(human, model).statistic if enough else None}
    return result


def agree(run_dir: str, human_csv: str) -> None:
    judged = {}
    eval_dir = os.path.join(run_dir, "exercises", "evaluation")
    for name in os.listdir(eval_dir):
        if name.endswith("_evaluation.json"):
            with open(os.path.join(eval_dir, name), encoding="utf-8") as f:
                rec = json.load(f)
            first = next((j for j in rec.get("judge") or [] if j.get("scores")), None)  # repeat 0 is the judge's score
            if first:
                for dim, s in first["scores"].items():
                    judged[(rec["module_id"], dim)] = s["score"]
    pairs = defaultdict(list)
    with open(human_csv, encoding="utf-8") as f:
        for row in csv.DictReader(f):
            key = (row["module_id"], row["dimension"])
            if row.get("score") and key in judged:
                pairs[row["dimension"]].append((int(row["score"]), judged[key]))
    print(json.dumps(agreement(pairs), indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=["export", "agree"])
    parser.add_argument("--run-dir", required=True)
    parser.add_argument("--out", default="rating_packet")
    parser.add_argument("--human")
    args = parser.parse_args()
    export(args.run_dir, args.out) if args.command == "export" else agree(args.run_dir, args.human)
