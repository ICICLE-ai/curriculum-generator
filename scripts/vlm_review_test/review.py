#!/usr/bin/env python3
"""Reviews the manifest's slide screenshots with a local vision model (vLLM, OpenAI-compatible) using the production
slide-review prompt and schema, and compares each verdict with deepseek-v4-flash's from the original run.

    python scripts/vlm_review_test/review.py --base-url http://localhost:8011/v1 --model Qwen/Qwen3-VL-8B-Instruct \
        --shots-root <job dir holding tmp/slide_review> --out vlm_review_test

Writes <out>/results.json (every verdict) and <out>/summary.md (agreement, speed, side-by-side issues).
"""
import argparse
import json
import os
import statistics
import sys
import time
from typing import Any, Dict, List

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import instructor
from openai import OpenAI

from digitalagedu.core.llm.ai_setup import image_url
from digitalagedu.core.llm.presentation_prompts import SlideReview, build_slide_review_messages

HERE = os.path.dirname(os.path.abspath(__file__))


def review(client, model: str, item: Dict[str, Any], shot_path: str) -> Dict[str, Any]:
    """One production-style review (no earlier slides attached; deepseek saw up to 3)."""
    started = time.monotonic()
    try:
        verdict, completion = client.chat.completions.create_with_completion(
            model=model, response_model=SlideReview, max_retries=1, max_tokens=4096, temperature=0,
            messages=build_slide_review_messages(item["label"], item["focus"], image_url(shot_path), []),
        )
        usage = getattr(completion, "usage", None)
        return {"issues": [i for i in verdict.issues if i.strip()], "polish": verdict.polish,
                "seconds": round(time.monotonic() - started, 1),
                "completion_tokens": getattr(usage, "completion_tokens", None)}
    except Exception as err:  # one bad reply never stops the test
        return {"error": repr(err)[:500], "seconds": round(time.monotonic() - started, 1)}


def summarize(results: List[Dict[str, Any]], model: str) -> str:
    """Accept/reject agreement with deepseek, speed, and every slide's issues side by side."""
    ok = [r for r in results if "error" not in r["local"]]
    pairs = [(not r["deepseek_issues"], not r["local"]["issues"]) for r in ok]
    both_accept = sum(d and l for d, l in pairs)
    both_reject = sum(not d and not l for d, l in pairs)
    only_deepseek_rejects = sum(l and not d for d, l in pairs)
    only_local_rejects = sum(d and not l for d, l in pairs)
    local_s = [r["local"]["seconds"] for r in ok]
    deep_s = [r["deepseek_seconds"] for r in results]
    med = lambda xs: round(statistics.median(xs), 1) if xs else None
    lines = [
        f"# Local slide review vs deepseek-v4-flash", "",
        f"Model: `{model}`. Slides: {len(results)}, replies: {len(ok)}, errors: {len(results) - len(ok)}.", "",
        "| | deepseek accepts | deepseek rejects |", "|---|---|---|",
        f"| **local accepts** | {both_accept} | {only_deepseek_rejects} |",
        f"| **local rejects** | {only_local_rejects} | {both_reject} |", "",
        f"Agreement: {round(100 * (both_accept + both_reject) / len(pairs)) if pairs else 0}% "
        f"({both_accept + both_reject}/{len(pairs)}).", "",
        f"Seconds per review, median: local {med(local_s)}, deepseek {med(deep_s)} "
        "(deepseek's time includes NRP queueing).", "",
        f"Issues per slide, mean: local {round(statistics.mean(len(r['local']['issues']) for r in ok), 2) if ok else None}, "
        f"deepseek {round(statistics.mean(len(r['deepseek_issues']) for r in results), 2)}.", "",
        "Agreement on accept/reject is not enough on its own: read the side-by-side issues below and check them "
        "against the screenshots (outputs/vlm_review_test/shots/<id>.png on the machine that downloaded them).", "",
    ]
    for r in results:
        lines += [f"## {r['id']}", f"{r['label']}", "", "**deepseek:**"]
        lines += [f"- {i}" for i in r["deepseek_issues"]] or ["- (accepted)"]
        lines += ["", f"**local** ({r['local'].get('seconds')} s):"]
        if "error" in r["local"]:
            lines.append(f"- ERROR: {r['local']['error']}")
        else:
            lines += [f"- {i}" for i in r["local"]["issues"]] or ["- (accepted)"]
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--manifest", default=os.path.join(HERE, "manifest.json"))
    p.add_argument("--shots-root", help="Directory holding the manifest's tmp/slide_review paths "
                                        "(default: the manifest's source_job_dir)")
    p.add_argument("--out", default="vlm_review_test")
    args = p.parse_args()

    manifest = json.load(open(args.manifest, encoding="utf-8"))
    root = args.shots_root or manifest["source_job_dir"]
    client = instructor.from_openai(OpenAI(base_url=args.base_url, api_key="local", timeout=600),
                                    mode=instructor.Mode.JSON_SCHEMA)
    os.makedirs(args.out, exist_ok=True)
    results = []
    for n, item in enumerate(manifest["items"], 1):
        local = review(client, args.model, item, os.path.join(root, item["shot"]))
        results.append({**item, "local": local})
        status = local.get("error") or ("accepted" if not local["issues"] else f"{len(local['issues'])} issues")
        print(f"[{n}/{len(manifest['items'])}] {item['id']}: {status} in {local['seconds']} s "
              f"(deepseek: {len(item['deepseek_issues']) or 'accepted'})", flush=True)
        with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as f:
            json.dump({"model": args.model, "results": results}, f, indent=1)  # rewritten each slide: survives a kill
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summarize(results, args.model))
    print(f"Done -> {args.out}/summary.md")


if __name__ == "__main__":
    main()
