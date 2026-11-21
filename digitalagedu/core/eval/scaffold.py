"""Step-by-step TODO check: fills the starter's stub functions from the verified solution one at a time, in file
order (the order a student works through them), and runs the week's tests after each. Good scaffolding unlocks tests
gradually: none pass on the bare starter, each step unlocks some, and all pass once every stub is filled. No LLM."""
import ast
import os
import re
from typing import Any, Dict, List, Optional, Sequence, Tuple

from digitalagedu.core.eval.bloom import test_names
from digitalagedu.core.llm.generation_trace import attribute_failures
from digitalagedu.core.llm.sandbox import run_in_sandbox

_FUNCS = (ast.FunctionDef, ast.AsyncFunctionDef)


def _defs(code: str) -> Dict[str, ast.AST]:
    """Top-level functions and classes, and class methods, by name (f, Class, Class.method)."""
    found = {}
    for node in ast.parse(code).body:
        if isinstance(node, _FUNCS + (ast.ClassDef,)):
            found[node.name] = node
        if isinstance(node, ast.ClassDef):
            found.update({f"{node.name}.{sub.name}": sub for sub in node.body if isinstance(sub, _FUNCS)})
    return found


def _span(node: ast.AST) -> Tuple[int, int]:
    """1-based first and last line, decorators included."""
    return min([node.lineno] + [d.lineno for d in node.decorator_list]), node.end_lineno


def _stubs(starter: str) -> List[str]:
    """Functions and methods the student must write (a TODO or NotImplementedError in them), in file order."""
    lines = starter.splitlines()
    found = []
    for name, node in sorted(_defs(starter).items(), key=lambda kv: _span(kv[1])[0]):
        if isinstance(node, _FUNCS):
            start, end = _span(node)
            text = "\n".join(lines[start - 1:end])
            if "TODO" in text or "NotImplementedError" in text:
                found.append(name)
    return found


def fill(starter: str, solution: str, names: Sequence[str], extra: Sequence[str] = ()) -> str:
    """The starter with `names` replaced by the solution's versions, plus the solution's `extra` top-level defs
    appended (helpers the starter left out, which the filled functions may call).
    shortcut: copies the solution's lines as they are, so a method indented differently in the two files won't
    compile (that step then shows every test failing); re-indent the block if that turns up."""
    lines, sol_lines = starter.splitlines(), solution.splitlines()
    starter_defs, sol_defs = _defs(starter), _defs(solution)
    for name in sorted(names, key=lambda n: _span(starter_defs[n])[0], reverse=True):  # bottom-up keeps line numbers valid
        a, b = _span(starter_defs[name])
        c, d = _span(sol_defs[name])
        lines[a - 1:b] = sol_lines[c - 1:d]
    for name in extra:
        c, d = _span(sol_defs[name])
        lines += ["", ""] + sol_lines[c - 1:d]
    return "\n".join(lines) + "\n"


def _short(test: str) -> str:
    return test.split(".")[-1]  # failures are logged as test_x, bloom.test_names gives Class.test_x


def _passing(code: str, tests: str, all_tests: List[str], module_id: str, fixture_dirs: Sequence[str],
             timeout: int) -> Tuple[Optional[List[str]], Optional[str]]:
    """(tests that pass, the test that hung). Passing is None after a timeout: the tests after the hung one never ran."""
    ok, log = run_in_sandbox(code, tests, module_id=module_id, artifact_sources=list(fixture_dirs), timeout=timeout)
    if ok:
        return list(all_tests), None
    failures = attribute_failures(log)
    hung = next((f["test"] for f in failures if "timed out" in f["exception"]), None)
    if hung:
        return None, hung
    if any(f["test"] == "<script>" for f in failures):  # the file failed on import: nothing ran
        return [], None
    failing = {_short(f["test"]) for f in failures}
    return [t for t in all_tests if t not in failing], None


def check(starter: str, solution: str, shipped_tests: str, module_id: str, fixture_dirs: Sequence[str] = (),
          timeout: int = 300) -> Dict[str, Any]:
    """Runs the tests on the bare starter, then after filling each stub in turn. 300 s per run by default, not the
    generation sandbox's 120 s: here a timeout only costs an unknown step, and the check isn't on the run's clock."""
    # The shipped tests import the student's <id>_exercise; the sandbox serves the code under test as <id>_solution
    tests = re.sub(rf"\b{re.escape(module_id)}_exercise\b", f"{module_id}_solution", shipped_tests)
    try:
        stubs, starter_defs, sol_defs = _stubs(starter), _defs(starter), _defs(solution)
    except SyntaxError as err:
        return {"error": f"starter or solution does not parse: {err}"}
    all_tests = [_short(t) for t in test_names(tests)]
    result: Dict[str, Any] = {
        "tests": all_tests,
        "stubs": [n for n in stubs if n in sol_defs],
        "stubs_without_solution": [n for n in stubs if n not in sol_defs],
        # Helpers the student must write with no stub to guide them; added to every step so each stub is measured alone
        "solution_only_defs": [n for n, node in sol_defs.items() if "." not in n and n not in starter_defs],
        "steps": [],
    }
    if all_tests:  # the bare starter runs even with no stubs: a starter that passes everything gives the work away
        previous: Optional[List[str]] = None
        for k in range(len(result["stubs"]) + 1):
            code = fill(starter, solution, result["stubs"][:k], result["solution_only_defs"])
            passing, hung = _passing(code, tests, all_tests, module_id, fixture_dirs, timeout)
            newly = sorted(set(passing) - set(previous)) if passing is not None and previous is not None else None
            result["steps"].append({"filled": result["stubs"][k - 1] if k else None, "passing": passing,
                                    "newly_passing": newly, "timed_out": hung})
            previous = passing
    result["flags"] = flags(result)
    return result


def flags(result: Dict[str, Any]) -> Dict[str, Any]:
    """Rule-based reading of the steps; shares are None when the step they need timed out or nothing ran."""
    steps, n = result["steps"], len(result["tests"])
    share = lambda step: len(step["passing"]) / n if step["passing"] is not None and n else None
    unlocks = [s["newly_passing"] for s in steps[1:] if s["newly_passing"] is not None]
    known = [s for s in steps if s["passing"] is not None]
    return {
        "no_stubs": not result["stubs"],
        "starter_pass_share": share(steps[0]) if steps else None,  # should be ~0: these tests assess no student work
        "pass_without_student_work": steps[0]["passing"] if steps else None,
        "all_filled_pass_share": share(steps[-1]) if steps else None,  # should be 1: below it, the starter's fixed code is off
        "fail_with_all_filled": sorted(set(result["tests"]) - set(steps[-1]["passing"]))
                                if steps and steps[-1]["passing"] is not None else None,
        # A stub can legitimately unlock nothing when its tests also need a later stub; many such steps is the flag
        "steps_unlocking_nothing": [s["filled"] for s in steps[1:] if s["newly_passing"] == []],
        "largest_unlock_share": max((len(u) for u in unlocks), default=0) / n if unlocks and n else None,
        # Tests that passed and then failed after a later stub was filled
        "regressions": sorted({t for a, b in zip(known, known[1:]) for t in set(a["passing"]) - set(b["passing"])}),
        "timed_out_steps": sum(s["timed_out"] is not None for s in steps),
    }


def check_week(module_dir: str, fixture_dirs: Sequence[str] = (), timeout: int = 300) -> Dict[str, Any]:
    """check() on a finished week's exercise.py, solution.py and test.py."""
    clean_id = os.path.basename(module_dir)

    def read(suffix: str) -> str:
        path = os.path.join(module_dir, f"{clean_id}_{suffix}")
        if not os.path.isfile(path):
            return ""
        with open(path, encoding="utf-8", errors="replace") as f:
            return f.read()

    return check(read("exercise.py"), read("solution.py"), read("test.py"), clean_id, fixture_dirs, timeout)
