"""Bloom alignment: each objective's level, which tests assess it, and rule-based flags on the result."""
import ast
from typing import Any, Dict, List

from digitalagedu.core.eval.llm import clip, structured
from digitalagedu.core.eval.schemas import BLOOM_LEVELS, BloomLevels, TestMap
from digitalagedu.core.llm.gates import iter_test_functions

# Levels a unit test can't assess (recall and explanation): reported apart from real coverage gaps
UNTESTABLE = {"remember", "understand"}


def test_names(test_code: str) -> List[str]:
    """test_* functions and test_* methods of classes in the test file ([] when it can't be parsed)."""
    try:
        tree = ast.parse(test_code)
    except SyntaxError:
        return []
    return [name for name, _ in iter_test_functions(tree)]


def classify(client, model: str, objectives: List[str]) -> BloomLevels:
    listed = "\n".join(f"{i}. {o}" for i, o in enumerate(objectives))
    return structured(client, model, BloomLevels,
                      "You classify learning objectives by Bloom's revised taxonomy "
                      "(remember, understand, apply, analyze, evaluate, create), judging the task the student must "
                      "perform, not just the verb.",
                      f"Classify each objective, in order:\n{listed}",
                      max_tokens=8192)  # good replies took <3k tokens: a runaway fails in half the time, then retries


def map_tests(client, model: str, objectives: List[str], test_code: str) -> TestMap:
    names = test_names(test_code)
    listed = "\n".join(f"{i}. {o}" for i, o in enumerate(objectives))
    which = (f"Map every one of these tests: {names}." if names
             else "The file has no test_ functions; map its top-level asserts as test_name 'module'.")
    return structured(client, model, TestMap,
                      "You audit whether unit tests assess stated learning objectives. Quote the assert lines verbatim. "
                      "A test assesses an objective only if passing it requires the skill the objective names.",
                      f"LEARNING OBJECTIVES (0-based):\n{listed}\n\n{which}\n\nTEST FILE:\n```python\n{clip(test_code)}\n```")


def flags(levels: List[str], mappings: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Pure rule-based checks on the classified levels and the test mapping (dicts as TestMapping.model_dump()).
    Levels are reported (in evaluate's `objectives`), never capped by student level: no policy says which levels a
    grade may reach (decided 2026-11-21, dev/plans/quality_gates.md)."""
    rank = {lvl: i for i, lvl in enumerate(BLOOM_LEVELS)}
    covered: Dict[int, List[Dict[str, Any]]] = {}
    for m in mappings:
        idx = m.get("objective_index")
        if isinstance(idx, int) and 0 <= idx < len(levels):
            covered.setdefault(idx, []).append(m)
    untested = [i for i in range(len(levels)) if i not in covered]
    return {
        "objective_count": len(levels),
        "untested_objectives": [i for i in untested if levels[i] not in UNTESTABLE],
        "untestable_by_unit_test": [i for i in untested if levels[i] in UNTESTABLE],
        "low_level_tests_only": [i for i, ms in covered.items()
                                 if rank[levels[i]] >= rank["analyze"] and all(m["checks_only_structure"] for m in ms)],
        "unmapped_tests": [m["test_name"] for m in mappings if m.get("objective_index") is None],
        "coverage": (len(levels) - len(untested)) / len(levels) if levels else None,
    }


def evaluate(client, model: str, objectives: List[str], test_code: str) -> Dict[str, Any]:
    if not objectives:
        return {"error": "no learning objectives found in the trace"}
    classified = classify(client, model, objectives).objectives
    # The model may return fewer or reordered entries; align by position and pad so the flags stay index-safe
    levels = [classified[i].level if i < len(classified) else "apply" for i in range(len(objectives))]
    mappings = [m.model_dump() for m in map_tests(client, model, objectives, test_code).tests]
    return {
        "objectives": [{"objective": o, "level": lvl, "rationale": classified[i].rationale if i < len(classified) else None}
                       for i, (o, lvl) in enumerate(zip(objectives, levels))],
        "classified_count": len(classified),  # < objective count means padded levels ("apply"); read flags with care
        "test_map": mappings,
        "flags": flags(levels, mappings),
    }
