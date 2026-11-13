"""Rubric judge: scores one week on digitalagedu/core/eval/rubric.yaml, with evidence before each score."""
import os
from typing import Any, Dict, List

import yaml

from digitalagedu.core.eval.llm import clip, structured, user_content
from digitalagedu.core.eval.load import WeekBundle
from digitalagedu.core.eval.schemas import RubricVerdict

RUBRIC_PATH = os.path.join(os.path.dirname(__file__), "rubric.yaml")  # in the package: the image copies no configs/


def load_rubric(path: str = RUBRIC_PATH) -> List[Dict[str, Any]]:
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)["dimensions"]


def rubric_text(rubric: List[Dict[str, Any]]) -> str:
    return "\n\n".join(
        f"- {d['id']}: {d['question']}\n" + "\n".join(f"    {k}: {v}" for k, v in d["anchors"].items())
        for d in rubric
    )


def score_week(client, model: str, bundle: WeekBundle, slide_pngs: List[str], slide_texts: List[str],
               run_facts: str, student_level: str, rubric: List[Dict[str, Any]]) -> Dict[str, Any]:
    objectives = "\n".join(f"- {o}" for o in bundle.objectives) or "(none recorded)"
    slides = ("The slide screenshots follow, in order." if slide_pngs else
              "Slides could not be rendered; their text, in order:\n"
              + "\n\n".join(f"[Slide {i + 1}]\n{t}" for i, t in enumerate(slide_texts)))
    text = (
        f"STUDENT LEVEL: {student_level}\nWEEK {bundle.week}: {bundle.module_id}\n\n"
        f"RUN DATA THE WEEK SHOULD TEACH FROM:\n{clip(run_facts, 4000)}\n\n"
        f"STATED LEARNING OBJECTIVES:\n{objectives}\n\n"
        f"STUDENT OVERVIEW:\n{clip(bundle.overview, 8000)}\n\n"
        f"STARTER EXERCISE:\n```python\n{clip(bundle.exercise)}\n```\n\n"
        f"UNIT TESTS (the exercise's assessment):\n```python\n{clip(bundle.tests)}\n```\n\n{slides}"
    )
    verdict = structured(
        client, model, RubricVerdict,
        "You are an experienced instructor reviewing one week of course materials before using them. Score every "
        "rubric dimension below from 1 to 5 using its anchors. For each, first cite specific evidence (quotes, slide "
        "numbers, test names), then give the score. Polish and length are not quality: judge what students would "
        f"learn.\n\nRUBRIC:\n{rubric_text(rubric)}",
        user_content(text, slide_pngs),
    )
    wanted = [d["id"] for d in rubric]
    got = {s.dimension: s.model_dump() for s in verdict.scores if s.dimension in wanted}
    return {"scores": got, "missing_dimensions": [d for d in wanted if d not in got],
            "judged_without_images": not slide_pngs}
