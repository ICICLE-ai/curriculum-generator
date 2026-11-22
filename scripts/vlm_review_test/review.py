#!/usr/bin/env python3
"""Reviews the manifest's slide screenshots with a local vision model (vLLM, OpenAI-compatible) using the production
slide-review prompt and schema, and again with a strict layout checklist added (STRICT_SYSTEM), and compares each verdict with deepseek-v4-flash's from the original run.

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
from concurrent.futures import ThreadPoolExecutor
from typing import Any, Dict, List, Sequence

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

import instructor
from openai import OpenAI

from digitalagedu.core.llm.ai_setup import image_url
from digitalagedu.core.llm.presentation_prompts import SLIDE_REVIEW_SYSTEM, SlideReview, build_slide_review_messages

HERE = os.path.dirname(os.path.abspath(__file__))

# Run 1 (job ebcb8d5c): with the production prompt Qwen3-VL-8B saw the problems deepseek flagged but filed every one
# under `polish` and accepted all 45 slides. This checklist makes layout problems blocking by rule, not by judgment.
STRICT_SYSTEM = SLIDE_REVIEW_SYSTEM + """

Before answering, check the screenshot against each of these. Any one that is true is an ISSUE, never polish:
1. Text is cut off, clipped, or ends mid-word (for example a label ending in '...' or a half-visible line).
2. Text does not fit inside its box or card: it touches or crosses the box's edge.
3. Two boxes, cards, images or text blocks overlap or touch each other.
4. Anything runs off the edge of the slide, or sits partly outside it.
5. A box, band or heading is empty, or is a label with no content under it.
6. Text is too small to read when the slide is projected.
7. A term, column name or symbol on the slide is not explained anywhere on the slide.
Report each one you find in `issues` as a fix naming the element. A slide where none is true may still have polish.
Give at most 3 polish items."""

VARIANTS = {"local": SLIDE_REVIEW_SYSTEM, "strict": STRICT_SYSTEM}  # result key -> system prompt


def earlier_shots(items: List[Dict[str, Any]], n: int) -> List[str]:
    """Up to 3 earlier slides shown with item n, as production shows the deck's last 3 accepted slides.
    shortcut: picks from the manifest's sampled slides that deepseek accepted, not the full deck's accepted slides;
    exact only if the manifest records each deck's accepted shots."""
    week = items[n]["week"]
    return [i["shot"] for i in items[:n] if i["week"] == week and not i["deepseek_issues"]][-3:]


def review(client, model: str, item: Dict[str, Any], shot_path: str, system: str = SLIDE_REVIEW_SYSTEM,
           earlier: Sequence[str] = ()) -> Dict[str, Any]:
    """One production-style review of `shot_path` next to the `earlier` slide paths, with `system` as the prompt."""
    started = time.monotonic()
    messages = build_slide_review_messages(item["label"], item["focus"], image_url(shot_path),
                                           [image_url(p) for p in earlier])
    messages[0]["content"] = system
    try:
        verdict, completion = client.chat.completions.create_with_completion(
            model=model, response_model=SlideReview, max_retries=1, max_tokens=4096, temperature=0,
            messages=messages,
        )
        usage = getattr(completion, "usage", None)
        return {"issues": [i for i in verdict.issues if i.strip()], "polish": verdict.polish,
                "seconds": round(time.monotonic() - started, 1),
                "completion_tokens": getattr(usage, "completion_tokens", None)}
    except Exception as err:  # one bad reply never stops the test
        return {"error": repr(err)[:500], "seconds": round(time.monotonic() - started, 1)}


def agreement(results: List[Dict[str, Any]], key: str, model: str, title: str) -> List[str]:
    """Accept/reject agreement with deepseek and speed for one prompt variant."""
    ok = [r for r in results if "error" not in r[key]]
    pairs = [(not r["deepseek_issues"], not r[key]["issues"]) for r in ok]
    both_accept = sum(d and l for d, l in pairs)
    both_reject = sum(not d and not l for d, l in pairs)
    only_deepseek_rejects = sum(l and not d for d, l in pairs)
    only_local_rejects = sum(d and not l for d, l in pairs)
    local_s = [r[key]["seconds"] for r in ok]
    deep_s = [r["deepseek_seconds"] for r in results]
    med = lambda xs: round(statistics.median(xs), 1) if xs else None
    return [
        f"## {title}", "",
        f"Model: `{model}`. Slides: {len(results)}, replies: {len(ok)}, errors: {len(results) - len(ok)}.", "",
        "| | deepseek accepts | deepseek rejects |", "|---|---|---|",
        f"| **local accepts** | {both_accept} | {only_deepseek_rejects} |",
        f"| **local rejects** | {only_local_rejects} | {both_reject} |", "",
        f"Agreement: {round(100 * (both_accept + both_reject) / len(pairs)) if pairs else 0}% "
        f"({both_accept + both_reject}/{len(pairs)}).", "",
        f"Seconds per review, median: local {med(local_s)}, deepseek {med(deep_s)} "
        "(deepseek's time includes NRP queueing).", "",
        f"Issues per slide, mean: local {round(statistics.mean(len(r[key]['issues']) for r in ok), 2) if ok else None}, "
        f"deepseek {round(statistics.mean(len(r['deepseek_issues']) for r in results), 2)}.", "",
    ]


def summarize(results: List[Dict[str, Any]], model: str) -> str:
    """Agreement and speed per prompt variant, then every slide's issues side by side."""
    lines = ["# Local slide review vs deepseek-v4-flash", ""]
    lines += agreement(results, "local", model, "Production prompt")
    lines += agreement(results, "strict", model, "Strict layout checklist prompt")
    lines += ["Agreement on accept/reject is not enough on its own: read the side-by-side issues below and check them "
              "against the screenshots (outputs/vlm_review_test/shots/<id>.png on the machine that downloaded them).", ""]
    for r in results:
        lines += [f"## {r['id']}", f"{r['label']}", "", "**deepseek:**"]
        lines += [f"- {i}" for i in r["deepseek_issues"]] or ["- (accepted)"]
        for key in VARIANTS:
            lines += ["", f"**{key}** ({r[key].get('seconds')} s):"]
            if "error" in r[key]:
                lines.append(f"- ERROR: {r[key]['error']}")
            else:
                lines += [f"- {i}" for i in r[key]["issues"]] or ["- (accepted)"]
        lines.append("")
    return "\n".join(lines)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("--base-url", required=True)
    p.add_argument("--model", required=True)
    p.add_argument("--manifest", default=os.path.join(HERE, "manifest.json"))
    p.add_argument("--shots-root", help="Directory holding the manifest's tmp/slide_review paths "
                                        "(default: the manifest's source_job_dir)")
    p.add_argument("--shots-dir", help="Flat folder of <id>.png screenshots (outputs/vlm_review_test/shots), "
                                       "used instead of --shots-root, e.g. when copied to an NRP volume")
    p.add_argument("--out", default="vlm_review_test")
    p.add_argument("--workers", type=int, default=4, help="reviews sent to the server at once")
    args = p.parse_args()

    manifest = json.load(open(args.manifest, encoding="utf-8"))
    root = args.shots_root or manifest["source_job_dir"]
    client = instructor.from_openai(OpenAI(base_url=args.base_url, api_key="local", timeout=600),
                                    mode=instructor.Mode.JSON_SCHEMA)
    os.makedirs(args.out, exist_ok=True)
    items = manifest["items"]

    shot_of = {i["shot"]: i["id"] for i in items}
    path = (lambda p: os.path.join(args.shots_dir, f"{shot_of[p]}.png")) if args.shots_dir else (lambda p: os.path.join(root, p))

    def one(n: int) -> Dict[str, Any]:
        item = items[n]
        earlier = [path(p) for p in earlier_shots(items, n)]
        verdicts = {key: review(client, args.model, item, path(item["shot"]), system, earlier)
                    for key, system in VARIANTS.items()}
        return {**item, "earlier_shots": len(earlier), **verdicts}

    results = []
    # --workers requests at once: the server batches them (run 1 used ~7% of its KV cache serving one at a time)
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        for n, result in enumerate(pool.map(one, range(len(items))), 1):
            results.append(result)
            status = lambda v: v.get("error") or ("accepted" if not v["issues"] else f"{len(v['issues'])} issues")
            print(f"[{n}/{len(items)}] {result['id']} ({result['earlier_shots']} earlier): "
                  + ", ".join(f"{key} {status(result[key])} in {result[key]['seconds']} s" for key in VARIANTS)
                  + f" (deepseek: {len(result['deepseek_issues']) or 'accepted'})", flush=True)
            with open(os.path.join(args.out, "results.json"), "w", encoding="utf-8") as f:
                json.dump({"model": args.model, "results": results}, f, indent=1)  # rewritten each slide: survives a kill
    with open(os.path.join(args.out, "summary.md"), "w", encoding="utf-8") as f:
        f.write(summarize(results, args.model))
    print(f"Done -> {args.out}/summary.md")


if __name__ == "__main__":
    main()
