"""Reads a finished week from disk as a student sees it (no reference solution, logs or Arbiter verdicts)."""
import glob
import json
import os
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass
class WeekBundle:
    module_id: str
    week: int
    module_dir: str
    overview: str
    exercise: str
    tests: str
    deck_path: str
    objectives: List[str]
    formulation: Dict[str, Any] = field(default_factory=dict)


def _read(path: str) -> str:
    if not os.path.isfile(path):
        return ""
    with open(path, encoding="utf-8", errors="replace") as f:
        return f.read()


def latest_formulation(module_dir: str) -> Dict[str, Any]:
    """Agent 0's final contract: the highest-numbered trace/problem_formulation_vN.json ({} if none)."""
    versions = glob.glob(os.path.join(module_dir, "trace", "problem_formulation_v*.json"))
    if not versions:
        return {}
    newest = max(versions, key=lambda p: int(re.search(r"_v(\d+)\.json$", p).group(1)))
    return json.loads(_read(newest))


def list_finished_weeks(exercises_dir: str) -> List[str]:
    """Module dirs whose sandbox verification passed and whose deck exists, in week order."""
    found = []
    for module_dir in sorted(glob.glob(os.path.join(exercises_dir, "Week_*", "*"))):
        clean_id = os.path.basename(module_dir)
        verification = os.path.join(module_dir, f"{clean_id}_verification.json")
        deck = os.path.join(module_dir, f"{clean_id}_presentation.pptx")
        if os.path.isfile(verification) and os.path.isfile(deck) and json.loads(_read(verification)).get("verified"):
            found.append(module_dir)
    return found


def load_week(module_dir: str) -> WeekBundle:
    clean_id = os.path.basename(module_dir)
    week = int(re.search(r"Week_(\d+)", module_dir).group(1))
    out = lambda suffix: os.path.join(module_dir, f"{clean_id}_{suffix}")
    formulation = latest_formulation(module_dir)
    return WeekBundle(
        module_id=clean_id, week=week, module_dir=module_dir,
        overview=_read(out("overview.md")), exercise=_read(out("exercise.py")), tests=_read(out("test.py")),
        deck_path=out("presentation.pptx"), objectives=list(formulation.get("learning_objectives") or []),
        formulation=formulation,
    )


def deck_text(deck_path: str) -> List[str]:
    """Each slide's visible text, in order (the fallback when the deck can't be rendered)."""
    from pptx import Presentation
    slides = []
    for slide in Presentation(deck_path).slides:
        parts = [shape.text_frame.text.strip() for shape in slide.shapes if shape.has_text_frame]
        slides.append("\n".join(p for p in parts if p))
    return slides


def render_slides(deck_path: str, out_dir: str) -> Tuple[List[str], List[str]]:
    """(slide PNGs, slide texts) for the final deck; PNGs are [] when LibreOffice can't render it."""
    from digitalagedu.core.llm.slide_render import render_deck_pngs
    os.makedirs(out_dir, exist_ok=True)
    return render_deck_pngs(deck_path, out_dir), deck_text(deck_path)
